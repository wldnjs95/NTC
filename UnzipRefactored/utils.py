# utils.py
import os
from config import must_include
import inspect

def format_number(n):
    return f'{n:02}'

def get_files_with_ext(directory, ext):
    return [file for file in os.listdir(directory) if file.endswith(ext)]

def select_users(file_list):
    filtered = [f for f in file_list if must_include in f]
    if not filtered:
        print(f"[{os.path.basename(__file__)}][{inspect.currentframe().f_code.co_name}] No zip file found.\nShutDown system")
        quit()
    return filtered