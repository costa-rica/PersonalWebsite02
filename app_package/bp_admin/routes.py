
from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory, make_response
import bcrypt
from flask_login import login_required, login_user, logout_user, current_user
import logging
from logging.handlers import RotatingFileHandler
import os
import json
from pw_models import dict_sess, dict_engine, text, dict_base, Users
from app_package.bp_users.utils import send_reset_email, send_confirm_email, \
    userPermission
from app_package.bp_admin.utils import formatExcelHeader, \
    load_database_util, fix_recalls_wb_util, fix_investigations_wb_util
import pandas as pd
import shutil
from datetime import datetime
import openpyxl


import zipfile



#Setting up Logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter_terminal = logging.Formatter('%(asctime)s:%(filename)s:%(name)s:%(message)s')

#initialize a logger
logger_bp_admin = logging.getLogger(__name__)
logger_bp_admin.setLevel(logging.DEBUG)

file_handler = RotatingFileHandler(os.path.join(os.environ.get('PROJECT_ROOT'),'logs','bp_admin.log'), mode='a', maxBytes=5*1024*1024,backupCount=2)
file_handler.setFormatter(formatter)

#where the stream_handler will print
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter_terminal)

# logger_sched.handlers.clear() #<--- This was useful somewhere for duplicate logs
logger_bp_admin.addHandler(file_handler)
logger_bp_admin.addHandler(stream_handler)


salt = bcrypt.gensalt()


bp_admin = Blueprint('bp_admin', __name__)
sess_users = dict_sess['sess_users']

@bp_admin.before_request
def before_request():
    logger_bp_admin.info(f"-- ***** in before_request route --")
    ###### TEMPORARILY_DOWN: redirects to under construction page ########
    if os.environ.get('TEMPORARILY_DOWN') == '1':
        if request.url != request.url_root + url_for('bp_main.temporarily_down')[1:]:
            # logger_bp_users.info("*** (logger_bp_users) Redirected ")
            logger_bp_admin.info(f'- request.referrer: {request.referrer}')
            logger_bp_admin.info(f'- request.url: {request.url}')
            return redirect(url_for('bp_main.temporarily_down'))

@bp_admin.route('/admin_page', methods = ['GET', 'POST'])
@login_required
def admin_page():
    users_list=[i.email for i in sess_users.query(Users).all()]
    
    with open(os.path.join(current_app.config['DIR_DB_FILES_UTILITY'],'added_users.txt')) as json_file:
        get_users_dict=json.load(json_file)
        json_file.close()
    # get_users_list=list(get_users.keys())
    if request.method == 'POST':
        formDict = request.form.to_dict()
        print('formDict:::', formDict)
        if formDict.get('add_privilege'):
            
            get_users_dict[formDict.get('add_user')]='add privilege'
        else:
            get_users_dict[formDict.get('add_user')]='no add privileges'
        
        added_users_file=os.path.join(current_app.config['DIR_DB_FILES_UTILITY'], 'added_users.txt')
        with open(added_users_file, 'w') as json_file:
            json.dump(get_users_dict, json_file)
        
        return redirect(url_for('users.admin'))
    return render_template('admin/admin.html', users_list=get_users_dict)



