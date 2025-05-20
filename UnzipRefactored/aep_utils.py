# aep_utils.py
import os, shutil
from utils import get_files_with_ext, select_users

def get_aep(directory, main_folder_name):
    aep_list = get_files_with_ext(directory, main_folder_name + '.aep')
    if len(aep_list) == 0:
        print('no aep file exist\nShutdown system')
        quit()
    elif len(aep_list) == 1:
        return aep_list[0]
    else:
        user_aep = select_users(aep_list)
        return user_aep[0]

def copy_aep(directory, new_folder_name, product_name):
    aep_file = get_aep(directory, product_name)
    new_path = os.path.join(directory, new_folder_name)
    new_file_name = product_name + '.aep'
    shutil.copy(aep_file, os.path.join(new_path, new_file_name))
    print('aep copy finished')
