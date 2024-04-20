from pw_models import engine, DatabaseSession, text, Users
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_login import LoginManager
from pytz import timezone
from datetime import datetime
from flask import g

login_manager= LoginManager()
login_manager.login_view = 'bp_users.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    print("-- def load_user(user_id) --")
    # NOTE: This could be a problem we are usign this g.db_session cavalierly her
    g.db_session = DatabaseSession()
    user = g.db_session.query(Users).filter_by(id = user_id).first()
    print("* created a g.db_session *")
    return user

def teardown_appcontext(exception=None):
    print("- in teardown_appcontext")
    db_session = g.pop('db_session', None)
    if db_session is not None:
        if exception is None:
            db_session.commit()
        else:
            db_session.rollback()
        print("----- db_session.close() -----")
        db_session.close()



def custom_logger(logger_filename):
    """
    Creates and configures a logger with both file and stream handlers, while ensuring
    no duplicate handlers are added.
    :param logger_filename: Filename for the log file.
    :return: Configured logger object.
    """
    path_to_logs = os.path.join(os.environ.get('PROJECT_ROOT'), 'logs')
    full_log_path = os.path.join(path_to_logs, logger_filename)

    # Formatter setup
    formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
    formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

    # Logger setup
    logger = logging.getLogger(logger_filename)  # Use the filename as the logger's name
    logger.setLevel(logging.DEBUG)

    # Avoid adding multiple handlers to the same logger
    if not logger.handlers:  # Check if the logger already has handlers
        # File handler setup
        file_handler = RotatingFileHandler(full_log_path, mode='a', maxBytes=5*1024*1024, backupCount=2)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream handler setup
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter_terminal)
        logger.addHandler(stream_handler)

    return logger

def custom_logger_init():

    logging.Formatter.converter = timetz

    formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
    formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

    logger_init = logging.getLogger('__init__')
    logger_init.setLevel(logging.DEBUG)

    file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','__init__.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter_terminal)

    stream_handler_tz = logging.StreamHandler()

    logger_init.addHandler(file_handler)
    logger_init.addHandler(stream_handler)

    logging.getLogger('werkzeug').setLevel(logging.DEBUG)
    logging.getLogger('werkzeug').addHandler(file_handler)

    return logger_init

# timezone 
def timetz(*args):
    return datetime.now(timezone('Europe/Paris') ).timetuple()



#####################################
## OBE due to teardown_appcontext ###
#####################################
def wrap_up_session(db_session, custom_logger):
    custom_logger.info("- accessed wrap_up_session -")
    try:
        # perform some database operations
        db_session.commit()
        custom_logger.info("- perfomed: db_session.commit() -")
    except:
        db_session.rollback()  # Roll back the transaction on error
        custom_logger.info("- perfomed: db_session.rollback() -")
        raise
    finally:
        db_session.close()  # Ensure the session is closed in any case
        custom_logger.info("- perfomed: db_session.close() -")

