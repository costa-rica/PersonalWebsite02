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



# def get_favicon(url):
#     response = requests.get(url)
#     soup = BeautifulSoup(response.content, 'html.parser')
#     link = soup.find("link", rel="icon")
#     if link:
#         favicon_url = link['href']
#         if favicon_url.startswith('/'):
#             favicon_url = url + favicon_url
#         return favicon_url
#     # If no favicon in HTML, try the default location
#     return f"{url.rstrip('/')}/favicon.ico"

# # favicon_url = get_favicon("https://www.example.com")

# def get_meta_description(url):
#     response = requests.get(url)
#     soup = BeautifulSoup(response.content, 'html.parser')
#     meta_desc = soup.find("meta", attrs={"name": "description"})
#     if meta_desc:
#         return meta_desc['content']
#     return None

# # description = get_meta_description("https://www.example.com")



# def download_favicon(url):
#     try:
#         # Send a GET request to the URL
#         response = requests.get(url)
#         response.raise_for_status()
        
#         # Parse the HTML content of the page
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         # Find the link to the favicon
#         favicon_link = soup.find("link", rel="icon") or soup.find("link", rel="shortcut icon")
#         if favicon_link is None:
#             print("Favicon not found on the webpage.")
#             return

#         # Get the href attribute of the favicon link
#         favicon_url = favicon_link.get('href')
#         if favicon_url is None:
#             print("Favicon link found, but it does not have a 'href' attribute.")
#             return
        
#         # Make the favicon URL absolute if it is relative
#         favicon_url = urljoin(url, favicon_url)
        
#         # Download the favicon
#         response = requests.get(favicon_url)
#         response.raise_for_status()
        
#         # Write the content to a file
#         favicon_filename = "favicon.ico"
#         with open(favicon_filename, 'wb') as f:
#             f.write(response.content)
        
#         print(f"Favicon downloaded successfully and saved as {favicon_filename}")
        
#     except requests.HTTPError as http_err:
#         print(f"HTTP error occurred: {http_err}")
#     except Exception as err:
#         print(f"An error occurred: {err}")

# # if __name__ == "__main__":
# #     url = input("Enter the URL of the website: ")
# #     download_favicon(url)

