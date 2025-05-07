import os
import zipfile
import shutil
import numpy
import cv2

mainFolderName = 'Popcorn' # also used for aep name
mustInclude = '(POPCORN)'
photoFolderName = '[photo]'
convW = []

def numberToStr(n):
    if n < 10:
        return '0' + str(n)
    else:
        return str(n)

def png_to_jpg(Dir, quality):
    count = 1
    os.chdir(Dir)
    photo_list = os.listdir(Dir)

    for photo in photo_list :
        if '.jpg' not in photo and '.JPG' not in photo :
            if '.jpeg' in photo or '.JPEG' in photo:
                cut = 5
            elif '.png' in photo or '.PNG' in photo:
                cut = 4
            img = cv2.imdecode(numpy.fromfile(photo, dtype=numpy.uint8), cv2.IMREAD_COLOR)
            cv2.imwrite(numberToStr(count)+'.jpg', img, [cv2.IMWRITE_JPEG_QUALITY,quality])
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
    dir_to_extract = os.path.join(innerDir, user_zip[:-4], photoFolderName)
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
    newPath = os.path.join(cur_dir, newFolder_name)
    newFileName = mainFolderName + '.aep'

    shutil.copy(aep_File, os.path.join(newPath, newFileName))
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