@bp_admin.route('/database_page', methods=["GET","POST"])
@login_required
def database_page():
    tableNamesList=['investigations','tracking_inv','recalls','tracking_re','user']
    # tableNamesList= db.engine.table_names()
    legend='Database downloads'
    if request.method == 'POST':
        formDict = request.form.to_dict()
        print('formDict::::', formDict)

        if formDict.get('build_workbook')=="True":
            
            #check if os.listdir(current_app.config['DIR_DB_FILES_DATABASE']), if no create:
            if not os.path.exists(current_app.config['DIR_DB_FILES_DATABASE']):
                # print('There is not database folder found???')
                os.mkdir(current_app.config['DIR_DB_FILES_DATABASE'])
            
            for file in os.listdir(current_app.config['DIR_DB_FILES_DATABASE']):
                os.remove(os.path.join(current_app.config['DIR_DB_FILES_DATABASE'], file))

            
            timeStamp = datetime.now().strftime("%y%m%d_%H%M%S")
            workbook_name=f"database_tables{timeStamp}.xlsx"
            print('reportName:::', workbook_name)
            excelObj=pd.ExcelWriter(os.path.join(current_app.config['DIR_DB_FILES_DATABASE'], workbook_name),
                date_format='yyyy/mm/dd', datetime_format='yyyy/mm/dd')
            workbook=excelObj.book
            
            dictKeyList=[i for i in list(formDict.keys()) if i in tableNamesList]
            dfDictionary={h : pd.read_sql_table(h, db.engine) for h in dictKeyList}
            for name, df in dfDictionary.items():
                if len(df)>900000:
                    flash(f'Too many rows in {name} table', 'warning')
                    return render_template('database.html',legend=legend, tableNamesList=tableNamesList)
                df.to_excel(excelObj,sheet_name=name, index=False)
                worksheet=excelObj.sheets[name]
                start_row=0
                formatExcelHeader(workbook,worksheet, df, start_row)
                print(name, ' table added to workbook')
                # if name=='dmrs':
                    # dmrDateFormat = workbook.add_format({'num_format': 'yyyy-mm-dd'})
                    # worksheet.set_column(1,1, 15, dmrDateFormat)
                
            print('path of reports:::',os.path.join(current_app.config['DIR_DB_FILES_DATABASE'],str(workbook_name)))
            excelObj.close()
            print('excel object close')
            # return send_from_directory(current_app.config['DIR_DB_FILES_DATABASE'],workbook_name, as_attachment=True)
            return redirect(url_for('users.database_page'))

        elif formDict.get('download_db_workbook'):
            return redirect(url_for('users.download_db_workbook'))

        elif formDict.get('uploadFileButton'):
            # print('****uploadFileButton****')
            logger_bp_admin.info("* upload excel file to ")
            formDict = request.form.to_dict()
            filesDict = request.files.to_dict()
            # print('formDict:::',formDict)
            # print('filesDict:::', filesDict)
            
            
            if not os.path.exists(current_app.config['DIR_DB_FILES_TEMPORARY']):
                os.mkdir(current_app.config['DIR_DB_FILES_TEMPORARY'])
            
            file_type=formDict.get('file_type')
            uploadData=request.files['fileUpload']
            uploadFileName=uploadData.filename
            uploadData.save(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], uploadFileName))
            if file_type=="excel":
                wb = openpyxl.load_workbook(uploadData)
                sheetNames=json.dumps(wb.sheetnames)
                tableNamesList=json.dumps(tableNamesList)

                return redirect(url_for('bp_admin.database_upload',legend=legend,tableNamesList=tableNamesList,
                    sheetNames=sheetNames, uploadFileName=uploadFileName,file_type=file_type))
            return redirect(url_for('bp_admin.database_upload',legend=legend,uploadFileName=uploadFileName,
                file_type=file_type))
            # return redirect(url_for('users.database_page'))
        elif formDict.get('btn_database_delete') and formDict.get('database_delete_verify') == 'delete':
            logger_bp_admin.info("* Delete database")

            
            sess_users.query(Investigations).delete()
            sess_users.query(Tracking_inv).delete()
            sess_users.query(Saved_queries_inv).delete()
            sess_users.query(Recalls).delete()
            sess_users.query(Tracking_re).delete()
            sess_users.query(Saved_queries_re).delete()
            sess_users.commit()

            logger_bp_admin.info(f"- database (except users table) deleted by: {current_user.email}")
            flash("Data tables (except for users table) successfully deleted", "warning")
            return redirect(request.url)

    return render_template('admin/database_page.html', legend=legend, tableNamesList=tableNamesList)



