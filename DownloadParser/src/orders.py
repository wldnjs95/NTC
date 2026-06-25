"""
주문 목록 로딩.

기존 흐름:
    날짜 입력 → search_page() 가 페이지를 돌며 STARTDATE~ENDDATE 안의 것만 큐(target_contents)에 채움
    → main() 이 큐를 순회하며 zip 직링크까지 한 번에 받아 다운로드.

새 흐름 (GUI 목록 기반):
    OrdersLoader.load_next(n_pages) 로 메타데이터만 가져온다.
    zip 직링크는 비싸므로(상세 페이지 1회 추가 요청) 다운로드 시점에만 가져온다.

쓰임:
    loader = OrdersLoader()
    new_orders = loader.load_next(n_pages=2)   # 페이지 1~2
    more = loader.load_next(n_pages=2)         # 페이지 3~4
"""

from __future__ import annotations

import os
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable, List

from bs4 import BeautifulSoup

from . import config
from .log_setup import logger
from .parsers import extract_order_metadata


# 한 batch 에 동시 fetch 할 페이지 수.
# 서버가 페이지당 4~5초 응답이라 순차로는 너무 느림.
# 5개 동시 → 한 batch 가 4~5초로 줄어듦.
PARALLEL_FETCH = 5


@dataclass
class Order:
    """다운로드 후보 한 건. zip_url 은 다운로드 시점에 채워짐."""
    order_date: str          # "0519" (MMDD)
    customer_name: str       # "김XX"
    product_type: str        # "세로전용 식전영상"
    d_day: str               # "MMDD" 결혼식 날짜 + D-day 합쳐진 코드 (zip 파일명용)
    is_fast: bool
    text_page_link: str      # 상세 페이지 URL (zip 직링크는 여기서 다시 받음)
    zip_filename: str        # 최종 저장 파일명 (...zip)

    # 수정 탭 전용
    order_num: str = ""              # 행의 data-order_num (수정요청 이미지 조회용)
    is_revision: bool = False        # 수정 탭(step=2) 주문 여부

    # 런타임 상태
    already_downloaded: bool = False   # 로드 시점 디스크 확인 결과
    zip_url: str = ""                  # 다운로드 시점에 채워짐

    @property
    def row_id(self) -> str:
        """Treeview 행 식별자. zip_filename 이 유일."""
        return self.zip_filename


