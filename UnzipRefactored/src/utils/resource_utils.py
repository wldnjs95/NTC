import os
import sys

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):  
        # EXE build
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # run.py
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', relative_path))
