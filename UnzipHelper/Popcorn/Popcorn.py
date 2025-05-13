import os
import zipfile
import shutil
import numpy
import cv2

main_folder_name = 'Popcorn' # also used for aep name
must_include = '(POPCORN)'
photo_folder_name = '[photo]'
conversion_widths = []

def format_number(n):
    if n < 10:
        return '0' + str(n)
    else:
        return str(n)

def convert_images_to_jpg(directory, quality):
    count = 1
    os.chdir(directory)
    photo_list = os.listdir(directory)

    for photo in photo_list :
        if '.jpg' not in photo and '.JPG' not in photo :
            if '.jpeg' in photo or '.JPEG' in photo:
                cut = 5
            elif '.png' in photo or '.PNG' in photo:
                cut = 4
            img = cv2.imdecode(numpy.fromfile(photo, dtype=numpy.uint8), cv2.IMREAD_COLOR)
            cv2.imwrite(format_number(count)+'.jpg', img, [cv2.IMWRITE_JPEG_QUALITY,quality])
            count = count + 1
            os.remove(photo)
    
    count = str(count)
    print(count + ' converted to jpg')

def select_users(userlist):
    if len(userlist)==0:
       print('It is empty')
       print('ShutDown system')
       quit()

    multiple_selection = []
    i = 1
    print('Select multiple from below(numbers only, type 0 to end selection)')
    for item in userlist:
        if(item.find(must_include) != -1):
            multiple_selection.append(item)

    return multiple_selection
 
def get_files_with_ext(directory,Ext):
    return [ file for file in os.listdir(directory) if file.endswith(Ext)]

def ensure_folder_exists(directory, folder):
    new_directory = os.path.join(directory, folder)
    if os.path.isdir(new_directory):
        return 1

def unzip_selected_files(start_dir):
    cur_dir = start_dir
    zip_list = get_files_with_ext(cur_dir, '.zip')
    user_zip = select_users(zip_list)
    last_unzipped_index = -1

    for file in user_zip:
        if os.path.isdir(file[:-4]):
            last_unzipped_index += 1

    if last_unzipped_index < len(user_zip):
        if last_unzipped_index == -1:
            last_unzipped_index = 0
        print("Latest Zip Stopped at", user_zip[last_unzipped_index], "Starting from there...")
        for i in range(last_unzipped_index, len(user_zip)):
            extract_zip_file(cur_dir, cur_dir, user_zip[i])
            copy_aep(os.getcwd(), user_zip[i][:-4])
    else:
        print("No more zip to unzip")
    
    return main_folder_name

def extract_zip_file(cur_dir, inner_dir, zip_filename):
    dir_to_extract = os.path.join(inner_dir, zip_filename[:-4], photo_folder_name)
    print('Unzipping file:', zip_filename)
    zip_path = os.path.join(cur_dir, zip_filename)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dir_to_extract)
    print('Unzip is done')
    conversion_widths.append(dir_to_extract)

def get_aep(Dir):
    cur_dir = Dir
    aep_list = get_files_with_ext(cur_dir, main_folder_name + '.aep')
    size = len(aep_list)
    if size == 0:
        print('no aep file exist')
        print('Shutdown system')
        quit()

    elif size == 1:
        return aep_list[0]
    else:
        user_aep = select_users(aep_list)
        return user_aep

def copy_aep(Dir, newFolder_name):
    cur_dir = Dir
    file_list = os.listdir(cur_dir)

    #GET AEP
    aep_File = get_aep(cur_dir)
    #COPY AEP
    newPath = os.path.join(cur_dir, newFolder_name)
    newFileName = main_folder_name + '.aep'

    shutil.copy(aep_File, os.path.join(newPath, newFileName))
    #CHANGE
    #경로에서 ./ 를 / 로 변경 문제없는지 확인
    #shutil.copy(aep_File, newPath + './'+newFolder_name + '.aep')
    #os.path.join으로 바꿈

    print('aep copy finished')

def way_to_start():
    start_dir = os.getcwd()
    unzip_selected_files(start_dir)
    return start_dir, main_folder_name


myDir, myFolder = way_to_start()
for i in conversion_widths:
    convert_images_to_jpg(i,100)
