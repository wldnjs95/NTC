"""
프로그램 전역 설정.
모든 상수·URL·경로는 이 파일에서만 관리한다.
"""

import os
import threading
from pathlib import Path


# 프로그램 메타 정보
APP_NAME = "보자기카드 다운로더"
APP_VERSION = "2.0.8"
APP_VENDOR = "NTC"

# 보자기카드 페이지의 탭 (URL 의 step 파라미터)
STEP_REGISTERED = "1"   # 등록 — 압축(zip) 다운로드
STEP_MODIFIED = "2"     # 수정 — 이미지 원본 다운로드 (변환 불필요)

# 보자기카드 영상주문 검색 페이지 URL 템플릿.
# {admin_id} 는 첫 실행 시 사용자가 입력한 SITE_ADMIN_ID 로 런타임 치환.
# 이렇게 두면 EXE 디컴파일해도 ID 가 박혀있지 않음.
BASE_URL_TEMPLATE = (
    "http://bojagicard.com/join/mov_list.php"
    "?page=1&SITE_ADMIN_ID={admin_id}&step=1"
    "&&dates=&datee=&id=&list_mode=&keyword=&Search_mode="
    "&Search_text=&category=&color=&style=&stylegroup=&list_type=&mode="
)

# 런타임에 license_input 에서 채워짐. 빈 값이면 검색 호출 시 에러.
SITE_ADMIN_ID: str = ""


def base_url() -> str:
    """현재 SITE_ADMIN_ID 가 들어간 검색 URL."""
    return BASE_URL_TEMPLATE.format(admin_id=SITE_ADMIN_ID)

# 다운로드 파일을 저장할 폴더 (기본값은 매핑된 네트워크 드라이브).
# GUI 의 "찾아보기" 로 런타임에 덮어쓸 수 있음.
DOWNLOAD_DIR = r"Z:\partner_bojagi"

# 다운로드 직링크가 만들어질 때 앞에 붙는 호스트
FILE_HOST = "http://gwl2.bojagicard.com"

# ── 수정 탭(수정요청 이미지) 관련 ──
# 수정요청 이미지 목록은 '로그인'해야만 보인다. (SITE_ADMIN_ID 파라미터만으론 빈 응답)
LOGIN_URL = "http://bojagicard.com/join/login_proc.html"
LOGIN_PAGE = "http://bojagicard.com/join/login.html"
# 한 주문의 수정요청(시안) 이미지 목록을 주는 AJAX 엔드포인트.
# 호출: SIAN_LIST_URL?order_num=<mvXXXX>&category=
SIAN_LIST_URL = "http://bojagicard.com/join/mov_list_sian_list.php"
# 수정요청 이미지 src 가 '/upload/...' 처럼 / 로 시작하면 앞에 붙일 호스트
IMAGE_HOST = "http://bojagicard.com"

# 검색 상한 (20page, infinite loop 방지)
MAX_PAGES = 20

# 다운로드 후 50KB 미만이면 의심 파일로 경고
MIN_VALID_FILE_BYTES = 50_000

# 페이지 응답 인코딩 (서버 변경에 따라 cp949 → utf-8)
RESPONSE_ENCODING = "utf-8"

# 네트워크 타임아웃 (초)
HTTP_TIMEOUT = 30

# 동시에 받을 zip 파일 개수.
# 1 = 순차 (한 파일씩, 전체 진행률 바가 byte 단위로 부드럽게 차오름).
# 2 이상 = 병렬 (속도 ↑, 단 전체 진행률 바는 파일 완료 카운트 기반).
PARALLEL_DOWNLOADS = 3

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

# 사용자별 데이터 디렉터리 (로그 폴더의 부모) — 라이센스 파일 등 저장
DATA_DIR = LOG_DIR.parent
LICENSE_FILE = DATA_DIR / "admin_id.bin"
# 로그인 비밀번호 (수정요청 이미지 조회용). admin_id 와 같은 방식으로 PC 단위 암호화 저장.
ADMIN_PW_FILE = DATA_DIR / "admin_pw.bin"

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
