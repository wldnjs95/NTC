"""
커스텀 모달 다이얼로그.

tkinter.messagebox 는 OS 시스템 다이얼로그라 내부 아이콘을 바꿀 수 없다.
이 모듈은 CTkToplevel 기반의 자체 다이얼로그로, 아이콘 영역에
src/gui/assets/ntc_logo.png 를 직접 표시한다.

쓰임:
    from .dialogs import show_error, show_info
    show_error(self, "입력 오류", "MMDD 형식으로 입력하세요")
"""

from __future__ import annotations

import os
import tkinter as tk
import warnings

import customtkinter as ctk


_ICON_PATH = os.path.join(os.path.dirname(__file__), "assets", "ntc_logo.png")
_ICON_SUBSAMPLE = 4   # 원본 256x256 → 64x64

# CTkLabel + tk.PhotoImage 사용 시 HiDPI 경고가 뜨므로 그 메시지만 차단.
warnings.filterwarnings(
    "ignore",
    message=r"CTkLabel Warning: Given image is not CTkImage.*",
    category=UserWarning,
)

# tk.PhotoImage 는 Tk 초기화 후에만 만들 수 있어 lazy 로드.
_icon_cache: "tk.PhotoImage | None" = None
_icon_loaded = False


def _load_icon() -> "tk.PhotoImage | None":
    global _icon_cache, _icon_loaded
    if _icon_loaded:
        return _icon_cache
    _icon_loaded = True
    try:
        img = tk.PhotoImage(file=_ICON_PATH)
        if _ICON_SUBSAMPLE > 1:
            img = img.subsample(_ICON_SUBSAMPLE, _ICON_SUBSAMPLE)
        _icon_cache = img
    except tk.TclError:
        _icon_cache = None
    return _icon_cache


def show_error(parent, title: str, message: str) -> None:
    """파이썬 아이콘 없는 커스텀 에러 모달."""
    _show_dialog(parent, title, message)


def show_info(parent, title: str, message: str) -> None:
    """info 도 같은 디자인 사용."""
    _show_dialog(parent, title, message)


def prompt_text(
    parent,
    title: str,
    message: str,
    placeholder: str = "",
    initial: str = "",
) -> str | None:
    """
    텍스트 입력 모달. 확인 시 입력 문자열 반환, 취소/X 시 None 반환.
    Enter = 확인, Escape = 취소.
    """
    icon = _load_icon()
    result: dict = {"value": None}

    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.transient(parent)

    body = ctk.CTkFrame(dialog, fg_color="transparent")
    body.pack(padx=24, pady=(24, 8), fill="both", expand=True)

    if icon is not None:
        ctk.CTkLabel(body, image=icon, text="").pack(side="left", padx=(0, 16))

    right = ctk.CTkFrame(body, fg_color="transparent")
    right.pack(side="left", fill="both", expand=True)

    ctk.CTkLabel(
        right, text=message, justify="left", anchor="nw", wraplength=360,
    ).pack(fill="x", pady=(0, 10))

    entry = ctk.CTkEntry(right, width=320, placeholder_text=placeholder)
    if initial:
        entry.insert(0, initial)
    entry.pack(fill="x")
    entry.focus_set()

    btns = ctk.CTkFrame(dialog, fg_color="transparent")
    btns.pack(pady=(0, 18))

    def _ok():
        result["value"] = entry.get().strip()
        dialog.destroy()

    def _cancel():
        result["value"] = None
        dialog.destroy()

    ctk.CTkButton(btns, text="취소", width=80, command=_cancel,
                  fg_color="transparent", border_width=1,
                  border_color=("#D5D5DC", "#3A3A3F"),
                  text_color=("#1A1A1F", "#F2F2F7"),
                  hover_color=("#F0F0F5", "#26262A")).pack(side="left", padx=(0, 8))
    ctk.CTkButton(btns, text="확인", width=80, command=_ok).pack(side="left")

    dialog.update_idletasks()
    pw, ph = parent.winfo_width(), parent.winfo_height()
    px, py = parent.winfo_x(), parent.winfo_y()
    dw, dh = dialog.winfo_width(), dialog.winfo_height()
    dialog.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

    dialog.bind("<Return>", lambda _e: _ok())
    dialog.bind("<Escape>", lambda _e: _cancel())
    dialog.grab_set()
    parent.wait_window(dialog)
    return result["value"]


def _show_dialog(parent, title: str, message: str) -> None:
    icon = _load_icon()

    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.resizable(False, False)
    dialog.transient(parent)

    body = ctk.CTkFrame(dialog, fg_color="transparent")
    body.pack(padx=24, pady=(24, 12), fill="both", expand=True)

    if icon is not None:
        ctk.CTkLabel(body, image=icon, text="").pack(side="left", padx=(0, 16))

    ctk.CTkLabel(
        body, text=message, justify="left", anchor="nw", wraplength=360
    ).pack(side="left", fill="both", expand=True)

    btn = ctk.CTkButton(dialog, text="확인", width=80, command=dialog.destroy)
    btn.pack(pady=(0, 18))
    btn.focus_set()

    # 부모 윈도우 중앙으로 배치 — 위치 계산 위해 update_idletasks 로 크기 확정
    dialog.update_idletasks()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    px = parent.winfo_x()
    py = parent.winfo_y()
    dw = dialog.winfo_width()
    dh = dialog.winfo_height()
    dialog.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")

    dialog.bind("<Return>", lambda _e: dialog.destroy())
    dialog.bind("<Escape>", lambda _e: dialog.destroy())
    dialog.grab_set()
    parent.wait_window(dialog)
