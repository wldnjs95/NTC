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
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional

from . import config
from .downloader import download
from .helpers import format_memory
from .log_setup import logger, user_log
from .page import search_page
from .parsers import get_zip_full_link
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


def download_selected(
    orders: List,
    notify: Callable = lambda *a, **kw: None,
) -> None:
    """
    GUI 가 선택한 Order 목록을 동시에 N개씩 다운로드 (config.PARALLEL_DOWNLOADS).

    각 Order 는 text_page_link 까지만 채워져 있고, 실제 zip 직링크는 여기서 가져온다.
    이미 받은 항목은 자동 스킵. 사용자가 중지를 누르면 진행 중인 다운로드도
    chunk loop 안에서 cancel_event 를 확인해 자체 중단됨.

    전체 진행률은 '완료된 파일 수 / 전체' 기준 (byte 단위 합산은 시작 시점에 총 크기를
    모르므로 정확한 비율이 들쭉날쭉할 수 있어 단순 카운트가 더 안정적임).
    각 행의 byte 단위 진행은 item_progress 이벤트로 그 행 상태 컬럼에만 표시.
    """
    config.cancel_event.clear()
    ensure_download_path()

    total, _used, free = shutil.disk_usage(config.DOWNLOAD_DIR)
    logger.info("total mem : %s" % format_memory(total))
    logger.info("free mem : %s" % format_memory(free))

    user_log.info(f"저장 폴더: {config.DOWNLOAD_DIR} (여유: {format_memory(free)})")
    user_log.info(
        f"선택 항목 {len(orders)}건 다운로드 시작 — 동시 {config.PARALLEL_DOWNLOADS}개"
    )
    notify("progress", current=0, total=len(orders))

    def _process_one(idx_in_order: int, order) -> None:
        if config.cancel_event.is_set():
            return
        if order.already_downloaded:
            user_log.info(f"건너뜀 (다운완료): {order.zip_filename}")
            notify("item_done", row_id=order.row_id, status="다운완료")
            return

        user_log.info(f"받는 중: {order.zip_filename}")
        notify("item_status", row_id=order.row_id, status="받는 중")

        # 다운로드 직링크는 여기서 한 번에 가져온다 (지연 fetch).
        try:
            order.zip_url = get_zip_full_link(order.text_page_link)
        except Exception as exc:
            user_log.error(f"링크 추출 실패: {order.zip_filename} → {exc}")
            notify("item_status", row_id=order.row_id, status="오류")
            return

        def _on_chunk(
            done,
            total_bytes,
            _row=order.row_id,
            _name=order.zip_filename,
            _idx=idx_in_order,
        ):
            # 행별 진행 (퍼센트) — 모든 모드에서.
            notify(
                "item_progress",
                row_id=_row,
                bytes_done=done,
                bytes_total=total_bytes,
                filename=_name,
            )
            # 전체 byte 단위 부드러운 진행률은 순차(N=1) 일 때만 의미 있음.
            # 병렬에선 여러 파일 chunk 가 섞여 와서 바가 들쭉날쭉해지므로 emit 안 함.
            if config.PARALLEL_DOWNLOADS == 1:
                notify(
                    "chunk",
                    file_index=_idx,
                    total_files=len(orders),
                    bytes_done=done,
                    bytes_total=total_bytes,
                    filename=_name,
                )

        download(order.zip_url, config.DOWNLOAD_DIR, order.zip_filename, on_chunk=_on_chunk)

        target_path = os.path.join(config.DOWNLOAD_DIR, order.zip_filename)
        if (
            os.path.exists(target_path)
            and os.path.getsize(target_path) >= config.MIN_VALID_FILE_BYTES
        ):
            saved_size = os.stat(target_path).st_size
            logger.info(order.zip_filename + " : CHECK DOWNLOADED SIZE : " + str(saved_size))
            user_log.info(
                f"받기 완료: {order.zip_filename} ({format_memory(saved_size)})"
            )
            order.already_downloaded = True
            notify("item_done", row_id=order.row_id, status="완료")
        else:
            user_log.error(f"받기 실패: {order.zip_filename} (사이즈 부족)")
            order.already_downloaded = False
            notify("item_status", row_id=order.row_id, status="오류")

    completed = 0
    with ThreadPoolExecutor(max_workers=config.PARALLEL_DOWNLOADS) as ex:
        futures = [ex.submit(_process_one, i + 1, o) for i, o in enumerate(orders)]
        for future in as_completed(futures):
            if config.cancel_event.is_set():
                user_log.info(f"사용자 요청으로 중지 ({completed}/{len(orders)} 완료)")
                notify("status", text="중지됨")
                # 진행 중 download() 는 chunk 루프에서 cancel_event 확인해 자체 중단,
                # 미시작 future 는 _process_one 초입의 cancel 체크로 즉시 빠짐
                break
            try:
                future.result()
            except Exception as exc:
                user_log.error(f"작업 예외: {exc}")
            completed += 1
            notify("progress", current=completed, total=len(orders))

    user_log.info(f"모든 다운로드 완료 — 총 {completed}/{len(orders)}건 처리")
    notify("done", message=f"{completed}/{len(orders)}건 처리 완료")


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
