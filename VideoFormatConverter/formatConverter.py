import subprocess
import os
import glob
from shutil import copyfile

FFMPEG_PATH = r"ffmpeg\bin\ffmpeg.exe"

conversion_src = "footages_raw"
conversion_dst = "footages_converted"
targetFormat = "mp4"

def convert_to_mp4(input_file, output_file=None):
    if output_file is None:
        base, _ = os.path.splitext(input_file)
        output_file = f"{base}." + targetFormat
    command = [FFMPEG_PATH, '-i', input_file, output_file]
    try:
        subprocess.run(command, check=True)
        print(f"{input_file} 파일을 성공적으로 {output_file} 로 변환 하였습니다.")
    except subprocess.CalledProcessError as e:
        print(f"확장자 변환 중 오류가 발생했습니다.: {e}")



def DirectoryExist(path):
    return os.path.isdir(path)

def FileExist(path):
    return os.path.isfile(path)

def run():
    if DirectoryExist(conversion_dst) == False:
        os.makedirs(conversion_dst)
        print("작업 폴더가 존재하지 않습니다. " + conversion_dst + "폴더를 생성합니다.")
        
    if DirectoryExist(conversion_src) == False:
        os.makedirs(conversion_src)
        print("작업 폴더가 존재하지 않습니다. " + conversion_src + " 폴더에 영상 파일을 넣고 프로그램을 다시 시작 해주세요.")
        return -1
    
    files_to_convert = glob.glob(conversion_src + "/*");
    for file in files_to_convert:
        
        file_src = file
        file_dst = file.replace(conversion_src, conversion_dst).split('.')[0] + "." + targetFormat

        if(FileExist(file_dst)):
            print(file_dst + "위치에 이미 파일이 존재합니다. " + conversion_dst + "폴더 내부를 모두 비워주세요.")
            return -1
            
        if(file.split('.')[1] == targetFormat):
            copyfile(file_src, file_dst)
        else:
            convert_to_mp4(file_src, file_dst)


run()
