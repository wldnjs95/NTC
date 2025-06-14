# aep_utils.py
import os, shutil
from src.utils.general_utils import get_files_with_ext, select_users
from src.utils.logging_utils import log_user, log_debug, log_error
from src.utils.state import global_state

def get_aep(directory):
    log_debug(f'Get aep started at directory: {directory}')
    aep_list = get_files_with_ext(directory,'.aep')
    if aep_list:
        log_debug(f'Aep file: {aep_list[0]}')
        return aep_list[0]
    else:
        log_debug(f'No aep file found in {directory}')
        return None

def copy_aep(directory, new_folder_name):
    log_debug(f'Copy aep started at directory: {directory}')
    aep_file = get_aep(directory)
    new_path = os.path.join(directory, new_folder_name)
    new_file_name = global_state.product_name + '.aep'
    shutil.copy(aep_file, os.path.join(new_path, new_file_name))
    log_user('Aep copy finished')
