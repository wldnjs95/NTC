"""
수정요청(시안) 이미지 다운로드.

배경:
    수정 탭의 "수정내역" 에 고객이 올린 '수정요청 이미지' 는 **로그인해야만** 보인다.
    (SITE_ADMIN_ID 파라미터만으로는 목록은 보이지만 수정요청 이미지는 빈 응답)
    기존 코드는 로그인 없이 직링크로 접근해 '작업 원본' zip 을 받아왔는데, 수정 탭에서는
    그게 아니라 이 모듈로 로그인 → 수정요청 이미지를 받아야 한다.

흐름:
    sess = make_logged_in_session()                  # 1) 로그인 (1회)
    urls = fetch_revision_image_urls(sess, order_num)# 2) 수정요청 이미지 URL 목록
    download_images(sess, urls, folder, ...)         # 3) 이미지 저장
"""

import os
from typing import Callable, List, Optional

import requests
from bs4 import BeautifulSoup

from . import config
from . import license_input
from .log_setup import logger, user_log


_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def make_logged_in_session() -> requests.Session:
    """
    저장된 관리자 ID + 비밀번호로 로그인한 requests.Session 을 반환.
    실패 시 RuntimeError.
    """
    admin_id = config.SITE_ADMIN_ID or (license_input.load_admin_id() or "")
    pw = license_input.load_admin_pw()
    if not admin_id:
        raise RuntimeError("관리자 ID 가 없습니다")
    if not pw:
        raise RuntimeError("로그인 비밀번호가 저장돼 있지 않습니다 (비밀번호 변경에서 입력하세요)")

    s = requests.Session()
    s.headers.update({"User-Agent": _UA})
    s.post(
        config.LOGIN_URL,
        data={"id": admin_id, "pwd": pw},
        headers={"Referer": config.LOGIN_PAGE},
        timeout=config.HTTP_TIMEOUT,
    )
    # 로그인 성공 판정: 'logon' 쿠키가 생기면 성공.
    if "logon" not in s.cookies.get_dict():
        raise RuntimeError("로그인 실패 — 관리자 ID/비밀번호를 확인하세요")
    logger.info("logged in as %s", admin_id)
    return s


def fetch_revision_image_urls(session: requests.Session, order_num: str) -> List[str]:
    """한 주문(order_num)의 수정요청 이미지 URL 목록을 반환 (로그인 세션 필요)."""
    if not order_num:
        return []
    url = f"{config.SIAN_LIST_URL}?order_num={order_num}&category="
    r = session.get(
        url,
        headers={"X-Requested-With": "XMLHttpRequest", "Referer": config.base_url()},
        timeout=config.HTTP_TIMEOUT,
    )
    html = r.content.decode("utf-8", "replace")
    soup = BeautifulSoup(html, "html.parser")

    urls: List[str] = []
    for im in soup.find_all("img"):
        src = (im.get("src") or "").strip()
        if not src:
            continue
        if src.startswith("//"):
            src = "http:" + src
        elif src.startswith("/"):
            src = config.IMAGE_HOST + src
        elif not src.startswith("http"):
            src = config.IMAGE_HOST + "/" + src.lstrip("/")
        urls.append(src)
    logger.info("order %s revision images: %d", order_num, len(urls))
    return urls


def download_images(
    session: requests.Session,
    urls: List[str],
    folder: str,
    on_each: Optional[Callable[[int, int, str], None]] = None,
) -> int:
    """
    이미지들을 folder 에 저장. 파일명은 URL 의 마지막 경로 조각.
    on_each(현재, 전체, 파일명) 콜백으로 진행 상황을 알린다.
    저장한 파일 수 반환.
    """
    os.makedirs(folder, exist_ok=True)
    saved = 0
    n = len(urls)
    for i, u in enumerate(urls, start=1):
        if config.cancel_event.is_set():
            break
        fname = u.split("/")[-1].split("?")[0] or f"image_{i}.jpg"
        if on_each:
            on_each(i, n, fname)
        try:
            r = session.get(u, timeout=config.HTTP_TIMEOUT)
            r.raise_for_status()
            with open(os.path.join(folder, fname), "wb") as f:
                f.write(r.content)
            saved += 1
        except Exception as exc:
            user_log.error(f"이미지 받기 실패: {fname} → {exc}")
            logger.warning("image download failed %s: %s", u, exc)
    return saved
