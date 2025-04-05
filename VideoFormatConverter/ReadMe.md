# Video Format Converter

## 요구사항

> [FFMPEG Python Wrapper](https://pypi.org/project/imageio-ffmpeg/), [OpenCV](https://pypi.org/project/opencv-python/)

>PIP  
> ```commandline  
> pip install opencv imageio-ffmpeg  
> ```

>CONDA
> ```commandline
> conda install -c conda-forge opencv imageio-ffmpeg
> ```

## 코드

### Program.py

실행 코드

{PWD}에서 "노벰버송"이 포함된 이름과 .zip 확장자를 가진 파일을 찾고, 압축 해제 후 내용물을 .mp4로 변환한 후 실행 위치에서 .aep 파일을 찾아 압축 해제된 폴더에 복사한다.

----

### ImplementationTarget.py

노벰버송 원본 코드, formatConverter 합병 이전 코드

----

### formatConverter.py

conversion_src 폴더 내부에 있는 영상들을 conversion_dst 내부에 targetFormat으로 변환하여 저장함.

* 이미 targetFormat인 파일은 그냥 복사됨.

[FFMPEG 공식문서](https://www.ffmpeg.org/ffmpeg.html)
