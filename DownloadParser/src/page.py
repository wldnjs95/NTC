"""
페이지 단위 크롤링.

흐름:
    search_page(URL)
       └── 한 페이지의 HTML을 받아 BeautifulSoup 으로 파싱
       └── get_customer_rows() : <tr class="td7"> 를 뽑아 고객 리스트 반환
       └── filter_customers_in_range() : 주문일이 STARTDATE~ENDDATE 안에 드는 고객만 다운로드 큐에 추가
       └── 종료 조건을 만나기 전까지 next_page_url() 로 다음 페이지로 이동
"""

import re
import urllib.request

from bs4 import BeautifulSoup

from . import config
from .log_setup import logger
from .parsers import get_order_date
from .downloader import add_to_download_list


# search_page 반환 코드
NO_CUSTOMERS_ON_PAGE = 555    # 그 페이지에 행이 0개 → 더 진행할 의미 없음
RANGE_EXHAUSTED = 1           # 검색 기간보다 이전 주문이 나옴 → 더 갈 필요 없음
NO_MORE_PAGES = -1            # MAX_PAGES 한도까지 다 돔
CANCELLED = -99               # GUI 에서 사용자가 중지 버튼 누름


def get_customer_rows(soup):
    """
    파싱된 HTML에서 고객 행을 뽑는다.
    셀렉터 `table.tbl1 > tr.td7` 는 보자기카드 영상주문 목록 페이지의 표 구조.
    """
    logger.info("executed")
    customers = soup.select("table.tbl1 > tr.td7")
    if len(customers) == 0:
        logger.info("[%s] No customer data exists" % "get_customer_rows")
        return -1
    return customers


def next_page_url(page_url: str) -> str:
    """URL 의 page=N 부분에서 N을 +1 한 새 URL 을 만든다."""
    logger.info("executed")
    numbers = re.sub(r"[^0-9]", "", page_url)
    new_page_number = str(int(numbers[0]) + 1)
    return page_url.replace("page=" + numbers[0], "page=" + new_page_number)


def filter_customers_in_range(customers) -> int:
    """
    검색된 고객 중 주문일(orderDate)이 STARTDATE ~ ENDDATE 범위인 고객만 다운로드 큐에 추가.

    한 페이지를 다 돌고 나서, 마지막 행이 STARTDATE 보다 이전이고 'fast' 태그가 아니면
    더 이상 뒤 페이지를 볼 필요 없으므로 RANGE_EXHAUSTED (999) 를 반환.
    """
    logger.info("executed")

    for single_customer in customers:
        fast = 0
        class_attr = single_customer["class"]
        if "fast" in class_attr:
            fast = 1

        order_date = get_order_date(single_customer)
        logger.info("start, end : " + config.STARTDATE + " " + config.ENDDATE)
        logger.info("orderDate : " + order_date)

        if config.STARTDATE <= order_date <= config.ENDDATE:
            add_to_download_list(single_customer)
            continue

        if order_date < config.STARTDATE:
            # 이미 검색 범위보다 과거 → 'fast' 처리 상품이 아니라면 여기서 끊는다.
            if fast == 0:
                return 999
            # fast 상품은 주문일이 더 빠를 수 있으니 계속 본다.
            continue

    return 0


def search_page(single_page_url: str) -> int:
    """페이지를 1번부터 차례로 가져오며 고객을 필터링하여 다운로드 큐에 모은다."""
    logger.info("executed")

    limit = 0
    s_page = single_page_url

    while limit < config.MAX_PAGES:
        if config.cancel_event.is_set():
            return CANCELLED
        numbers = re.sub(r"[^0-9]", "", single_page_url)
        logger.info("Searching Page : %s" % numbers[0])
        limit += 1

        # 서버 응답 받기. timeout 으로 무한 대기 방지.
        with urllib.request.urlopen(s_page, timeout=config.HTTP_TIMEOUT) as response:
            html = response.read().decode(config.RESPONSE_ENCODING)
            soup = BeautifulSoup(html, "html.parser")

        customers = get_customer_rows(soup)
        if customers == -1:
            return NO_CUSTOMERS_ON_PAGE

        if filter_customers_in_range(customers) == 999:
            return RANGE_EXHAUSTED

        s_page = next_page_url(s_page)

    return NO_MORE_PAGES
