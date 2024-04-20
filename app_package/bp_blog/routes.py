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
    get_title, sanitize_directory_name, replace_code_snippet_jinja, remove_head, \
    remove_body_tags, replace_p_elements_with_img, read_html_to_soup, \
    remove_line_height_from_p_tags

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
    # print("-- blog_post_list --")
    
    # print(blog_posts_list)
    # print("-- blog_post_list --")
    # print("-- blog_post_list --")
        
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
        print("------------------------------")
        formDict = request.form.to_dict()
        print("formDict: ", formDict)
        request_files = request.files
        print("request_files: ", request_files)

        if formDict.get('what_kind_of_post') == 'post_article_mult_files':
            logger_bp_blog.info(f"- post_article_mult_files -")

            # post_zip = request_files["post_article_single_zip_file"]
            # post_zip_filename = post_zip.filename
            uploaded_html_file = request_files["post_article_mult_file_html_file"]
            # print("dir(uploaded_html_file): ", dir(uploaded_html_file))
            # print("filename: ", uploaded_html_file.filename)

            # create new_blogpost to get post_id number
            new_blogpost = BlogPosts(user_id=current_user.id)
            
            db_session.add(new_blogpost)
            db_session.flush()
            # sess_users.commit()
            # create post_id string
            new_blog_id = new_blogpost.id
            new_post_dir_name = f"{new_blog_id:04d}_post"
            # new_blogpost.post_id_name_string = new_post_dir_name
            new_blogpost.post_dir_name = new_post_dir_name
            new_blogpost.post_html_filename = uploaded_html_file.filename
            # new_blogpost.images_dir_name = "images"
            # sess_users.commit()

            # make temproary directory called 'temp_zip' to hold the uploaded zip file
            temp_zip_db_fp = os.path.join(current_app.config.get('DIR_BLOG'),'temp_zip')
            if not os.path.exists(temp_zip_db_fp):
                os.mkdir(temp_zip_db_fp)
            else:
                shutil.rmtree(temp_zip_db_fp)
                os.mkdir(temp_zip_db_fp)

            # make path of new post dir NAME 00##_post
            new_blog_dir_fp = os.path.join(current_app.config.get('DIR_BLOG_POSTS'), new_post_dir_name)
            logger_bp_blog.info(f"- new_blog_dir_fp: {new_blog_dir_fp} -")

            # Save zip files to temp
            if request_files.get("post_article_mult_file_image_zip_file"):
                # post_zip = request_files["post_article_single_zip_file"] ### <-- replaced by post_images_zip

                new_blogpost.images_dir_name = "images"
                # sess_users.commit()

                post_images_zip = request_files.get("post_article_mult_file_image_zip_file")
                post_images_zip_filename = post_images_zip.filename
                post_images_zip.save(os.path.join(temp_zip_db_fp, secure_filename(post_images_zip_filename)))
                post_images_zip_folder_name_nospaces = post_images_zip_filename.replace(" ", "_")

                # decompress uploaded IMAGES file in temp_zip
                with zipfile.ZipFile(os.path.join(temp_zip_db_fp, post_images_zip_folder_name_nospaces), 'r') as zip_ref:
                # with zipfile.ZipFile(os.path.join(temp_zip_db_fp, zip_folder_name_nospaces), 'r') as zip_ref:
                    print("- unzipping file --")
                    print("-- zip_ref.namelist() --")
                    print(zip_ref.namelist())
                    print("-- z------ --")
                    unzipped_files_dir_name = zip_ref.namelist()[0]
                    
                    unzipped_temp_dir = os.path.join(temp_zip_db_fp, new_post_dir_name)
                    print(f"- {unzipped_temp_dir} --")
                    zip_ref.extractall(unzipped_temp_dir)

            if request_files.get("post_article_mult_file_code_zip_file"):
                post_code_snippet_zip = request_files.get("post_article_mult_file_code_zip_file")
                post_code_snippet_zip_filename = post_code_snippet_zip.filename
                post_code_snippet_zip.save(os.path.join(temp_zip_db_fp, secure_filename(post_code_snippet_zip_filename)))
                post_code_snippet_zip_folder_name_nospaces = post_code_snippet_zip_filename.replace(" ", "_")

                # decompress uploaded CODE SNIPPETS file in temp_zip
                with zipfile.ZipFile(os.path.join(temp_zip_db_fp, post_code_snippet_zip_folder_name_nospaces), 'r') as zip_ref:
                # with zipfile.ZipFile(os.path.join(temp_zip_db_fp, zip_folder_name_nospaces), 'r') as zip_ref:
                    print("- unzipping file --")
                    print("-- zip_ref.namelist() --")
                    print(zip_ref.namelist())
                    print("-- z------ --")
                    unzipped_files_dir_name = zip_ref.namelist()[0]
                    
                    unzipped_temp_dir = os.path.join(temp_zip_db_fp, new_post_dir_name)
                    print(f"- {unzipped_temp_dir} --")
                    zip_ref.extractall(unzipped_temp_dir)
            

            if request_files.get("post_article_mult_file_image_zip_file") or request_files.get("post_article_mult_file_code_zip_file"):

                unzipped_dir_list = [ f.path for f in os.scandir(unzipped_temp_dir) if f.is_dir() ]
                
                # delete the __MACOSX dir
                for path_str in unzipped_dir_list:
                    if path_str[-8:] == "__MACOSX":
                        shutil.rmtree(path_str)
                        print(f"- removed {path_str[-8:]} -")


                # make new post dir in blog/posts/
                # temp_zip path
                source = unzipped_temp_dir
                logger_bp_blog.info(f"- SOURCE: {source}")

                # db/posts/0000_post
                # destination = os.path.join(current_app.config.get('DB_ROOT'), "posts")
                destination = current_app.config.get('DIR_BLOG_POSTS')

                dest = shutil.move(source, destination, copy_function = shutil.copytree) 
                logger_bp_blog.info(f"Destination path: {dest}")

                #save html file in destination
                uploaded_html_file.save(os.path.join(current_app.config.get('DIR_BLOG_POSTS'), new_post_dir_name, uploaded_html_file.filename))

                # ADD Images ---
                # beautiful soup to search and replace img src with {{ url_for('custom_static', ___, __ ,__)}}
                # new_index_text = replace_img_src_jinja(os.path.join(new_blog_dir_fp,post_html_filename), post_images_dir_name)
                new_index_text = replace_img_src_jinja(os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename), "images")
                
                if new_index_text == "Error opening index.html":# cannot imagine how this is possible, but we'll leave it.
                    flash(f"Missing index.html? There was an problem trying to opening {os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename)}.", "warning")
                    # return redirect(request.url)
                    return redirect(url_for('bp_blog.blog_delete', post_id=new_blog_id))

                # remove existing post_html_filename
                os.remove(os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename))

                # write a new index.html with new code that references images in image folder
                index_html_writer = open(os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename), "w")
                index_html_writer.write(new_index_text)
                index_html_writer.close()


                # Re write for code snippet
                new_index_text = replace_code_snippet_jinja(os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename))

                if new_index_text == "Error opening index.html":# cannot imagine how this is possible, but we'll leave it.
                    flash(f"Missing index.html? There was an problem trying to opening {os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename)}.", "warning")
                    # return redirect(request.url)
                    return redirect(url_for('bp_blog.blog_delete', post_id=new_blog_id))

                # remove existing post_html_filename
                os.remove(os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename))

                # write a new index.html with new code that references images in image folder
                index_html_writer = open(os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename), "w")
                index_html_writer.write(new_index_text)
                index_html_writer.close()

            else:# <-- No zip files included in post, just html
                logger_bp_blog.info(f"Create Blog directory 000#_post, path: {new_blog_dir_fp}")
                os.mkdir(new_blog_dir_fp)
                logger_bp_blog.info(f"save html file in new directory")
                uploaded_html_file.save(os.path.join(new_blog_dir_fp, uploaded_html_file.filename))
                
            
            # More Beautiful Soup Cleaning

            new_index_text = read_html_to_soup(os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename))

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
            except:
                logger_bp_blog.info(f"**** `line-height: 100%` in p elements not removed")

            # remove existing post_html_filename
            os.remove(os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename))

            # write a new index.html with new code that references images in image folder
            index_html_writer = open(os.path.join(new_blog_dir_fp,new_blogpost.post_html_filename), "w")
            index_html_writer.write(new_index_text)
            index_html_writer.close()


        elif formDict.get('what_kind_of_post') == 'post_article_single_zip':
            logger_bp_blog.info(f"- post_article_single_zip -")

            post_zip = request_files["post_article_single_zip_file"]
            post_zip_filename = post_zip.filename

            # create new_blogpost to get post_id number
            new_blogpost = BlogPosts(user_id=current_user.id)
            db_session.add(new_blogpost)
            db_session.flush()
            # sess_users.commit()
            # create post_id string
            new_blog_id = new_blogpost.id
            new_post_dir_name = f"{new_blog_id:04d}_post"
            # new_blogpost.post_id_name_string = new_post_dir_name
            new_blogpost.post_dir_name = new_post_dir_name
            # sess_users.commit()
            db_session.flush()

            # make temproary directory called 'temp_zip' to hold the uploaded zip file
            temp_zip_db_fp = os.path.join(current_app.config.get('DIR_BLOG'),'temp_zip')
            if not os.path.exists(temp_zip_db_fp):
                os.mkdir(temp_zip_db_fp)
            else:
                shutil.rmtree(temp_zip_db_fp)
                os.mkdir(temp_zip_db_fp)

            # save zip to temp_zip directory
            post_zip.save(os.path.join(temp_zip_db_fp, secure_filename(post_zip_filename)))
            zip_folder_name_nospaces = post_zip_filename.replace(" ", "_")

            # make path of new post dir 00##_post
            new_blog_dir_fp = os.path.join(current_app.config.get('DIR_BLOG_POSTS'), new_post_dir_name)
            logger_bp_blog.info(f"- new_blog_dir_fp: {new_blog_dir_fp} -")

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
            destination = current_app.config.get('DIR_BLOG_POSTS')

            dest = shutil.move(source, destination, copy_function = shutil.copytree) 
            logger_bp_blog.info(f"Destination path: {dest}") 

            # find root html file for post
            for file_name in os.listdir(dest):
                
                if file_name.endswith('.html'):
                    post_html_filename = file_name
                    post_html_file_name_and_path =  os.path.join(current_app.config.get('DIR_BLOG_POSTS'), 
                                            new_post_dir_name,post_html_filename)
                    post_html_filename = sanitize_directory_name(post_html_file_name_and_path)
                if os.path.isdir(os.path.join(dest,file_name)) and (
                        os.path.join(dest,file_name)[-4:] == '.fld' or 
                        os.path.join(dest,file_name)[-6:] == 'images'):
                    post_images_dir_name_and_path = os.path.join(dest,file_name)
                    post_images_dir_name = sanitize_directory_name(post_images_dir_name_and_path)
                    print("-----> post_images_dir_name:", post_images_dir_name)
                    new_blogpost.images_dir_name =post_images_dir_name

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

            # new_blogpost.images_dir_name = post_images_dir_name
            new_blogpost.word_doc_to_html_filename = post_html_filename
            new_blogpost.title = get_title(os.path.join(new_blog_dir_fp,post_html_filename), "origin_from_word")
            # sess_users.commit()

            logger_bp_blog.info(f"- filename is {new_post_dir_name} -")

            flash(f'Post added successfully!', 'success')
            return redirect(url_for('bp_blog.blog_edit', post_id = new_blog_id))

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

