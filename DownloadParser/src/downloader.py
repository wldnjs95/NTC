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
    2) 같은 실행 중 같은 이름이 큐에 중복 등록되려 할 때  → 스킵
"""

import logging
import os
import time
from typing import Callable, Optional

import requests

from . import config
from .log_setup import logger, user_log
from .parsers import make_zip_filename, get_text_page_link, get_zip_full_link


def add_to_download_list(single_customer) -> int:
    """
    한 고객의 zip 파일명·직링크를 만들어 다운로드 큐에 추가.
    이미 받았거나 이번 실행 큐에 있으면 스킵.
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

    if os.path.isfile(target_path) and os.path.getsize(target_path) != 0:
        user_log.info(f"건너뜀 (다운완료): {file_name}")
        logger.warning("file [%s] already exists" % file_name)
        return 0

    if any(existing[0] == file_name for existing in config.target_contents):
        user_log.info(f"건너뜀 (이번 실행 중복): {file_name}")
        logger.warning("file [%s] already in queue" % file_name)
        return 0

    user_log.info(f"대기열 추가: {sc_name}")
    config.target_contents.append([file_name, sc_link])
    return 0


# 청크 진행률 콜백 주기 — 너무 자주 호출하면 큐 폭주, 너무 드물면 부드럽지 않음.
_CHUNK_NOTIFY_INTERVAL = 0.1   # 초당 최대 10회 갱신
_CHUNK_SIZE = 64 * 1024        # 64KB 단위로 받기


def download(
    url: str,
    address: str,
    file_name: str,
    on_chunk: Optional[Callable[[int, int], None]] = None,
) -> int:
    """
    하나의 zip 파일을 스트리밍으로 받아 디스크에 저장.

    on_chunk(downloaded_bytes, total_bytes) 콜백이 주기적으로 호출돼
    GUI 에서 byte 단위 진행률을 그릴 수 있게 한다. 호출 주기는 약 100ms.

    파일 받는 도중 config.cancel_event 가 set 되면 즉시 중단.
    """
    target_path = os.path.join(address, file_name)
    logger.info("download path : [%s]" % target_path)

    try:
        logging.info("downloading : [%s]" % file_name)

        with requests.get(url, stream=True, timeout=config.HTTP_TIMEOUT) as response:
            response.raise_for_status()
            total = int(response.headers.get("Content-Length", "0") or "0")
            logger.info(file_name + " [ size  : " + str(total) + "]")

            if total and total < config.MIN_VALID_FILE_BYTES:
                user_log.warning(f"⚠ {file_name} 이 50KB 미만 — 내용 확인 필요")
                logger.warning(file_name + " : FILE SIZE IS LESS THAN 50K, NEEDS TO BE CHECKED")

            downloaded = 0
            last_notify = time.monotonic()

            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=_CHUNK_SIZE):
                    if config.cancel_event.is_set():
                        # 부분 다운로드 파일은 남겨둠. 다음 실행에서 size>0 이라
                        # add_to_download_list 가 스킵할 수 있음 — 필요시 user 가 수동 삭제.
                        break
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)

                    now = time.monotonic()
                    if on_chunk and (now - last_notify >= _CHUNK_NOTIFY_INTERVAL):
                        on_chunk(downloaded, total)
                        last_notify = now

            if on_chunk:
                on_chunk(downloaded, total)   # 완료 시 마지막 한 번 (100%)

        return 0

    except Exception as e:
        user_log.error(f"받기 실패: {file_name} → {e}")
        logger.critical("ERROR WHILE DOWNLOAD")
        logger.critical(str(e))
        return 0
