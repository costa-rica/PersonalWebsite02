from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request,current_app, get_flashed_messages, \
    send_from_directory
import os
from datetime import datetime
import time
import logging
from logging.handlers import RotatingFileHandler

import jinja2
from flask_login import login_user, current_user, logout_user, login_required
from app_package.bp_blog.utils import create_blog_posts_list, replace_img_src_jinja, \
    get_title, sanitize_directory_name

from pw_models import dict_sess, text, Users, BlogPosts
from werkzeug.utils import secure_filename
import shutil
import zipfile
import jinja2
import re

#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_bp_blog = logging.getLogger(__name__)
logger_bp_blog.setLevel(logging.DEBUG)

#where do we store logging information
file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),"logs",'bp_blog.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_bp_blog.addHandler(file_handler)
logger_bp_blog.addHandler(stream_handler)

bp_blog = Blueprint('bp_blog', __name__)
sess_users = dict_sess['sess_users']

@bp_blog.route('/get_post_images/<post_dir_name>/<img_dir_name>/<filename>')
def get_post_files(post_dir_name, img_dir_name,filename):
    logger_bp_blog.info(f"- in get_post_files route for {post_dir_name}/{img_dir_name}/{filename}")

    return send_from_directory(os.path.join(current_app.config.get('DIR_DB_AUX_BLOG_POSTS'),post_dir_name, img_dir_name), filename)

@bp_blog.route("/blog", methods=["GET"])
def index():

    blog_posts_list = create_blog_posts_list()
        
    items = ['date', 'title', 'description']

    print("blog_posts_list: ", blog_posts_list)
    return render_template('blog/index.html', blog_posts_list=blog_posts_list)

@bp_blog.route("/view_post/<post_dir_name>")
def view_post(post_dir_name):
    post_id = re.findall(r'\d+', post_dir_name)
    post = sess_users.get(BlogPosts,post_id)

    templates_path_lists = [
        os.path.join(current_app.config.root_path,"templates"),
        # os.path.join(current_app.config.get('DB_ROOT'),"posts", post_id_name_string)
        os.path.join(current_app.config.get('DIR_DB_AUX_BLOG_POSTS'), post_dir_name)
    ]

    templateLoader = jinja2.FileSystemLoader(searchpath=templates_path_lists)

    templateEnv = jinja2.Environment(loader=templateLoader)
    template_parent = templateEnv.get_template("blog/view_post.html")
    template_layout = templateEnv.get_template("_layout.html")
    # template_post_index = templateEnv.get_template("index.html")
    template_post_index = templateEnv.get_template(post.word_doc_to_html_filename)

    # If post has a sub folder

    # create a list called post_items_list

    #["<folder_name>/<file_name>"]

    return template_parent.render(template_layout=template_layout, template_post_index=template_post_index, \
        # post_id_name_string=post_id_name_string, \
        post_dir_name=post_dir_name, \
        url_for=url_for, get_flashed_messages=get_flashed_messages, current_user=current_user)


# formerly blog_user_home
@bp_blog.route("/manage_blogposts", methods=["GET","POST"])
@login_required
def manage_blogposts():
    print('--- In  manage_blogposts ----')
    logger_bp_blog.info(f"- In manage_blogposts -")

    if not current_user.is_authenticated:
        return redirect(url_for('bp_main.home'))

    all_my_posts=sess_users.query(BlogPosts).filter_by(user_id=current_user.id).all()
    posts_details_list=[]
    for i in all_my_posts:
        posts_details_list.append([i.id, i.title, i.date_published.strftime("%m/%d/%Y"),
            i.description, i.word_doc_to_html_filename])
    
    column_names=['id', 'blog_title', 'delete','date_published',
         'blog_description','word_doc']

    if request.method == 'POST':
        formDict=request.form.to_dict()
        print('formDict::', formDict)
        if formDict.get('delete_record_id')!='':
            post_id=formDict.get('delete_record_id')
            print(post_id)

            return redirect(url_for('bp_blog.blog_delete', post_id=post_id))

    return render_template('blog/manage_blogposts.html', posts_details_list=posts_details_list, len=len,
        column_names=column_names)


