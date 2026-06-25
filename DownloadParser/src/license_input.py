"""
관리자 ID (SITE_ADMIN_ID) 입력·저장·로드 모듈.

EXE 안에는 관리자 ID 를 박지 않고, 첫 실행 시 사용자에게 입력받아 로컬에
저장. 다른 PC 로 EXE 복사해도 ID 없으니 동작 안 함.

저장 위치:
    %LOCALAPPDATA%\\NTC\\BojagiDownloader\\admin_id.bin

Windows: DPAPI (CryptProtectData) 로 PC 단위 암호화. 그 PC 의 Windows
계정만 복호화 가능 → 파일을 다른 PC 로 복사해도 풀 수 없음.
macOS/Linux 개발 환경: 평문 저장 (현실적으로 fallback).
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from typing import Optional

from . import config


_VALIDATION_TIMEOUT = 10   # 초


# ──────────────────────────────────────────────────────────────────────
# 저장 / 로드 (DPAPI 또는 평문)
# ──────────────────────────────────────────────────────────────────────

def _encrypt(plain: str) -> bytes:
    if sys.platform == "win32":
        try:
            import win32crypt   # type: ignore
            return win32crypt.CryptProtectData(
                plain.encode("utf-8"),
                "BojagiAdminID",   # description
                None, None, None, 0,
            )
        except ImportError:
            pass   # pywin32 없으면 평문 fallback
    return plain.encode("utf-8")


def _decrypt(data: bytes) -> str:
    if sys.platform == "win32":
        try:
            import win32crypt   # type: ignore
            _, decrypted = win32crypt.CryptUnprotectData(
                data, None, None, None, 0
            )
            return decrypted.decode("utf-8")
        except ImportError:
            pass
    return data.decode("utf-8")


def load_admin_id() -> Optional[str]:
    """저장된 관리자 ID 를 읽어옴. 없거나 손상되면 None."""
    p = config.LICENSE_FILE
    if not p.exists():
        return None
    try:
        raw = p.read_bytes()
        return _decrypt(raw)
    except Exception:
        return None


def save_admin_id(admin_id: str) -> None:
    """관리자 ID 를 PC 단위 암호화해 저장."""
    config.LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    encrypted = _encrypt(admin_id)
    config.LICENSE_FILE.write_bytes(encrypted)


def clear_admin_id() -> None:
    """저장된 ID 삭제. ID 변경 시 호출."""
    if config.LICENSE_FILE.exists():
        config.LICENSE_FILE.unlink()


# ──────────────────────────────────────────────────────────────────────
# 로그인 비밀번호 (수정요청 이미지 조회용) — admin_id 와 동일하게 PC 단위 암호화
# ──────────────────────────────────────────────────────────────────────

def load_admin_pw() -> Optional[str]:
    """저장된 로그인 비밀번호를 읽어옴. 없거나 손상되면 None."""
    p = config.ADMIN_PW_FILE
    if not p.exists():
        return None
    try:
        return _decrypt(p.read_bytes())
    except Exception:
        return None


def save_admin_pw(pw: str) -> None:
    """로그인 비밀번호를 PC 단위 암호화해 저장."""
    config.ADMIN_PW_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.ADMIN_PW_FILE.write_bytes(_encrypt(pw))


def clear_admin_pw() -> None:
    """저장된 비밀번호 삭제."""
    if config.ADMIN_PW_FILE.exists():
        config.ADMIN_PW_FILE.unlink()


# ──────────────────────────────────────────────────────────────────────
# 유효성 검증
# ──────────────────────────────────────────────────────────────────────

def _count_account_orders(html: str) -> int:
    """
    페이지 상단 요약(모바일웨딩영상 / 식전영상 / 식중감사영상 / 빠른제작)의
    'N 건' 숫자를 모두 합산해 계정 전체 주문 규모를 가늠한다.

    틀린 ID 는 같은 빈 껍데기를 받아 전부 0 → 합계 0.
    한 건이라도 있으면 합계 > 0 (등록 탭이 비어 있고 수정/다른 카테고리에만
    있어도 잡힘). '주문 0건인 정상 계정' 과 '틀린 ID' 는 서버 응답이
    동일해 여기서도 구분되지 않으므로, 그 경우는 호출부에서 사용자에게 확인한다.
    """
    from bs4 import BeautifulSoup
    text = re.sub(r"\s+", " ", BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
    m = re.search(r"모바일웨딩영상.*?일반영상\s*[\d,]+\s*건", text)
    if not m:
        return 0
    nums = re.findall(r"([\d,]+)\s*건", m.group(0))
    return sum(int(n.replace(",", "")) for n in nums)


def validate_admin_id(admin_id: str) -> tuple[str, str]:
    """
    관리자 ID 가 실제 보자기카드 서버에서 유효한지 확인.

    서버는 틀린 ID 에도 정상 ID 와 동일한 빈 페이지(title='영상주문 관리',
    tbl1 존재, 행 0건)를 돌려주므로 둘을 100% 구분할 수 없다. 그래서 상단
    요약의 전체 주문 합계로 판단하고, 합계가 0 이면 '애매' 로 돌려 호출부가
    사용자에게 확인하도록 한다.

    반환: (status, message)
        status="valid" : 합계 1 건 이상 → 통과
        status="empty" : 합계 0 건 → 틀린 ID 이거나 진짜 빈 계정 (확인 필요)
        status="error" : 입력 형식 오류 / 네트워크 오류 / 페이지 마커 없음
    """
    if not admin_id or not admin_id.isalnum():
        return "error", "ID 가 비어있거나 영숫자가 아닙니다"

    url = (
        "http://bojagicard.com/join/mov_list.php"
        f"?page=1&SITE_ADMIN_ID={urllib.parse.quote(admin_id)}&step=1"
        "&&dates=&datee=&id=&list_mode=&keyword=&Search_mode="
        "&Search_text=&category=&color=&style=&stylegroup=&list_type=&mode="
    )
    try:
        with urllib.request.urlopen(url, timeout=_VALIDATION_TIMEOUT) as r:
            html = r.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return "error", f"네트워크 오류: {exc}"

    if "영상주문" not in html or "tbl1" not in html:
        return "error", "서버 응답에 주문 페이지 마커가 없습니다"

    total = _count_account_orders(html)
    if total > 0:
        return "valid", f"정상 (계정 전체 주문 {total:,}건 확인)"
    return "empty", "등록·수정 어디에서도 주문을 찾지 못했습니다"
