# zip_utils.py
import os, zipfile
from src.utils.aep_utils import copy_aep
from src.utils.general_utils import get_files_with_ext, select_users
from src.utils.logging_utils import log_user, log_debug, log_error
import inspect
from src.utils.state import global_state

from src.config.config import VALID_EXTENSIONS

def log_current_function():
    caller =  inspect.stack()[1].function 
    return caller

def unzip_selected_files(start_dir):
    log_user(f"Unzip attempted at directory: {start_dir}")
    log_debug(f"{log_current_function()} Activated")
    zip_list = get_files_with_ext(start_dir, '.zip')
    user_zip = select_users(zip_list)
    
    if not user_zip:
        log_user("압축 파일이 존재하지 않습니다")
        return False

    for i, zip_file in enumerate(user_zip):
        folder_name = os.path.join(start_dir, zip_file[:-4])
        if not os.path.isdir(folder_name):
            log_user(f"Unzipping: {zip_file}")
            extract_path = os.path.join(folder_name, "["+global_state.product_name.lower()+"]")
            original_dir = os.path.join(extract_path, "original")
            os.makedirs(original_dir, exist_ok=True)
            
            with zipfile.ZipFile(os.path.join(start_dir, zip_file), 'r') as z:
                log_debug(f"Extracting {zip_file} to {extract_path}")
                file_list = z.namelist()
                log_debug(f"Files in zip: {file_list}")
                
                image_files = [
                    file for file in file_list
                    if file.lower().endswith(VALID_EXTENSIONS) and '/' not in file
                ]
                if not image_files:
                    log_user(f"압축 파일 {zip_file}에 이미지가 없거나, 내부에 폴더가 포함되어 있습니다. 폴더 구조를 확인해주세요.")
                    log_error(f"❌ No image files at root level in {zip_file}. Exiting.")
                    log_debug(f"Error: No root-level images found in '{zip_file}'.")
                    return False
                
                log_debug(f"Extracting {zip_file} to {original_dir}")
                z.extractall(original_dir)
            global_state.conversion_targets_mapping[original_dir] = extract_path
            copy_aep(start_dir, zip_file[:-4])
        else:
            log_user(f'Skipping already extracted: {zip_file}')
        
    return True