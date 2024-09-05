코드 : formatConverter.py
동작방식 : conversion_src 폴더 내부에 있는 영상들을 conversion_dst 내부에 targetFormat으로 변환하여 저장함.

* 이미 targetFormat인 파일은 그냥 복사됨.

* FFMPEG_PATH에 존재하는 ffmpeg.exe로 여러개의 확장자를 가지는 영상을 변환, python 라이브러리 아니고 shell에 명령줄 보내는 방식

# ffmpeg 공식문서 : https://www.ffmpeg.org/ffmpeg.html