
# src/core/file_operations.py
import os
import zipfile
import shutil
from .app_state import global_state
from src.utils.logging_utils import log_debug, log_error

def get_files_with_ext(directory, extension):
    return [f for f in os.listdir(directory) if f.endswith(extension)]

def unzip_selected_files(directory):
    # This function needs to be implemented based on the logic from the original gui_main.py
    pass

def convert_images_to_jpg(directory):
    # This function needs to be implemented based on the logic from the original gui_main.py
    pass

def export_diagnostics():
    zip_name = "UnzipHelper_Diagnostics.zip"
    zip_path = os.path.join(os.getcwd(), zip_name)

    with zipfile.ZipFile(zip_path, 'w') as zipf:
        if os.path.exists(log_utils.LOG_FILE):
            zipf.write(log_utils.LOG_FILE, arcname="logs/app.log")
        if os.path.exists(product_store.APPDATA_FILE):
            zipf.write(product_store.APPDATA_FILE, arcname="config/ntc_wedding_products.json")

    return zip_path