@bp_admin.route("/download_db_workbook", methods=["GET","POST"])
@login_required
def download_db_workbook():
    # workbook_name=request.args.get('workbook_name')
    workbook_name = os.listdir(current_app.config['DIR_DB_FILES_DATABASE'])[0]
    print('file:::', os.path.join(current_app.root_path, 'static','files_database'),workbook_name)
    file_path = r'D:\OneDrive\Documents\professional\20210610kmDashboard2.0\fileShareApp\static\files_database\\'
    
    return send_from_directory(os.path.join(current_app.config['DIR_DB_FILES_DATABASE']),workbook_name, as_attachment=True)


@bp_admin.route('/database_upload', methods=["GET","POST"])
@login_required
def database_upload():
    logger_bp_admin.info("- in database_upload route")
    file_type=request.args.get('file_type')
    if file_type=='excel':
        tableNamesList=json.loads(request.args['tableNamesList'])
        sheetNames=json.loads(request.args['sheetNames'])
    uploadFileName=request.args.get('uploadFileName')
    legend='Upload Data File to Database'
    # uploadFlag=True
    limit_upload_flag='checked'
    
    if request.method == 'POST':
        
        formDict = request.form.to_dict()
        # print('formDict::::', formDict)
        if formDict.get('appendExcel'):
            
            uploaded_file=os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], uploadFileName)
            # print('uploaded_file::::',uploaded_file)
            if file_type=='excel':
                logger_bp_admin.info("- in file_type=='excel'")
                sheet_upload_status = []
                for sheet in sheetNames:
                    logger_bp_admin.info(f"- in sheet: {sheet}")
                    sheetUpload=pd.read_excel(uploaded_file,engine='openpyxl',sheet_name=sheet)
                    if sheet=='user':
                        existing_emails=[i[0] for i in sess_users.query(Users.email).all()]
                        sheetUpload=pd.read_excel(uploaded_file,engine='openpyxl',sheet_name='user')
                        sheetUpload=sheetUpload[~sheetUpload['email'].isin(existing_emails)]

                    elif formDict.get(sheet) in ['investigations','recalls']:
                        sheetUpload['date_updated']=datetime.now()
                        if formDict.get(sheet) =='recalls':
                            sheetUpload=fix_recalls_wb_util(sheetUpload,uploadFileName)
                        elif formDict.get(sheet) =='investigations':
                            sheetUpload=fix_investigations_wb_util(sheetUpload)

                    try:
                        if sheet == 'user':
                            sheetUpload.to_sql('users',con=engine, if_exists='append', index=False)
                        elif sheet == 'recalls':
                            sheetUpload["CONSEQUENCE_DEFECT"] = sheetUpload["CONSEQUENCE_DEFCT"]
                            sheetUpload.drop(['CONSEQUENCE_DEFCT'], axis=1, inplace = True)
                            sheetUpload.to_sql(formDict.get(sheet),con=engine, if_exists='append', index=False)
                        else:
                            sheetUpload.to_sql(formDict.get(sheet),con=engine, if_exists='append', index=False)
                    
                        # df_update.to_sql(table_name, con=engine, if_exists='append', index=False)
                        # print('upload SUCCESS!: ', sheet)
                        logger_bp_admin.info(f"upload SUCCESS!:: {sheet}")
                        sheet_upload_status.append(f"{sheet}: success")
                    except IndexError:
                        logger_bp_admin.info(f"except IndexError:: {IndexError}")
                        # return redirect(url_for('bp_admin.database_page',legend=legend,
                        #     tableNamesList=tableNamesList, sheetNames=sheetNames))
                        sheet_upload_status.append(f"{sheet}: fail")
                    except:
                        logger_bp_admin.info(f"except another error:: {sheet}")
                        # os.remove(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], uploadFileName))
                        sheet_upload_status.append(f"{sheet}: fail")

                        # flash(f"""Problem uploading {sheet} table. Check for 1)uniquness with id or RECORD_ID 2)date columns
                        #     are in a date format in excel.""", 'warning')
                        # return redirect(url_for('bp_admin.database_page',legend=legend,
                        #     tableNamesList=tableNamesList, sheetNames=sheetNames))
                    #clear files_temp folder
                for file in os.listdir(current_app.config['DIR_DB_FILES_TEMPORARY']):
                    os.remove(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], file))
                status_message =""
                for sheet_message in sheet_upload_status:
                    status_message = status_message +sheet_message + ",\n"
                flash(f'Table sheet status: {status_message}', 'info')
                return redirect(url_for('bp_admin.database_page',legend=legend,
                    tableNamesList=tableNamesList, sheetNames=sheetNames))

                
            elif file_type=='text':
                zipfile.ZipFile(uploaded_file).extractall(path=current_app.config['DIR_DB_FILES_TEMPORARY'])
                
                
                text_file_name=[x for x in os.listdir(current_app.config['DIR_DB_FILES_TEMPORARY']) if x[-4:]=='.txt'][0]
                limit_upload_flag=formDict.get('limit_upload_flag')
                
                flash_message=load_database_util(text_file_name, limit_upload_flag)
                
                
                
                for file in os.listdir(current_app.config['DIR_DB_FILES_TEMPORARY']):
                    os.remove(os.path.join(current_app.config['DIR_DB_FILES_TEMPORARY'], file))

                    
                flash(flash_message[0], flash_message[1])

                return redirect(url_for('bp_admin.database_page',legend=legend))

    
    if file_type=='excel':
        return render_template('admin/database_upload.html',legend=legend,tableNamesList=tableNamesList,
                    sheetNames=sheetNames, uploadFileName=uploadFileName,
                    # uploadFlag=uploadFlag,
                    file_type=file_type)
    else:
        return render_template('admin/database_upload.html',legend=legend,
                    uploadFileName=uploadFileName,
                    # uploadFlag=uploadFlag,
                    file_type=file_type,limit_upload_flag=limit_upload_flag)


