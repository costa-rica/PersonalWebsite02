from flask import Blueprint
from flask import render_template, send_from_directory, current_app, url_for,  \
    get_flashed_messages
from flask_login import login_required, login_user, logout_user, current_user
import os
import jinja2
from app_package._common.utilities import custom_logger, wrap_up_session

logger_bp_main = custom_logger('bp_main.log')

bp_main = Blueprint('bp_main', __name__)



@bp_main.route("/", methods=["GET","POST"])
def home():
    logger_bp_main.info(f"-- in home page route --")

    return render_template('main/home.html')

@bp_main.route("/about", methods=["GET","POST"])
def about():
    logger_bp_main.info(f"-- in about page route --")

    return render_template('main/about.html')

@bp_main.route("/resume", methods=["GET","POST"])
def resume():
    logger_bp_main.info(f"-- in resume route --")

    return render_template('main/resume.html')


@bp_main.route("/about_this_page", methods=["GET","POST"])
def about_this_page():
    logger_bp_main.info(f"-- in about page route --")

    return render_template('main/about_this_site.html')

@bp_main.route("/<page>", methods=["GET","POST"])
def pages(page):
    logger_bp_main.info(f"-- in {page} route --")

    return render_template('main/pages.html', page=page)


# Website Assets static data
@bp_main.route('/website_assets_favicon/<filename>')
def website_assets_favicon(filename):
    logger_bp_main.info("-- in website_assets_favicon -")
    dir = current_app.config.get('DIR_ASSETS_FAVICONS')
    logger_bp_main.info(f"file_to_server: {os.path.join(dir, filename)}")
    return send_from_directory(dir, filename)

# Media all images, videos, resume, etc.,
@bp_main.route('/media/<filename>')
def media(filename):
    logger_bp_main.info("-- in media -")
    dir = current_app.config.get('DIR_MEDIA')
    logger_bp_main.info(f"file_to_server: {os.path.join(dir, filename)}")
    return send_from_directory(dir, filename)

# # Media all images, videos, resume, etc.,
# @bp_main.route('/blog_icons/<filename>')
# def blog_icons(filename):
#     logger_bp_main.info("-- in blog_icons -")
#     dir = current_app.config.get('DIR_BLOG_ICONS')
#     logger_bp_main.info(f"file_to_server: {os.path.join(dir, filename)}")
#     return send_from_directory(dir, filename)



# never used
# # Website Files static data
# @bp_main.route('/website_files/<filename>')
# def website_files(filename):
#     print("-- entered website_files -")
#     return send_from_directory(current_app.config.get('DIR_DB_AUX_FILES_WEBSITE'), filename)