@bp_blog.route("/create_post", methods=["GET","POST"])
@login_required
def create_post():
    if not current_user.is_authenticated:
        return redirect(url_for('bp_main.home'))

    logger_bp_blog.info(f"- user has blog post permission -")

    default_date = datetime.utcnow().strftime("%Y-%m-%d")

    if request.method == 'POST':
        print("------------------------------")
        formDict = request.form.to_dict()
        print("formDict: ", formDict)
        request_files = request.files
        print("request_files: ", request_files)
        
        #######################################################
        # NOTE: Old method comes from whatSticks09web
        # It is deleted from code b
        ######################################################

        if formDict.get('dropdown_upload_zip_type') == 'origin_from_word':
            logger_bp_blog.info(f"- origin_from_word -")
        
            post_zip = request_files["zip_file_origin_word"]
            post_zip_filename = post_zip.filename

            # create new_blogpost to get post_id number
            new_blogpost = BlogPosts(user_id=current_user.id)
            sess_users.add(new_blogpost)
            sess_users.commit()
            # create post_id string
            new_blog_id = new_blogpost.id
            new_post_dir_name = f"{new_blog_id:04d}_post"
            # new_blogpost.post_id_name_string = new_post_dir_name
            new_blogpost.post_dir_name = new_post_dir_name
            sess_users.commit()

            # make temproary directory called 'temp_zip' to hold the uploaded zip file
            temp_zip_db_fp = os.path.join(current_app.config.get('DIR_DB_AUX_BLOG'),'temp_zip')
            if not os.path.exists(temp_zip_db_fp):
                os.mkdir(temp_zip_db_fp)
            else:
                shutil.rmtree(temp_zip_db_fp)
                os.mkdir(temp_zip_db_fp)

            # save zip to temp_zip directory
            post_zip.save(os.path.join(temp_zip_db_fp, secure_filename(post_zip_filename)))
            zip_folder_name_nospaces = post_zip_filename.replace(" ", "_")

            # make path of new post dir 00##_post
            new_blog_dir_fp = os.path.join(current_app.config.get('DIR_DB_AUX_BLOG_POSTS'), new_post_dir_name)
            logger_bp_blog.info(f"- new_blog_dir_fp: {new_blog_dir_fp} -")
            
            # unzipped_files_dir_name = "temp_name"

            # decompress uploaded file in temp_zip
            with zipfile.ZipFile(os.path.join(temp_zip_db_fp, zip_folder_name_nospaces), 'r') as zip_ref:
                print("- unzipping file --")
                unzipped_files_dir_name = zip_ref.namelist()[0]


                
                unzipped_temp_dir = os.path.join(temp_zip_db_fp, new_post_dir_name)
                print(f"- {unzipped_temp_dir} --")
                zip_ref.extractall(unzipped_temp_dir)

            logger_bp_blog.info(f"- decompressing and extracting to here: {os.path.join(temp_zip_db_fp)}")
            
            unzipped_dir_list = [ f.path for f in os.scandir(unzipped_temp_dir) if f.is_dir() ]
            
            # delete the __MACOSX dir
            for path_str in unzipped_dir_list:
                if path_str[-8:] == "__MACOSX":
                    shutil.rmtree(path_str)
                    print(f"- removed {path_str[-8:]} -")

            # temp_zip path
            source = unzipped_temp_dir
            logger_bp_blog.info(f"- SOURCE: {source}")

            # db/posts/0000_post
            # destination = os.path.join(current_app.config.get('DB_ROOT'), "posts")
            destination = current_app.config.get('DIR_DB_AUX_BLOG_POSTS')

            dest = shutil.move(source, destination, copy_function = shutil.copytree) 
            logger_bp_blog.info(f"Destination path: {dest}") 

            # find root html file for post
            for file_name in os.listdir(dest):
                
                if file_name.endswith('.html'):
                    post_html_filename = file_name
                    post_html_file_name_and_path =  os.path.join(current_app.config.get('DIR_DB_AUX_BLOG_POSTS'), 
                                            new_post_dir_name,post_html_filename)
                    post_html_filename = sanitize_directory_name(post_html_file_name_and_path)
                if os.path.isdir(os.path.join(dest,file_name)) and os.path.join(dest,file_name)[-4:] == '.fld':
                    post_images_dir_name_and_path = os.path.join(dest,file_name)
                    post_images_dir_name = sanitize_directory_name(post_images_dir_name_and_path)

            
            # TODO: Rename folder containig images
            # check for spaces adn extra charaters
            ## if exists replace and rename directory
            # print("*** Sanatize .fld Name ***")
            # zip_folder_name_nospaces_no_dot_zip = zip_folder_name_nospaces[:4]
            # print("zip_folder_name_nospaces_no_dot_zip: ", zip_folder_name_nospaces_no_dot_zip)
            # directory_path =  os.path.join(new_blog_dir_fp, zip_folder_name_nospaces_no_dot_zip, unzipped_files_dir_name)
            # directory_path =  os.path.join(current_app.config.get('DIR_DB_AUX_BLOG_POSTS'), 
            #                                 new_post_dir_name,unzipped_files_dir_name[:-1])
            # unzipped_files_dir_name = sanitize_directory_name(directory_path)
            
            print("Adding unzipped_files_dir_name: ", unzipped_files_dir_name)
            print("*** END sanatize .fld ***")
            


            # beautiful soup to search and replace img src with {{ url_for('custom_static', ___, __ ,__)}}
            # new_index_text = replace_img_src_jinja(os.path.join(new_blog_dir_fp,post_html_filename), unzipped_files_dir_name)
            new_index_text = replace_img_src_jinja(os.path.join(new_blog_dir_fp,post_html_filename), post_images_dir_name)
            if new_index_text == "Error opening index.html":# cannot imagine how this is possible, but we'll leave it.
                flash(f"Missing index.html? There was an problem trying to opening {os.path.join(new_blog_dir_fp,post_html_filename)}.", "warning")
                # return redirect(request.url)
                return redirect(url_for('bp_blog.blog_delete', post_id=new_blog_id))

            # remove existing post_html_filename
            os.remove(os.path.join(new_blog_dir_fp,post_html_filename))

            # write a new index.html with new code that references images in image folder
            index_html_writer = open(os.path.join(new_blog_dir_fp,post_html_filename), "w")
            index_html_writer.write(new_index_text)
            index_html_writer.close()

            # delete compressed file
            shutil.rmtree(temp_zip_db_fp)

            new_blogpost.images_dir_name = post_images_dir_name
            new_blogpost.word_doc_to_html_filename = post_html_filename
            new_blogpost.title = get_title(os.path.join(new_blog_dir_fp,post_html_filename), "origin_from_word")
            sess_users.commit()

            logger_bp_blog.info(f"- filename is {new_post_dir_name} -")


        flash(f'Post added successfully!', 'success')
        return redirect(url_for('bp_blog.blog_edit', post_id = new_blog_id))
        # return redirect(request.url)
        # return redirect(url_for('blog.create_post'))


    return render_template('blog/create_post.html', default_date=default_date)


