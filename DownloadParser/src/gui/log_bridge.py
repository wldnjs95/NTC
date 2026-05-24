"""
백그라운드 워커가 logger.info(...) 로 남기는 메시지를 GUI 가 그리도록
스레드 세이프 큐로 옮겨주는 logging.Handler.

워커 스레드에서 emit() 호출 → 큐에 push.
GUI 메인 스레드에서 tkinter.after() 로 주기적으로 queue.get_nowait() → 텍스트박스에 그림.
"""

import logging
import queue


class QueueLogHandler(logging.Handler):
    """logger 출력을 큐에 쌓는 핸들러. GUI 가 큐를 polling 한다."""

    def __init__(self) -> None:
        super().__init__()
        self.queue: queue.Queue = queue.Queue()

    def emit(self, record: logging.LogRecord) -> None:
        self.queue.put(self.format(record))
