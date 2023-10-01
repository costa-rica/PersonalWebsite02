from flask import current_app
from flask_login import current_user
import json
# import requests
# from datetime import datetime, timedelta
from pw_models import dict_sess, dict_engine, Users
# import time
# from flask_mail import Message
# from app_package import mail
import os
# from werkzeug.utils import secure_filename
# import zipfile
# import shutil
import logging
from logging.handlers import RotatingFileHandler
# import re
import pandas as pd
from datetime import datetime
import csv


#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_bp_admin = logging.getLogger(__name__)
logger_bp_admin.setLevel(logging.DEBUG)


#where do we store logging information
file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),"logs",'bp_admin.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_bp_admin.addHandler(file_handler)
logger_bp_admin.addHandler(stream_handler)

#return excel files formatted
def formatExcelHeader(workbook,worksheet, df, start_row):
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'align':'center',
        'border': 0})
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(start_row, col_num, value,header_format)
        width=len(value)+1 if len(value)>8 else 8
        worksheet.set_column(col_num,col_num,width)



# def load_database_util(text_file_name, limit_upload_flag):
def load_database_util(text_file_name, limit_upload_flag):
    #this util takes unzipped text file > converts to DF > appends to sqlite
    # print('***in load_database_util***')
    logger_bp_admin.info(f"- in load_database_util ")
    if "inv" in text_file_name:
        col_names=['NHTSA_ACTION_NUMBER', 'MAKE','MODEL','YEAR','COMPNAME',
            'MFR_NAME','ODATE','CDATE','CAMPNO','SUBJECT',
          'SUMMARY']
        if limit_upload_flag:
            df_inv=pd.read_csv(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], text_file_name),
                sep='\t', lineterminator='\r', names=col_names,header=None,nrows=1000)
        else:
            df_inv=pd.read_csv(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], text_file_name),
                sep='\t', lineterminator='\r', names=col_names,header=None)
        
        # This converts all column objects to dates then back to string. Note: sqlalchemy will convert back to date
        # as long as in the format %Y-%m-%d
        df_inv['ODATE']=pd.to_datetime(df_inv['ODATE'],format='%Y%m%d').dt.strftime('%Y-%m-%d')
        df_inv['CDATE']=pd.to_datetime(df_inv['CDATE'],format='%Y%m%d').dt.strftime('%Y-%m-%d')
        df_inv['km_notes']=''
        df_inv['date_updated']=pd.to_datetime(datetime.now())
        df_inv['files']=''
        df_inv['categories']=''
        df_inv['linked_records']=''
        df_inv['source_file']=text_file_name
        df_inv['source_file_notes']=''
        df_inv['NHTSA_ACTION_NUMBER']=df_inv['NHTSA_ACTION_NUMBER'].map(lambda x: x.lstrip('\n'))
        try:
            # df_inv.to_sql('investigations',db.engine, if_exists='append',index=False)
            df_inv.to_sql('investigations',engine, if_exists='append',index=False)
            return (f'Table successfully uploaded to database!', 'success')
        except:
            return (f"""Problem uploading: Check for 1)uniquness with id or RECORD_ID 2)date columns
                        are in a date format in excel.""",'warning')
    else:
        col_names=['RECORD_ID', 'CAMPNO', 'MAKETXT', 'MODELTXT', 'YEAR', 'MFGCAMPNO',
            'COMPNAME', 'MFGNAME', 'BGMAN', 'ENDMAN', 'RCLTYPECD', 'POTAFF',
            'ODATE', 'INFLUENCED_BY', 'MFGTXT', 'RCDATE', 'DATEA', 'RPNO', 'FMVSS',
            'DESC_DEFECT', 'CONSEQUENCE_DEFCT', 'CORRECTIVE_ACTION','NOTES',
            'RCL_CMPT_ID','MFR_COMP_NAME','MFR_COMP_DESC','MFR_COMP_PTNO']
        # df_re=pd.read_csv(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], text_file_name),
            # sep='\t', lineterminator='\r', names=col_names,header=None)

        # NOTE: Old prior to kmdashboard03 (Jun 2023)
        # if limit_upload_flag:
        #     df_re=pd.read_csv(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], text_file_name),
        #         names=col_names,header=None, sep='\t',nrows=1000)
        # else:
        #     df_re=pd.read_csv(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], text_file_name),
        #         names=col_names,header=None, sep='\t')

        df_re = read_FLAT_RCL_to_df(text_file_name, limit_upload_flag)

        df_re['YEAR']=df_re['YEARTXT'][:4]
        df_re.drop(['YEARTXT'], axis=1, inplace = True)
        df_re['BGMAN']=df_re['BGMAN'][:9]
        df_re['ENDMAN']=df_re['ENDMAN'][:9]
        df_re['ODATE']=df_re['ODATE'][:9]
        df_re['RCDATE']=df_re['RCDATE'][:9]
        df_re['DATEA']=df_re['DATEA'][:9]
        # try:
        # df_re['BGMAN']=pd.to_datetime(df_re['BGMAN'],format='%Y-%m-%d').dt.strftime('%Y-%m-%d')
        # except ValueError:
        df_re['BGMAN']=pd.to_datetime(df_re['BGMAN'],format='%Y%m%d').dt.strftime('%Y-%m-%d')
        # try:
        #     df_re['ENDMAN']=pd.to_datetime(df_re['ENDMAN'],format='%Y-%m-%d')
        # except ValueError:
        df_re['ENDMAN']=pd.to_datetime(df_re['ENDMAN'],format='%Y%m%d').dt.strftime('%Y-%m-%d')
        # df_re['ENDMAN']=pd.to_datetime(df_re['ENDMAN'],format='%Y-%m-%d')
        # try:
        #     df_re['ODATE']=pd.to_datetime(df_re['ODATE'],format='%Y-%m-%d')
        # except ValueError:
        df_re['ODATE']=pd.to_datetime(df_re['ODATE'],format='%Y%m%d').dt.strftime('%Y-%m-%d')
        # df_re['ODATE']=pd.to_datetime(df_re['ODATE'],format='%Y-%m-%d')
        # try:
        #     df_re['RCDATE']=pd.to_datetime(df_re['RCDATE'],format='%Y-%m-%d')
        # except ValueError:
        df_re['RCDATE']=pd.to_datetime(df_re['RCDATE'],format='%Y%m%d').dt.strftime('%Y-%m-%d')
        # df_re['RCDATE']=pd.to_datetime(df_re['RCDATE'],format='%Y-%m-%d')
        # df_re['DATEA']=pd.to_datetime(df_re['DATEA'],format='%Y-%m-%d')
        # try:
        #     df_re['DATEA']=pd.to_datetime(df_re['DATEA'],format='%Y-%m-%d')
        # except ValueError:
        df_re['DATEA']=pd.to_datetime(df_re['DATEA'],format='%Y%m%d').dt.strftime('%Y-%m-%d')
        df_re['km_notes']=''
        df_re['date_updated']=pd.to_datetime(datetime.now())
        df_re['files']=''
        df_re['categories']=''
        df_re['linked_records']=''
        df_re['source_file']=text_file_name
        df_re['source_file_notes']=''
        
        try:
            # df_re.to_sql('recalls',db.engine, if_exists='append',index=False)
            df_re.to_sql('recalls',engine, if_exists='append',index=False)
            return (f'Table successfully uploaded to database!', 'success')
        except:
            return (f"""Problem uploading: Check for 1)uniquness with id or RECORD_ID 2)date columns
            are in a date format in excel.""",'warning')