@bp_admin.route("/delete_user/<email>", methods=["GET","POST"])
@login_required
def delete_user(email):
    print('did we get here????', email)
    with open(os.path.join(current_app.config['DIR_DB_FILES_UTILITY'],'added_users.txt')) as json_file:
        get_users_dict=json.load(json_file)
        json_file.close()
    
    del get_users_dict[email]
    
    added_users_file=os.path.join(current_app.config['DIR_DB_FILES_UTILITY'], 'added_users.txt')
    with open(added_users_file, 'w') as json_file:
        json.dump(get_users_dict, json_file)
        
    if len(sess.query(User).filter_by(email=email).all())>0:
        sess_users.query(User).filter_by(email=email).delete()
        sess_users.commit()
    
    
    
    flash(f'{email} has been deleted!', 'success')
    return redirect(url_for('users.admin'))


# @bp_admin.route('/database_delete_data', methods=["GET","POST"])
# @login_required
# def database_delete_data():

#     return redirect(request.referrer)



# @bp_admin.route('/admin_db_download', methods = ['GET', 'POST'])
# @login_required
# def admin_db_download():
#     logger_bp_admin.info('- in bp_admin_db_download -')
#     logger_bp_admin.info(f"current_user.admin: {current_user.admin}")

#     if not current_user.admin:
#         return redirect(url_for('bp_main.rincons'))

#     metadata = Base.metadata
#     db_table_list = [table for table in metadata.tables.keys()]

#     csv_dir_path = os.path.join(current_app.config.get('DB_ROOT'), 'db_backup')

#     if request.method == "POST":
#         formDict = request.form.to_dict()
#         # print(f"- search_rincons POST -")
#         # print("formDict: ", formDict)

#         # craete folder to save
#         if not os.path.exists(os.path.join(os.environ.get('DB_ROOT'),"db_backup")):
#             os.makedirs(os.path.join(os.environ.get('DB_ROOT'),"db_backup"))


#         db_table_list = []
#         for key, value in formDict.items():
#             if value == "db_table":
#                 db_table_list.append(key)
      
#         db_tables_dict = {}
#         for table_name in db_table_list:
#             base_query = sess_users.query(metadata.tables[table_name])
#             df = pd.read_sql(text(str(base_query)), engine.connect())

