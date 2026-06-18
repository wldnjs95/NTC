"""
백그라운드 워커.

두 가지 작업을 GUI 가 freeze 되지 않게 별도 스레드에서 실행한다.

  1) 브라우즈 (load_orders) — 사이트에서 주문 메타데이터를 페이지 단위로 가져옴
  2) 다운로드 (download_selected) — GUI 가 선택한 Order 들을 순차 다운로드

이벤트는 모두 큐에 (kind, kwargs) 형태로 push.
"""

import queue
import threading
import traceback
from typing import List, Optional

from .. import config
from ..app import download_selected
from ..log_setup import logger, user_log
from ..orders import Order, OrdersLoader


class DownloadWorker:
    """browse / download 두 모드를 가진 워커."""

    def __init__(self, event_queue: queue.Queue) -> None:
        self.event_queue = event_queue
        self.thread: Optional[threading.Thread] = None
        self.loader = OrdersLoader()

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    # ──────────────────────────────────────────────────────────────────
    # 브라우즈 — 등록·수정 양 탭을 한 번에 로드
    # ──────────────────────────────────────────────────────────────────
    def start_browse_all(self, n_pages: int, steps: List[str]) -> None:
        """
        지정한 step 들(등록·수정)을 한 스레드에서 순차 로드한 뒤,
        한 번의 `all_loaded` 이벤트로 {step: orders} 를 전달한다.

        탭별로 따로 fetch 하던 기존 방식(백그라운드 silent 프리페치)에서 생기던
        전환 레이스를 없애기 위해, 처음부터 양쪽을 다 받아 캐시에 채운다.
        """
        if self.is_running():
            return
        self.thread = threading.Thread(
            target=self._browse_all, args=(n_pages, list(steps)), daemon=True
        )
        self.thread.start()

    def _browse_all(self, n_pages: int, steps: List[str]) -> None:
        results: dict = {}
        try:
            config.cancel_event.clear()
            for step in steps:
                label = "수정" if step == config.STEP_MODIFIED else "등록"
                self._notify("status", text=f"{label} 목록 불러오는 중...")

                # step 전환 + 처음부터 다시 로드
                self.loader.set_step(step)
                self.loader.reset()

                def on_page(page_no: int, _label: str = label) -> None:
                    self._notify("status", text=f"{_label} 목록 — 페이지 {page_no} 로드 완료")

                orders = self.loader.load_next(n_pages=n_pages, on_progress=on_page)
                results[step] = orders
                user_log.info(f"{label} 탭 {len(orders)}건 로드 완료 (페이지 {self.loader.next_page - 1}장)")

            self._notify("all_loaded", results=results)
            total = sum(len(v) for v in results.values())
            self._notify("status", text=f"전체 {total}건 로드 완료")

        except Exception as exc:
            trace = traceback.format_exc()
            logger.critical("BROWSE_ALL UNCAUGHT:\n" + trace)
            user_log.error(f"목록 로드 실패: {exc}")
            self._notify("error", message=str(exc), trace=trace)
        finally:
            self._notify("finished", mode="browse")

    # ──────────────────────────────────────────────────────────────────
    # 다운로드
    # ──────────────────────────────────────────────────────────────────
    def start_download(self, orders: List[Order]) -> None:
        if self.is_running():
            return
        self.thread = threading.Thread(
            target=self._download, args=(orders,), daemon=True
        )
        self.thread.start()

    def _download(self, orders: List[Order]) -> None:
        try:
            download_selected(orders, notify=self._notify)
        except Exception as exc:
            trace = traceback.format_exc()
            logger.critical("DOWNLOAD UNCAUGHT:\n" + trace)
            user_log.error(f"오류로 중단됨: {exc}")
            self._notify("error", message=str(exc), trace=trace)
        finally:
            self._notify("finished", mode="download")

    # ──────────────────────────────────────────────────────────────────
    def _notify(self, kind: str, **kwargs) -> None:
        self.event_queue.put((kind, kwargs))
