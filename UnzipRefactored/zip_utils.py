# zip_utils.py
import os, zipfile
from config import conversion_widths, photo_folder_name
from aep_utils import copy_aep
from utils import get_files_with_ext, select_users

def unzip_selected_files(start_dir):
    zip_list = get_files_with_ext(start_dir, '.zip')
    user_zip = select_users(zip_list)

    for i, zip_file in enumerate(user_zip):
        folder_name = os.path.join(start_dir, zip_file[:-4])
        if not os.path.isdir(folder_name):
            print("Unzipping:", zip_file)
            extract_path = os.path.join(folder_name, photo_folder_name)
            with zipfile.ZipFile(os.path.join(start_dir, zip_file), 'r') as z:
                z.extractall(extract_path)
            conversion_widths.append(extract_path)
            copy_aep(start_dir, zip_file[:-4])
        else:
            print(f'Skipping already extracted: {zip_file}')