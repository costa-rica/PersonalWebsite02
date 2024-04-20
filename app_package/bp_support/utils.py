from flask import current_app, url_for
from flask_login import current_user
import json
from flask_mail import Message
from app_package import mail
import os
from app_package._common.utilities import custom_logger


logger_bp_support = custom_logger('bp_support.log')


def send_message_to_nick(name, email, message):
    logger_bp_support.info("Nick email:")
    logger_bp_support.info(os.environ.get('MAIL_NICK_GMAIL'))
    subject = "Open Mindset Support"
    msg = Message(subject,
        sender=current_app.config.get('MAIL_USERNAME'),
        recipients=[current_app.config.get('MAIL_NICK_GMAIL')])
    msg.body = f'Message from: {name} \n email: {email} \n {message}'
    mail.send(msg)

def send_confirm_email(name, email, message):
    msg = Message('Message successfully sent',
        sender=current_app.config.get('MAIL_USERNAME'),
        recipients=[email])
    msg.body = f'Hi {name}, \n Thanks for your message: \n {message}'
    mail.send(msg)
