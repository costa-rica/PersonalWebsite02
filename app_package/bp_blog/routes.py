from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request,current_app, get_flashed_messages, \
    send_from_directory, g
import os
from datetime import datetime
import time
import logging
from logging.handlers import RotatingFileHandler
import jinja2
from flask_login import login_user, current_user, logout_user, login_required
from app_package.bp_blog.utils import create_blog_posts_list, replace_img_src_jinja, \
    get_title, sanitize_directory_name, remove_head, \
    remove_body_tags, replace_p_elements_with_img, read_html_to_soup, \
    remove_line_height_from_p_tags, remove_MACOSX_files, check_for_dir_if_not_exist_make_dir, \
    unzip_blog_files_and_extract_to_dir, replace_code_snippet_filename_with_jinja_include_block, \
    delete_old_write_new_index_html, replace_span_with_background_styling_with_contents

from pw_models import DatabaseSession, text, Users, BlogPosts
from werkzeug.utils import secure_filename
import shutil
import zipfile
import jinja2
import re
from app_package._common.utilities import custom_logger, wrap_up_session

logger_bp_blog = custom_logger('bp_blog.log')


bp_blog = Blueprint('bp_blog', __name__)
# sess_users = dict_sess['sess_users']

@bp_blog.before_request
def before_request():
    logger_bp_blog.info("-- def before_request() --")
    # Assign a new session to a global `g` object, accessible during the whole request
    g.db_session = DatabaseSession()
    
    # Use getattr to safely access g.referrer, defaulting to None if it's not set
    if getattr(g, 'referrer', None) is None:
        if request.referrer:
            g.referrer = request.referrer
        else:
            g.referrer = "No referrer"
    
    logger_bp_blog.info("-- def before_request() END --")


## Access images for Posted articles
@bp_blog.route('/get_post_images/<post_dir_name>/<img_dir_name>/<filename>')
def get_post_files(post_dir_name, img_dir_name,filename):
    logger_bp_blog.info(f"- in get_post_files route for {post_dir_name}/{img_dir_name}/{filename}")
    dir = os.path.join(current_app.config.get('DIR_BLOG_POSTS'),post_dir_name, img_dir_name)
    if not os.path.exists(os.path.join(dir, filename)):
        logger_bp_blog.info(f"-----------> MISSING FILE: {os.path.join(dir, filename)} <------")

    return send_from_directory(dir, filename)

## Access icons for Linked articles
@bp_blog.route('/get_blog_icons/<filename>')
def get_blog_icons(filename):
    logger_bp_blog.info(f"- in get_blog_icons route -")
    dir = current_app.config.get('DIR_BLOG_ICONS')
    logger_bp_blog.info(f"looking for file: {os.path.join(dir, filename)}")

    if not os.path.exists(os.path.join(dir, filename)):
        logger_bp_blog.info(f"-----------> MISSING FILE: {os.path.join(dir, filename)} <------")

    return send_from_directory(dir, filename)

@bp_blog.route("/blog_home", methods=["GET"])
def blog_home():
    logger_bp_blog.info(f"- in blog index page -")
    db_session = g.db_session
    blog_posts_list = create_blog_posts_list(db_session)
        
    items = ['date', 'title', 'description']

    # print("blog_posts_list: ", blog_posts_list)
    return render_template('blog/blog_home.html', blog_posts_list=blog_posts_list)

