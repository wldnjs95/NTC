"""
다운로드 큐 등록 + 실제 파일 다운로드.

전체 흐름:
    page.filter_customers_in_range()
        └── add_to_download_list(customer)   ← 큐(config.target_contents)에 [이름.zip, 직링크] 추가
    app.main()
        └── for item in target_contents:
                download(url, dir, filename) ← 한 건씩 받기

중복 처리:
    1) 디스크에 이미 존재 + 크기 > 0  → 스킵 (이미 받은 파일)
    2) 같은 실행 중 같은 이름이 큐에 중복 등록되려 할 때  → 스킵 (검색 페이지 갱신 사이 중복 노출 대비)
    실제로 받을 때는 한 번에 하나씩 순차 진행하므로 한 프로세스 안에서 race 없음.
"""

import logging
import os

import requests
from urllib3 import PoolManager

from . import config
from .log_setup import logger, user_log
from .parsers import make_zip_filename, get_text_page_link, get_zip_full_link


def add_to_download_list(single_customer) -> int:
    """
    한 고객의 zip 파일명·직링크를 만들어 다운로드 큐에 추가.

    스킵 조건:
      - 디스크에 이미 있고 크기가 0 이 아님  → 이전 실행에서 받은 파일
      - 같은 파일명이 이미 큐에 있음        → 같은 실행 안 중복
    """
    logger.info("executed")

    sc_name = make_zip_filename(single_customer)
    txt_link = get_text_page_link(single_customer)
    http_txt_link = txt_link.replace("https", "http")
    sc_link = get_zip_full_link(http_txt_link)

    logger.info("adding file download list")
    logger.info("file name : [%s] " % sc_name)
    logger.info("direct link : [%s] " % sc_link)

    file_name = sc_name + ".zip"
    target_path = os.path.join(config.DOWNLOAD_DIR, file_name)

    # 스킵 1: 이미 디스크에 있음
    if os.path.isfile(target_path) and os.path.getsize(target_path) != 0:
        user_log.info(f"건너뜀 (이미 받음): {file_name}")
        logger.warning("file [%s] already exists" % file_name)
        return 0

    # 스킵 2: 같은 이름이 이번 실행 큐에 이미 들어가 있음
    if any(existing[0] == file_name for existing in config.target_contents):
        user_log.info(f"건너뜀 (이번 실행 중복): {file_name}")
        logger.warning("file [%s] already in queue" % file_name)
        return 0

    user_log.info(f"대기열 추가: {sc_name}")
    config.target_contents.append([file_name, sc_link])
    return 0


def download(url: str, address: str, file_name: str) -> int:
    """
    하나의 zip 파일을 받아 디스크에 저장.

    Content-Length 가 50KB 미만이면 의심 파일로 경고.
    예외가 나도 main() 흐름이 끊기지 않도록 여기서 잡고 critical 로 로깅한다.
    """
    target_path = os.path.join(address, file_name)
    logger.info("download path : [%s]" % target_path)

    try:
        logging.info("downloading : [%s]" % file_name)

        with open(target_path, "wb") as file:
            pool = PoolManager()
            pre_response = pool.request("GET", url, preload_content=False)
            content_bytes = pre_response.headers.get("Content-Length")
            logger.info(file_name + " [ size  : " + str(content_bytes) + "]")

            if content_bytes and int(content_bytes) < config.MIN_VALID_FILE_BYTES:
                user_log.warning(f"⚠ {file_name} 이 50KB 미만 — 내용 확인 필요")
                logger.warning(file_name + " : FILE SIZE IS LESS THAN 50K, NEEDS TO BE CHECKED")

            response = requests.get(url, timeout=config.HTTP_TIMEOUT)
            file.write(response.content)

        return 0

    except Exception as e:
        user_log.error(f"받기 실패: {file_name} → {e}")
        logger.critical("ERROR WHILE DOWNLOAD")
        logger.critical(str(e))
        return 0
