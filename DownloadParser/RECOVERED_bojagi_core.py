# Bojagi Card download program — recovered core functions
# Source: 0519 0519.exe (PyInstaller + Python 3.10, built 2023-05-08)
# Extraction tools: pyinstxtractor -> pycdc + pycdas (recovered from Python 3.10 disassembly)
#
# This file is not guaranteed to be 100% identical to the original source;
# it is pseudo-source recovered from bytecode.
# Variable names, function names, and string constants are extracted directly
# from the disassembly and are accurate.

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
# Global settings (as in the original)
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
# Core functions (failure points)
# ──────────────────────────────────────────────────────────────────────────────

def searchPage(singlePageURL):
    """Iterate through search pages and collect the customer list. Max 100 pages."""
    logger.info('executed')
    limit = 0
    sPage = singlePageURL
    while limit < 100:
        numbers = re.sub('[^0-9]', '', singlePageURL)
        logger.info('Searching Page : %s' % numbers[0])    # <- logging stops here
        limit += 1

        # ★ Suspected failure point #1 — urlopen may hang waiting for a response
        with urllib.request.urlopen(sPage) as response:
            html = response.read().decode('cp949')         # ★ #2 forced cp949 decoding
            soup = BeautifulSoup(html, 'html.parser')

        myCustomers = getCustomerLists(soup)
        if myCustomers == -1:
            return 555                                      # ★ #3 exit immediately on empty result

        result = searchValidCustomers(myCustomers)
        if result == 999:
            return 1
        sPage = getNextPage(sPage)
    return -1


def getCustomerLists(soup):
    """Extract customer rows with BeautifulSoup. Depends on the CSS selector."""
    logger.info('executed')
    customers = soup.select('table.tbl1 > tr.td7')         # ★ #4 returns empty list if the selector breaks
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
# Main / exception wrapper
# ──────────────────────────────────────────────────────────────────────────────

def main():
    # Parse STARTDATE / ENDDATE from the sys.executable filename (e.g. "0519 0519.exe")
    global STARTDATE, ENDDATE
    STARTDATE, ENDDATE = os.path.basename(sys.executable).split('.')[0].split(' ')

    checkDateNormality()
    isValidAddress()

    total, used, free = shutil.disk_usage(diskLabel)
    logger.info('total mem : %s' % memoryFormatting(total))
    logger.info('free mem : %s' % memoryFormatting(free))
    logger.info('executed')

    searchPage(BaseURL)
    # ... followed by the download loop (calls the download function)


def Run_CatchException():
    try:
        main()
    except Exception as exc:
        print('critical error occured, program will shutdown')
        print(exc)
        logger.info('CHECK SHUTDOWN REASON : ' + str(exc))   # ★ #5 this log is also missing -> strong evidence no exception was raised
        os.system('pause')
        sys.exit()
    print('Program ended successfully.')
    sys.exit()


# Other functions: memoryFormatting, checkDateNormality, isValidAddress,
#                  getType, getName, getDday, getZipName, getOrderDate,
#                  getTextLink, getFullLink, addToDownloadList,
#                  searchValidCustomers, download, PrintProgressBar
# — See /tmp/exe-decompile/bojagi_disasm.txt for the full disassembly