@bp_blog.route("/view_post/<post_dir_name>")
def view_post(post_dir_name):
    db_session = g.db_session
    post_id = re.findall(r'\d+', post_dir_name)
    post = db_session.get(BlogPosts,post_id)

    templates_path_lists = [
        os.path.join(current_app.config.root_path,"templates"),
        # os.path.join(current_app.config.get('DB_ROOT'),"posts", post_id_name_string)
        os.path.join(current_app.config.get('DIR_BLOG_POSTS'), post_dir_name)
    ]

    templateLoader = jinja2.FileSystemLoader(searchpath=templates_path_lists)

    templateEnv = jinja2.Environment(loader=templateLoader)
    template_parent = templateEnv.get_template("blog/view_post.html")
    template_layout = templateEnv.get_template("_layout.html")
    # template_post_index = templateEnv.get_template("index.html")

    # Delete if, keep else after editing BlogPost model and moving data
    if post.word_doc_to_html_filename != None:
        print("post.word_doc_to_html_filename: ", post.word_doc_to_html_filename)
        template_post_index = templateEnv.get_template(post.word_doc_to_html_filename)
    else:
        template_post_index = templateEnv.get_template(post.post_html_filename)

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
    db_session = g.db_session
    if not current_user.is_authenticated:
        return redirect(url_for('bp_main.home'))

    # all_my_posts=sess_users.query(BlogPosts).filter_by(user_id=current_user.id).all()
    all_my_posts=db_session.query(BlogPosts).filter_by(user_id=current_user.id).all()
    posts_details_list=[]
    for i in all_my_posts:
        if i.word_doc_to_html_filename != None:
            posts_details_list.append([i.id, i.title, i.date_published.strftime("%m/%d/%Y"),
                i.description, i.word_doc_to_html_filename])
        else:
            posts_details_list.append([i.id, i.title, i.date_published.strftime("%m/%d/%Y"),
                i.description, "link details"])
    
    column_names=['id', 'Title', 'Delete','Date Pub',
         'Description','Edit Post']

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
    db_session = g.db_session

    default_date = datetime.utcnow().strftime("%Y-%m-%d")

    if request.method == 'POST':
        formDict = request.form.to_dict()
        request_files = request.files

        if formDict.get('what_kind_of_post') == 'post_article_mult_files':
            logger_bp_blog.info(f"- post_article_mult_files -")

            uploaded_html_file = request_files["post_article_mult_file_html_file"]

            # create new_blogpost to get post_id number
            new_blogpost = BlogPosts(user_id=current_user.id)
            
            db_session.add(new_blogpost)
            db_session.flush()
            # create post_id string
            new_blog_id = new_blogpost.id
            new_post_dir_name = f"{new_blog_id:04d}_post"

            new_blogpost.post_dir_name = new_post_dir_name
            new_blogpost.post_html_filename = uploaded_html_file.filename

            # make temproary directory called 'temp_zip' to hold the uploaded zip file
            temp_zip_db_fp = os.path.join(current_app.config.get('DIR_BLOG'),'temp_zip')
            check_for_dir_if_not_exist_make_dir(temp_zip_db_fp)

            # make name and directory for path of new post dir NAME 00##_post
            # new_blog_dir_fp = os.path.join(current_app.config.get('DIR_BLOG_POSTS'), new_post_dir_name)
            new_blog_dir_file_path = os.path.join(current_app.config.get('DIR_BLOG_POSTS'), new_post_dir_name)
            check_for_dir_if_not_exist_make_dir(new_blog_dir_file_path)
            logger_bp_blog.info(f"- new_blog_dir_file_path (now exists): {new_blog_dir_file_path} -")

            new_blog_post_path_and_file_name = os.path.join(new_blog_dir_file_path,new_blogpost.post_html_filename)

            #save html file in destination
            uploaded_html_file.save(os.path.join(current_app.config.get('DIR_BLOG_POSTS'), new_post_dir_name, uploaded_html_file.filename))

            # Save zip files to temp
            if request_files.get("post_article_mult_file_image_zip_file"):

                new_blogpost.images_dir_name = "images"

                post_images_zip = request_files.get("post_article_mult_file_image_zip_file")
                post_images_zip_filename = post_images_zip.filename
                post_images_zip.save(os.path.join(temp_zip_db_fp, secure_filename(post_images_zip_filename)))
                post_images_zip_folder_name_nospaces = post_images_zip_filename.replace(" ", "_")
                # dir_name_for_unzip_and_extract = os.path.join(temp_zip_db_fp, post_images_zip_folder_name_nospaces)

                # decompress uploaded IMAGES file in temp_zip
                unzip_blog_files_and_extract_to_dir(temp_zip_db_fp, post_images_zip_folder_name_nospaces, "images")

                # Remove any __MACOSX dir or files
                unzipped_temp_dir = os.path.join(temp_zip_db_fp, "images")
                remove_MACOSX_files(unzipped_temp_dir)

                # Entirely moves the unzipped_temp_dir directory to new_blog_dir_file_path
                dest_new_post_images = shutil.move(unzipped_temp_dir, new_blog_dir_file_path, copy_function = shutil.copytree) 
                logger_bp_blog.info(f"Destination for images path: {dest_new_post_images}")

                # Beautiful Soup HTML editing here
                # -- img elements (start): find all img elements and replace with jinja2 include block {} <---
                new_index_text = replace_img_src_jinja(new_blog_post_path_and_file_name, "images")
                
                # in case there was a problem w/ Beautiful Soup writing a new blog post .html file stop the process and let user know this blog has error
                if new_index_text == "Error opening index.html":# cannot imagine how this is possible, but we'll leave it.
                    flash(f"Could not find new blog post .html? There was an problem trying to opening {new_blog_post_path_and_file_name}.", "warning")
                    # return redirect(request.url)
                    return redirect(url_for('bp_blog.blog_delete', post_id=new_blog_id))

                delete_old_write_new_index_html(new_blog_post_path_and_file_name, new_index_text)
                # -- img elements (end)

            if request_files.get("post_article_mult_file_code_zip_file"):
                post_code_snippet_zip = request_files.get("post_article_mult_file_code_zip_file")
                post_code_snippet_zip_filename = post_code_snippet_zip.filename
                post_code_snippet_zip.save(os.path.join(temp_zip_db_fp, secure_filename(post_code_snippet_zip_filename)))
                post_code_snippet_zip_folder_name_nospaces = post_code_snippet_zip_filename.replace(" ", "_")


                # unzip_blog_files_and_extract_to_dir(dir_name_for_unzip_and_extract, "code_snippets")
                unzip_blog_files_and_extract_to_dir(temp_zip_db_fp, post_code_snippet_zip_folder_name_nospaces, "code_snippets")

                # Remove any __MACOSX dir or files
                unzipped_temp_dir = os.path.join(temp_zip_db_fp, "code_snippets")
                remove_MACOSX_files(unzipped_temp_dir)
                # remove_MACOSX_files(os.path.join(temp_zip_db_fp, new_post_dir_name))

                #Move code_snippets folder (unzipped_temp_dir) from temp to the new blog directory (ie. blog/posts/post#### or in this code is new_blog_dir_file_path)
                dest_new_post_code_snippets = shutil.move(unzipped_temp_dir, new_blog_dir_file_path, copy_function = shutil.copytree) 
                logger_bp_blog.info(f"Destination for code_snippet path: {dest_new_post_code_snippets}")

                # Beautiful Soup HTML editing here
                # -- p elements for code_snippets (start): find all p elements whose contents contain a file name in the list of uploaded code snippet file names
                #  and replace with jinja2 include block {} <---
                new_index_text = replace_code_snippet_filename_with_jinja_include_block(new_blog_post_path_and_file_name, new_post_dir_name)
                if new_index_text == "Error opening index.html":# cannot imagine how this is possible, but we'll leave it.
                    flash(f"Missing index.html? There was an problem trying to opening {new_blog_post_path_and_file_name}.", "warning")
                    # return redirect(request.url)
                    return redirect(url_for('bp_blog.blog_delete', post_id=new_blog_id))
                
                delete_old_write_new_index_html(new_blog_post_path_and_file_name, new_index_text)
                # -- p elements for code_snippets (end)
            
            # More Beautiful Soup Cleaning
            new_index_text = read_html_to_soup(new_blog_post_path_and_file_name)

            try:
                new_index_text = remove_head(new_index_text)
                logger_bp_blog.info(f"----> head successfully removed")
            except:
                logger_bp_blog.info(f"***** head not removed")

            try:
                new_index_text = remove_body_tags(new_index_text)
                logger_bp_blog.info(f"----> body tags successfully removed")
            except:
                logger_bp_blog.info(f"**** body tags not removed")

            try:
                new_index_text = replace_p_elements_with_img(new_index_text)
                logger_bp_blog.info(f"----> p elements for img successfully removed")
            except:
                logger_bp_blog.info(f"**** p elements with img not removed")

            try:
                new_index_text = remove_line_height_from_p_tags(new_index_text)
                logger_bp_blog.info(f"----> `line-height: 100%` in p elements successfully removed")
            except Exception as e:
                logger_bp_blog.info(f"{type(e).__name__}: {e}")
                logger_bp_blog.info(f"**** `line-height: 100%` in p elements not removed")

            # ## Print test before removeing highlights
            # # write a new index.html with new code that references images in image folder
            # test_folder_path = "/Users/nick/Documents/_testData/PersonalWeb02-blogposts"
            # test_path_and_name = os.path.join(test_folder_path,"test_version05.html")
            # index_html_writer = open(test_path_and_name, "w")
            # index_html_writer.write(new_index_text)
            # index_html_writer.close()

            try:
                # -OLD DELETE- p elements for Illustration captions (start): find all p elements whose contents contain the word "Illustration" and remove highlights
                ## search all span elements with background styling and replaces with its contents
                # Remove highilghts from "Illustration #" cross references and Heading 1 cross references
                new_index_text = replace_span_with_background_styling_with_contents(new_index_text)
                logger_bp_blog.info(f"----> highlights on the word 'Illustration' removed in p elements -> span element successfully replaced w contents")
            except Exception as e:
                logger_bp_blog.info(f"{type(e).__name__}: {e}")
                logger_bp_blog.info(f"**** highlights on the word 'Illustration' NOT removed in p elements -> span element NOT replaced w contents")
                # -- p elements for Illustration captions (end)

            delete_old_write_new_index_html(new_blog_post_path_and_file_name, new_index_text)


        elif formDict.get('what_kind_of_post') == 'post_link':
            logger_bp_blog.info(f"- post_link -")

            # create new_blogpost to get post_id number
            new_blogpost = BlogPosts(user_id=current_user.id)
            db_session.add(new_blogpost)
            db_session.flush()
            # create post_id string
            new_blog_id = new_blogpost.id
            new_blogpost.title=formDict.get('blog_title')
            new_blogpost.description=formDict.get('blog_description')
            new_blogpost.url=formDict.get('blog_url')
            db_session.flush()

            flash(f'Post added successfully!', 'success')
            return redirect(url_for('bp_blog.blog_edit', post_id = new_blog_id))


    return render_template('blog/create_post.html', default_date=default_date)


