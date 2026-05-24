"""
다운로드 작업을 백그라운드 스레드에서 실행하는 래퍼.

GUI 가 freeze 되지 않도록 app.main() 을 별도 스레드에서 돌리고,
notify 콜백 / 예외를 모두 큐로 전달한다.
"""

import queue
import threading
import traceback
from typing import Optional

from ..app import main as run_download
from ..log_setup import logger, user_log


class DownloadWorker:
    """app.main() 을 백그라운드 스레드에서 실행하고 이벤트를 큐에 넣어 GUI 에 전달."""

    def __init__(self, event_queue: queue.Queue) -> None:
        self.event_queue = event_queue
        self.thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def start(self, start_date: str, end_date: str) -> None:
        if self.is_running():
            return
        self.thread = threading.Thread(
            target=self._run, args=(start_date, end_date), daemon=True
        )
        self.thread.start()

    def _notify(self, kind: str, **kwargs) -> None:
        self.event_queue.put((kind, kwargs))

    def _run(self, start_date: str, end_date: str) -> None:
        try:
            run_download(start=start_date, end=end_date, notify=self._notify)
        except Exception as exc:
            trace = traceback.format_exc()
            # 파일에는 풀 traceback, 사용자 화면에는 한 줄 요약
            logger.critical("UNCAUGHT EXCEPTION:\n" + trace)
            user_log.error(f"오류로 중단됨: {exc}")
            self._notify("error", message=str(exc), trace=trace)
        finally:
            self._notify("finished")