@bp_blog.route("/edit/<post_id>", methods=['GET','POST'])
@login_required
def blog_edit(post_id):
    if not current_user.is_authenticated:
        return redirect(url_for('main.home'))

    post = sess_users.query(BlogPosts).filter_by(id = post_id).first()
    title = post.title
    description = post.description
    post_time_stamp_utc = post.time_stamp_utc.strftime("%Y-%m-%d")


    if post.date_published in ["", None]:
        post_date = ""
    else:
        post_date = post.date_published.strftime("%Y-%m-%d")

    if request.method == 'POST':
        formDict = request.form.to_dict()

        title = formDict.get("blog_title")
        description = formDict.get("blog_description")
        date = formDict.get("blog_date_published")

        post.title = formDict.get("blog_title")
        post.description = formDict.get("blog_description")
        if formDict.get('blog_date_published') == "":
            post.date_published = None
        else:
            post.date_published = datetime.strptime(formDict.get('blog_date_published'), "%Y-%m-%d")
        sess_users.commit()

        flash("Post successfully updated", "success")
        return redirect(request.url)

    return render_template('blog/edit_post.html', title= title, description = description, 
        post_date = post_date, post_time_stamp_utc = post_time_stamp_utc)



@bp_blog.route("/delete/<post_id>", methods=['GET','POST'])
@login_required
def blog_delete(post_id):
    post_to_delete = sess_users.query(BlogPosts).get(int(post_id))

    print("where did the reqeust come from: ", request.referrer)
    print("-------------------------------------------------")

    if current_user.id != post_to_delete.user_id:
        return redirect(url_for('blog.post_index'))
    logger_bp_blog.info('-- In delete route --')
    logger_bp_blog.info(f'post_id:: {post_id}')

    # delete word document in templates/blog/posts
    # blog_dir_for_delete = os.path.join(current_app.config.get('DB_ROOT'), "posts",post_to_delete.post_id_name_string)
    blog_dir_for_delete = os.path.join(current_app.config.get('DIR_DB_AUX_BLOG_POSTS'),post_to_delete.post_dir_name)

    # new_blog_dir_fp = os.path.join(current_app.config.get('DIR_DB_AUX_BLOG_POSTS'), new_post_dir_name)

    try:
        shutil.rmtree(blog_dir_for_delete)
    except:
        logger_bp_blog.info(f'No {blog_dir_for_delete} in static folder')

    # delete from database
    sess_users.query(BlogPosts).filter(BlogPosts.id==post_id).delete()
    sess_users.commit()
    print(' request.referrer[len("create_post")*-1: ]:::', request.referrer[len("create_post")*-1: ])
    if request.referrer[len("create_post")*-1: ] == "create_post":
        return redirect(request.referrer)

    flash(f'Post removed successfully!', 'success')
    return redirect(url_for('bp_blog.manage_blogposts'))





