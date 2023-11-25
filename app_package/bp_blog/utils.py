# import pandas as pd
import os
from flask import current_app
from pw_models import dict_sess, Users, BlogPosts
import logging
from logging.handlers import RotatingFileHandler
from bs4 import BeautifulSoup
import re
# import requests
# from urllib.parse import urljoin


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

sess_users = dict_sess['sess_users']

def create_blog_posts_list(number_of_posts_to_return=False):
    #Blog
    blog_posts = sess_users.query(BlogPosts).all()

    blog_posts_list =[]
    for post in blog_posts:
        if post.date_published in ["", None]:
            post_date = post.time_stamp_utc.strftime("%Y-%m-%d")
        else:
            post_date = post.date_published.strftime("%Y-%m-%d")
        post_title = post.title
        post_description = post.description if post.description != None else "No description"
        
        
        if post.post_dir_name != None:## Blogpost is an Article
            post_string_id = post.post_dir_name
            if post.blogpost_index_image_filename not in ["", None, "no_image"]:
                # blogpost_image = os.path.join(current_app.config.get('DIR_DB_AUX_BLOG_POSTS'), post.images_dir_name, post.blogpost_index_image_filename)
                blog_posts_list.append((post_date,post_title,post_description,
                    post_string_id,post.blogpost_index_image_filename,post.post_dir_name, post.images_dir_name))
            else:
                blog_posts_list.append((post_date,post_title,post_description,post_string_id))
        else:## BlogPost is a link
            post_string_id = post.url
            # favicon_obj = get_favicon(post.url)
            # print("----> favicon_obj: ", favicon_obj)
            # meta_content_obj = get_meta_description(post.url)
            if post.icon_file != None:
                icon_filename = post.icon_file
            else:
                
                icon_filename = "medium.png"
            print("---> post.icon_file: ", post.icon_file)
            blog_posts_list.append((post_date,post_title,post_description,post_string_id,icon_filename))
        # blog_posts_list.append((post_date,post_title,post_description,post_string_id))
    

    blog_posts_list.sort(key=lambda tuple_element: tuple_element[0], reverse=True)
    if number_of_posts_to_return:
        blog_posts_list = blog_posts_list[:number_of_posts_to_return]

    # print("- blog_posts_list -")
    # print(blog_post_list_most_recent)

    return blog_posts_list

# replace the code snippet
def replace_code_snippet_jinja(blog_post_index_file_path_and_name):

    try:
        #read html into beautifulsoup
        with open(blog_post_index_file_path_and_name) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
    except FileNotFoundError:
        return "Error opening index.html"



    # Define the style to match
    target_style = "line-height: 100%; margin-bottom: 0in; background: #000000"
    # Extract the path from the variable
    directory_path_code_snippet = os.path.dirname(blog_post_index_file_path_and_name)
    # Get a list of filenames in the directory, sorted in ascending order
    # filenames = sorted([f for f in os.listdir(directory_path) if f.startswith(('01', '02'))])
    filenames = sorted([f for f in os.listdir(directory_path_code_snippet) if f[:2].isdigit()])

    # Iterate over each <p> element and replace it with the corresponding Jinja include statement
    for i, p in enumerate(soup.find_all('p', style=target_style)):
        if i < len(filenames):
            include_statement = f"{{% include '{filenames[i]}' %}}"
            p.replace_with(include_statement)
        else:
            break  # Break the loop if there are more <p> tags than files



    # print(soup)
    return str(soup)

def replace_img_src_jinja(blog_post_index_file_path_and_name, img_dir_name):
    
    logger_bp_blog.info(f"- Reading file to replace img src jinja: {blog_post_index_file_path_and_name} -")
    logger_bp_blog.info(blog_post_index_file_path_and_name)
    
    try:
        #read html into beautifulsoup
        with open(blog_post_index_file_path_and_name) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
    except FileNotFoundError:
        return "Error opening index.html"

    #get all images tags in html
    image_list = soup.find_all('img')


    # check all images have src or remove
    # for img in image_list:
    for img in soup.find_all('img'):
        # temp_dict = {}
        try:
            if img.get('src') == "":
                image_list.remove(img)
                # print("removed img")
            else:
                # print("***** REPLACING src *****")
                # img['src'] = "{{ url_for('blog.custom_static', post_id_name_string=post_id_name_string,img_dir_name='" + \
                #     img['src'][:img['src'].find("/")] \
                #     +"', filename='"+ img['src'][img['src'].find("/")+1:]+"')}}"
                img['src'] = "{{ url_for('bp_blog.get_post_files', post_dir_name=post_dir_name,img_dir_name='" + \
                    img_dir_name \
                    +"', filename='"+ img['src'][img['src'].find("/")+1:]+"')}}"
        except AttributeError:
            image_list.remove(img)
            # print('removed img with exception')



    # print(soup)
    return str(soup)


