from flask import Blueprint
from flask import render_template, send_from_directory, current_app, url_for,  \
    get_flashed_messages, request, flash, redirect
# from flask_login import login_required, login_user, logout_user, current_user
import os
import logging
from logging.handlers import RotatingFileHandler
import jinja2
import requests
from app_package.bp_support.utils import send_message_to_nick, send_confirm_email
# from app_package import secure_headers

bp_support = Blueprint('bp_support', __name__)

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

logger_bp_support = logging.getLogger(__name__)
logger_bp_support.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','support_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

logger_bp_support.addHandler(file_handler)
logger_bp_support.addHandler(stream_handler)




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

    # send message to nick@dashanddata.com
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


