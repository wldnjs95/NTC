import os, zipfile, shutil, cv2

aep_name, wedding_type, main_folder_name, must_include, converted_dirs = 'sweetonly15.x', '[sweetonly]', 'sweetonly', '스윗온리', []

def convert_images_to_jpg(directory, quality=100):
    os.chdir(directory)
    for photo in os.listdir(directory):
        if not photo.lower().endswith(('.jpg', '.jpeg')):
            img = cv2.imread(photo)
            cv2.imwrite(photo.rsplit('.', 1)[0] + '.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, quality])
            os.remove(photo)

def filter_files_by_keyword(file_list):
    return [file for file in file_list if must_include in file] or (print('No matching files found.\nShutting down.') or exit())

def unzip_and_prepare_directories(start_dir):
    zip_files = filter_files_by_keyword([f for f in os.listdir(start_dir) if f.endswith('.zip')])
    for i, zip_file in enumerate(zip_files):
        if not os.path.isdir(zip_file[:-4]):
            print("Unzipping:", zip_file)
            with zipfile.ZipFile(os.path.join(start_dir, zip_file), 'r') as zip_ref:
                zip_ref.extractall(os.path.join(start_dir, zip_file[:-4], wedding_type))
            converted_dirs.append(os.path.join(start_dir, zip_file[:-4], wedding_type))
            copy_aep_file(start_dir, zip_file[:-4])

def copy_aep_file(directory, new_folder):
    aep_files = filter_files_by_keyword([f for f in os.listdir(directory) if f.endswith(aep_name + '.aep')])
    if not aep_files:
        print('No AEP file found.\nShutting down.') or exit()
    shutil.copy(aep_files[0], os.path.join(directory, new_folder, new_folder + '15.x.aep'))

start_directory = os.getcwd()
unzip_and_prepare_directories(start_directory)
for dir in converted_dirs: 
    convert_images_to_jpg(dir)