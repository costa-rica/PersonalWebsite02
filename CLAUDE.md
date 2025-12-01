# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based personal website application with blog functionality, user authentication, and administrative features. The application uses SQLAlchemy with SQLite databases and follows Flask's blueprint pattern for modular organization.

## Development Commands

### Running the Application

```bash
# Development mode
flask run
```

The application entry point is `run.py`. Flask configuration is controlled via `.flaskenv` (sets FLASK_APP=run) and `.env` (environment-specific settings).

### Python Dependencies

```bash
# Install dependencies
pip install -r req_personalWebsite02.txt
```

Note: The application depends on an external library called PersonalWebsite02Library (currently commented out in requirements). This library provides:
- `pw_models`: Database models (Base, engine, DatabaseSession, Users, BlogPosts)
- `pw_config`: Configuration classes (ConfigWorkstation, ConfigDev, ConfigProd)
- `pw_tools`: Blog utilities (HTML processing, code snippet replacement, image handling)

**See `docs/CLAUDE-PersonalWebsite02Library.md` for detailed documentation on `pw_config`, `pw_tools`, and `pw_models`.**

## Architecture

### Application Factory Pattern

The app uses the factory pattern via `create_app()` in `app_package/__init__.py`:
- Initializes Flask extensions (LoginManager, Mail, secure headers)
- Creates necessary directories for databases, project resources, assets, blog posts, logs, and media
- Automatically creates SQLite database if it doesn't exist
- Registers all blueprints

### Configuration System

Configuration is environment-aware (app_package/_common/config.py:4-13):
- Uses `FLASK_CONFIG_TYPE` environment variable to select config
- Options: 'dev' (ConfigDev), 'prod' (ConfigProd), default (ConfigWorkstation)
- Each config class imported from external `pw_config` library

### Blueprint Structure

The application is organized into six blueprints:

1. **bp_main**: Core pages (home, about, resume)
2. **bp_users**: Authentication (login, logout, registration, password reset)
3. **bp_blog**: Blog functionality (posting, viewing, managing blog posts)
4. **bp_admin**: Administrative features
5. **bp_support**: Support-related features
6. **bp_error**: Error handling routes

Each blueprint follows this structure:
- `routes.py`: Route definitions
- `utils.py`: Blueprint-specific utilities (where applicable)

### Database Management

- Uses SQLAlchemy with SQLite backend
- Database session management via Flask's `g` object and `teardown_appcontext`
- Session lifecycle in `app_package/_common/utilities.py:23-32`
- Database location controlled by environment variables (DATABASE_ROOT, DB_NAME_BLOGPOST)

### Logging System

Custom logging implementation (app_package/_common/utilities.py:36-92):
- Rotating file handlers (5MB max, 2 backups)
- Per-blueprint loggers via `custom_logger(logger_filename)`
- Logs stored in PROJECT_ROOT/logs/
- Timezone-aware logging (Europe/Paris)

## Styling and Frontend Assets

**IMPORTANT:** This application uses SASS/SCSS for styling. All style modifications should be made to the source SCSS files in `app_package/static/scss/`, NOT directly to the compiled CSS files.

### SCSS Structure

- **Source files**: `app_package/static/scss/`
  - `style.scss`: Main SCSS file that imports all partials
  - `_main.scss`: Styles for main pages (home, about, resume, etc.)
  - `_navbar.scss`: Navigation styles
  - `_buttons.scss`: Button styles
  - `_users.scss`: User authentication pages
  - `_blog.scss`: Blog-related styles
  - `_support.scss`: Support pages
  - `_admin.scss`: Admin pages

- **Compiled output**: `app_package/static/css/`
  - `style.css`: Compiled CSS (auto-generated, do not edit directly)
  - `style.css.map`: Source map for debugging

### Workflow for Style Changes

1. Modify the appropriate SCSS file in `app_package/static/scss/`
2. Compile SCSS to CSS using the Sass compiler:
   ```bash
   sass app_package/static/scss/style.scss app_package/static/css/style.css
   ```
3. The compiled CSS will be automatically used by the application

## Blog Posting Workflow

The blog system has a specific workflow for creating posts (from README.md):

1. Convert .odt file to HTML
2. Compress all .png files into an "images" folder (.zip can have any name, will be renamed)
3. Extract code snippets:
   - Create separate .html files named "codeSnippet##-SomeDescription.html"
   - Format: `<div class="div_code"><code>` with code indented 4 spaces
   - Compress into "code_snippets.zip"

Blog utilities handle:
- Unzipping and extracting blog files
- Replacing code snippet filenames with Jinja include blocks
- Processing image sources for Jinja templates
- HTML sanitization and formatting

## Environment Configuration

Key environment variables (.env):
- `DATABASE_ROOT`: Database storage location
- `PROJECT_ROOT`: Application root directory
- `PROJECT_RESOURCES_ROOT`: Static resources (blog posts, images, favicons)
- `CONFIG_ROOT`: External configuration files directory
- `CONFIG_FILE_NAME`: Main config file (config_personalWebsite02.json)
- `FLASK_CONFIG_TYPE`: Environment type ('dev', 'prod', or workstation)
- `DB_NAME_BLOGPOST`: Blog database filename (BlogPosts.db)
- `API_URL`: API endpoint (default: http://localhost:5001)
- `TEMPORARILY_DOWN`: Feature flag for maintenance mode (0 or 1)

## Directory Structure Created at Startup

The application creates these directories if they don't exist (app_package/__init__.py:41-56):
- Database: uploads, downloads
- Project resources: assets (images, favicons), blog posts, logs, media

## Authentication

- Uses Flask-Login extension
- Login manager configured in `app_package/_common/utilities.py:10-21`
- User loader queries Users table from database
- Login view: 'bp_users.login'

## Important Notes

- Python 3.11+ required
- Database sessions should be accessed via `g.db_session`
- The `wrap_up_session()` utility is marked as OBE (overcome by events) due to teardown_appcontext handling
- Security headers implemented via `secure` library
- Email functionality available through Flask-Mail
