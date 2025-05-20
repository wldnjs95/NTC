# zip_utils.py
import os, zipfile
from aep_utils import copy_aep
from utils import get_files_with_ext, select_users
from logging_utils import log_user, log_debug, log_error
import inspect
from state import global_state

def log_current_function():
    caller =  inspect.stack()[1].function 
    return caller

def unzip_selected_files(start_dir):
    log_debug(f"{log_current_function()} Activated")
    zip_list = get_files_with_ext(start_dir, '.zip')
    user_zip = select_users(zip_list)

    for i, zip_file in enumerate(user_zip):
        folder_name = os.path.join(start_dir, zip_file[:-4])
        if not os.path.isdir(folder_name):
            log_user(f"Unzipping: {zip_file}")
            extract_path = os.path.join(folder_name, "["+global_state.product_name.lower()+"]")
            with zipfile.ZipFile(os.path.join(start_dir, zip_file), 'r') as z:
                z.extractall(extract_path)
            global_state.conversion_widths.append(extract_path)
            copy_aep(start_dir, zip_file[:-4])
        else:
            log_user(f'Skipping already extracted: {zip_file}')