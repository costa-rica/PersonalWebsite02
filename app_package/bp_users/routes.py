
from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory, make_response, \
    g
import bcrypt
from flask_login import login_required, login_user, logout_user, current_user
import logging
from logging.handlers import RotatingFileHandler
import os
import json
# from pw_models import dict_sess, dict_engine, text, Users
from pw_models import DatabaseSession, text, Users

from app_package.bp_users.utils import send_reset_email, send_confirm_email
import datetime
import requests
# from app_package import secure_headers
from app_package._common.utilities import custom_logger, wrap_up_session



logger_bp_users = custom_logger('bp_users.log')
bp_users = Blueprint('bp_users', __name__)
# sess_users = dict_sess['sess_users']


@bp_users.before_request
def before_request():
    logger_bp_users.info("-- def before_request() --")
    # Assign a new session to a global `g` object, accessible during the whole request
    g.db_session = DatabaseSession()
    
    # Use getattr to safely access g.referrer, defaulting to None if it's not set
    if getattr(g, 'referrer', None) is None:
        if request.referrer:
            g.referrer = request.referrer
        else:
            g.referrer = "No referrer"
    
    logger_bp_users.info("-- def before_request() END --")


@bp_users.route('/login', methods = ['GET', 'POST'])
def login():
    logger_bp_users.info('- in login')
    db_session = g.db_session
    if current_user.is_authenticated:
        return redirect(url_for('bp_blog.manage_blogposts'))
    
    logger_bp_users.info(f'- in login route')

    page_name = 'Login'
    if request.method == 'POST':
        # session.permanent = True
        formDict = request.form.to_dict()
        print(f"formDict: {formDict}")
        email = formDict.get('email')

        user = db_session.query(Users).filter_by(email=email).first()

        # verify password using hash
        password = formDict.get('password')

        if user:
            if password:
                if bcrypt.checkpw(password.encode(), user.password):
                    login_user(user)

                    return redirect(url_for('bp_blog.manage_blogposts'))
                else:
                    flash('Password or email incorrectly entered', 'warning')
            else:
                flash('Must enter password', 'warning')

        else:
            flash('No user by that name', 'warning')


    return render_template('users/login.html', page_name = page_name)

@bp_users.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('bp_blog.blog_home'))
    db_session = g.db_session
    page_name = 'Register'
    print("--- ACCEPTED_EMAILS ---")
    print(current_app.config.get('ACCEPTED_EMAILS'))
    print(type(current_app.config.get('ACCEPTED_EMAILS')))


    if request.method == 'POST':
        formDict = request.form.to_dict()
        new_email = formDict.get('email')

        if new_email not in current_app.config.get('ACCEPTED_EMAILS'):
            flash("This email is not permitted to have an account", "warning")
            return redirect(url_for('bp_main.home'))

        check_email = db_session.query(Users).filter_by(email = new_email).all()

        logger_bp_users.info(f"check_email: {check_email}")

        if len(check_email)==1:
            flash(f'The email you entered already exists you can sign in or try another email.', 'warning')
            return redirect(url_for('bp_users.register'))

        hash_pw = bcrypt.hashpw(formDict.get('password').encode(), bcrypt.gensalt())
        new_user = Users(email = new_email, password = hash_pw)
        db_session.add(new_user)
        # db_session.commit() - teardown_appcontext will auto-commit

        # # /check_invite_json
        # headers = {'Content-Type': 'application/json'}
        # payload={}
        # payload['TR_VERIFICATION_PASSWORD']=current_app.config.get("TR_VERIFICATION_PASSWORD")
        # result = requests.request('POST',current_app.config.get("API_URL") + "/check_invite_json",headers= headers, data=str(json.dumps(payload)))

        # Send email confirming succesfull registration
        try:
            send_confirm_email(new_email)
        except:
            flash(f'Problem with email: {new_email}', 'warning')
            return redirect(url_for('bp_users.login'))

        #log user in
        print('--- new_user ---')
        print(new_user)
        login_user(new_user)
        flash(f'Succesfully registered: {new_email}', 'info')
        return redirect(url_for('bp_main.home'))

    return render_template('users/register.html', page_name = page_name)

@bp_users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('bp_main.home'))

@bp_users.route('/reset_password', methods = ["GET", "POST"])
def reset_password():
    page_name = 'Request Password Change'
    if current_user.is_authenticated:
        return redirect(url_for('bp_main.user_home'))
    db_session = g.db_session
    if request.method == 'POST':
        formDict = request.form.to_dict()
        email = formDict.get('email')
        user = db_session.query(Users).filter_by(email=email).first()
        if user:
        # send_reset_email(user)
            logger_bp_users.info(f'Email reaquested to reset: {email}')
            send_reset_email(user)
            flash('Email has been sent with instructions to reset your password','info')
            # return redirect(url_for('bp_users.login'))
        else:
            flash('Email has not been registered with What Sticks','warning')

        return redirect(url_for('bp_users.reset_password'))
    return render_template('users/reset_request.html', page_name = page_name)

@bp_users.route('/reset_password/<token>', methods = ["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('bp_main.user_home'))
    user = Users.verify_reset_token(token)
    logger_bp_users.info(f'user:: {user}')
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('bp_users.reset_password'))
    if request.method == 'POST':
        db_session = g.db_session
        formDict = request.form.to_dict()
        if formDict.get('password_text') != '':
            # Re-query user with active session to avoid detached object issue
            active_user = db_session.query(Users).filter_by(id=user.id).first()
            hash_pw = bcrypt.hashpw(formDict.get('password_text').encode(), bcrypt.gensalt())
            active_user.password = hash_pw
            # teardown_appcontext will auto-commit
            flash('Password successfully updated', 'info')
            return redirect(url_for('bp_users.login'))
        else:
            flash('Must enter non-empty password', 'warning')
            return redirect(url_for('bp_users.reset_token', token=token))

    return render_template('users/reset_request.html', page_name='Reset Password')


# ########################
# # recaptcha
# ########################

# @bp_users.route("/sign-user-up", methods=['POST'])
# def sign_up_user():
#     # print(request.form)
#     secret_response = request.form['g-recaptcha-response']

#     verify_response = requests.post(url=f"{current_app.config.get('VERIFY_URL_CAPTCHA')}?secret={current_app.config.get('SECRET_KEY_CAPTCHA')}&response={secret_response}").json()
#     print(verify_response)
#     if verify_response['success'] == False or verify_response['score'] < 0.5:
#         abort(401)

#     formDict = request.form.to_dict()
#     print(formDict)
    
#     # get email, name and message

#     senders_name = formDict.get('name')
#     senders_email = formDict.get('email')
#     senders_message = formDict.get('message')

#     #send message to nick@dashanddata.com

#     # Send email confirming succesfully sent message to nick@dashanddata.com
#     try:
#         send_message_to_nick(senders_name, senders_email, senders_message)
#     except:
#         print('*** not successsuflly send_message_to_nick ***')
#     try:
#         send_confirm_email(senders_name, senders_email, senders_message)
#     except:
#         print('*** not successsuflly send_confirm_email')
#         flash(f'Problem with email: {new_email}', 'warning')
#         return redirect(url_for('bp_users.login'))



#     flash(f'Message has been sent to nick@dashanddata.com. A verification has been sent to your email as well.', 'success')
#     return redirect(url_for('bp_users.home'))


    # return redirect(url_for('home'))





