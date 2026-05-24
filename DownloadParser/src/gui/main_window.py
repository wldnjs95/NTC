"""
보자기카드 다운로드 프로그램의 메인 윈도우.

레이아웃 (위 → 아래):
    [날짜 입력]     검색 기간을 MMDD 형식으로 두 칸 입력
    [저장 경로]     기본값 config.DOWNLOAD_DIR + "찾아보기" 폴더 선택
    [시작 / 중지 버튼]
    [진행률 바 + 상태 라벨]
    [실시간 로그 텍스트박스]
"""

import logging
import os
import queue
import subprocess
import sys
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

import customtkinter as ctk

from .. import config
from ..log_setup import user_log
from .log_bridge import QueueLogHandler
from .worker import DownloadWorker


_GUI_LOG_FORMAT = "%(asctime)s  %(message)s"
_POLL_INTERVAL_MS = 100


class BojagiDownloaderApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("보자기카드 자료 일괄 다운로드")
        self.geometry("760x600")
        self.minsize(640, 480)

        # 워커 ↔ GUI 사이 이벤트 큐 (("status"|"progress"|"done"|"error"|"finished", kwargs))
        self.event_queue: queue.Queue = queue.Queue()
        self.worker = DownloadWorker(self.event_queue)

        # 사용자용 로그(user_log) 만 GUI 진행 상황 박스로 흘려보낸다.
        # 개발자용 상세 로그(logger) 는 파일에만 쌓이고 GUI 에는 표시되지 않음.
        self.log_handler = QueueLogHandler()
        self.log_handler.setFormatter(logging.Formatter(_GUI_LOG_FORMAT, datefmt="%H:%M:%S"))
        user_log.addHandler(self.log_handler)

        self._build_widgets()
        self._poll_events()

    # ──────────────────────────────────────────────────────────────────
    # UI 구성
    # ──────────────────────────────────────────────────────────────────
    def _build_widgets(self) -> None:
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # 1) 날짜 입력
        date_frame = ctk.CTkFrame(self)
        date_frame.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(date_frame, text="검색 기간 (MMDD)").pack(
            side="left", padx=(12, 8), pady=12
        )
        self.start_entry = ctk.CTkEntry(date_frame, width=80, placeholder_text="")
        self.start_entry.pack(side="left", pady=12)
        ctk.CTkLabel(date_frame, text="~").pack(side="left", padx=8, pady=12)
        self.end_entry = ctk.CTkEntry(date_frame, width=80, placeholder_text="")
        self.end_entry.pack(side="left", pady=12)
        ctk.CTkLabel(
            date_frame,
            text="(예: 0519 ~ 0526)",
            text_color=("gray50", "gray60"),
        ).pack(side="left", padx=(12, 0), pady=12)

        # 2) 저장 폴더 (기본 = config.DOWNLOAD_DIR, "폴더 선택" 으로 변경 가능)
        path_frame = ctk.CTkFrame(self)
        path_frame.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(path_frame, text="저장 폴더").pack(
            side="left", padx=(12, 8), pady=10
        )
        self.path_entry = ctk.CTkEntry(path_frame)
        self.path_entry.insert(0, config.DOWNLOAD_DIR)
        self.path_entry.pack(
            side="left", fill="x", expand=True, padx=(0, 8), pady=10
        )
        ctk.CTkButton(
            path_frame, text="폴더 선택", width=90, command=self._on_browse
        ).pack(side="left", padx=(0, 12), pady=10)

        # 3) 시작 / 중지 버튼
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=16, pady=8)
        self.start_button = ctk.CTkButton(
            button_frame, text="다운로드 시작", width=140, command=self._on_start
        )
        self.start_button.pack(side="left", padx=(0, 8))
        self.stop_button = ctk.CTkButton(
            button_frame, text="중지", width=120, command=self._on_stop, state="disabled"
        )
        self.stop_button.pack(side="left")

        # 4) 진행률 + 상태
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=16, pady=8)
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=12, pady=(12, 4))
        self.status_label = ctk.CTkLabel(progress_frame, text="대기 중", anchor="w")
        self.status_label.pack(fill="x", padx=12, pady=(0, 12))

        # 5) 진행 상황 박스 + 헤더에 "로그 폴더 열기" 버튼
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        header = ctk.CTkFrame(log_frame, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 0))
        ctk.CTkLabel(header, text="진행 상황", anchor="w").pack(side="left")
        ctk.CTkButton(
            header,
            text="로그 폴더 열기",
            width=110,
            height=24,
            command=self._on_open_log_folder,
        ).pack(side="right")

        self.log_textbox = ctk.CTkTextbox(log_frame, wrap="none")
        self.log_textbox.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    # ──────────────────────────────────────────────────────────────────
    # 버튼 핸들러
    # ──────────────────────────────────────────────────────────────────
    def _on_start(self) -> None:
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        path = self.path_entry.get().strip()

        if not (_is_mmdd(start) and _is_mmdd(end)):
            messagebox.showerror("입력 오류", "날짜는 MMDD 4자리 숫자여야 합니다 (예: 0519)")
            return
        if start > end:
            messagebox.showerror("입력 오류", "시작 날짜는 끝 날짜보다 빨라야 합니다")
            return
        if not path:
            messagebox.showerror("입력 오류", "저장 폴더를 선택해 주세요")
            return

        # 이번 실행 동안 사용할 저장 경로를 config 에 반영
        config.DOWNLOAD_DIR = path

        self.log_textbox.delete("1.0", "end")
        self.status_label.configure(text="검색 준비 중...")

        # 검색 단계는 총량을 모르므로 indeterminate 애니메이션.
        # 다운로드가 시작되면 (첫 progress 이벤트 도착 시) determinate 로 전환됨.
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        self.worker.start(start, end)

    def _on_stop(self) -> None:
        config.cancel_event.set()
        self.status_label.configure(text="중지하는 중...")

    def _on_open_log_folder(self) -> None:
        """OS별 파일 탐색기로 로그 폴더 열기. 없으면 미리 만들고 연다."""
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = str(config.LOG_DIR)
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path], check=False)
            else:
                subprocess.run(["xdg-open", path], check=False)
        except Exception as e:
            messagebox.showerror("폴더 열기 실패", f"{path}\n\n{e}")

    def _on_browse(self) -> None:
        """폴더 선택 dialog. 취소하면 기존 값 유지."""
        current = self.path_entry.get().strip()
        selected = filedialog.askdirectory(
            title="저장 폴더 선택",
            initialdir=current if current else "/",
        )
        if selected:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, selected)

    # ──────────────────────────────────────────────────────────────────
    # 이벤트 큐 polling (GUI 메인 스레드에서 주기적으로 실행)
    # ──────────────────────────────────────────────────────────────────
    def _poll_events(self) -> None:
        # 로그 큐 비우기
        while not self.log_handler.queue.empty():
            try:
                msg = self.log_handler.queue.get_nowait()
            except queue.Empty:
                break
            self.log_textbox.insert("end", msg + "\n")
            self.log_textbox.see("end")

        # 워커 이벤트 큐 비우기
        while not self.event_queue.empty():
            try:
                kind, kwargs = self.event_queue.get_nowait()
            except queue.Empty:
                break
            self._handle_worker_event(kind, kwargs)

        self.after(_POLL_INTERVAL_MS, self._poll_events)

    def _handle_worker_event(self, kind: str, kwargs: dict) -> None:
        if kind == "status":
            self.status_label.configure(text=kwargs.get("text", ""))
        elif kind == "progress":
            # 첫 progress 이벤트 = 다운로드 단계 시작. indeterminate → determinate 전환.
            current, total = kwargs.get("current", 0), kwargs.get("total", 0)
            self._ensure_determinate()
            ratio = current / total if total else 0
            self.progress_bar.set(ratio)
            self.status_label.configure(text=f"{current} / {total} 진행 중")
        elif kind == "done":
            self._ensure_determinate()
            self.progress_bar.set(1.0)
            self.status_label.configure(text=kwargs.get("message", "완료"))
        elif kind == "error":
            self._ensure_determinate()
            self.progress_bar.set(0)
            self.status_label.configure(text="오류가 발생했습니다")
            messagebox.showerror(
                "다운로드 오류",
                f"{kwargs.get('message', '알 수 없는 오류')}\n\n"
                f"자세한 내용은 아래 진행 기록을 확인하세요.",
            )
        elif kind == "finished":
            # 워커 스레드가 어떤 이유로든 끝난 직후 호출. 버튼 상태 복귀.
            self._ensure_determinate()
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def _ensure_determinate(self) -> None:
        """indeterminate 애니메이션을 멈추고 일반 진행률 모드로 전환. 멱등."""
        if str(self.progress_bar.cget("mode")) == "indeterminate":
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")


def _is_mmdd(s: str) -> bool:
    return len(s) == 4 and s.isdigit() and 1 <= int(s[:2]) <= 12 and 1 <= int(s[2:]) <= 31


def launch() -> None:
    app = BojagiDownloaderApp()
    app.mainloop()
