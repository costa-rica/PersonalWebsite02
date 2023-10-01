from flask import Blueprint
from flask import render_template, current_app, request
# from app_package.utils import logs_dir
import os
import logging
from logging.handlers import RotatingFileHandler
import jinja2
import werkzeug

#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_bp_error = logging.getLogger(__name__)
logger_bp_error.setLevel(logging.DEBUG)


#where do we store logging information
file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),"logs",'error_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_bp_error.addHandler(file_handler)
logger_bp_error.addHandler(stream_handler)


bp_error = Blueprint('bp_error', __name__)

if os.environ.get('FLASK_CONFIG_TYPE')=='prod':
    @bp_error.app_errorhandler(400)
    def handle_400(err):
        logger_bp_error.info(f'@bp_error.app_errorhandler(400), err: {err}')
        logger_bp_error.info(f'- request.referrer: {request.referrer}')
        logger_bp_error.info(f'- request.url: {request.url}')
        error_message = "Something went wrong. Maybe you entered something I wasn't expecting?"
        return render_template('errors/error_template.html', error_number="400", error_message=error_message)
    #messaged copied from: https://www.pingdom.com/blog/the-5-most-common-http-errors-according-to-google/

    @bp_error.app_errorhandler(401)
    def handle_401(err):
        logger_bp_error.info(f'@bp_error.app_errorhandler(401), err: {err}')
        logger_bp_error.info(f'- request.referrer: {request.referrer}')
        logger_bp_error.info(f'- request.url: {request.url}')
        error_message = "This error happens when a website visitor tries to access a restricted web page but isn’t authorized to do so, usually because of a failed login attempt."
        return render_template('errors/error_template.html', error_number="401", error_message=error_message)
    #message copied form: https://www.pingdom.com/blog/the-5-most-common-http-errors-according-to-google/

    @bp_error.app_errorhandler(404)
    def handle_404(err):

        logger_bp_error.info(f'@bp_error.app_errorhandler(404), err: {err}')
        logger_bp_error.info(f'- request.referrer: {request.referrer}')
        logger_bp_error.info(f'- request.url: {request.url}')
        error_message = "This page doesn't exist. Check what was typed in the address bar."
        return render_template('errors/error_template.html', error_number="404", error_message=error_message, description = err.description)
    #404 occurs if address isnt' right

    @bp_error.app_errorhandler(500)
    def handle_500(err):
        logger_bp_error.info(f'@bp_error.app_errorhandler(500), err: {err}')
        logger_bp_error.info(f'- request.referrer: {request.referrer}')
        logger_bp_error.info(f'- request.url: {request.url}')
        error_message = f"Could be anything... ¯\_(ツ)_/¯  ... try again or send email to {current_app.config['MAIL_USERNAME']}."
        return render_template('errors/error_template.html', error_number="500", error_message=error_message)

    @bp_error.app_errorhandler(502)
    def handle_502(err):
        logger_bp_error.info(f'@bp_error.app_errorhandler(502), err: {err}')
        logger_bp_error.info(f'- request.referrer: {request.referrer}')
        logger_bp_error.info(f'- request.url: {request.url}')
        error_message = f"Could be anything... ¯\_(ツ)_/¯  ... try again or send email to {current_app.config['MAIL_USERNAME']}."
        return render_template('errors/error_template.html', error_number="502", error_message=error_message)


    @bp_error.app_errorhandler(AttributeError)
    @bp_error.app_errorhandler(KeyError)
    @bp_error.app_errorhandler(TypeError)
    @bp_error.app_errorhandler(FileNotFoundError)
    @bp_error.app_errorhandler(ValueError)
    # def error_key(FileNotFoundError):
    def error_key(e):
        error_message = f"Could be anything... ¯\_(ツ)_/¯  ... try again or send email to {current_app.config['MAIL_USERNAME']}."
        return render_template('errors/error_template_app_error.html', error_number="", error_message=e)


    @bp_error.app_errorhandler(jinja2.exceptions.TemplateNotFound)
    @bp_error.app_errorhandler(jinja2.exceptions.UndefinedError)
    @bp_error.app_errorhandler(werkzeug.routing.exceptions.BuildError)
    def error_key(e):
        error_message = f"Could be anything... ¯\_(ツ)_/¯  ... try again or send email to {current_app.config['MAIL_USERNAME']}."
        return render_template('errors/error_template_app_error.html', error_number="", error_message=e,
        error_message_2 = e)

