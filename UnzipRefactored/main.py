# main.py
from zip_utils import unzip_selected_files
from image_utils import convert_images_to_jpg
import config
import os
import customtkinter as ctk

def main():
    start_dir = os.getcwd()
    unzip_selected_files(start_dir)

    for path in config.conversion_widths:
        convert_images_to_jpg(path, quality=100)

if __name__ == "__main__":
    main()