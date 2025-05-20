# logging_utils.py
import logging
from datetime import datetime
import sys

# Optional GUI label (set externally)
status_label = None

def init_logging(logfile="app.log"):
    logging.basicConfig(
        level=logging.DEBUG,  # 파일에는 DEBUG 이상 모두 기록됨
        filename=logfile,
        filemode="a",  # 기존 로그 덮어쓰기
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

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
        self.original_stdout = sys.__stdout__

    def write(self, message):
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

def log_debug(msg):
    logging.debug(msg)             # 로그 파일만 기록

def log_error(msg):
    logging.error(msg)

def log_exception(msg):
    logging.exception(msg)
