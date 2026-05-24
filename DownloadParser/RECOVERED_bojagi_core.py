# 보자기카드 다운로드 프로그램 — 핵심 함수 복원
# 출처: 0519 0519.exe (PyInstaller + Python 3.10, 2023-05-08 빌드)
# 추출 도구: pyinstxtractor → pycdc + pycdas (Python 3.10 디스어셈블 기반 복원)
#
# 이 파일은 원본 소스 100% 동일 보장은 아니며, 바이트코드에서 복원한 의사 소스입니다.
# 변수명/함수명/문자열 상수는 디스어셈블에서 그대로 추출되어 정확합니다.

import re
import sys
import os
import logging
import logging.handlers
import shutil
from time import sleep
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from requests import get
from urllib3 import PoolManager

# ──────────────────────────────────────────────────────────────────────────────
# 전역 설정 (원본 그대로)
# ──────────────────────────────────────────────────────────────────────────────
BaseURL = ('http://bojagicard.com/join/mov_list.php'
           '?page=1&SITE_ADMIN_ID=ntccomm&step=1&&dates=&datee=&id='
           '&list_mode=&keyword=&Search_mode=&Search_text=&category='
           '&color=&style=&stylegroup=&list_type=&mode=')

downloadServerAddress = 'Z:\\partner_bojagi'
diskLabel = 'Z:\\'
STARTDATE = '0000'
ENDDATE = '0000'
targetContents = []

myDict = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB', 5: 'PB', 6: 'EB', 7: 'ZB'}

formatter = logging.Formatter('%(asctime)s - [%(funcName)s] - %(levelname)s - %(message)s')
logger = logging.getLogger('JW-LOG')
logger.setLevel(logging.DEBUG)
time_handler = logging.handlers.TimedRotatingFileHandler(
    filename='Time Rotate Log.log', when='D', backupCount=10)
time_handler.setFormatter(formatter)
logger.addHandler(time_handler)
logger.propagate = False


# ──────────────────────────────────────────────────────────────────────────────
# 핵심 함수 (장애 발생 지점)
# ──────────────────────────────────────────────────────────────────────────────

def searchPage(singlePageURL):
    """검색 페이지를 순회하며 고객 목록을 수집. 최대 100페이지."""
    logger.info('executed')
    limit = 0
    sPage = singlePageURL
    while limit < 100:
        numbers = re.sub('[^0-9]', '', singlePageURL)
        logger.info('Searching Page : %s' % numbers[0])    # ← 로그가 여기서 멈춤
        limit += 1

        # ★ 장애 의심 지점 ① — urlopen이 응답을 못 받고 hang 가능
        with urllib.request.urlopen(sPage) as response:
            html = response.read().decode('cp949')         # ★ ② cp949 디코딩 강제
            soup = BeautifulSoup(html, 'html.parser')

        myCustomers = getCustomerLists(soup)
        if myCustomers == -1:
            return 555                                      # ★ ③ 빈 결과면 즉시 종료

        result = searchValidCustomers(myCustomers)
        if result == 999:
            return 1
        sPage = getNextPage(sPage)
    return -1


def getCustomerLists(soup):
    """BeautifulSoup으로 고객 행을 추출. CSS 셀렉터 의존."""
    logger.info('executed')
    customers = soup.select('table.tbl1 > tr.td7')         # ★ ④ 셀렉터 깨지면 빈 리스트
    if len(customers) == 0:
        logger.info('[%s] No customer data exists' %
                    sys._getframe().f_code.co_name)
        return -1
    return customers


def getNextPage(singlePageURL):
    logger.info('executed')
    number = re.sub('[^0-9]', '', singlePageURL)
    newPageNumber = str(int(number[0]) + 1)
    newPageURL = singlePageURL.replace('page=' + number[0], 'page=' + newPageNumber)
    return newPageURL


# ──────────────────────────────────────────────────────────────────────────────
# 메인/예외 래퍼
# ──────────────────────────────────────────────────────────────────────────────

def main():
    # sys.executable 파일명에서 STARTDATE/ENDDATE 파싱 (예: "0519 0519.exe")
    global STARTDATE, ENDDATE
    STARTDATE, ENDDATE = os.path.basename(sys.executable).split('.')[0].split(' ')

    checkDateNormality()
    isValidAddress()

    total, used, free = shutil.disk_usage(diskLabel)
    logger.info('total mem : %s' % memoryFormatting(total))
    logger.info('free mem : %s' % memoryFormatting(free))
    logger.info('executed')

    searchPage(BaseURL)
    # ... 이후 다운로드 루프 (download 함수 호출)


def Run_CatchException():
    try:
        main()
    except Exception as exc:
        print('critical error occured, program will shutdown')
        print(exc)
        logger.info('CHECK SHUTDOWN REASON : ' + str(exc))   # ★ ⑤ 이 로그도 없음 → 예외 미발생 강력 시사
        os.system('pause')
        sys.exit()
    print('Program ended successfully.')
    sys.exit()


# 기타 함수: memoryFormatting, checkDateNormality, isValidAddress,
#           getType, getName, getDday, getZipName, getOrderDate,
#           getTextLink, getFullLink, addToDownloadList,
#           searchValidCustomers, download, PrintProgressBar
# — 전체 디스어셈블은 /tmp/exe-decompile/bojagi_disasm.txt 참조
