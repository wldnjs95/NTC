"""
ttk.Treeview 와 ttk.Scrollbar 를 customtkinter 테마와 매칭되는 모던한 모습으로 스타일링.

customtkinter 가 자기 위젯만 테마 적용해 주므로, ttk 기반 위젯(Treeview/Scrollbar) 은
별도로 ttk.Style 로 색·폰트·간격을 맞춰줘야 함.
"""

from __future__ import annotations

import sys
from tkinter import ttk

import customtkinter as ctk


# theme.json 의 색을 그대로 가져와 ttk 에도 적용.
# 두 값짜리 튜플은 (light, dark) 순서.
_PALETTE = {
    "bg_window":     ("#F7F7F8", "#161617"),
    "bg_panel":      ("#FFFFFF", "#1F1F22"),
    "bg_panel_alt":  ("#FAFAFC", "#26262A"),
    "border":        ("#E5E5EA", "#2D2D30"),
    "border_strong": ("#D5D5DC", "#36363A"),
    "text":          ("#1A1A1F", "#F2F2F7"),
    "text_muted":    ("#6E6E76", "#98989D"),
    "accent":        ("#5B6CFF", "#5B6CFF"),
    "accent_text":   ("#FFFFFF", "#FFFFFF"),
    # 선택된 행 배경. 액센트의 옅은 tint — 버튼과 시각적으로 구분됨.
    "row_selected":  ("#E5EAFF", "#2E335A"),
    "row_alt":       ("#F7F7F8", "#1A1A1C"),
    "row_hover":     ("#EEF0FF", "#2A2D40"),
}


# 행 태그 색. apply_tree_tags() 가 현재 appearance mode 에 맞게 ttk 에 등록.
#
# 핵심: 행에 적용할 태그는 항상 "한 개" 만. 합성 태그 (fast_already 등) 를
# 미리 등록해 두고 행 상태에 따라 알맞은 단일 태그를 골라 적용한다.
# 이유: ttk.Treeview 에 여러 태그를 적용하면 나중에 configure 된 태그의
# 빈 background='' 가 앞 태그의 background tint 를 덮어씌우는 버그성 동작이
# 있어, 다운로드 후 fast tint 가 사라지는 증상이 발생함.
_FAST_BG = ("#FFF1ED", "#2D2422")
_ALREADY_FG = ("#9A9A9F", "#7A7A82")
_DONE_FG = ("#1F7A3A", "#5BCC7E")
_ERROR_FG = ("#B23A3A", "#FF7A7A")

TAG_COLORS = {
    "fast":          {"background": _FAST_BG,  "foreground": (None, None)},
    "already":       {"background": (None, None), "foreground": _ALREADY_FG},
    "done":          {"background": (None, None), "foreground": _DONE_FG},
    "error":         {"background": (None, None), "foreground": _ERROR_FG},
    "fast_already":  {"background": _FAST_BG,  "foreground": _ALREADY_FG},
    "fast_done":     {"background": _FAST_BG,  "foreground": _DONE_FG},
    "fast_error":    {"background": _FAST_BG,  "foreground": _ERROR_FG},
}


def pick_row_tag(is_fast: bool, modifier: str | None) -> str:
    """
    행에 적용할 단일 태그 결정.

    modifier: None (대기 또는 받는 중) | "already" | "done" | "error"
    is_fast: 빠른 처리 행이면 True
    """
    if modifier and is_fast:
        return f"fast_{modifier}"
    if modifier:
        return modifier
    if is_fast:
        return "fast"
    return ""   # 빈 문자열 = 태그 없음 (기본 스타일)


def _platform_font_family() -> str:
    """주문 목록 표(ttk.Treeview)용 폰트.

    번들된 Noto Sans KR (구글 폰트). main_window 에서 _load_bundled_font() 로
    이미 프로세스에 로드돼 있어 시스템 설치 없이도 사용 가능. 만약 로드 실패면
    Tk 가 알아서 기본 폰트로 대체한다.
    """
    return "Noto Sans KR"


def _pick(pair: tuple) -> str:
    """현재 appearance mode 에 맞는 색 선택 (Light 면 [0], Dark 면 [1])."""
    return pair[1] if ctk.get_appearance_mode() == "Dark" else pair[0]


def apply_tree_style(tree: ttk.Treeview) -> None:
    """
    ttk.Treeview 스타일을 customtkinter 테마와 통일.
    한 번 호출하면 같은 프로세스의 모든 Treeview 에 영향.
    """
    style = ttk.Style()

    # 'clam' 테마가 가장 커스터마이즈 잘 됨. 'aqua'(macOS) 는 색 무시되는 속성이 많음.
    if "clam" in style.theme_names():
        style.theme_use("clam")

    font_family = _platform_font_family()

    style.configure(
        "Treeview",
        background=_pick(_PALETTE["bg_panel"]),
        fieldbackground=_pick(_PALETTE["bg_panel"]),
        foreground=_pick(_PALETTE["text"]),
        rowheight=30,
        borderwidth=0,
        relief="flat",
        font=(font_family, 12),
    )

    style.configure(
        "Treeview.Heading",
        background=_pick(_PALETTE["bg_panel_alt"]),
        foreground=_pick(_PALETTE["text_muted"]),
        font=(font_family, 11, "bold"),
        relief="flat",
        borderwidth=0,
        padding=(8, 8),
    )

    # 선택된 행: 액센트의 옅은 tint 배경, 글자색은 기본 그대로.
    # (강한 인디고 배경 + 흰 글자는 버튼 색과 겹쳐 시각적으로 시끄러우므로 회피)
    style.map(
        "Treeview",
        background=[("selected", _pick(_PALETTE["row_selected"]))],
        foreground=[("selected", _pick(_PALETTE["text"]))],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", _pick(_PALETTE["border"]))],
    )

    # 스크롤바도 같이
    style.configure(
        "Vertical.TScrollbar",
        background=_pick(_PALETTE["bg_panel"]),
        troughcolor=_pick(_PALETTE["bg_panel"]),
        bordercolor=_pick(_PALETTE["bg_panel"]),
        arrowcolor=_pick(_PALETTE["text_muted"]),
    )


def apply_tree_tags(tree: ttk.Treeview) -> None:
    """현재 appearance mode 에 맞춰 행 태그 색을 적용 (이미 추가된 항목에도 즉시 반영)."""
    for tag, colors in TAG_COLORS.items():
        kwargs = {}
        bg = colors["background"]
        fg = colors["foreground"]
        if bg[0] is not None:
            kwargs["background"] = _pick(bg)
        if fg[0] is not None:
            kwargs["foreground"] = _pick(fg)
        tree.tag_configure(tag, **kwargs)


def container_bg() -> str:
    """tree 를 감싸는 tk.Frame 의 배경. ttk 와 색 매칭."""
    return _pick(_PALETTE["bg_panel"])
