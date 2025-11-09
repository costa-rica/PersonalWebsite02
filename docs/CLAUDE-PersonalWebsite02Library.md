# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

PersonalWebsite02Library is a Python library package that provides essential modules for the PersonalWebsite02 Flask application. It contains configuration classes, SQLAlchemy database models, and utility tools for blog post processing.

## Installation & Development

**Install the library in editable mode (recommended for development):**

```bash
# From the PersonalWebsite02Library directory
pip install -e .
```

Editable mode allows changes to the library code to be immediately available without reinstalling.

**Standard installation:**

```bash
pip install .
```

**Build the package:**

```bash
python setup.py sdist bdist_wheel
```

**Verify installation:**
After installation, verify all subpackages are available:

```bash
python -c "from setuptools import find_packages; print('\n'.join(find_packages()))"
```

Should show: `pw_config`, `pw_models`, `pw_tools`, `pw_tools.blog`, `pw_tools._common`

## Environment Configuration

This library requires a `.env` file with specific environment variables. The configuration is loaded at runtime via `pw_config/config.py`.

**Critical environment variables:**

- `FLASK_CONFIG_TYPE`: Determines configuration class ('dev', 'prod', or defaults to workstation)
- `WS_CONFIG_TYPE`: Used by pw_tools for config selection (matches FLASK_CONFIG_TYPE pattern)
- `DATABASE_ROOT`: Path to database directory
- `PROJECT_ROOT`: Path to main Flask application
- `PROJECT_RESOURCES_ROOT`: Path to project resources (blog posts, assets, logs, media)
- `CONFIG_ROOT`: Path to directory containing config JSON files
- `CONFIG_FILE_NAME`: Name of main config JSON file (e.g., "config_personalWebsite02.json")
- `DB_NAME_BLOGPOST`: Database filename (default: "BlogPosts.db")

The library expects an external JSON configuration file (location specified by `CONFIG_ROOT` + `CONFIG_FILE_NAME`) containing sensitive keys like `SECRET_KEY`, mail server credentials, API keys, and admin settings.

## Architecture

### Module Structure

**pw_config/** - Configuration classes

- `config.py`: Contains `ConfigBasic`, `ConfigWorkstation`, `ConfigDev`, `ConfigProd` classes
- Loads settings from environment variables and external JSON config file
- Sets up database paths, project resource directories, email configuration, and captcha settings

**pw_models/** - SQLAlchemy ORM models

- `Base.py`: Creates SQLAlchemy Base, engine, and DatabaseSession factory
- `modelsUsers.py`: Contains two models:
  - `Users`: Authentication model with email, password, permissions, and password reset tokens
  - `BlogPosts`: Blog content model with fields for title, description, category, post directory structure, images, code snippets, tags, and publication date
- `config.py`: Small helper that imports the appropriate config based on environment

**pw_tools/** - Utility functions

- `_common/config_and_logger.py`: Sets up shared logger and config for tools
- `blog/blog_upload_tools.py`: BeautifulSoup-based functions for processing blog post HTML:
  - Converting image src attributes to Jinja2 templates
  - Replacing code snippet filenames with Jinja2 include blocks
  - Extracting titles from HTML (handles both Word-generated and hand-written HTML)
  - Sanitizing directory names
  - Removing/modifying HTML elements (head, body tags, p elements, spans)

### Database Structure

Uses SQLite with SQLAlchemy ORM. Database URI: `sqlite:///{DATABASE_ROOT}{DB_NAME_BLOGPOST}`

**Key relationships:**

- `Users.posts` → one-to-many with `BlogPosts` via `BlogPosts.user_id`

**BlogPosts important fields:**

- `post_dir_name`: Directory name in PROJECT_RESOURCES_ROOT/blog/posts/
- `post_html_filename`: Main HTML file for the post
- `image_filename_for_blogpost_home`: Featured image for blog index page
- `type_for_blogpost_home`: Either "article" (full post) or "link" (external URL)
- `has_images`, `has_code_snippets`: Boolean flags for post content types
- `icon_file`: Icon displayed on blog home page
- `url`: For external link-type posts

### Directory Structure (Runtime)

The library expects the following directory structure at runtime (paths defined by environment variables):

```
{PROJECT_RESOURCES_ROOT}/
├── assets/
│   ├── images/
│   └── favicons/
├── blog/
│   ├── posts/          # Each blog post has its own subdirectory
│   │   └── {post_dir_name}/
│   │       ├── index.html or {post_html_filename}
│   │       ├── images/
│   │       └── code_snippets/
│   └── icons/
├── logs/               # Application logs (ws_analysis.log)
└── media/

{DATABASE_ROOT}/
├── BlogPosts.db
├── db_upload/
└── db_download/
```

## Blog Post Processing Workflow

The blog upload tools process HTML from Word documents or hand-written HTML:

1. **Title extraction**: Uses BeautifulSoup to find first h1-h4 tag (hand-written) or span in first p tag (Word-generated)
2. **Image src replacement**: Converts all img src attributes to Jinja2 `url_for()` calls
3. **Code snippet embedding**: Replaces p tags containing code snippet filenames with Jinja2 `{% include %}` blocks
4. **HTML cleanup**: Removes head tags, unwraps body tags, converts p+img to div.blog_img
5. **Styling cleanup**: Removes line-height from p tags, removes background styling from spans

## Configuration Classes

Three configuration classes inherit from `ConfigBasic`:

- **ConfigWorkstation**: For local development (DEBUG=True)
- **ConfigDev**: For development server (DEBUG=True, TEMPLATES_AUTO_RELOAD=True)
- **ConfigProd**: For production (DEBUG=False, TESTING=False, PROPAGATE_EXCEPTIONS=True)

Selection is based on `FLASK_CONFIG_TYPE` environment variable ('dev', 'prod', or defaults to workstation).

## Important Notes

- Database sessions must be manually closed when using `DatabaseSession()` (see `Users.verify_reset_token()` for pattern)
- The logger writes to `{PROJECT_RESOURCES_ROOT}/logs/ws_analysis.log` with 5MB rotation
- Blog post processing functions use BeautifulSoup with 'html.parser'
- Configuration loading happens at module import time, so environment variables must be set before importing
