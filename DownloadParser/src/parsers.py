"""
한 명의 고객(`<tr class="td7">` BeautifulSoup 객체)에서 필요한 필드를 뽑아내는 함수들.

검색 페이지의 각 행 구조 (보자기카드 HTML 기준):
- 첫 번째 <span>            : 고객 이름
- 두 번째 <span>            : 상품 타입 (예: '식전영상', 'BGM변경전용 식전영상' 등)
- 6번째에서 마지막인 <td>   : 주문일 (yyyy-mm-dd 형식)
- 2번째에서 마지막인 <td>   : 결혼식 D-day (예: "2026-06-20 D-32")
- target="_blank" 링크 중 2번째 : 본문 페이지 URL (여기서 진짜 다운로드 링크가 나옴)
- 클래스에 'fast' 가 있으면 빠른 처리 상품
"""

import re

import requests
from bs4 import BeautifulSoup

from . import config
from .log_setup import logger


def get_product_type(single_customer) -> str:
    """
    상품 타입: target=_blank 인 첫 <a> 의 텍스트 (상품 상세 페이지 링크).
    등록 탭 / 수정 탭 모두 동일 구조.
    """
    a = single_customer.find("a", {"target": "_blank"})
    return a.text.strip() if a else ""


def get_customer_name(single_customer) -> str:
    """
    고객명: onclick 에 'windowcopen' 이 들어간 <a> 의 텍스트.
    수정 탭에는 앞에 '▶수정내역' 토글이 끼어 들어가서 span 인덱스 기반은 깨짐.
    onclick=windowcopen 은 양쪽 탭 모두 고객 정보 팝업 링크라서 안정적.
    """
    for a in single_customer.find_all("a"):
        if "windowcopen" in (a.get("onclick") or ""):
            return a.text.strip()
    # fallback (등록 탭 옛 동작)
    return single_customer.span.text


def get_dday(single_customer) -> str:
    """
    뒤에서 두 번째 <td>의 텍스트에서 결혼식 일자와 D-day 숫자를 합쳐 반환.
    예) td.text = "2026-06-20 D-32" → "06-20-32" 형태 (숫자만 뽑음)
    """
    date_text = single_customer.select("td")[-2].text.split(" ")[-2].strip()
    numbers = re.findall(r"\d+", date_text)
    return numbers[1] + numbers[2]


def get_order_date(single_customer) -> str:
    """뒤에서 6번째 <td> = 주문일. 'YYYY-MM-DD' → 'YYYYMMDD'."""
    logger.info("executed")
    return single_customer.select("td")[-6].text.strip().replace("-", "")


def make_zip_filename(single_customer) -> str:
    """
    저장될 zip 파일 이름을 만든다.
    형식: "{주문일}_{D-day} {이름} {상품타입}{빠른여부}"
    예)   "0414_0425 장형구 세로전용 식전영상 (빠른)"
    """
    fastname = ""
    if "fast" in str(single_customer):
        fastname = " (빠른)"

    return "{0}_{1} {2} {3}{4}".format(
        get_order_date(single_customer),
        get_dday(single_customer),
        get_customer_name(single_customer),
        get_product_type(single_customer),
        fastname,
    )


def get_text_page_link(single_customer) -> str:
    """
    target="_blank" 인 <a> 태그 중 2번째 → 본문 페이지 링크.
    이 페이지를 다시 받아야 실제 zip 직링크가 나온다.
    """
    logger.info("executed")
    anchors = single_customer.find_all("a", {"target": "_blank"})
    return anchors[1]["href"]


def get_zip_full_link(http_text_link: str) -> str:
    """
    본문 페이지를 가져와 <script> 태그 안의 자바스크립트 문자열에서
    실제 zip 다운로드 경로를 뽑아내고, 호스트를 붙여 반환한다.

    원본 페이지의 <script>:
        ...; var url = '/upload/202604/mv1776165132.zip?hash=...'; ...
    → "http://gwl2.bojagicard.com/upload/202604/mv1776165132.zip?hash=..."
    """
    logger.info("executed")
    response = requests.get(http_text_link, timeout=config.HTTP_TIMEOUT)
    html = response.text
    text_soup = BeautifulSoup(html, "html.parser")

    # <script>...</script> 안의 텍스트를 ';' 로 자른 3번째 조각, 그걸 "'"로 자른 2번째 조각이 경로
    up_link = text_soup.find("script").text.split(";")[2].split("'")[1]
    return config.FILE_HOST + up_link


def extract_order_metadata(single_customer, step: str = "1") -> dict:
    """
    한 행에서 zip 직링크를 제외한 모든 메타데이터를 추출.

    step="2" (수정 탭) 이면 파일명 뒤(확장자 앞)에 " (수정)" 접미사가 붙어
    등록 탭의 같은 고객 zip 과 같은 폴더에서도 안 섞임.
    예) "0414_0425 장형구 식전영상 (수정).zip"

    zip 직링크(get_zip_full_link) 는 상세 페이지를 한 번 더 받아야 해서 비싸다.
    목록 화면에서는 필요 없으므로 다운로드 시점까지 미룬다.
    """
    is_fast = "fast" in str(single_customer)
    text_link = get_text_page_link(single_customer)
    text_link = text_link.replace("https", "http")

    suffix = " (수정)" if step == "2" else ""
    zip_filename = make_zip_filename(single_customer) + suffix + ".zip"

    return {
        "order_date": get_order_date(single_customer),
        "customer_name": get_customer_name(single_customer),
        "product_type": get_product_type(single_customer),
        "d_day": get_dday(single_customer),
        "is_fast": is_fast,
        "text_page_link": text_link,
        "zip_filename": zip_filename,
    }
