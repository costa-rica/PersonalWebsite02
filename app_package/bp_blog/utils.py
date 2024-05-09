import os
from flask import current_app
from pw_models import BlogPosts
import re
from app_package._common.utilities import custom_logger, wrap_up_session
import shutil
import zipfile

logger_bp_blog = custom_logger('bp_blog.log')


def create_blog_posts_list(db_session, number_of_posts_to_return=False):

    blog_posts = db_session.query(BlogPosts).all()

    blog_posts_list =[]
    for post in blog_posts:
        if post.date_published in ["", None]:
            post_date = post.time_stamp_utc.strftime("%Y-%m-%d")
        else:
            post_date = post.date_published.strftime("%Y-%m-%d")
        post_title = post.title
        post_description = post.description if post.description != None else "No description"
        
        if post.type_for_blogpost_home == "article":                  ## Blogpost is an Article

            if post.has_images:
                flag_use_image_from_blogpost_in_blog_home = False
                if post.image_filename_for_blogpost_home in os.listdir(os.path.join(
                    current_app.config.get('DIR_BLOG_POSTS'), f"{post.id:04d}_post","images")):
                    flag_use_image_from_blogpost_in_blog_home = True

                blog_posts_list.append((
                                        post.type_for_blogpost_home,# new 20240509
                                        post_date,
                                        post_title,
                                        post_description,
                                        str(post.id),# < --- used to create link to blog article
                                        post.image_filename_for_blogpost_home,
                                        post.post_dir_name, 
                                        flag_use_image_from_blogpost_in_blog_home
                                        ))
            else:
                blog_posts_list.append((
                                        post.type_for_blogpost_home,# new 20240509
                                        post_date,
                                        post_title,
                                        post_description,
                                        str(post.id),# < --- used to create link to blog article
                                        post.image_filename_for_blogpost_home
                                        ))
        
        else:                                           ## BlogPost is a Link to other site
            post_string_id = post.url

            if post.icon_file != None:
                icon_filename = post.icon_file
            else:
                icon_filename = "medium.png"

            logger_bp_blog.info(f"---> post.icon_file: {post.icon_file}")
            blog_posts_list.append((
                                    post.type_for_blogpost_home,# new 20240509
                                    post_date,
                                    post_title,
                                    post_description,
                                    # post_string_id,
                                    post.url,# < --- used to create link to outside website with my article
                                    icon_filename))
    

    blog_posts_list.sort(key=lambda tuple_element: tuple_element[1], reverse=True)
    if number_of_posts_to_return:
        blog_posts_list = blog_posts_list[:number_of_posts_to_return]


    return blog_posts_list


def remove_MACOSX_files(unzipped_temp_dir):

    unzipped_dir_list = [ f.path for f in os.scandir(unzipped_temp_dir) if f.is_dir() ]
    
    # delete the __MACOSX dir
    for path_str in unzipped_dir_list:
        if path_str[-8:] == "__MACOSX":
            shutil.rmtree(path_str)
            logger_bp_blog.info(f"- removed {path_str[-8:]} -")

def check_for_dir_if_not_exist_make_dir(dir_to_make_path):

    if not os.path.exists(dir_to_make_path):
        os.mkdir(dir_to_make_path)
    else:
        shutil.rmtree(dir_to_make_path)
        os.mkdir(dir_to_make_path)
        logger_bp_blog.info(f"- created: {dir_to_make_path} -")

def unzip_blog_files_and_extract_to_dir(temp_zip_db_fp, zip_folder_name_nospaces, sub_folder_name=None):

    # decompress uploaded IMAGES file in temp_zip
    dir_name_for_unzip_and_extract = os.path.join(temp_zip_db_fp, zip_folder_name_nospaces)
    with zipfile.ZipFile(dir_name_for_unzip_and_extract, 'r') as zip_ref:
    # with zipfile.ZipFile(os.path.join(temp_zip_db_fp, zip_folder_name_nospaces), 'r') as zip_ref:
        logger_bp_blog.info("- unzipping file --")
        logger_bp_blog.info(zip_ref.namelist())
        unzipped_files_dir_name = zip_ref.namelist()[0]
        # unzipped_temp_dir = os.path.join(temp_zip_db_fp, "images")
        if sub_folder_name:
            unzipped_temp_dir = os.path.join(temp_zip_db_fp, sub_folder_name)
        else:
            unzipped_temp_dir = os.path.join(temp_zip_db_fp)
        zip_ref.extractall(unzipped_temp_dir)

# def delete_old_write_new_index_html(new_blog_dir_file_path, new_blogpost, new_index_text):
def delete_old_write_new_index_html(new_blog_post_path_and_file_name, new_index_text):
    
    if os.path.exists(new_blog_post_path_and_file_name):
        # remove existing post_html_filename
        os.remove(new_blog_post_path_and_file_name)

    # write a new index.html with new code that references images in image folder
    index_html_writer = open(new_blog_post_path_and_file_name, "w")
    index_html_writer.write(new_index_text)
    index_html_writer.close()



