"""
보자기카드 다운로드 프로그램의 메인 윈도우 (목록 기반 UI).

레이아웃 (위 → 아래):
    [저장 경로 + 폴더 선택]
    [새로고침 / 더 불러오기 / 범례]
    [주문 목록 테이블] — Treeview, 다중 선택 가능
    [선택 카운트 + 다운로드/중지 버튼]
    [진행률 바 + 상태]
    [실시간 진행 로그 + 로그 폴더 열기]

동작 흐름:
    1) 프로그램 실행 → 첫 페이지 자동 로드 (2페이지)
    2) 작업자가 행 선택 (단일 / Shift+클릭 범위 / Ctrl+클릭 토글 — Treeview 기본 지원)
    3) [다운로드 시작] → download_selected() 실행
"""

import logging
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from tkinter import ttk
from typing import Dict, List

import customtkinter as ctk

from .. import config
from .. import license_input
from ..helpers import format_memory
from ..log_setup import user_log
from ..orders import Order
from .dialogs import prompt_text, show_error, show_info
from .log_bridge import QueueLogHandler
from .style_helpers import apply_tree_style, apply_tree_tags, container_bg, pick_row_tag
from .worker import DownloadWorker


_THEME_PATH = os.path.join(os.path.dirname(__file__), "theme.json")
_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "ntc_logo.png")
# 번들된 Noto Sans KR (구글 폰트). 시스템에 설치돼 있지 않아도 런타임에 로드해
# 어느 PC 에서나 동일한 글꼴로 보이게 한다. theme.json / style_helpers 의 family
# 이름("Noto Sans KR")과 반드시 일치해야 한다.
_FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "NotoSansKR-Variable.ttf")


def _load_bundled_font() -> None:
    """앱 폰트를 프로세스에 로드. 위젯/테마가 폰트를 쓰기 전에 한 번 호출."""
    try:
        ctk.FontManager.load_font(_FONT_PATH)
    except Exception:
        pass   # 실패해도 OS 기본 폰트로 동작 (글자만 다르게 보임)

# 체크박스 표시 문자 (선택 / 미선택). 둥근 모서리 사각 (U+25A2 / U+25A3).
_CHECK_ON = "▣"
_CHECK_OFF = "▢"


_GUI_LOG_FORMAT = "%(asctime)s  %(message)s"
_POLL_INTERVAL_MS = 100

# 시각 위계를 위한 버튼 스타일 키.
# Primary(인디고): 1차 액션 (선택 항목 다운로드, 선택 날짜 다운로드)
# Secondary(투명+보더): 보조 액션 (폴더 선택/열기, 새로고침, 전체선택/해제, 로그폴더 열기 등)
_SECONDARY_BTN = {
    "fg_color": "transparent",
    "border_width": 1,
    "border_color": ("#D5D5DC", "#3A3A3F"),
    "text_color": ("#1A1A1F", "#F2F2F7"),
    "hover_color": ("#F0F0F5", "#26262A"),
}

# 상태 컬럼 표시 텍스트
_STATUS_PENDING = "대기"
_STATUS_DONE = "완료"
_STATUS_SKIP = "다운완료"
_STATUS_DOWNLOADING = "받는 중"
_STATUS_ERROR = "오류"

# Treeview 'values' 튜플에서 상태 컬럼의 인덱스.
# columns = (order_date, customer, product, status) 순서이므로 마지막인 3번.
# 컬럼이 추가/삭제되면 이 상수만 수정.
_STATUS_COL_INDEX = 3

# 헤더 표시 텍스트. 정렬 화살표 (▲▼) 가 뒤에 붙으면 동적으로 갱신.
_HEADING_TEXT = {
    "#0": "",
    "order_date": "주문일",
    "customer": "고객명",
    "product": "상품",
    "status": "상태",
}


class BojagiDownloaderApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"보자기카드 자료 일괄 다운로드 v{config.APP_VERSION}")
        # 초기 크기를 넉넉히 — 모든 영역(목록·다운로드 버튼·진행률·로그·푸터)이
        # 처음부터 한 화면에 다 보이도록. minsize 도 모든 요소가 항상 보이는
        # 높이로 잡아, 사용자가 창을 줄여도 아래쪽이 잘리지 않게 한다.
        self.geometry("1040x900")
        self.minsize(900, 840)
        # 위젯·오버레이 배치가 끝날 때까지 창을 숨겨, 홈화면이 잠깐 비쳤다가
        # 로딩으로 넘어가는 깜빡임을 없앤다. 준비 끝나면 deiconify 로 한 번에 표시.
        self.withdraw()

        # 워커 ↔ GUI 이벤트 큐
        self.event_queue: queue.Queue = queue.Queue()
        self.worker = DownloadWorker(self.event_queue)

        # 현재 화면에 있는 Order 들. row_id(=zip_filename) → Order
        self.orders: Dict[str, Order] = {}

        # Shift+클릭 범위 선택을 위한 앵커. 마지막 plain-click 한 행 id 를 기억.
        self._click_anchor: str | None = None

        # 컬럼 헤더 정렬 상태. None 이면 정렬 안 됨.
        self._sort_col: str | None = None
        self._sort_reverse: bool = False

        # 현재 활성 탭의 step 코드 (등록/수정)
        self._current_step: str = config.STEP_REGISTERED

        # 탭별 캐시. 다른 탭으로 갈 때 현재 데이터를 여기 저장하고,
        # 돌아올 때 네트워크 호출 없이 복원. 새로고침 시 전부 비움.
        # step → row_id → Order
        self._tab_cache: Dict[str, Dict[str, Order]] = {}

        # 다운로드 순차 대기열. 다운로드 중에 다른(또는 같은) 탭에서 또 다운로드를
        # 누르면 즉시 시작하지 않고 여기 쌓아두었다가, 현재 작업이 끝나면 자동으로
        # 다음 작업을 시작한다. 각 항목: {"orders": [...], "path": str, "label": str}
        self._download_queue: List[dict] = []

        # 사용자 로그를 GUI 박스로 흘려보내는 핸들러
        self.log_handler = QueueLogHandler()
        self.log_handler.setFormatter(logging.Formatter(_GUI_LOG_FORMAT, datefmt="%H:%M:%S"))
        user_log.addHandler(self.log_handler)

        # 위젯/테마가 폰트를 참조하기 전에 번들 폰트를 먼저 로드한다.
        _load_bundled_font()

        ctk.set_appearance_mode("System")
        # 커스텀 모던 테마 (없으면 기본값 fallback)
        try:
            ctk.set_default_color_theme(_THEME_PATH)
        except Exception:
            ctk.set_default_color_theme("blue")

        # 윈도우/모달 타이틀바 아이콘. iconphoto(default=True) 로 모든 자식
        # 모달(messagebox 등) 도 같은 아이콘을 상속받음 → 파이썬 깃털 안 보임.
        # 인스턴스 속성으로 보관해 GC 방지.
        try:
            self._window_icon = tk.PhotoImage(file=_ICON_PATH)
            self.iconphoto(True, self._window_icon)
        except tk.TclError:
            pass

        self._build_widgets()
        # 창이 뜨는 첫 프레임부터 로딩 오버레이를 보여준다 — 관리자 ID 검증
        # (네트워크) + 첫 로드까지 빈 메인화면이 잠깐 노출되는 걸 막음.
        self._show_loading_overlay("준비 중...")
        # 레이아웃을 미리 계산해 오버레이가 전체 크기로 자리잡게 한 뒤 창을 표시.
        # → 홈화면이 깜빡 비쳤다가 로딩으로 넘어가는 현상 제거.
        self.update_idletasks()
        self.deiconify()
        self._poll_events()

        # 일부 환경(고DPI 디스플레이 / PyInstaller 프로즌 빌드)에서는 mainloop 가
        # 시작되기 전에 호출한 deiconify() 가 실제로 창을 표시하지 못해, 창이
        # WS_VISIBLE 없이 숨겨진 채로 남는다(데이터는 로드되는데 화면만 안 뜸).
        # 이벤트 루프에 진입한 직후 한 번 더 확실히 표시해 이 문제를 막는다.
        self.after(0, self._force_show)

        # 윈도우가 그려진 직후에 관리자 ID 확인 → 정상이면 첫 페이지 로드.
        # 모달이 부모 윈도우 위치를 참조하므로 윈도우가 렌더된 후 호출해야 함.
        self.after(150, self._startup_check)

    def _force_show(self) -> None:
        """mainloop 진입 직후 호출되어 메인 창을 확실히 화면에 표시한다."""
        try:
            self.deiconify()
            self.state("normal")
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _startup_check(self) -> None:
        """
        관리자 ID 확보 후 첫 페이지 로드.

        저장된 ID 가 있으면 네트워크 재검증 없이 바로 신뢰하고 로드한다.
        - 시작 시 네트워크 검증을 하면: ① 1~2초 멈춤(버벅임), ② 오프라인/서버
          불안정 시 정상 ID 도 실패해 재입력 요구, ③ 등록 0건인 정상 계정이
          매 시작마다 확인 모달에 걸림 — 모두 같은 PC 재사용을 방해한다.
        - 잘못된 ID 가 저장돼 있으면 목록이 비어 보이고, 'ID 변경' 으로 고치면 됨.
        ID 유효성 검증은 '처음 입력하는 순간' 에만 한다 (_request_admin_id).
        """
        stored = license_input.load_admin_id()
        if stored:
            config.SITE_ADMIN_ID = stored
            user_log.info("저장된 관리자 ID 사용")
            self._ensure_pw_then_browse()
        else:
            # 저장된 ID 없음 → 바로 입력 모달 (네트워크 없음)
            self._request_admin_id(is_startup=True)

    def _ensure_pw_then_browse(self) -> None:
        """로그인 비밀번호(수정요청 이미지용)가 없으면 한 번 입력받은 뒤 목록을 로드한다.
        비밀번호는 수정 탭 다운로드에만 필요하므로, 입력을 취소해도 목록 로드는 진행한다."""
        if license_input.load_admin_pw() is None:
            self._request_password(is_startup=True)
        else:
            self._start_browse(append=False)

    def _request_password(self, is_startup: bool) -> None:
        """로그인 비밀번호 입력 모달 (마스킹). 저장 후 동작 이어감."""
        # 입력 단계에선 '불러오는 중' 오버레이를 내린다 (로딩 표시 ↔ 입력 대기 모순 제거).
        # 입력이 끝나면 _start_browse 가 로드 시점에 오버레이를 다시 띄운다.
        self._hide_loading_overlay()
        pw = prompt_text(
            self,
            title="로그인 비밀번호",
            message="보자기카드 로그인 비밀번호를 입력하세요.",
            placeholder="비밀번호",
            show="●",
        )
        if pw:
            license_input.save_admin_pw(pw)
            user_log.info("로그인 비밀번호 저장 완료")
        else:
            user_log.info("비밀번호 입력을 건너뜀 (수정요청 이미지는 받을 수 없음)")
        # 시작 단계면 비번 유무와 상관없이 목록 로드로 진행
        if is_startup:
            self._start_browse(append=False)

    def _validate_admin_id_async(self, admin_id: str, on_result) -> None:
        """
        관리자 ID 네트워크 검증을 백그라운드 스레드에서 수행.
        on_result(status: str, msg: str) 는 항상 메인스레드에서 호출된다.
        status 는 'valid' / 'empty' / 'error' (validate_admin_id 참고).
        """
        def work() -> None:
            status, msg = license_input.validate_admin_id(admin_id)
            # 결과를 메인스레드로 마샬링 (Tk 위젯은 메인스레드에서만 건드림)
            self.after(0, lambda: on_result(status, msg))

        threading.Thread(target=work, daemon=True).start()

    def _request_admin_id(self, is_startup: bool) -> None:
        """
        관리자 ID 입력 모달을 띄우고, 입력값을 백그라운드로 검증.
        - is_startup=True  : 취소 시 앱 종료
        - is_startup=False : 취소 시 아무 변경 없이 복귀 (ID 변경 메뉴)

        검증 결과별 동작:
        - valid : 저장 + 로드
        - empty : 주문 0건 (틀린 ID 이거나 진짜 빈 계정) → 확인 다이얼로그.
                  '이 ID로 계속' 이면 저장+로드, '다시 입력' 이면 재요청.
        - error : 형식/네트워크 오류 → 에러 모달 후 재요청.
        """
        # 입력(설정) 단계에선 '불러오는 중' 오버레이를 내려, 로딩 표시와 입력 대기가
        # 동시에 보이는 모순을 없앤다. 입력이 끝나면 검증/로드 시점에 다시 표시.
        self._hide_loading_overlay()
        new_id = prompt_text(
            self,
            title="관리자 ID 입력",
            message=(
                "보자기카드 관리자 ID 를 입력하세요.\n"
            ),
            placeholder=""
        )
        if not new_id:
            if is_startup:
                self.destroy()   # 시작 시 취소 → 종료
            return               # 변경 시 취소 → 그대로 둠

        # 검증 동안 오버레이 표시 (변경 메뉴 경로는 아직 안 떠 있을 수 있음)
        self._show_loading_overlay("관리자 ID 확인 중...")

        def commit() -> None:
            license_input.save_admin_id(new_id)
            config.SITE_ADMIN_ID = new_id
            user_log.info("관리자 ID 저장 완료")
            # ID 가 바뀌면 계정이 달라지므로 비밀번호도 새로 입력받는다.
            license_input.clear_admin_pw()
            self._hide_loading_overlay()
            self._request_password(is_startup=True)

        def on_result(status: str, msg: str) -> None:
            if status == "valid":
                commit()
                return

            self._hide_loading_overlay()
            if status == "empty":
                proceed = messagebox.askyesno(
                    "주문을 찾지 못했습니다",
                    f"입력한 ID '{new_id}' 로 등록·수정 어디에서도 주문을 찾지 못했습니다.\n"
                    "ID 가 정확하다면 이대로 진행해도 됩니다 (목록이 비어 보일 수 있음).\n\n"
                    "[예] 이 ID로 계속    /    [아니오] 다시 입력",
                )
                if proceed:
                    self._show_loading_overlay("불러오는 중...")
                    commit()
                else:
                    self._request_admin_id(is_startup=is_startup)
            else:   # error
                show_error(self, "관리자 ID 오류", f"확인 실패: {msg}\n\n다시 입력해 주세요.")
                self._request_admin_id(is_startup=is_startup)

        self._validate_admin_id_async(new_id, on_result)

    # ──────────────────────────────────────────────────────────────────
    # UI 구성
    # ──────────────────────────────────────────────────────────────────
    def _build_widgets(self) -> None:
        # 0) 최상단 줄 — 새로고침 (가장 좌상단)
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=16, pady=(16, 4))
        self.refresh_button = ctk.CTkButton(
            top_frame, text="새로고침", width=90,
            command=lambda: self._start_browse(append=False),
            **_SECONDARY_BTN,
        )
        self.refresh_button.pack(side="left")

        # 1) 저장 폴더
        path_frame = ctk.CTkFrame(self)
        path_frame.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(path_frame, text="저장 폴더").pack(side="left", padx=(12, 8), pady=10)
        self.path_entry = ctk.CTkEntry(path_frame)
        self.path_entry.insert(0, config.DOWNLOAD_DIR)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=10)
        # 사용자가 직접 path 를 타이핑한 뒤 Enter 또는 포커스 이동 시 즉시 commit.
        # commit = config.DOWNLOAD_DIR 갱신 + 이미 받음 상태 재계산.
        self.path_entry.bind("<Return>", lambda _e: self._commit_path())
        self.path_entry.bind("<FocusOut>", lambda _e: self._commit_path())
        ctk.CTkButton(
            path_frame, text="폴더 선택", width=90, command=self._on_browse_folder,
            **_SECONDARY_BTN,
        ).pack(side="left", padx=(0, 6), pady=10)
        ctk.CTkButton(
            path_frame, text="폴더 열기", width=90, command=self._on_open_download_folder,
            **_SECONDARY_BTN,
        ).pack(side="left", padx=(0, 12), pady=10)

        # 2) 컨트롤 줄: 범례(빠른 처리) + 날짜 범위 일괄 선택
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=16, pady=(0, 4))

        # 범례 — pill (새로고침이 있던 좌측 끝 자리로 이동)
        ctk.CTkLabel(
            ctrl,
            text="빠른 처리",
            fg_color=("#FFF1ED", "#2D2422"),
            text_color=("#8C5A45", "#D9B098"),
            corner_radius=4,
            font=ctk.CTkFont(size=11),
        ).pack(side="left", ipadx=10, ipady=2)

        # 오른쪽: 필터 그룹 (날짜 범위 + 1차 액션)
        ctk.CTkButton(
            ctrl, text="선택 날짜 다운로드", width=130,
            command=self._on_download_in_date_range,
        ).pack(side="right")
        self.end_date_entry = ctk.CTkEntry(ctrl, width=70, placeholder_text="0607")
        self.end_date_entry.pack(side="right", padx=(0, 8))
        ctk.CTkLabel(ctrl, text="~").pack(side="right", padx=6)
        self.start_date_entry = ctk.CTkEntry(ctrl, width=70, placeholder_text="0531")
        self.start_date_entry.pack(side="right")
        ctk.CTkLabel(ctrl, text="기간(MMDD):").pack(side="right", padx=(0, 6))

        # 3) 주문 목록 테이블 (ttk.Treeview — 다중 선택, 컬럼, 색상 태그 모두 기본 지원)
        # 탭(등록/수정)을 이 카드 상단에 넣어 테이블과 한 덩어리처럼 보이게 한다.
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=16, pady=4)

        # 3-1) 카드 상단 탭 바 — 등록/수정 (오른쪽 정렬, 테이블 위에 얹힌 형태)
        tab_bar = ctk.CTkFrame(list_frame, fg_color="transparent")
        tab_bar.pack(fill="x", padx=8, pady=(8, 0))
        self.tab_segment = ctk.CTkSegmentedButton(
            tab_bar,
            values=["등록", "수정"],
            command=self._on_tab_change,
            selected_color=("#FFFFFF", "#2D2D30"),
            selected_hover_color=("#F5F5F7", "#36363A"),
            unselected_color=("#EBEBF0", "#1F1F22"),
            unselected_hover_color=("#E0E0E5", "#26262A"),
            text_color=("#1A1A1F", "#F2F2F7"),
            text_color_disabled=("#A0A0A8", "#5C5C62"),
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.tab_segment.set("등록")
        self.tab_segment.pack(side="right")

        tree_container = tk.Frame(list_frame, bg=container_bg(), highlightthickness=0, bd=0)
        tree_container.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        # 좌측 #0 컬럼에 체크박스 문자 (☐/☑) 표시.
        # 클릭하면 그 행이 토글됨 (_on_tree_click 핸들러).
        columns = ("order_date", "customer", "product", "status")
        self.tree = ttk.Treeview(
            tree_container, columns=columns, show="tree headings", selectmode="extended"
        )
        # 헤더 + 클릭 시 정렬. _on_header_click 이 정렬 + 화살표 갱신을 담당.
        for col, base_text in _HEADING_TEXT.items():
            self.tree.heading(
                col, text=base_text, command=lambda c=col: self._on_header_click(c)
            )

        self.tree.column("#0", width=36, anchor="center", stretch=False)
        self.tree.column("order_date", width=80, anchor="center", stretch=False)
        self.tree.column("customer", width=120, anchor="w", stretch=False)
        self.tree.column("product", width=440, anchor="w", stretch=True)
        self.tree.column("status", width=110, anchor="center", stretch=False)

        # ttk 스타일 + 행 태그 색을 customtkinter 테마와 통일
        apply_tree_style(self.tree)
        apply_tree_tags(self.tree)

        vsb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # 빈 목록 안내 — 주문이 0건일 때 표 가운데에 띄운다 (예: 수정 탭 0건).
        # 평소엔 숨김(place_forget). _update_empty_state 가 토글.
        self._empty_label = ctk.CTkLabel(
            tree_container,
            text="주문 목록이 없습니다.",
            text_color=("gray45", "gray60"),
            font=ctk.CTkFont(size=15),
        )

        # 클릭 = 그 행만 토글 (Gmail/Notion 스타일).
        # 선택 변경되면 체크박스 글자도 갱신 + 카운트 라벨 갱신.
        self.tree.bind("<Button-1>", self._on_tree_click)
        self.tree.bind("<<TreeviewSelect>>", lambda _e: (
            self._update_selection_label(),
            self._update_checkboxes(),
        ))

        # 4) 선택 카운트 + 액션 버튼
        action = ctk.CTkFrame(self, fg_color="transparent")
        action.pack(fill="x", padx=16, pady=(4, 4))
        # 좌측: 정보 + 보조 (선택 카운트, 전체선택/해제) — 부드러운 스타일
        self.selection_label = ctk.CTkLabel(action, text="선택 0건 / 전체 0건")
        self.selection_label.pack(side="left", padx=(4, 12))

        self.select_all_button = ctk.CTkButton(
            action, text="전체 선택", width=90, command=self._on_select_all,
            **_SECONDARY_BTN,
        )
        self.select_all_button.pack(side="left", padx=(0, 4))
        self.invert_button = ctk.CTkButton(
            action, text="선택 해제", width=90, command=self._on_clear_selection,
            **_SECONDARY_BTN,
        )
        self.invert_button.pack(side="left")

        # 대기열 표시 pill — 다운로드가 예약돼 기다리는 중일 때만 노출.
        # (있음 = '다운로드 대기 중', 없음 = 그냥 idle 로 명확히 구분)
        self.queue_label = ctk.CTkLabel(
            action, text="",
            fg_color=("#FFF1ED", "#2D2422"),
            text_color=("#8C5A45", "#D9B098"),
            corner_radius=6,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        # 처음엔 숨김 — _update_queue_indicator 가 필요할 때 pack.

        # 우측: 1차 액션 (다운로드/중지) — 인디고 강조, 시선이 우측 끝에 도달
        self.start_button = ctk.CTkButton(
            action, text="선택 항목 다운로드", width=160, command=self._on_start_download
        )
        self.start_button.pack(side="right")
        self.stop_button = ctk.CTkButton(
            action, text="중지", width=80, command=self._on_stop, state="disabled",
            **_SECONDARY_BTN,
        )
        self.stop_button.pack(side="right", padx=(0, 8))

        # 5) 진행률 + 상태
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=16, pady=6)
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=12, pady=(10, 4))
        self.status_label = ctk.CTkLabel(progress_frame, text="대기 중", anchor="w")
        self.status_label.pack(fill="x", padx=12, pady=(0, 10))

        # 6) 진행 로그
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=False, padx=16, pady=(4, 16))

        header = ctk.CTkFrame(log_frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(6, 0))
        ctk.CTkLabel(header, text="진행 상황", anchor="w").pack(side="left")
        ctk.CTkButton(
            header, text="로그 폴더 열기", width=110, height=24,
            command=self._on_open_log_folder,
            **_SECONDARY_BTN,
        ).pack(side="right")

        self.log_textbox = ctk.CTkTextbox(log_frame, wrap="none", height=140)
        self.log_textbox.pack(fill="both", expand=True, padx=12, pady=(4, 10))

        # 7) 푸터 — 프로그램 메타정보 (우측) + 관리자 ID 변경 링크 (좌측)
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkLabel(
            footer,
            text=f"{config.APP_NAME} v{config.APP_VERSION} · {config.APP_VENDOR}",
            text_color=("gray50", "gray60"),
            font=ctk.CTkFont(size=12),
        ).pack(side="right")
        change_id = ctk.CTkLabel(
            footer,
            text="관리자 ID 변경",
            text_color=("gray50", "gray60"),
            font=ctk.CTkFont(size=12, underline=True),
            cursor="hand2",
        )
        change_id.pack(side="left")
        change_id.bind("<Button-1>", lambda _e: self._on_change_admin_id())

        change_pw = ctk.CTkLabel(
            footer,
            text="비밀번호 변경",
            text_color=("gray50", "gray60"),
            font=ctk.CTkFont(size=12, underline=True),
            cursor="hand2",
        )
        change_pw.pack(side="left", padx=(16, 0))
        change_pw.bind("<Button-1>", lambda _e: self._on_change_password())

        # 8) 로딩 오버레이 — 화면 전체를 덮어 입력을 차단하고 "불러오는 중" 메시지를
        # 보여준다. 처음엔 숨김 (place 하지 않음). _show/_hide 로 토글.
        self._loading_overlay = ctk.CTkFrame(
            self, fg_color=("#EEF0F4", "#161618"), corner_radius=0
        )
        # 가운데 카드
        card = ctk.CTkFrame(
            self._loading_overlay, fg_color=("#FFFFFF", "#2A2A2E"), corner_radius=14
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        self._loading_title = ctk.CTkLabel(
            card, text="목록 불러오는 중...",
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        self._loading_title.pack(padx=48, pady=(30, 6))
        self._loading_msg = ctk.CTkLabel(
            card, text="잠시만 기다려 주세요",
            text_color=("gray40", "gray70"), font=ctk.CTkFont(size=12),
        )
        self._loading_msg.pack(padx=48, pady=(0, 18))
        self._loading_bar = ctk.CTkProgressBar(card, width=260, mode="indeterminate")
        self._loading_bar.pack(padx=48, pady=(0, 30))

    def _show_loading_overlay(self, title: str = "목록 불러오는 중...") -> None:
        """화면 전체를 덮는 로딩 오버레이를 띄우고 입력을 차단."""
        self._loading_title.configure(text=title)
        self._loading_msg.configure(text="잠시만 기다려 주세요")
        self._loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._loading_overlay.lift()      # 모든 위젯 위로
        self._loading_bar.start()
        # 오버레이가 덮긴 하지만 이중 안전장치로 탭 입력도 비활성화
        self.tab_segment.configure(state="disabled")

    def _hide_loading_overlay(self) -> None:
        """로딩 오버레이를 걷어내고 입력을 복구."""
        self._loading_bar.stop()
        self._loading_overlay.place_forget()
        self.tab_segment.configure(state="normal")

    def _set_loading_message(self, text: str) -> None:
        """오버레이가 떠 있을 때만 보조 메시지를 갱신."""
        if self._loading_overlay.winfo_ismapped():
            self._loading_msg.configure(text=text)

    def _on_change_admin_id(self) -> None:
        """푸터의 'ID 변경' 클릭 시. 재입력 받고 (백그라운드 검증) 성공 시 새로고침."""
        user_log.info("관리자 ID 변경 요청")
        self._request_admin_id(is_startup=False)

    def _on_change_password(self) -> None:
        """푸터의 '비밀번호 변경' 클릭 시. 새 비밀번호를 입력받아 저장 (마스킹)."""
        user_log.info("로그인 비밀번호 변경 요청")
        pw = prompt_text(
            self,
            title="로그인 비밀번호 변경",
            message="보자기카드 로그인 비밀번호를 입력하세요.",
            placeholder="비밀번호",
            show="●",
        )
        if pw:
            license_input.save_admin_pw(pw)
            user_log.info("로그인 비밀번호 저장 완료")
            show_info(self, "완료", "비밀번호가 저장되었습니다.")

    # ──────────────────────────────────────────────────────────────────
    # 동작
    # ──────────────────────────────────────────────────────────────────
    def _on_tab_change(self, value: str) -> None:
        """
        등록/수정 탭 전환.

        양 탭은 시작(새로고침) 시 이미 둘 다 로드되어 캐시에 들어있으므로,
        전환은 항상 캐시 복원만 한다 — 네트워크 호출도, 레이스도 없음.
        """
        new_step = (
            config.STEP_REGISTERED if value == "등록" else config.STEP_MODIFIED
        )
        if new_step == self._current_step:
            return
        self._current_step = new_step

        cached = self._tab_cache.get(new_step)
        if cached is not None:
            # 캐시에서 표시 (pop 아님 — 양쪽 캐시는 새로고침 전까지 계속 유지)
            self._restore_from_cache(cached)
            # 다운로드 진행 중이면 진행바·상태를 그대로 둬서 표시가 안 깨지게 한다.
            # (다운로드 중엔 worker.is_running() == True)
            if not self.worker.is_running():
                self.progress_bar.set(0)
                self.status_label.configure(text="대기 중")
            user_log.info(f"탭 전환: {value} — 캐시에서 {len(cached)}건 표시")
        else:
            # 정상 흐름에선 도달하지 않음 (로딩 중엔 오버레이가 입력을 막음).
            # 캐시가 비어있는 예외 상황이면 안전하게 전체 재로드.
            self._start_browse(append=False)

    def _restore_from_cache(self, cached_orders: Dict[str, Order]) -> None:
        """
        캐시된 Order 들로 트리 다시 채우기 (네트워크 호출 없음).

        화면(트리·선택·날짜)만 갱신하고 버튼/진행바/상태는 건드리지 않는다 —
        다운로드 진행 중에 탭을 전환해도 진행 표시가 깨지지 않도록. 진행바·버튼
        초기화는 호출부(all_loaded / _on_tab_change)가 상황에 맞게 처리.
        """
        self.tree.delete(*self.tree.get_children())
        self.orders.clear()
        # _append_orders 가 self.orders 에 추가 + 트리에 행 삽입
        self._append_orders(list(cached_orders.values()))
        self._update_selection_label()
        self._autofill_date_range()
        self._update_empty_state()

    def _update_empty_state(self) -> None:
        """주문이 0건이면 표 가운데에 '주문 목록이 없습니다.' 안내를 띄우고,
        1건 이상이면 숨긴다."""
        if self.tree.get_children():
            self._empty_label.place_forget()
        else:
            self._empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def _start_browse(self, append: bool = False) -> None:
        """
        등록·수정 양 탭을 모두 불러와 캐시에 채운 뒤 현재 탭을 표시한다.
        (시작·새로고침·ID 변경이 호출)

        로드가 끝날 때까지 화면 전체를 오버레이로 가려 입력을 차단하고
        "불러오는 중" 메시지를 보여준다 → 사용자는 확실히 대기 상태가 됨.
        끝나면 양쪽 캐시가 채워져 이후 탭 전환은 즉시 캐시 복원.
        """
        if self.worker.is_running():
            return
        self._tab_cache.clear()   # 양쪽 탭 캐시 무효화 (둘 다 새로 받음)
        self.tree.delete(*self.tree.get_children())
        self.orders.clear()
        self.refresh_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self._show_loading_overlay("목록 불러오는 중...")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        # 현재 탭을 먼저 받아 메시지가 자연스럽게 흐르도록 step 순서 구성.
        other_step = (
            config.STEP_MODIFIED
            if self._current_step == config.STEP_REGISTERED
            else config.STEP_REGISTERED
        )
        # MAX_PAGES 까지 시도 — OrdersLoader 가 빈 페이지에서 자동으로 exhausted 처리.
        self.worker.start_browse_all(
            n_pages=config.MAX_PAGES,
            steps=[self._current_step, other_step],
        )

    def _on_start_download(self) -> None:
        selected_ids = self.tree.selection()
        if not selected_ids:
            messagebox.showinfo("선택 없음", "다운로드할 항목을 먼저 선택해 주세요.")
            return
        selected_orders = [self.orders[row_id] for row_id in selected_ids if row_id in self.orders]
        if not selected_orders:
            return

        path = self.path_entry.get().strip()
        if not path:
            messagebox.showerror("입력 오류", "저장 폴더를 선택해 주세요")
            return

        label = "수정" if self._current_step == config.STEP_MODIFIED else "등록"
        # 선택 시점의 주문·경로를 스냅샷 (이후 탭 전환/선택 변경에 영향 안 받게)
        job = {"orders": selected_orders, "path": path, "label": label}

        if self.worker.is_running():
            # 이미 다운로드(또는 로드) 진행 중 → 대기열에 넣고 끝나면 자동 실행.
            self._download_queue.append(job)
            user_log.info(
                f"대기열 추가: [{label}] {len(selected_orders)}건 "
                f"— 현재 작업 후 진행 (대기 {len(self._download_queue)}건)"
            )
            self._update_queue_indicator()
            return

        # 새 사용자 액션으로 바로 시작하는 경우에만 로그 초기화.
        self.log_textbox.delete("1.0", "end")
        self._begin_download_job(job)

    def _begin_download_job(self, job: dict) -> None:
        """대기열의 한 작업(또는 즉시 시작 작업)을 실제로 시작한다."""
        config.DOWNLOAD_DIR = job["path"]
        self.status_label.configure(
            text=f"[{job['label']}] {len(job['orders'])}건 다운로드 준비 중..."
        )
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)

        self.refresh_button.configure(state="disabled")
        # start_button 은 활성 유지 — 진행 중에도 다음 작업을 대기열에 넣을 수 있게.
        self.stop_button.configure(state="normal")

        user_log.info(f"[{job['label']}] {len(job['orders'])}건 다운로드 시작")
        self.worker.start_download(job["orders"])

    def _update_queue_indicator(self) -> None:
        """대기열 pill 갱신 — 대기 작업이 있으면 표시, 없으면 숨김."""
        if self._download_queue:
            parts = [f"{j['label']} {len(j['orders'])}건" for j in self._download_queue]
            self.queue_label.configure(text="⏳ 대기열  " + "  ·  ".join(parts))
            if not self.queue_label.winfo_ismapped():
                self.queue_label.pack(side="left", padx=(16, 0), ipadx=10, ipady=2)
        else:
            self.queue_label.pack_forget()

    def _on_stop(self) -> None:
        config.cancel_event.set()
        if self._download_queue:
            n = len(self._download_queue)
            self._download_queue.clear()
            user_log.info(f"대기 중이던 {n}건도 함께 취소됨")
            self._update_queue_indicator()
        self.status_label.configure(text="중지하는 중...")

    def _commit_path(self) -> None:
        """
        path_entry 값을 config.DOWNLOAD_DIR 에 반영하고 화면의 모든 행에 대해
        '다운완료' 상태를 재계산한다. 경로가 안 바뀌었으면 no-op.
        """
        path = self.path_entry.get().strip()
        if not path:
            return
        if path == config.DOWNLOAD_DIR:
            return
        old = config.DOWNLOAD_DIR
        config.DOWNLOAD_DIR = path
        user_log.info(f"저장 폴더 변경: {old} → {path}")
        self._refresh_already_status()

    def _refresh_already_status(self) -> None:
        """현재 화면의 각 Order 에 대해 디스크 존재 + 사이즈를 다시 확인하고
        '다운완료' 태그 / 상태 컬럼을 갱신."""
        found_on_disk = 0
        changed = 0
        for row_id, order in self.orders.items():
            target_path = os.path.join(config.DOWNLOAD_DIR, order.zip_filename)
            exists = os.path.isfile(target_path)
            if exists:
                found_on_disk += 1
            new_already = (
                exists
                and os.path.getsize(target_path) >= config.MIN_VALID_FILE_BYTES
            )
            if new_already == order.already_downloaded:
                continue
            order.already_downloaded = new_already
            changed += 1
            if not self.tree.exists(row_id):
                continue

            # 합성 태그 단일 적용 (fast tint 유지)
            modifier = "already" if new_already else None
            tag = pick_row_tag(order.is_fast, modifier)
            self.tree.item(row_id, tags=[tag] if tag else [])

            # 상태 컬럼 갱신
            values = list(self.tree.item(row_id, "values"))
            if len(values) > _STATUS_COL_INDEX:
                values[_STATUS_COL_INDEX] = (
                    _STATUS_SKIP if new_already else _STATUS_PENDING
                )
                self.tree.item(row_id, values=values)

        user_log.info(
            f"폴더 재확인: 전체 {len(self.orders)}건 / 디스크에서 발견 {found_on_disk}건 / 상태 변경 {changed}건"
        )

    def _on_browse_folder(self) -> None:
        current = self.path_entry.get().strip()
        selected = filedialog.askdirectory(
            title="저장 폴더 선택", initialdir=current if current else "/"
        )
        if selected:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, selected)
            self._commit_path()

    def _on_select_all(self) -> None:
        self.tree.selection_set(self.tree.get_children())

    def _autofill_date_range(self) -> None:
        """
        현재 화면에 로드된 주문 중 가장 빠른 날짜·가장 늦은 날짜를 자동으로
        시작·끝 입력칸에 채운다. 새로고침마다 호출되어 현재 데이터 범위를 반영.
        사용자가 직접 수정한 값이 있어도 덮어씀 — 항상 "현재 가진 전체 범위" 가 기본.
        """
        if not self.orders:
            return
        dates = [o.order_date for o in self.orders.values() if o.order_date]
        if not dates:
            return
        min_d = min(dates)
        max_d = max(dates)
        self.start_date_entry.delete(0, "end")
        self.start_date_entry.insert(0, min_d)
        self.end_date_entry.delete(0, "end")
        self.end_date_entry.insert(0, max_d)

    def _on_download_in_date_range(self) -> None:
        """
        주문일이 [시작, 끝] MMDD 범위인 행만 선택하고 곧바로 다운로드.

        규칙:
          start <= end → 정상 범위
          start  > end → 연말 → 연초 wrap-around 만 허용 (start_month ≥ 11 AND end_month ≤ 2)
                         그 외 (예: 0531 ~ 0530, 0701 ~ 0601) 는 입력 오류로 처리
        기존 수동 체크는 모두 무시되고 날짜 범위로 덮어씌워짐.
        """
        start = self.start_date_entry.get().strip()
        end = self.end_date_entry.get().strip()
        if not (_is_valid_mmdd(start) and _is_valid_mmdd(end)):
            messagebox.showerror("입력 오류", "MMDD 4자리 숫자로 입력하세요 (예: 0531)")
            return

        if start <= end:
            in_range = lambda d: start <= d <= end
            range_desc = f"{start} ~ {end}"
        else:
            # start > end. 연말→연초 패턴만 wrap 로 인정.
            start_month = int(start[:2])
            end_month = int(end[:2])
            is_wrap = start_month >= 11 and end_month <= 2
            if not is_wrap:
                messagebox.showerror(
                    "입력 오류",
                    f"시작 날짜를 더 빠른 날짜로 입력하세요.\n\n"
                    "(연말-연초 범위는 시작이 11~12월, 끝이 1~2월일 때만 \n"
                    " 자동으로 해를 넘기는 것으로 처리합니다)",
                )
                return
            in_range = lambda d: d >= start or d <= end
            range_desc = f"{start} ~ 1231 + 0101 ~ {end} (연말-연초)"

        matching = [
            row_id for row_id, order in self.orders.items()
            if in_range(order.order_date)
        ]
        if not matching:
            messagebox.showinfo(
                "결과 없음",
                f"주문일 {range_desc} 범위에 해당하는 주문이 없습니다.",
            )
            return

        user_log.info(f"날짜 범위 {range_desc} 의 {len(matching)}건 선택 → 다운로드 시작")
        self.tree.selection_set(tuple(matching))
        self._on_start_download()

    def _on_clear_selection(self) -> None:
        self.tree.selection_remove(self.tree.selection())

    def _on_open_log_folder(self) -> None:
        """OS 별 파일 탐색기로 로그 폴더 열기. 없으면 미리 만들고 연다."""
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self._open_in_explorer(str(config.LOG_DIR))

    def _on_open_download_folder(self) -> None:
        """저장 폴더를 OS 파일 탐색기로 연다. 존재하지 않으면 안내."""
        # entry 값이 아직 commit 안 됐을 수 있으므로 먼저 동기화.
        self._commit_path()
        path = config.DOWNLOAD_DIR
        if not path or not os.path.isdir(path):
            messagebox.showerror(
                "폴더 열기 실패",
                f"폴더가 존재하지 않습니다:\n{path or '(빈 경로)'}",
            )
            return
        self._open_in_explorer(path)

    def _open_in_explorer(self, path: str) -> None:
        """OS 별 파일 탐색기 호출 공통 헬퍼."""
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as e:
            messagebox.showerror("폴더 열기 실패", f"{path}\n\n{e}")

    # ──────────────────────────────────────────────────────────────────
    # 이벤트 polling
    # ──────────────────────────────────────────────────────────────────
    def _poll_events(self) -> None:
        # 로그 큐
        while not self.log_handler.queue.empty():
            try:
                msg = self.log_handler.queue.get_nowait()
            except queue.Empty:
                break
            self.log_textbox.insert("end", msg + "\n")
            self.log_textbox.see("end")

        # 워커 이벤트 큐
        while not self.event_queue.empty():
            try:
                kind, kwargs = self.event_queue.get_nowait()
            except queue.Empty:
                break
            self._handle_worker_event(kind, kwargs)

        self.after(_POLL_INTERVAL_MS, self._poll_events)

    def _handle_worker_event(self, kind: str, kwargs: dict) -> None:
        if kind == "status":
            text = kwargs.get("text", "")
            self.status_label.configure(text=text)
            # 로딩 오버레이가 떠 있으면 그 메시지도 같이 갱신 (화면이 가려져 있으므로)
            self._set_loading_message(text)

        elif kind == "all_loaded":
            # 등록·수정 양 탭을 한 번에 받음 → 둘 다 캐시에 채우고 현재 탭만 표시.
            results: Dict[str, List[Order]] = kwargs.get("results", {})
            for step, orders in results.items():
                self._tab_cache[step] = {o.row_id: o for o in orders}

            self._ensure_determinate()
            self.progress_bar.set(0)
            self.status_label.configure(text="대기 중")
            self._restore_from_cache(self._tab_cache.get(self._current_step, {}))
            self._hide_loading_overlay()
            self.refresh_button.configure(state="normal")
            self.start_button.configure(state="normal")
            user_log.info(
                "전체 로드 완료 — "
                f"등록 {len(self._tab_cache.get(config.STEP_REGISTERED, {}))}건 / "
                f"수정 {len(self._tab_cache.get(config.STEP_MODIFIED, {}))}건"
            )

        elif kind == "progress":
            self._ensure_determinate()
            current = kwargs.get("current", 0)
            total = kwargs.get("total", 0)
            ratio = current / total if total else 0
            self.progress_bar.set(ratio)
            self.status_label.configure(
                text=f"{current} / {total} 진행 중" + (
                    " — " + kwargs.get("filename", "") if kwargs.get("filename") else ""
                )
            )

        elif kind == "item_progress":
            # 한 행의 byte 진행을 그 행 상태 컬럼에 퍼센트로 표시 (병렬·순차 공통).
            self._ensure_determinate()
            row_id = kwargs.get("row_id")
            done = kwargs.get("bytes_done", 0)
            total_bytes = kwargs.get("bytes_total", 0) or 0
            if row_id and self.tree.exists(row_id):
                if total_bytes:
                    pct = int(done * 100 / total_bytes)
                    status_text = f"받는 중 {pct}%"
                else:
                    status_text = f"받는 중 {format_memory(done)}"
                values = list(self.tree.item(row_id, "values"))
                if len(values) > _STATUS_COL_INDEX:
                    values[_STATUS_COL_INDEX] = status_text
                    self.tree.item(row_id, values=values)

        elif kind == "chunk":
            # 순차 모드 (N=1) 에서만 발사됨. 전체 진행률 바를 byte 단위로 부드럽게.
            self._ensure_determinate()
            file_index = kwargs.get("file_index", 1)
            total_files = kwargs.get("total_files", 1) or 1
            done = kwargs.get("bytes_done", 0)
            total_bytes = kwargs.get("bytes_total", 0) or 0
            filename = kwargs.get("filename", "")

            file_ratio = (done / total_bytes) if total_bytes else 0
            overall = ((file_index - 1) + file_ratio) / total_files
            self.progress_bar.set(min(overall, 1.0))

            if total_bytes:
                self.status_label.configure(
                    text=(
                        f"받는 중 ({file_index}/{total_files}) "
                        f"{format_memory(done)} / {format_memory(total_bytes)} — {filename}"
                    )
                )
            else:
                self.status_label.configure(
                    text=f"받는 중 ({file_index}/{total_files}) {format_memory(done)} — {filename}"
                )

        elif kind == "item_status":
            row_id = kwargs.get("row_id")
            status = kwargs.get("status", "")
            if row_id and self.tree.exists(row_id):
                values = list(self.tree.item(row_id, "values"))
                if len(values) > _STATUS_COL_INDEX:
                    values[_STATUS_COL_INDEX] = status
                    self.tree.item(row_id, values=values)
                # 상태에 따라 행 태그도 동기화 (fast tint 유지하면서)
                is_fast = self.orders[row_id].is_fast if row_id in self.orders else False
                if status == _STATUS_ERROR:
                    modifier = "error"
                elif status == _STATUS_SKIP:
                    modifier = "already"
                else:   # "받는 중" 등 진행 중 — 별도 색 modifier 없음
                    modifier = None
                tag = pick_row_tag(is_fast, modifier)
                self.tree.item(row_id, tags=[tag] if tag else [])

        elif kind == "item_done":
            row_id = kwargs.get("row_id")
            status = kwargs.get("status", _STATUS_DONE)
            if row_id and self.tree.exists(row_id):
                values = list(self.tree.item(row_id, "values"))
                if len(values) > _STATUS_COL_INDEX:
                    values[_STATUS_COL_INDEX] = status
                    self.tree.item(row_id, values=values)
                # 합성 태그 단일 적용 (fast tint 유지)
                is_fast = self.orders[row_id].is_fast if row_id in self.orders else False
                modifier = "already" if status == _STATUS_SKIP else "done"
                tag = pick_row_tag(is_fast, modifier)
                self.tree.item(row_id, tags=[tag] if tag else [])
                if row_id in self.orders:
                    self.orders[row_id].already_downloaded = True

        elif kind == "done":
            self._ensure_determinate()
            self.progress_bar.set(1.0)
            self.status_label.configure(text=kwargs.get("message", "완료"))

        elif kind == "error":
            # 로딩 중 오류면 오버레이에 갇히지 않도록 먼저 걷어냄
            self._hide_loading_overlay()
            self._ensure_determinate()
            self.progress_bar.set(0)
            self.status_label.configure(text="오류가 발생했습니다")
            self.refresh_button.configure(state="normal")
            self.start_button.configure(state="normal")
            messagebox.showerror(
                "오류",
                f"{kwargs.get('message', '알 수 없는 오류')}\n\n자세한 내용은 진행 기록을 확인하세요.",
            )

        elif kind == "finished":
            self._ensure_determinate()
            # 다운로드가 끝났고 대기열이 남아 있으면 다음 작업을 자동 시작.
            if kwargs.get("mode") == "download" and self._download_queue:
                nxt = self._download_queue.pop(0)
                user_log.info(
                    f"대기열 다음 작업 시작: [{nxt['label']}] {len(nxt['orders'])}건 "
                    f"(남은 대기 {len(self._download_queue)}건)"
                )
                self._update_queue_indicator()
                self._begin_download_job(nxt)
                return
            self.refresh_button.configure(state="normal")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def _append_orders(self, orders: List[Order]) -> None:
        for order in orders:
            row_id = order.row_id
            if row_id in self.orders:
                continue  # 중복 표시 방지
            self.orders[row_id] = order

            modifier = "already" if order.already_downloaded else None
            tag = pick_row_tag(order.is_fast, modifier)
            tags = [tag] if tag else []

            status = _STATUS_SKIP if order.already_downloaded else _STATUS_PENDING

            self.tree.insert(
                "",
                "end",
                iid=row_id,
                text=_CHECK_OFF,              # 좌측 체크박스 초기 미선택
                values=(order.order_date, order.customer_name, order.product_type, status),
                tags=tags,
            )

    def _update_selection_label(self) -> None:
        total = len(self.tree.get_children())
        selected = len(self.tree.selection())
        self.selection_label.configure(text=f"선택 {selected}건 / 전체 {total}건")

    def _update_checkboxes(self) -> None:
        """현재 selection 상태를 #0 컬럼의 ☐/☑ 글자에 반영."""
        selected = set(self.tree.selection())
        for row_id in self.tree.get_children():
            mark = _CHECK_ON if row_id in selected else _CHECK_OFF
            if self.tree.item(row_id, "text") != mark:
                self.tree.item(row_id, text=mark)

    def _on_header_click(self, col: str) -> None:
        """헤더 클릭 → 그 컬럼 기준 정렬. 같은 컬럼 다시 클릭하면 역순."""
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False

        # 각 행의 정렬 키 추출. #0 은 tree text, 나머지는 values 의 해당 컬럼.
        def sort_key(row_id):
            val = self.tree.set(row_id, col) if col != "#0" else self.tree.item(row_id, "text")
            # 숫자 가능하면 숫자로 (주문일 0531 같은 거)
            try:
                return (0, float(val))
            except (ValueError, TypeError):
                return (1, str(val))

        rows = sorted(self.tree.get_children(""), key=sort_key, reverse=self._sort_reverse)
        for index, row_id in enumerate(rows):
            self.tree.move(row_id, "", index)

        # 헤더 텍스트 갱신 — 정렬된 컬럼에만 화살표
        arrow = " ▼" if self._sort_reverse else " ▲"
        for c, base in _HEADING_TEXT.items():
            self.tree.heading(c, text=(base + arrow) if c == col else base)

    def _on_tree_click(self, event) -> str | None:
        """
        - 일반 클릭         : 그 행 하나만 토글 + 앵커 갱신
        - Shift+클릭        : 앵커 ~ 클릭한 행까지 범위 추가 선택 (Gmail/Finder 스타일)
        - 빈 공간 클릭      : 무시
        """
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return None

        shift_pressed = bool(event.state & 0x0001)
        current = set(self.tree.selection())

        if shift_pressed and self._click_anchor is not None:
            # 앵커와 클릭한 행 사이 모든 행을 선택 목록에 추가
            all_rows = list(self.tree.get_children())
            try:
                i_anchor = all_rows.index(self._click_anchor)
                i_target = all_rows.index(row_id)
            except ValueError:
                # 앵커가 더 이상 트리에 없음 (새로고침 등) → 단일 토글로 처리
                shift_pressed = False
            else:
                lo, hi = sorted([i_anchor, i_target])
                current.update(all_rows[lo:hi + 1])

        if not shift_pressed:
            if row_id in current:
                current.discard(row_id)
            else:
                current.add(row_id)
            self._click_anchor = row_id   # plain-click 때만 앵커 갱신

        self.tree.selection_set(tuple(current))
        return "break"   # Treeview 의 기본 클릭 동작 (단일 선택) 차단

    def _ensure_determinate(self) -> None:
        if str(self.progress_bar.cget("mode")) == "indeterminate":
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")


def _is_valid_mmdd(s: str) -> bool:
    """MMDD 형식 검증 (4자리 숫자, 월·일 범위 체크)."""
    if len(s) != 4 or not s.isdigit():
        return False
    mm, dd = int(s[:2]), int(s[2:])
    return 1 <= mm <= 12 and 1 <= dd <= 31


def launch() -> None:
    app = BojagiDownloaderApp()
    app.mainloop()