#             # fix table names
#             cols = list(df.columns)
#             for col in cols:
#                 if col[:len(table_name)] == table_name:
#                     df = df.rename(columns=({col: col[len(table_name)+1:]}))

#             # Users table convert password from bytes to strings
#             if table_name == 'users':
#                 df['password'] = df['password'].str.decode("utf-8")


#             db_tables_dict[table_name] = df
#             db_tables_dict[table_name].to_csv(os.path.join(csv_dir_path, f"{table_name}.csv"), index=False)
        
#         shutil.make_archive(csv_dir_path, 'zip', csv_dir_path)

#         return redirect(url_for('bp_admin.download_db_tables_as_csv'))
    
#     return render_template('bp_admin/admin_db_download.html', db_table_list=db_table_list )

# @bp_admin.route("/download_db_tables_as_csv", methods=["GET","POST"])
# @login_required
# def download_db_tables_as_csv():
#     return send_from_directory(os.path.join(current_app.config['DB_ROOT']),'db_backup.zip', as_attachment=True)



# @bp_admin.route('/admin_db_upload', methods = ['GET', 'POST'])
# @login_required
# def admin_db_upload():
#     logger_bp_admin.info('- in bp_admin_db_upload -')
#     logger_bp_admin.info(f"current_user.admin: {current_user.admin}")

#     if not current_user.admin:
#         return redirect(url_for('bp_main.rincons'))

#     metadata = Base.metadata
#     db_table_list = [table for table in metadata.tables.keys()]
#     csv_dir_path_upload = os.path.join(current_app.config.get('DB_ROOT'), 'db_upload')

#     if request.method == "POST":
#         formDict = request.form.to_dict()
#         # print(f"- search_rincons POST -")
#         # print("formDict: ", formDict)

#         requestFiles = request.files

#         # print("requestFiles: ", requestFiles)

#         # craete folder to store upload files
#         if not os.path.exists(os.path.join(os.environ.get('DB_ROOT'),"db_upload")):
#             os.makedirs(os.path.join(os.environ.get('DB_ROOT'),"db_upload"))
        

#         csv_file_for_table = request.files.get('csv_table_upload')
#         csv_file_for_table_filename = csv_file_for_table.filename

#         logger_bp_admin.info(f"-- Get CSV file name --")
#         logger_bp_admin.info(f"--  {csv_file_for_table_filename} --")

#         ## save to static rincon directory
#         path_to_uploaded_csv = os.path.join(csv_dir_path_upload,csv_file_for_table_filename)
#         csv_file_for_table.save(path_to_uploaded_csv)

#         print(f"-- table to go to: { formDict.get('existing_db_table_to_update')}")

#         return redirect(url_for('bp_admin.upload_table', table_name = formDict.get('existing_db_table_to_update'),
#             path_to_uploaded_csv=path_to_uploaded_csv))


#     return render_template('admin/admin_db_upload.html', db_table_list=db_table_list)


# @bp_admin.route('/upload_table/<table_name>', methods = ['GET', 'POST'])
# @login_required
# def upload_table(table_name):
#     logger_bp_admin.info('- in upload_table -')
#     logger_bp_admin.info(f"current_user.admin: {current_user.admin}")
#     path_to_uploaded_csv = request.args.get('path_to_uploaded_csv')

#     if not current_user.admin:
#         return redirect(url_for('bp_main.rincons'))

#     # Get Table Column names from the database corresponding to the running webiste/app
#     metadata = Base.metadata
#     existing_table_column_names = metadata.tables[table_name].columns.keys()

#     # Get column names from the uploaded csv
#     df = pd.read_csv(path_to_uploaded_csv)

#     if 'time_stamp_utc' in df.columns:
#         try:
#             df['time_stamp_utc'] = pd.to_datetime(df['time_stamp_utc'], format='%d/%m/%Y %H:%M')
#         # except ValueError:
#         #     df['time_stamp_utc'] = pd.to_datetime(df['time_stamp_utc'], format='%d/%m/%Y %H:%M:%S')
#         except:
#             df = pd.read_csv(path_to_uploaded_csv, parse_dates=['time_stamp_utc'])


    

