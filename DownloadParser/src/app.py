"""
프로그램의 메인 흐름.

GUI 모드 / 콘솔 모드 양쪽에서 호출 가능:
- GUI    : main(start='0519', end='0526', notify=callback)
- 콘솔   : main() — sys.executable 이름에서 날짜를 파싱한다.

notify 콜백은 GUI 가 진행 상황을 받기 위한 채널이다. (kind, **kw) 형태로 호출.
콜백을 안 넘기면 무시되므로 콘솔 동작에는 영향 없음.
"""

import os
import shutil
import sys
from typing import Callable, Optional

from . import config
from .downloader import download
from .helpers import format_memory
from .log_setup import logger, user_log
from .page import search_page
from .validators import check_date_normality, ensure_download_path


def _parse_dates_from_executable_name() -> tuple[str, str]:
    """sys.executable 의 basename 에서 STARTDATE / ENDDATE 를 추출."""
    base = os.path.basename(sys.executable).split(".")[0]   # "0519 0526"
    return tuple(base.split(" "))


def main(
    start: Optional[str] = None,
    end: Optional[str] = None,
    notify: Callable = lambda *a, **kw: None,
) -> None:
    """
    검색 기간을 받아 다운로드를 실행한다.

    start / end 가 None 이면 실행 파일 이름에서 파싱 (기존 콘솔 모드).
    """
    if start is None or end is None:
        start, end = _parse_dates_from_executable_name()

    config.STARTDATE = start
    config.ENDDATE = end
    config.target_contents.clear()       # 재실행 시 누적 방지
    config.cancel_event.clear()

    check_date_normality()
    ensure_download_path()

    total, used, free = shutil.disk_usage(config.DOWNLOAD_DIR)
    logger.info("total mem : %s" % format_memory(total))
    logger.info("free mem : %s" % format_memory(free))
    logger.info("executed")

    user_log.info(f"검색 시작 — 기간 {start} ~ {end}")
    user_log.info(f"저장 폴더: {config.DOWNLOAD_DIR} (여유: {format_memory(free)})")

    # 1) 검색: 페이지를 순회하며 다운로드 대상 큐 채우기
    notify("status", text="검색 중...")
    search_page(config.BASE_URL)

    total_items = len(config.target_contents)
    user_log.info(f"검색 완료 — 다운로드 대상 {total_items}건")
    notify("status", text=f"{total_items}건 발견 — 다운로드 시작")
    notify("progress", current=0, total=total_items)

    if total_items == 0:
        user_log.info("다운로드 대상이 없습니다. 종료합니다.")
        notify("done", message="다운로드 대상이 없습니다")
        return

    # 2) 다운로드: 큐에 쌓인 항목을 하나씩 받기
    for count, item in enumerate(config.target_contents, start=1):
        if config.cancel_event.is_set():
            user_log.info(f"사용자 요청으로 중지되었습니다 ({count - 1}/{total_items} 완료)")
            notify("status", text="중지됨")
            return

        item_name, item_link = item[0], item[1]
        user_log.info(f"[{count}/{total_items}] 받는 중: {item_name}")
        notify("status", text=f"받는 중: {item_name}")
        download(item_link, config.DOWNLOAD_DIR, item_name)

        saved_size = os.stat(config.DOWNLOAD_DIR + "/" + item_name).st_size
        logger.info(item_name + " : CHECK DOWNLOADED SIZE : " + str(saved_size))
        user_log.info(f"[{count}/{total_items}] 받기 완료: {item_name} ({format_memory(saved_size)})")

        raw_percentage = count / total_items
        progress_text = "({0}/{1}), {2}% done.".format(
            count, total_items, round(raw_percentage * 100, 3)
        )
        logger.info("download progress : " + progress_text)
        notify("progress", current=count, total=total_items)

    user_log.info(f"모든 다운로드 완료 — 총 {total_items}건")
    notify("done", message=f"{total_items}건 다운로드 완료 — 폴더를 확인하세요")


def run_console() -> None:
    """콘솔용 진입점. 예외 시 사용자가 메시지를 볼 수 있게 pause."""
    try:
        main()
    except Exception as exc:
        print("critical error occured, program will shutdown")
        print(exc)
        # 원본 버그 수정: 'string' + Exception → TypeError. str(exc) 로 감싸야 함.
        logger.info("CHECK SHUTDOWN REASON : " + str(exc))
        os.system("pause")
        sys.exit()
    print("Program ended successfully.")
    sys.exit()
