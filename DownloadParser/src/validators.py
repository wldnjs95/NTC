"""
실행 전에 환경/입력이 정상인지 확인.

- check_date_normality : 파일명에서 파싱한 STARTDATE / ENDDATE 가 뒤집혔는지 검사
- ensure_download_path : 다운로드 폴더에 쓸 수 있는지 dry-run 으로 검사
"""

import os
import sys

from . import config
from .log_setup import logger, user_log


def check_date_normality() -> None:
    """STARTDATE > ENDDATE 면 (파일명이 잘못된 것) 종료 신호를 로그로 남긴다."""
    if config.STARTDATE > config.ENDDATE:
        caller = sys._getframe().f_code.co_name
        logger.error(
            "[ERROR][%s] Wrong target date, check file name and restart" % caller
        )
        logger.error("SYSTEM SHUTDOWN")
        return
    logger.info("[LOG][%s] date normality checked" % sys._getframe().f_code.co_name)


def ensure_download_path() -> None:
    """
    다운로드 디렉터리에 임시 파일을 쓰고 즉시 지운다.
    네트워크 드라이브가 마운트되지 않았으면 여기서 예외를 잡아 로그로 남긴다.
    """
    logger.info("downloading address : %s" % config.DOWNLOAD_DIR)
    probe_path = os.path.join(config.DOWNLOAD_DIR, "path check.txt")
    try:
        f = open(probe_path, "w")
        f.close()
        os.remove(probe_path)
    except Exception as e:
        user_log.error(f"저장 폴더에 쓸 수 없습니다: {config.DOWNLOAD_DIR}")
        user_log.error(f"  → {e}")
        logger.critical("DOWNLOAD PATH DOSEN'T EXIST")
        logger.critical(str(e))
