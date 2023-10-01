
from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory, make_response
import bcrypt
from flask_login import login_required, login_user, logout_user, current_user
import logging
from logging.handlers import RotatingFileHandler
import os
import json
from pw_models import dict_sess, dict_engine, text, Users

from app_package.bp_users.utils import send_reset_email, send_confirm_email
import datetime
import requests
# from app_package import secure_headers

#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_bp_users = logging.getLogger(__name__)
logger_bp_users.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','bp_users.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_bp_users.addHandler(file_handler)
logger_bp_users.addHandler(stream_handler)


salt = bcrypt.gensalt()


bp_users = Blueprint('bp_users', __name__)
sess_users = dict_sess['sess_users']

# @bp_users.before_request
# def before_request():
#     logger_bp_users.info("- in bp_users.before_request ")
#     ###### Keeps user logged in 31 days ########
#     session.permanent = True
#     current_app.permanent_session_lifetime = datetime.timedelta(days=31)
#     session.modified = True
#     logger_bp_users.info(f"!--> current_app.permanent_session_lifetime: {current_app.permanent_session_lifetime}")
#     ###### END Keeps user logged in 31 days ######## 
#     ###### TEMPORARILY_DOWN: redirects to under construction page ########
#     if os.environ.get('TEMPORARILY_DOWN') == '1':
#         if request.url != request.url_root + url_for('bp_main.temporarily_down')[1:]:
#             # logger_bp_users.info("*** (logger_bp_users) Redirected ")
#             logger_bp_users.info(f'- request.referrer: {request.referrer}')
#             logger_bp_users.info(f'- request.url: {request.url}')
#             return redirect(url_for('bp_main.temporarily_down'))



@bp_users.route('/login', methods = ['GET', 'POST'])
def login():
    print('- in login')
    if current_user.is_authenticated:
        return redirect(url_for('bp_blog.blog_user_home'))
    
    logger_bp_users.info(f'- in login route')

    page_name = 'Login'
    if request.method == 'POST':
        # session.permanent = True
        formDict = request.form.to_dict()
        print(f"formDict: {formDict}")
        email = formDict.get('email')

        user = sess_users.query(Users).filter_by(email=email).first()

        # verify password using hash
        password = formDict.get('password')

        if user:
            if password:
                if bcrypt.checkpw(password.encode(), user.password):
                    login_user(user)

                    return redirect(url_for('bp_blog.blog_user_home'))
                else:
                    flash('Password or email incorrectly entered', 'warning')
            else:
                flash('Must enter password', 'warning')
        # elif formDict.get('btn_login_as_guest'):
        #     user = sess_users.query(Users).filter_by(id=2).first()
        #     login_user(user)

        #     return redirect(url_for('dash.dashboard', dash_dependent_var='steps'))
        else:
            flash('No user by that name', 'warning')


    return render_template('users/login.html', page_name = page_name)

@bp_users.route('/register', methods = ['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('bp_main.user_home'))
    page_name = 'Register'
    if request.method == 'POST':
        formDict = request.form.to_dict()
        new_email = formDict.get('email')

        check_email = sess_users.query(Users).filter_by(email = new_email).all()

        logger_bp_users.info(f"check_email: {check_email}")

        if len(check_email)==1:
            flash(f'The email you entered already exists you can sign in or try another email.', 'warning')
            return redirect(url_for('bp_users.register'))

        hash_pw = bcrypt.hashpw(formDict.get('password').encode(), salt)
        new_user = Users(email = new_email, password = hash_pw)
        sess_users.add(new_user)
        sess_users.commit()

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
    # form = RequestResetForm()
    # if form.validate_on_submit():
    if request.method == 'POST':
        formDict = request.form.to_dict()
        email = formDict.get('email')
        user = sess_users.query(Users).filter_by(email=email).first()
        if user:
        # send_reset_email(user)
            logger_bp_users.info('Email reaquested to reset: ', email)
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
    logger_bp_users.info('user::', user)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('bp_users.reset_password'))
    if request.method == 'POST':

        formDict = request.form.to_dict()
        if formDict.get('password_text') != '':
            hash_pw = bcrypt.hashpw(formDict.get('password_text').encode(), salt)
            user.password = hash_pw
            sess_users.commit()
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





