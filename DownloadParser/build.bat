@echo off
REM Windows 빌드 스크립트. Python 3.10+ 가 설치된 환경에서 실행.
REM 사용법: build.bat
REM 결과:   dist\보자기카드 다운로드.exe   (GUI 윈도우 모드)

pip install -r requirements.txt

pyinstaller --onefile --noconsole ^
    --name "보자기카드 다운로드 v2.0.8" ^
    --icon "src/gui/assets/ntc_logo.ico" ^
    --hidden-import concurrent.futures.process ^
    --add-data "src/gui/theme.json;src/gui" ^
    --add-data "src/gui/assets/ntc_logo.png;src/gui/assets" ^
    --add-data "src/gui/assets/fonts/NotoSansKR-Variable.ttf;src/gui/assets/fonts" ^
    run.py

echo ----------------------------------------
echo Built: dist\보자기카드 다운로드.exe
echo ----------------------------------------
pause
