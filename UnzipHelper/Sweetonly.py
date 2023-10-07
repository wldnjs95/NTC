import os
import sys
import zipfile
import shutil

import cv2

from distutils.dir_util import copy_tree

WEDDING_TYPE = '[sweetonly]'
mainFolderName = 'sweetonly' # also used for aep name
mustInclude = '스윗온리'
convW = []

def png_to_jpg(Dir, quality):
    count = 0
    cur_dir = Dir#os.path.join(Dir,WEDDING_TYPE)
    os.chdir(cur_dir)
    photo_list = os.listdir(cur_dir)

    for photo in photo_list :
        if '.jpg' not in photo and '.JPG' not in photo :
            if '.jpeg' in photo or ',JPEG' in photo:
                cut = 5
            elif '.png' in photo or '.PNG' in photo:
                cut = 4
            img = cv2.imread(photo)
            cv2.imwrite(photo[:-cut]+'.jpg', img, [cv2.IMWRITE_JPEG_QUALITY,quality])
            count = count + 1
            os.remove(photo)
    
    count = str(count)
    print(count + ' converted to jpg')

def lovesome_userselection(userlist):
    if len(userlist)==0:
       print('It is empty')
       print('ShutDown system')
       quit()

    multipleSelection = []
    i = 1
    print('Select multiple from below(numbers only, type 0 to end selection)')
    for item in userlist:
        if(item.find(mustInclude) != -1):
            multipleSelection.append(item)

    return multipleSelection
 
def get_ext_file(Dir,Ext):
    return [ file for file in os.listdir(Dir) if file.endswith(Ext)]

def lovesome_folderExist(Dir, folder):
    newDir = os.path.join(Dir, folder)
    if os.path.isdir(newDir):
        return 1

def lovesome_unzip(startDir):

    cur_dir = startDir
    zip_list = get_ext_file(cur_dir, '.zip')
    user_zip = lovesome_userselection(zip_list)
    '''
    eflag = lovesome_folderExist(cur_dir, mainFolderName)
    innerDir = os.path.join(cur_dir, mainFolderName,WEDDING_TYPE)

    if eflag:
        print('Folder already exists')
    else:
        os.mkdir(mainFolderName)
        os.mkdir(innerDir)
    '''
    k=-1
    for i in user_zip:
        if(os.path.isdir(i[:-4])):
            k += 1
    
    if(k<len(user_zip)):
        if(k == -1): #no end == no unzip there was
            k = 0
        print("Latest Zip Stopped at ", user_zip[k], "Starting from there...")
        for i in range(k, len(user_zip)):
            unzip(cur_dir, cur_dir, user_zip[i])
            copyAep(os.getcwd(), user_zip[i][:-4])
    else:
        print("No more zip to unzip")
        
    return mainFolderName

def unzip(cur_dir, innerDir, user_zip):
    dir_to_extract = os.path.join(innerDir, WEDDING_TYPE, user_zip[:-4], WEDDING_TYPE)
    print('unzipping file : ' + user_zip)
    zip_dir = os.path.join(cur_dir, user_zip)
    with zipfile.ZipFile(zip_dir, 'r') as zip_ref:
        zip_ref.extractall(dir_to_extract)
    print('unzip is done')
    convW.append(dir_to_extract)

def get_aep(Dir):
    cur_dir = Dir
    aep_list = get_ext_file(cur_dir, mainFolderName + '.aep')
    size = len(aep_list)
    if size == 0:
        print('no aep file exist')
        print('Shutdown system')
        quit()

    elif size == 1:
        return aep_list[0]
    else:
        user_aep = lovesome_userselection(aep_list)
        return user_aep

def copyAep(Dir, newFolder_name):
    cur_dir = Dir
    file_list = os.listdir(cur_dir)

    #GET AEP
    aep_File = get_aep(cur_dir)
    #COPY AEP
    newPath = os.path.join(cur_dir, WEDDING_TYPE, newFolder_name)
    newFileName = newFolder_name + '.aep'

    shutil.copy(aep_File, os.path.join(WEDDING_TYPE, newPath, newFileName))
    #CHANGE
    #경로에서 ./ 를 / 로 변경 문제없는지 확인
    #shutil.copy(aep_File, newPath + './'+newFolder_name + '.aep')
    #os.path.join으로 바꿈

    print('aep copy finished')

def way_to_start():
    start_Dir = os.getcwd()
    newFoldername = lovesome_unzip(start_Dir)
    return start_Dir, newFoldername


myDir, myFolder = way_to_start()
for i in convW:
    png_to_jpg(i,100)
