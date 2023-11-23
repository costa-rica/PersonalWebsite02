from flask import current_app, url_for
from flask_login import current_user
import json
from flask_mail import Message
from app_package import mail
import os
# from werkzeug.utils import secure_filename
# import zipfile
# import shutil
import logging
from logging.handlers import RotatingFileHandler

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
