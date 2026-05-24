@echo off
REM Windows 빌드 스크립트. Python 3.10+ 가 설치된 환경에서 실행.
REM 사용법: build.bat
REM 결과:   dist\보자기카드 다운로드.exe   (GUI 윈도우 모드)

pip install -r requirements.txt

pyinstaller --onefile --noconsole ^
    --name "보자기카드 다운로드" ^
    --hidden-import concurrent.futures.process ^
    run.py

echo ----------------------------------------
echo Built: dist\보자기카드 다운로드.exe
echo ----------------------------------------
pause
