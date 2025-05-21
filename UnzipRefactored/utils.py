# utils.py
import os
import inspect
from logging_utils import log_user, log_debug, log_error
from state import global_state

def format_number(n):
    return f'{n:02}'

def get_files_with_ext(directory, ext):
    return [file for file in os.listdir(directory) if file.endswith(ext)]

def select_users(file_list):
    filtered = [f for f in file_list if global_state.must_include in f]
    if not filtered:
        log_debug(f"No zip file found.")
        log_debug(f"keyword: {global_state.must_include}")
        log_user(f"No zip file found.")
        return None
    log_debug(f"Found zip file: {filtered}")
    return filtered