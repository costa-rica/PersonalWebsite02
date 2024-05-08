from flask import Flask
# from app_package.config import config
from ._common.config import config
import os
# import logging
# from logging.handlers import RotatingFileHandler
from pytz import timezone
from datetime import datetime
from pw_models import Base, engine
from ._common.utilities import login_manager, custom_logger_init, teardown_appcontext
from flask_mail import Mail
import secure

if not os.path.exists(os.path.join(os.environ.get('PROJECT_ROOT'),'logs')):
    os.makedirs(os.path.join(os.environ.get('PROJECT_ROOT'), 'logs'))


logger_init = custom_logger_init()

logger_init.info(f'--- Starting Flask Starter---')
TEMPORARILY_DOWN = "ACTIVE" if os.environ.get('TEMPORARILY_DOWN') == "1" else "inactive"
logger_init.info(f"- TEMPORARILY_DOWN: {TEMPORARILY_DOWN}")
logger_init.info(f"- FLASK_CONFIG_TYPE: {os.environ.get('FLASK_CONFIG_TYPE')}")
logger_init.info(f"- MAIL_NICK_GMAIL: {config.MAIL_NICK_GMAIL}")


mail = Mail()
secure_headers = secure.Secure()

def create_app(config_for_flask = config):
    app = Flask(__name__)
    app.teardown_appcontext(teardown_appcontext)
    app.config.from_object(config_for_flask)
    login_manager.init_app(app)
    mail.init_app(app)

    logger_init.info(f"- DB_ROOT: {config_for_flask.DB_ROOT}")

    ############################################################################
    # database
    create_folder(config_for_flask.DATABASE_ROOT)
    create_folder(config_for_flask.DIR_DB_UPLOAD)
    create_folder(config_for_flask.DIR_DB_DOWNLOAD)
    # create folders for PROJECT_RESOURCES
    create_folder(config_for_flask.PROJECT_RESOURCES_ROOT)
    ## website folders
    create_folder(config_for_flask.DIR_ASSETS)
    create_folder(config_for_flask.DIR_ASSETS_IMAGES)
    create_folder(config_for_flask.DIR_ASSETS_FAVICONS)
    ## blog folders
    create_folder(config_for_flask.DIR_BLOG)
    create_folder(config_for_flask.DIR_BLOG_POSTS)
    ## logs
    create_folder(config_for_flask.DIR_LOGS)
    ## media - all other videos and images
    create_folder(config_for_flask.DIR_MEDIA)
    ############################################################################


    ############################################################################
    ## Build Sqlite database files for DB_NAME_BLOGPOST
    
    if os.path.exists(os.path.join(config_for_flask.DB_ROOT,os.environ.get('DB_NAME_BLOGPOST'))):
        logger_init.info(f"db already exists: {os.path.join(config_for_flask.DB_ROOT,os.environ.get('DB_NAME_BLOGPOST'))}")
    else:
        # dict_base['Base_users'].metadata.create_all(dict_engine['engine_users'])
        Base.metadata.create_all(engine)
        logger_init.info(f"NEW db created: {os.path.join(config_for_flask.DB_ROOT,os.environ.get('DB_NAME_BLOGPOST'))}")

    logger_init.info(f"- SQL_URI_USERS: sqlite:///{config_for_flask.DB_ROOT}{os.environ.get('DB_NAME_BLOGPOST')}")

    from app_package.bp_main.routes import bp_main
    from app_package.bp_users.routes import bp_users
    from app_package.bp_error.routes import bp_error
    from app_package.bp_blog.routes import bp_blog
    from app_package.bp_support.routes import bp_support
    from app_package.bp_admin.routes import bp_admin

    app.register_blueprint(bp_main)
    app.register_blueprint(bp_users)
    app.register_blueprint(bp_error)
    app.register_blueprint(bp_blog)
    app.register_blueprint(bp_support)
    app.register_blueprint(bp_admin)

    return app

def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger_init.info(f"created: {folder_path}")
