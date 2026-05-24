"""
로깅 설정.

두 개의 로거를 명확하게 분리한다:

- logger     (이름: "JW-LOG", 대상: 파일)
              개발자용. 함수 진입, HTTP 응답, 변수값, traceback 등 디버깅에 필요한
              상세 정보를 모두 기록한다. 파일에만 쌓이고 GUI 에는 노출 안 됨.

- user_log   (이름: "USER", 대상: 콘솔 + GUI 진행 상황 박스)
              사용자가 보고 이해할 메시지만. "검색 시작", "X건 발견",
              "받는 중: 김씨.zip", "받기 완료", "오류 발생" 같은 상황 알림.

코드 다른 곳에서는:
    from .log_setup import logger, user_log
    logger.info("내부 디버그용")          # 파일에만
    user_log.info("받기 완료: X.zip")     # 사용자에게 보임 + 파일에도 같이 남음
"""

import logging
import logging.handlers

from . import config


_FILE_FORMAT = "%(asctime)s - [%(funcName)s] - %(levelname)s - %(message)s"
_USER_FORMAT = "%(asctime)s  %(message)s"


def _build_file_logger() -> logging.Logger:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(config.LOG_PATH),
        when="D",
        backupCount=config.LOG_BACKUP_COUNT,
        encoding=config.LOG_ENCODING,
    )
    handler.setFormatter(logging.Formatter(_FILE_FORMAT))

    log = logging.getLogger("JW-LOG")
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    log.propagate = False
    return log


def _build_user_logger() -> logging.Logger:
    """사용자에게 보여줄 메시지 전용 로거.
    - 콘솔로도 출력 (콘솔 모드 호환)
    - GUI 가 시작될 때 QueueLogHandler 를 추가로 attach 해서 진행 상황 박스로 흘림
    - 동시에 파일 로거(logger) 에도 같은 메시지를 남기고 싶으면 user_log_and_file() 사용
    """
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(_USER_FORMAT, datefmt="%H:%M:%S"))

    log = logging.getLogger("USER")
    log.setLevel(logging.INFO)
    if not log.handlers:
        log.addHandler(handler)
    log.propagate = False
    return log


logger = _build_file_logger()
user_log = _build_user_logger()


def user_log_and_file(message: str, level: str = "info") -> None:
    """
    같은 메시지를 사용자 화면(GUI/콘솔) + 파일 로그 양쪽에 남긴다.
    중요한 사건(검색 시작, 오류 등) 처럼 둘 다에 흔적이 있어야 할 때 사용.
    """
    getattr(user_log, level)(message)
    getattr(logger, level)(message)


