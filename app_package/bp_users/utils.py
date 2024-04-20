from flask import current_app, url_for
from flask_login import current_user
import json
from flask_mail import Message
from app_package import mail
import os
import shutil
import pandas as pd
from datetime import datetime
import csv
from app_package._common.utilities import custom_logger, wrap_up_session

logger_bp_users = custom_logger('bp_users.log')


def send_reset_email(user):
    token = user.get_reset_token()
    logger_bp_users.info(f"current_app.config.get(MAIL_USERNAME): {current_app.config.get('MAIL_USERNAME')}")
    msg = Message('Password Reset Request',
                  sender=current_app.config.get('MAIL_USERNAME'),
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('bp_users.reset_token', token=token, _external=True)}

If you did not make this request, ignore email and there will be no change
'''

    mail.send(msg)


def send_confirm_email(email):
    if os.environ.get('CONFIG_TYPE') == 'prod':
        logger_bp_users.info(f"-- sending email to {email} --")
        msg = Message('Welcome to Dashboards and Databases',
            sender=current_app.config.get('MAIL_USERNAME'),
            recipients=[email])
        msg.body = 'You have succesfully signed up.'
        mail.send(msg)
        logger_bp_users.info(f"-- email sent --")
    else :
        logger_bp_users.info(f"-- Non prod mode, no email sent --")