def fix_recalls_wb_util(df_re,text_file_name):
        df_re['YEAR']=df_re['YEAR'][:4]
        df_re['BGMAN']=df_re['BGMAN'][:9]
        df_re['ENDMAN']=df_re['ENDMAN'][:9]
        df_re['ODATE']=df_re['ODATE'][:9]
        df_re['RCDATE']=df_re['RCDATE'][:9]
        df_re['DATEA']=df_re['DATEA'][:9]
        df_re['BGMAN']=pd.to_datetime(df_re['BGMAN'],format='%Y/%m/%d').dt.strftime('%Y-%m-%d')
        df_re['ENDMAN']=pd.to_datetime(df_re['ENDMAN'],format='%Y/%m/%d').dt.strftime('%Y-%m-%d')
        df_re['ODATE']=pd.to_datetime(df_re['ODATE'],format='%Y/%m/%d').dt.strftime('%Y-%m-%d')
        df_re['RCDATE']=pd.to_datetime(df_re['RCDATE'],format='%Y/%m/%d').dt.strftime('%Y-%m-%d')
        df_re['DATEA']=pd.to_datetime(df_re['DATEA'],format='%Y/%m/%d').dt.strftime('%Y-%m-%d')
        df_re['km_notes']=''
        df_re['date_updated']=pd.to_datetime(datetime.now())
        df_re['files']=''
        df_re['categories']=''
        df_re['linked_records']=''
        df_re['source_file']=text_file_name
        df_re['source_file_notes']=''
        return df_re