@bp_blog.route("/edit/<post_id>", methods=['GET','POST'])
@login_required
def blog_edit(post_id):
    if not current_user.is_authenticated:
        return redirect(url_for('main.home'))
    db_session = g.db_session
    post = db_session.query(BlogPosts).filter_by(id = post_id).first()
    title = post.title
    description = post.description
    post_time_stamp_utc = post.time_stamp_utc.strftime("%Y-%m-%d")
    list_of_link_post_icons = os.listdir(current_app.config.get('DIR_BLOG_ICONS'))
    
    if post.category not in [None, ""]:
        selected_category = post.category
    else:
        selected_category = "coding"
    

    if post.date_published in ["", None]:
        post_date = ""
    else:
        post_date = post.date_published.strftime("%Y-%m-%d")

    list_image_files = None
    # Select images from post directory 
    if post.images_dir_name not in ["", None]:
        list_image_files = os.listdir(os.path.join(current_app.config.get('DIR_BLOG_POSTS'),
            post.post_dir_name, post.images_dir_name))
        # print(file_names)
    selected_image = post.blogpost_index_image_filename
    selected_icon = post.icon_file
    if request.method == 'POST':
        formDict = request.form.to_dict()

        title = formDict.get("blog_title")
        description = formDict.get("blog_description")
        date = formDict.get("blog_date_published")
        selected_category = formDict.get("category_dropdown")

        post.title = formDict.get("blog_title")
        post.description = formDict.get("blog_description")
        post.category = formDict.get("category_dropdown")
        
        if formDict.get("image_filename_dropdown"):
            post.blogpost_index_image_filename = formDict.get("image_filename_dropdown")
        else:
            post.blogpost_index_image_filename = formDict.get('icon_filename_dropdown')
        post.icon_file = formDict.get('icon_filename_dropdown')
        if formDict.get('blog_date_published') == "":
            post.date_published = None
        else:
            post.date_published = datetime.strptime(formDict.get('blog_date_published'), "%Y-%m-%d")
        # sess_users.commit()

        flash("Post successfully updated", "success")
        return redirect(request.url)

    return render_template('blog/edit_post.html', title= title, description = description, 
        post_date = post_date, post_time_stamp_utc = post_time_stamp_utc, 
        selected_category=selected_category, list_image_files=list_image_files,
        selected_image=selected_image, list_of_link_post_icons=list_of_link_post_icons,
        selected_icon=selected_icon)


