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

    # Read last 7 days activities summary
    recent_activities = None
    try:
        project_resources_root = current_app.config.get('PROJECT_RESOURCES_ROOT')
        summary_file_path = os.path.join(project_resources_root, 'left-off-summarizer', 'last-7-days-activities-summary.md')

        if os.path.exists(summary_file_path):
            with open(summary_file_path, 'r', encoding='utf-8') as f:
                recent_activities = f.read().strip()
            logger_bp_main.info(f"Successfully loaded recent activities summary from {summary_file_path}")
        else:
            logger_bp_main.warning(f"Recent activities summary file not found: {summary_file_path}")
    except Exception as e:
        logger_bp_main.error(f"Error reading recent activities summary: {str(e)}")

    return render_template('main/home.html', recent_activities=recent_activities)

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