def fix_investigations_wb_util(df_inv):
    # Stringify dates - this will avoid importing 000' for time
    df_inv['ODATE']=df_inv['ODATE'].dt.strftime('%Y-%m-%d')
    df_inv['CDATE']=df_inv['CDATE'].dt.strftime('%Y-%m-%d')
    return df_inv

def read_FLAT_RCL_to_df(text_file_name, limit_upload_flag):
    logger_bp_admin.info(f"- in read_FLAT_RCL_to_df ")
    # Initialize an empty list to store the data
    data = []
    if limit_upload_flag:
        last_row = 1000
    else:
        last_row = 1 * 10**7
    # Open the file in read mode
    with open(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], text_file_name), 'r') as file:
        # Create a CSV reader object
        reader = csv.reader(file, delimiter='\t')
        
        # Skip the header line
        next(reader)
        
        # Iterate over each line in the file
        for line_number, line in enumerate(reader, start=2):
            if line_number > last_row:
                break
            try:
                # Access the fields based on their indices
                record_id = int(line[0])
                campno = line[1]
                maketxt = line[2]
                modeltxt = line[3]
                yeartxt = line[4]
                mfgcampno = line[5]
                compname = line[6]
                mfgname = line[7]
                bgman = datetime.strptime(line[8], "%Y%m%d") if "date" in line[8].lower() else line[8]
                endman = datetime.strptime(line[9], "%Y%m%d") if "date" in line[9].lower() else line[9]
                rcltypecd = line[10]
    #             potaff = int(line[11])
                # potaff = float(line[11])
                potaff = None if line[11] =="" else line[11]
                odate = datetime.strptime(line[12], "%Y%m%d") if "date" in line[12].lower() else line[12]
                influenced_by = line[13]
                mfgtxt = line[14]
                rcdate = datetime.strptime(line[15], "%Y%m%d") if "date" in line[15].lower() else line[15]
                datea = datetime.strptime(line[16], "%Y%m%d") if "date" in line[16].lower() else line[16]
                rpno = line[17]
                fmvss = line[18]
                desc_defect = line[19]
                consequence_defect = line[20]
                corrective_action = line[21]
                notes = line[22]
                rcl_cmpt_id = line[23]
                mfr_comp_name = line[24]
                mfr_comp_desc = line[25]
                mfr_comp_ptno = line[26]
                
                # Append the fields to the data list as a tuple
                data.append((record_id, campno, maketxt, modeltxt, yeartxt, mfgcampno, compname, mfgname, bgman, endman,
                            rcltypecd, potaff, odate, influenced_by, mfgtxt, rcdate, datea, rpno, fmvss, desc_defect,
                            consequence_defect, corrective_action, notes, rcl_cmpt_id, mfr_comp_name, mfr_comp_desc,
                            mfr_comp_ptno))
                
            except IndexError:
                print(f"Skipping line {line_number}: Invalid number of fields")

    # if limit_upload_flag:
        # Create a DataFrame from the collected data
    df = pd.DataFrame(data, columns=["RECORD_ID", "CAMPNO", "MAKETXT", "MODELTXT", "YEARTXT", "MFGCAMPNO", "COMPNAME",
                                    "MFGNAME", "BGMAN", "ENDMAN", "RCLTYPECD", "POTAFF", "ODATE", "INFLUENCED_BY",
                                    "MFGTXT", "RCDATE", "DATEA", "RPNO", "FMVSS", "DESC_DEFECT", "CONSEQUENCE_DEFECT",
                                    "CORRECTIVE_ACTION", "NOTES", "RCL_CMPT_ID", "MFR_COMP_NAME", "MFR_COMP_DESC",
                                    "MFR_COMP_PTNO"])
    
    logger_bp_admin.info(f"- finished read_FLAT_RCL_to_df, df count: {len(df)} ")
    return df


def handleDateColumns(pandasSeries):
    # Convert each row to a string with the desired format 'YYYY-MM-DD' or set it as '9999-01-01'
    pandasSeries = pandasSeries.apply(lambda x: x.strftime('%Y-%m-%d') if isinstance(x, datetime) else x)

    # Validate the date format and replace non-date strings with '9999-01-01'
    pandasSeries = pd.to_datetime(pandasSeries, errors='coerce').dt.strftime('%Y-%m-%d').fillna('9999-01-01')

    for _, row in df_inv.iterrows():
        try:
            example_row = ExampleTable(date_column=datetime.strptime(pandasSeries, '%Y-%m-%d').date())
            session.add(example_row)
        except Exception as e:
    #         print(f"Error processing row: {row} - {e}")
            pass