@bp_blog.route("/delete/<post_id>", methods=['GET','POST'])
@login_required
def blog_delete(post_id):
    db_session = g.db_session
    post_to_delete = db_session.query(BlogPosts).get(int(post_id))

    if current_user.id != post_to_delete.user_id:
        return redirect(url_for('blog.post_index'))
    logger_bp_blog.info('-- In delete route --')
    logger_bp_blog.info(f'post_id:: {post_id}')

    if post_to_delete.post_dir_name:
        blog_dir_for_delete = os.path.join(current_app.config.get('DIR_BLOG_POSTS'),post_to_delete.post_dir_name)

        try:
            shutil.rmtree(blog_dir_for_delete)
        except:
            logger_bp_blog.info(f'No {blog_dir_for_delete} in static folder')

    # delete from database
    db_session.query(BlogPosts).filter(BlogPosts.id==post_id).delete()
    # sess_users.commit()
    print(' request.referrer[len("create_post")*-1: ]:::', request.referrer[len("create_post")*-1: ])
    if request.referrer[len("create_post")*-1: ] == "create_post":
        return redirect(request.referrer)

    flash(f'Post removed successfully!', 'success')
    return redirect(url_for('bp_blog.manage_blogposts'))



@bp_blog.route("/blog_database_admin", methods=['GET','POST'])
@login_required
def blog_database_admin():

    return render_template('blog/blog_database_admin.html')

