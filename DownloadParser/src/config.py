"""
프로그램 전역 설정.
모든 상수·URL·경로는 이 파일에서만 관리한다.
"""

import os
import threading
from pathlib import Path

# 보자기카드 영상주문 검색 페이지 URL (페이지 번호는 page= 부분이 자동 증가)
BASE_URL = (
    "http://bojagicard.com/join/mov_list.php"
    "?page=1&SITE_ADMIN_ID=ntccomm&step=1"
    "&&dates=&datee=&id=&list_mode=&keyword=&Search_mode="
    "&Search_text=&category=&color=&style=&stylegroup=&list_type=&mode="
)

# 다운로드 파일을 저장할 폴더 (기본값은 매핑된 네트워크 드라이브).
# GUI 의 "찾아보기" 로 런타임에 덮어쓸 수 있음.
DOWNLOAD_DIR = r"Z:\partner_bojagi"

# 다운로드 직링크가 만들어질 때 앞에 붙는 호스트
FILE_HOST = "http://gwl2.bojagicard.com"

# 검색 상한 (20page, infinite loop 방지)
MAX_PAGES = 20

# 다운로드 후 50KB 미만이면 의심 파일로 경고
MIN_VALID_FILE_BYTES = 50_000

# 페이지 응답 인코딩 (서버 변경에 따라 cp949 → utf-8)
RESPONSE_ENCODING = "utf-8"

# 네트워크 타임아웃 (초)
HTTP_TIMEOUT = 30

# 로그 파일 위치
# Windows: %LOCALAPPDATA%\NTC\BojagiDownloader\logs\
# macOS/Linux 개발 환경: ~/.local/share/NTC/BojagiDownloader/logs/
#
# .exe 위치와 무관한 고정 경로에 두는 이유:
#   - 클라이언트가 exe 를 옮겨도 로그가 흩어지지 않음
#   - 네트워크 드라이브에 exe 를 둬도 로그는 항상 로컬에 안전하게 저장
#   - UnzipRefactored 와 동일한 NTC/ 폴더 아래로 묶여 진단 시 한 번에 찾기 쉬움

def _resolve_log_dir() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        return Path(base) / "NTC" / "BojagiDownloader" / "logs"
    return Path.home() / ".local" / "share" / "NTC" / "BojagiDownloader" / "logs"


LOG_DIR = _resolve_log_dir()
LOG_FILENAME = "Time Rotate Log.log"
LOG_PATH = LOG_DIR / LOG_FILENAME
LOG_BACKUP_COUNT = 10
LOG_ENCODING = "utf-8"

# 메모리 단위 (memoryFormatting에서 사용)
MEMORY_UNITS = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB", 5: "PB", 6: "EB", 7: "ZB"}

# 런타임에 main()이 실행 파일 이름에서 파싱해 채운다 ("0519 0526.exe" → "0519", "0526")
STARTDATE = "0000"
ENDDATE = "0000"

# 다운로드 대상 누적 리스트: [[파일명, 직링크], ...]
target_contents: list = []

# GUI 의 "중지" 버튼이 설정하는 취소 신호.
# 페이지/다운로드 루프가 매 반복마다 이 값을 보고 협조적으로 종료한다.
cancel_event = threading.Event()