class OrdersLoader:
    """페이지 단위 진행 상태를 갖는 주문 로더. '더 불러오기' 가 가능하도록 다음 페이지를 기억한다."""

    def __init__(self) -> None:
        self._next_page: int = 1
        self._exhausted: bool = False
        self._step: str = config.STEP_REGISTERED

    @property
    def exhausted(self) -> bool:
        return self._exhausted

    @property
    def next_page(self) -> int:
        return self._next_page

    @property
    def step(self) -> str:
        return self._step

    def reset(self) -> None:
        self._next_page = 1
        self._exhausted = False

    def set_step(self, step: str) -> None:
        """탭 변경. 다른 탭으로 이동 시 자동 reset 해서 처음부터 다시 로드."""
        if step != self._step:
            self._step = step
            self.reset()

    def load_next(
        self,
        n_pages: int = PARALLEL_FETCH,
        on_progress: Callable[[int], None] = lambda _i: None,
    ) -> List[Order]:
        """
        병렬 batch 로 페이지를 로드.

        PARALLEL_FETCH(=5) 개씩 동시에 fetch 하고, 페이지 순서대로 결과 합침.
        n_pages 만큼 받거나 / 빈 페이지를 만나거나 / MAX_PAGES 도달까지 반복.
        빈 페이지 발견 시 같은 batch 의 그 이후 페이지 결과는 폐기.
        """
        collected: List[Order] = []
        if self._exhausted:
            return collected

        remaining = n_pages
        while remaining > 0 and not self._exhausted:
            if config.cancel_event.is_set():
                break

            # 이번 batch 의 페이지 번호 목록
            batch_size = min(PARALLEL_FETCH, remaining)
            batch: List[int] = []
            for i in range(batch_size):
                p = self._next_page + i
                if p > config.MAX_PAGES:
                    break
                batch.append(p)
            if not batch:
                self._exhausted = True
                break

            # 병렬 fetch (페이지 번호 → 결과)
            results: dict[int, List[Order] | None] = {}
            with ThreadPoolExecutor(max_workers=len(batch)) as ex:
                future_to_page = {ex.submit(self._load_one_page, p): p for p in batch}
                for future in as_completed(future_to_page):
                    p = future_to_page[future]
                    try:
                        results[p] = future.result()
                    except Exception as exc:
                        logger.warning("page %d fetch failed: %s" % (p, exc))
                        results[p] = None
                    on_progress(p)

            # 페이지 순서대로 정리. 빈 페이지 만나면 같은 batch 의 그 이후도 폐기.
            empty_found = False
            for p in batch:
                orders = results.get(p)
                if orders is None:
                    self._exhausted = True
                    empty_found = True
                    break
                collected.extend(orders)
                self._next_page = p + 1

            if empty_found:
                break

            remaining -= len(batch)

        return collected

    def _load_one_page(self, page_number: int) -> List[Order] | None:
        """페이지 한 장 로드. 행이 없으면 None."""
        url = _build_page_url(page_number, self._step)
        logger.info("loading orders page=%d url=%s" % (page_number, url))

        with urllib.request.urlopen(url, timeout=config.HTTP_TIMEOUT) as response:
            html = response.read().decode(config.RESPONSE_ENCODING)

        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("table.tbl1 > tr.td7")
        if not rows:
            logger.info("page %d has no customer rows" % page_number)
            return None

        orders: List[Order] = []
        for row in rows:
            try:
                meta = extract_order_metadata(row, step=self._step)
            except Exception as exc:
                logger.warning("extract failed on a row: %s" % exc)
                continue

            zip_filename = meta["zip_filename"]
            is_revision = (self._step == config.STEP_MODIFIED)

            if is_revision:
                # 수정 탭: zip 이 아니라 '수정요청 이미지' 들을 폴더에 저장한다.
                # 폴더명 = zip_filename 에서 .zip 제거. 폴더에 파일이 있으면 '이미 받음'.
                folder = os.path.join(config.DOWNLOAD_DIR, zip_filename[:-4])
                already = os.path.isdir(folder) and any(os.scandir(folder)) \
                    if os.path.isdir(folder) else False
            else:
                target_path = os.path.join(config.DOWNLOAD_DIR, zip_filename)
                # 단순히 존재만 보지 않고 최소 사이즈도 충족해야 '이미 받음' 으로 인정.
                # 부분 다운로드 / 손상된 파일은 '대기' 로 두어 다시 받게 함.
                already = (
                    os.path.isfile(target_path)
                    and os.path.getsize(target_path) >= config.MIN_VALID_FILE_BYTES
                )

            orders.append(
                Order(
                    order_date=meta["order_date"],
                    customer_name=meta["customer_name"],
                    product_type=meta["product_type"],
                    d_day=meta["d_day"],
                    is_fast=meta["is_fast"],
                    text_page_link=meta["text_page_link"],
                    zip_filename=zip_filename,
                    order_num=meta.get("order_num", ""),
                    is_revision=is_revision,
                    already_downloaded=already,
                )
            )

        return orders


def _build_page_url(page_number: int, step: str = config.STEP_REGISTERED) -> str:
    """현재 SITE_ADMIN_ID 가 적용된 URL 에서 page=, step= 치환."""
    url = config.base_url()
    url = re.sub(r"page=\d+", f"page={page_number}", url)
    url = re.sub(r"step=\d+", f"step={step}", url)
    return url
