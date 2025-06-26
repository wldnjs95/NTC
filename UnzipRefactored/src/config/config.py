import os
import datetime


# config.py
VERSION_INFO = '2.6'
photo_folder_name = '[photo]'
jpeg_quality = 100

# ----------- demo launch info -----------
# This file is used to store demo launch information.

DEMO_MODE = False
LIMIT_DAYS = 10
LAUNCH_CUTOFF_DATE = datetime.date(2025, 5, 20)



# ----------- default product list -----------
default_product_info = {
    "recent_product": None,
    "product_list": {
        "bubbletap": {
            "product_name": "bubbletap",
            "must_include": "버블탭"
        },
        "popcorn": {
            "product_name": "popcorn",
            "must_include": "팝콘"
        },
        "couple": {
            "product_name": "couple",
            "must_include": "프로미스"
        },
        "everything": {
            "product_name": "everything",
            "must_include": "화이트필름"
        },
        "joa": {
            "product_name": "joa",
            "must_include": "좋아"
        },
        "Justthewayyouare": {
            "product_name": "Justthewayyouare",
            "must_include": "그대만을"
        },
        "lovesome": {
            "product_name": "lovesome",
            "must_include": "러브썸"
        },
        "lovex3": {
            "product_name": "lovex3",
            "must_include": "봄날"
        },
        "marriage": {
            "product_name": "marriage",
            "must_include": "지천비화"
        },
        "marryme": {
            "product_name": "marryme",
            "must_include": "메리플라워"
        },
        "marryme_m": {
            "product_name": "marryme_m",
            "must_include": "메리미"
        },
        "paintyou": {
            "product_name": "paintyou",
            "must_include": "러브크로마"
        },
        "santorini": {
            "product_name": "santorini",
            "must_include": "태양의연인"
        },
        "secretgarden": {
            "product_name": "secretgarden",
            "must_include": "시크릿가든"
        },
        "serendipity": {
            "product_name": "serendipity",
            "must_include": "세렌디피티"
        },
        "simple": {
            "product_name": "simple",
            "must_include": "멜로망스"
        },
        "starblossom": {
            "product_name": "starblossom",
            "must_include": "내마음의별"
        },
        "thousandyears": {
            "product_name": "thousandyears",
            "must_include": "천년의숲"
        },
        "yourspecial": {
            "product_name": "yourspecial",
            "must_include": "웨드루미나레"
        },
        "parents": {
            "product_name": "parents",
            "must_include": "아버지와 엄마"
        },
        "parents1": {
            "product_name": "parents1",
            "must_include": "감사1"
        },
        "parents2": {
            "product_name": "parents2",
            "must_include": "감사2"
        },
        "skyflower": {
            "product_name": "skyflower",
            "must_include": "가족바라기"
        },
        "heartbeat": {
            "product_name": "heartbeat",
            "must_include": "하트비트"
        }
        
        
    }
}