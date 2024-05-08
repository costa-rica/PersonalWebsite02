from flask import current_app
from flask_login import current_user
import json
# from ws_models import sess, engine, Users
from ws_models import engine, Users
import os
import logging
from logging.handlers import RotatingFileHandler
import pandas as pd
from datetime import datetime
import csv
from app_package._common.utilities import custom_logger


logger_bp_admin = custom_logger('bp_admin.log')


def get_user_loc_day_tuple(users_list):

    users_user_loc_day_tuples = []

    for user in users_list:
        # Ensure there are location days to evaluate
        if user.loc_day:
            # List comprehension to collect all date_time_utc_user_check_in values for the user
            dates = [loc_day.date_time_utc_user_check_in for loc_day in user.loc_day]
            
            # Calculate the min and max dates
            date_min = min(dates) if dates else None
            date_max = max(dates) if dates else None
            if date_min:
                date_min = date_min.strftime("%Y-%m-%d")
            if date_max:
                date_max = date_max.strftime("%Y-%m-%d")
        else:
            date_min = None
            date_max = None

        count_of_user_loc_day = len(user.loc_day)
        users_user_loc_day_tuples.append((user, count_of_user_loc_day, date_min, date_max))
    
    return users_user_loc_day_tuples



