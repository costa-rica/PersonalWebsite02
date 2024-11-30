# PersonalWebsite02Library

![nick-rodriguez.info Logo](https://nick-rodriguez.info/website_assets_favicon/logo02_whiteBck-180x112.png)

## Documentation

### To post blogs

Step 1: Convert .odt file to html

Step 2: Compress all .png files into an "images" folder

- compressed .zip file can be called anything it will ultimatly be renamed to "images" in the code.

Step 3: Code snippets

- compressed .zip file must be called "code_snippets".
- cut out all code snippets in the .html file and place them in their own .html files with the name "codeSnippet##-SomeDescription.html"
- the new "codeSnippet##-SomeDescription.html" should look like:
  ```
  <div class="div_code"><code>    start here
      Some code here... anything
  </code></div>
  ```
  - start code in the top line indented 4 spaces. Otherwise there will be an extra line.
  - OR you could just add a line to the bottom so the spaceing is the same on the top and bottom.
- compress these files into a "code_snippets" folder.

## .env

- Ubuntu server

```env
DATABASE_ROOT = "/home/nick/applications/databases/PersonalWebsite02/"
PROJECT_ROOT = "/home/nick/applications/PersonalWebsite02/"
PROJECT_RESOURCES_ROOT = "/home/nick/applications/project_resources/PersonalWebsite02/"
CONFIG_ROOT="/home/nick/applications/_config_files/"
CONFIG_FILE_NAME="config_personalWebsite02.json"
FLASK_CONFIG_TYPE='prod'
DB_NAME_BLOGPOST = "BlogPosts.db"
CONFIG_FILE_NAME_SUPPORT="support20231118.json"
API_URL = "http://localhost:5001"
BACKUP_ROOT = "/home/nick/applications/_backups"
TEMPORARILY_DOWN=0
```

- local workstation

```env
DATABASE_ROOT = /Users/nick/Documents/_databases/PersonalWebsite02/
PROJECT_ROOT = /Users/nick/Documents/PersonalWebsite02/
PROJECT_RESOURCES_ROOT = /Users/nick/Documents/_project_resources/PersonalWebsite02/
CONFIG_ROOT=/Users/nick/Documents/_config_files/
CONFIG_FILE_NAME="config_personalWebsite02.json"
FLASK_CONFIG_TYPE='dev'
DB_NAME_BLOGPOST = "BlogPosts.db"
CONFIG_FILE_NAME_SUPPORT="support20231118.json"
API_URL = "http://localhost:5001"
BACKUP_ROOT = "/home/nick/applications/_backups"
TEMPORARILY_DOWN=0
```
