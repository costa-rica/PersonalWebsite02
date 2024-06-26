from flask import Blueprint
from flask import render_template, send_from_directory, current_app, url_for,  \
    get_flashed_messages, request, flash, redirect
import os
import jinja2
import requests
from app_package.bp_support.utils import send_message_to_nick, send_confirm_email
from app_package._common.utilities import custom_logger

bp_support = Blueprint('bp_support', __name__)
logger_bp_support = custom_logger('bp_support.log')



@bp_support.route("/openmindset", methods=["GET","POST"])
def openmindset():
    logger_bp_support.info(f"-- in openmindset page route --")

    return render_template('support/openmindset.html', site_key=current_app.config.get('SITE_KEY_CAPTCHA'))

@bp_support.route("/openmindset_about", methods=["GET","POST"])
def openmindset_about():
    logger_bp_support.info(f"-- in openmindset_about page route --")

    return render_template('support/openmindsetAbout.html')


# @bp_main.route("/sign-user-up", methods=['POST'])
@bp_support.route("/send_me_a_message", methods=['POST'])
# def sign_up_user():
def send_me_a_message():
    # print(request.form)
    secret_response = request.form['g-recaptcha-response']

    verify_response = requests.post(
        url=f"{current_app.config.get('VERIFY_URL_CAPTCHA')}?secret={current_app.config.get('SECRET_KEY_CAPTCHA')}&response={secret_response}").json()
    print(verify_response)
    if verify_response['success'] == False or verify_response['score'] < 0.5:
        abort(401)

    formDict = request.form.to_dict()
    print("- formDict -")
    print(formDict)
    
    # get email, name and message
    senders_name = formDict.get('name')
    senders_email = formDict.get('email')
    senders_message = formDict.get('message')

    logger_bp_support.info("Nick email:")
    logger_bp_support.info(os.environ.get('MAIL_NICK_GMAIL'))

    # send message to os.environ.get('MAIL_NICK_GMAIL')
    try:
        send_message_to_nick(senders_name, senders_email, senders_message)
        logger_bp_support.info('- send_message_to_nick succeeded!')
    except:
        logger_bp_support.info('*** not successsuflly send_message_to_nick ***')
    # Send confirmation email to sender
    try:
        send_confirm_email(senders_name, senders_email, senders_message)
        logger_bp_support.info('- send_confirm_email succeeded!')
    except:
        logger_bp_support.info('*** not successsuflly send_confirm_email')
        flash(f'Problem with email: {senders_email}', 'warning')
        # return redirect(url_for('bp_users.login'))
        return redirect(url_for('bp_support.openmindset'))

    flash(f"Message has been sent to {current_app.config.get('MAIL_USERNAME')}. A verification has been sent to your email as well.", 'success')
    return redirect(url_for('bp_support.openmindset'))


@bp_support.route("/what_sticks_video01", methods=["GET","POST"])
def what_sticks_video01():
    logger_bp_support.info(f"-- in what_sticks_video01 page route --")

    return render_template('support/what_sticks_video01.html')

