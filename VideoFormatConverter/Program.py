import subprocess
import glob

import inspect
import os, zipfile, shutil, cv2

import mimetypes
import math
import logging
from time import time
from time import localtime
from time import strftime



TARGET_FILE = '노벰버송'
FFMPEG_PATH = r"ffmpeg\bin\ffmpeg.exe"
#https://stackoverflow.com/questions/14919609/how-to-check-if-a-file-is-a-video
#LOGGING

'''
ONS : On Screen Log - messeges that are printed onto the console(User visible)
OFS : Off Screen Log - messeges that are not printed onto the console

level
1 : info
2 : warning
3 : error
'''

def log_on_screen(msg, level = 0):
    t = strftime('%Y-%m-%d :%X.', localtime(time())) + str(round(time() * 1000))[-4:]
    if(level == 0):
        print(msg)
        logging.info(t + " ONS : " + msg)
        return
    if(level == 1):
        print("WARNING: ", msg)
        logging.warning(t + " ONS : " + msg)
        return
    if(level == 2):
        print("ERROR: ", msg)
        logging.error(t + " ONS : " + msg)
        return

def log_off_screen(msg, currentFunction, level = 0):
    t = strftime('%Y-%m-%d :%X.', localtime(time())) + str(round(time() * 1000))[-4:]
    if(level == 0):
        logging.info(t + " OFS : func = " + currentFunction + " : " + msg)
        return
    if(level == 1):
        logging.warning(t + " OFS : func = " + currentFunction + " : " + msg)
        return
    if(level == 2):
        logging.error(t + " OFS : func = " + currentFunction + " : " + msg)
        return

def getCurrentFunction():
    # get current function name
    frame = inspect.currentframe().f_back
    return inspect.getframeinfo(frame).function

#LOGGING

def getThreeDigitName(n):
    if (n > 99):
        log_on_screen("File number passed 99, naming rules are now off range of 000~099", 1)
        return n
    return str("0" * (2 - int(math.log10(n)))) + str(n)

def convertImagesAndVideos(targets, start_dir):
    log_off_screen("Media conversion started.", getCurrentFunction())
    for path in targets:
        log_on_screen("Processing folder " + path)
        os.chdir(path)#change directory for video, image processing
        fileList = [f for f in os.listdir(path) if not f.endswith('.aep')]
        images = 1
        videos = 1
        for f in fileList:
            if mimetypes.guess_type(os.path.join(path, f))[0].startswith('video'):
                convert_to_mp4(f, getThreeDigitName(videos), start_dir)
                videos += 1
            else:
                convert_to_jpg(f, getThreeDigitName(images))
                images += 1

def commandListToString(command):
    result = str()
    for i in command:
        result += i + " "
    return result

def convert_to_mp4(video, newName, start_dir):
    if not video.lower().endswith((".mp4")):
        path_o = os.path.join(os.getcwd(), video)
        path_t = os.path.join(os.getcwd(), newName + ".mp4")
        command = [os.path.join(start_dir, FFMPEG_PATH), '-i', path_o, path_t]
        try:
            #subprocess.run(command, check=True)
            CREATE_NO_WINDOW = 0x08000000
            subprocess.call(commandListToString(command), creationflags=CREATE_NO_WINDOW)
            #print(f"{input_file} 파일을 성공적으로 {output_file} 로 변환 하였습니다.")
            os.remove(video)
            log_on_screen(video + " converted to " + newName + ".mp4")
        except subprocess.CalledProcessError as e:
            log_on_screen("Cannot convert video, " + e, 2)

    else:
        os.rename(video, newName + '.' + video.split('.')[1])
        log_on_screen(video + " renamed to " + newName + '.' + video.split('.')[1])



def convert_to_jpg(photo, newName, quality=100):
    if not photo.lower().endswith(('.jpg', '.jpeg')):
        img = cv2.imread(photo)
        cv2.imwrite(newName + ".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        os.remove(photo)
        log_on_screen(photo + " converted to " + newName + ".jpg")
    else:
        os.rename(photo, newName + '.' + photo.split('.')[1])
        log_on_screen(photo + " renamed to " + newName + '.' + photo.split('.')[1])

def copy_aep_file(directory, new_folder, aep_name):
    log_off_screen("AEP copy started.", getCurrentFunction())
    target_file = aep_name +'.aep'
    log_on_screen("target aep file is : ",target_file)
    aep_files = [f for f in os.listdir(directory) if f.endswith('.aep')]
    if not aep_files:
        log_on_screen('No AEP file found.\nShutting down.', 1) or exit()
    shutil.copy(aep_files[0], os.path.join(directory, new_folder, new_folder + '_copy.aep'))
    

def unzip(start_dir):
    log_off_screen("Unzip started.", getCurrentFunction())
    target_dirs = list()
    zip_files = [f for f in os.listdir(start_dir) if f.endswith('.zip') and TARGET_FILE in f] #NovemberSong
    for i, zip_file in enumerate(zip_files):
        if not os.path.isdir(zip_file[:-4]):
            log_on_screen("Unzipping: " + zip_file)
            with zipfile.ZipFile(os.path.join(start_dir, zip_file), 'r') as zip_ref:
                zip_ref.extractall(os.path.join(start_dir, zip_file[:-4]))
                target_dirs.append(os.path.join(start_dir, zip_file[:-4]))
            copy_aep_file(start_dir, zip_file[:-4], zip_file[:-4])
    return target_dirs


def main():
    try:
        log_off_screen("=====================<Log Start>=====================", "=")
        log_off_screen("Program started.", getCurrentFunction())
        start_directory = os.getcwd()
        log_off_screen("Start directory is " + start_directory, getCurrentFunction())
        convert_target = unzip(start_directory)
        
        log_on_screen("Following folders will be processed")
        for i in range(0, len(convert_target)):
            log_on_screen(str(i) + " : " + convert_target[i])
            
        convertImagesAndVideos(convert_target, start_directory)
        log_off_screen("Program ended.", getCurrentFunction())

    except Exception as e:
        # print error log
        log_on_screen(f"An error occurred: {str(e)}", 2)
        print(f"An error occurred: {str(e)}")
    
    # maintain console screen
    input("Press Enter to close the console...")

logger = logging.getLogger(__name__)
logging.basicConfig(filename='log.txt', encoding='utf-8', level=logging.DEBUG)
main()


logger = logging.getLogger(__name__)
logging.basicConfig(filename='log.txt', encoding='utf-8', level=logging.DEBUG, filemode='a')

main()
