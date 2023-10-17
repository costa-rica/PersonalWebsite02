from flask import Blueprint
from flask import render_template, send_from_directory, current_app, url_for,  \
    get_flashed_messages
import os
import logging
from logging.handlers import RotatingFileHandler
import jinja2


bp_main = Blueprint('bp_main', __name__)

formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

logger_bp_main = logging.getLogger(__name__)
logger_bp_main.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','main_routes.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

logger_bp_main.addHandler(file_handler)
logger_bp_main.addHandler(stream_handler)


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
    logger_bp_main.info(f"-- in about page route --")

    templates_path_lists = [
        os.path.join(current_app.config.root_path,"templates"),
        os.path.join(current_app.config.get('DIR_DB_AUX_FILES_WEBSITE_TEMPLATES') )
    ]

    templateLoader = jinja2.FileSystemLoader(searchpath=templates_path_lists)

    templateEnv = jinja2.Environment(loader=templateLoader)
    template_parent = templateEnv.get_template("main/resume.html")
    template_layout = templateEnv.get_template("_layout.html")
    template_post_index = templateEnv.get_template("resumeNRodriguez.html")

    return template_parent.render(template_layout=template_layout, template_post_index=template_post_index, \
        url_for=url_for, get_flashed_messages=get_flashed_messages)

@bp_main.route("/about_this_page", methods=["GET","POST"])
def about_this_page():
    logger_bp_main.info(f"-- in about page route --")

    return render_template('main/about_this_site.html')

@bp_main.route("/<page>", methods=["GET","POST"])
def pages(page):
    logger_bp_main.info(f"-- in {page} route --")

    return render_template('main/pages.html', page=page)

# Website Files static data
@bp_main.route('/website_files/<filename>')
def website_files(filename):
    print("-- entered website_files -")
    return send_from_directory(current_app.config.get('DIR_DB_AUX_FILES_WEBSITE'), filename)