"""
보조 유틸리티 함수.
"""

import os

from . import config


def format_memory(num_bytes: int) -> str:
    """
    바이트 수를 사람이 읽기 좋은 단위(KB/MB/GB...)로 변환.
    1000 단위로 나누며 소수점 3자리까지 표시.
    예: 1_500_000 → "1.5 MB"
    """
    unit = 0
    temp = num_bytes
    while temp >= 1000:
        unit += 1
        temp = temp / 1000
    return str(round(temp, 3)) + " " + config.MEMORY_UNITS[unit]


def print_progress_bar(step_count: int, percent_text: str) -> None:
    """
    cmd 창의 제목 표시줄에 진행 바를 그린다 (Windows).
    step_count 는 0~10 사이 (각 1칸이 10% 진행).
    """
    bar = "["
    for _ in range(0, step_count):
        bar += "##"
    for _ in range(0, 10 - step_count):
        bar += "~~"
    bar += "], {0}%".format(percent_text)
    os.system("title " + bar)