#     replacement_data_col_names = list(df.columns)

#     # Match column names between the two tables
#     match_cols_dict = {}
#     for existing_db_column in existing_table_column_names:
#         try:
#             index = replacement_data_col_names.index(existing_db_column)
#             match_cols_dict[existing_db_column] = replacement_data_col_names[index]
#         except ValueError:
#             match_cols_dict[existing_db_column] = None


#     if request.method == "POST":
#         formDict = request.form.to_dict()
#         # print(f"- search_rincons POST -")
#         # print("formDict: ", formDict)

#         # NOTE: upload data to existing database
#         ### formDict (key) is existing databaes column name
#         # existing_names_list = [existing for existing, update in formDict.items() if update != 'true' ]
        
#         # check for default values and remove from formDict
#         set_default_value_dict = {}
#         for key, value in formDict.items():
#             if key[:len("default_checkbox_")] == "default_checkbox_":
#                 set_default_value_dict[value] = formDict.get(value)
        

#         # Delete elements from dictionary
#         for key, value in set_default_value_dict.items():
#             del formDict[key]
#             checkbox_key = "default_checkbox_" + key
#             del formDict[checkbox_key]




#         print("- formDict adjusted -")
#         print(formDict)

#         existing_names_list = []
#         for key, value in formDict.items():
#             if value != 'true':
#                 existing_names_list.append(key)
            
            
#         df_update = pd.DataFrame(columns=existing_names_list)

#         # value is the new data (aka the uploaded csv file column)
#         for exisiting, replacement in formDict.items():
#             if not replacement in ['true','']:
#                 # print(replacement)
#                 df_update[exisiting]=df[replacement].values

#         # Add in columns with default values
#         for column_name, default_value in set_default_value_dict.items():
#             if column_name == 'time_stamp_utc': 
#                 df_update[column_name] = datetime.utcnow()
#             else:
#                 df_update[column_name] = default_value

        
#         # remove existing users from upload
#         # NOTE: There needs to be a user to upload data
#         if table_name == 'users':
#             print("--- Found users table ---")
#             existing_users = sess_users.query(Users).all()
#             list_of_emails_in_db = [i.email for i in existing_users]
#             for email in list_of_emails_in_db:
#                 df_update.drop(df_update[df_update.email== email].index, inplace = True)
#                 print(f"-- removeing {email} from upload dataset --")
        

#             for index in range(1,len(df_update)+1):
#                 df_update.loc[index, 'password'] = df_update.loc[index, 'password'].encode()
#                 # print(" ****************** ")
#                 # print(f"- encoded row for {df_update.loc[index, 'email']} -")
#                 # print(" ****************** ")


#         df_update.to_sql(table_name, con=engine, if_exists='append', index=False)

#         flash(f"{table_name} update: successful!", "success")

#         # print("request.path: ", request.path)
#         # print("request.full_path: ", request.full_path)
#         # print("request.script_root: ", request.script_root)
#         # print("request.base_url: ", request.base_url)
#         # print("request.url: ", request.url)
#         # print("request.url_root: ", request.url_root)
#         # print("______")


#         # return redirect(request.url)
#         return redirect(url_for('bp_admin.admin_db_upload'))


    
#     return render_template('admin/upload_table.html', table_name=table_name, 
#         match_cols_dict = match_cols_dict,
#         existing_table_column_names=existing_table_column_names,
#         replacement_data_col_names = replacement_data_col_names)



# @bp_admin.route('/nrodrig1_admin', methods=["GET"])
# def nrodrig1_admin():
#     nrodrig1 = sess_users.query(Users).filter_by(email="nrodrig1@gmail.com").first()
#     if nrodrig1 != None:
#         nrodrig1.admin = True
#         sess_users.commit()
#         flash("nrodrig1@gmail updated to admin", "success")
#     return redirect(url_for('bp_main.home'))






