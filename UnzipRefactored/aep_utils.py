# aep_utils.py
import os, shutil
from utils import get_files_with_ext, select_users
from logging_utils import log_user, log_debug, log_error
from state import global_state

def get_aep(directory):
    aep_list = get_files_with_ext(directory, global_state.product_name + '.aep')
    if len(aep_list) == 0:
        log_user(f'{global_state.product_name}.aep file does not exist\n')
    elif len(aep_list) == 1:
        return aep_list[0]
    else:
        user_aep = select_users(aep_list)
        return user_aep[0]

def copy_aep(directory, new_folder_name):
    aep_file = get_aep(directory)
    new_path = os.path.join(directory, new_folder_name)
    new_file_name = global_state.product_name + '.aep'
    shutil.copy(aep_file, os.path.join(new_path, new_file_name))
    log_user('Aep copy finished')
