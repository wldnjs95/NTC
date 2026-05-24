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
    """두 번째 <span>의 텍스트 = 상품 타입."""
    return single_customer.select("span")[1].text


def get_customer_name(single_customer) -> str:
    """첫 번째 <span>의 텍스트 = 고객명."""
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
