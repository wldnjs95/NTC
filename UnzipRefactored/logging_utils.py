# logging_utils.py
import inspect
import logging
from datetime import datetime
import sys
import os

# Optional GUI label (set externally)
status_label = None

def init_logging(logfile="app.log"):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # 파일 핸들러 (UTF-8 인코딩 명시)
    file_handler = logging.FileHandler(logfile, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)

    # 콘솔 핸들러 (선택적으로 추가 가능)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(file_formatter)

    # 핸들러 중복 방지
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

class DualLogger:
    def __init__(self, textbox):
        self.textbox = textbox
        self.original_stdout = sys.__stdout__

    def write(self, message):
        self.textbox.insert("end", message)
        self.textbox.see("end")
        self.original_stdout.write(message)

    def flush(self):
        pass
    

class InfoOnlyLogger:
    def __init__(self, textbox):
        self.textbox = textbox
        self.original_stdout = sys.__stdout__ or sys.stdout or open(os.devnull, 'w') #exe build 에러 방지

    def write(self, message):
        with open("debug_log.txt", "a", encoding="utf-8") as f:
            f.write(f"WRITE CALLED: {message}\n")
            
        if "[INFO]" in message:
            self.textbox.insert("end", message)
            self.textbox.see("end")
        self.original_stdout.write(message)  # 터미널에도 출력

    def flush(self):
        pass


def log_user(msg):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}][INFO] {msg}")
    logging.info(msg)            

#def log_debug(msg):
#    logging.debug(msg)             # 로그 파일만 기록
    
def log_debug(message=""):
    caller = inspect.currentframe().f_back.f_code.co_name # 로그 파일만 기록
    logging.debug(f"[{caller}] {message}")

def log_error(msg):
    logging.error(msg)

def log_exception(msg):
    logging.exception(msg)
