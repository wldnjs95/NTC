"""
보자기카드 자료 일괄 다운로드 프로그램 진입점.

기본은 GUI 모드.
콘솔 모드(레거시)로 돌리려면:  python run.py --console
"""

import sys


def _is_console_mode() -> bool:
    return "--console" in sys.argv


if __name__ == "__main__":
    if _is_console_mode():
        from src.app import run_console
        run_console()
    else:
        from src.gui.main_window import launch
        launch()