def get_title(html_file_path_and_name, index_source):
    print("- In: blog/utils/get_title() -")
    title = ""
    #read html into beautifulsoup
    with open(html_file_path_and_name) as fp:
        soup = BeautifulSoup(fp, 'html.parser')

    # if index_source == "ms_word":
    if index_source == "origin_from_word":
        try:
            title = soup.p.find('span').contents[0]
        except:
            logger_bp_blog.info(f"- No title found ms_word -")

    # elif index_source == "original_html":
    elif index_source == "origin_from_html":
        list_of_soup_searches = ["h1", "h2", "h3", "h4"]
        
        for tag in list_of_soup_searches:
            title_tag = soup.find(tag)
            print("title_tag: ", title_tag)
            print("Examining tag: ", tag)
            if title_tag != None:
                break
        try:
            print("Getting contents for tag: ", tag)
            print(title_tag.contents[0])
            title=title_tag.contents[0]
        except:
            logger_bp_blog.info(f"- No title found origina_html  -")


    return title


def sanitize_directory_name(directory_path):
    # cleans file directory_path name, renames dir if necessary, returns directory_path string
    logger_bp_blog.info(f"- in sanitize_directory_name  -")
    # Get the directory name from the path
    directory_name = os.path.basename(directory_path)
    print("directory_name: ", directory_name)

    # # Remove non-alphanumeric characters
    # directory_name = re.sub(r'\W+', '', directory_name)

    # Remove .fld
    directory_name = re.sub('.fld', '', directory_name)


    # Replace spaces with underscores
    directory_name = directory_name.replace(' ', '_')
    print("directory_name (sanatized): ", directory_name)

    # Create the new directory path with the sanitized name
    new_directory_path = os.path.join(os.path.dirname(directory_path), directory_name)
    print("new_directory_path (sanatized): ", new_directory_path)

    # Rename the directory if the sanitized name is different
    if directory_path != new_directory_path:
        os.rename(directory_path, new_directory_path)
        print("Directory name sanitized and renamed successfully.")
    else:
        print("No changes needed.")
    
    return directory_name

def read_html_to_soup(blog_post_index_file_path_and_name):
    # Read the HTML file
    with open(blog_post_index_file_path_and_name, 'r', encoding='utf-8') as file:
        html_content = file.read()
    # Parse with Beautiful Soup
    soup = BeautifulSoup(html_content, 'html.parser')
    return str(soup)

def remove_head(html_content):
    # # Read the HTML file
    # with open(blog_post_index_file_path_and_name, 'r', encoding='utf-8') as file:
    #     html_content = file.read()

    # Parse with Beautiful Soup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove the <head> element
    if soup.head:
        soup.head.decompose()

    return str(soup)


def remove_body_tags(html_content):
    # # Read the HTML file
    # with open(blog_post_index_file_path_and_name, 'r', encoding='utf-8') as file:
    #     html_content = file.read()

    # Parse with Beautiful Soup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract content within <body> tags
    body_contents = ''.join(str(tag) for tag in soup.body.contents) if soup.body else str(soup)

    return str(body_contents)


def replace_p_elements_with_img(html_content):
    # Parse with Beautiful Soup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all 'p' tags 
    p_tags = soup.find_all('p')

    for p_tag in p_tags:
        # Check if 'p' tag contains an 'img' element
        img = p_tag.find('img')
        if img:
            # Create a new 'div' with class 'blog_img'
            new_div = soup.new_tag('div', **{'class': 'blog_img'})
            # Move the 'img' element to the new 'div'
            new_div.append(img.extract())
            # Replace the 'p' tag with the new 'div'
            p_tag.replace_with(new_div)

    return str(soup)

def remove_line_height_from_p_tags(html_content):
    # Parse with Beautiful Soup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Iterate through each 'p' tag and modify its 'style' attribute
    for p_tag in soup.find_all('p'):
        style = p_tag.get('style', '')  # Get the current 'style' attribute
        if 'line-height: 100%;' in style:
            # Remove 'line-height: 100%;' from the style
            new_style = style.replace('line-height: 100%;', '')
            # Update the 'style' attribute of the 'p' tag
            p_tag['style'] = new_style

    # Convert the modified soup_body back to string
    final_html_content = str(soup)

    return str(soup)

