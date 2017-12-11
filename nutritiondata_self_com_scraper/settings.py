import requests
import psycopg2
import random
import time
import json
import re
import os
from lxml import html
from pprint import pprint as pp
from multiprocessing.dummy import Pool


HEADERS = {
    'ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'ACCEPT_ENCODING': 'gzip, deflate, br',
    'ACCEPT_LANGUAGE': 'en-US,en;q=0.8,ru;q=0.6',
    'CONNECTION': 'keep-alive',
    'UPGRADE_INSECURE_REQUESTS': 1,
    'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
}

ROOT_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
SCRAPED_DATA_DIR = ROOT_DIR + "scraped_data/"
FAILED_HTMLS_DIR = ROOT_DIR + "failed_requests_htmls/"
HTML_DATA_FILE = SCRAPED_DATA_DIR + "htmls.csv"
TOP_MENU_FILE = ROOT_DIR + "base/top_menu.txt"
BASE_CATEGORY_URL = "http://nutritiondata.self.com/foods-{}000000000000000000.html"
ROOT_URL = "http://nutritiondata.self.com"
PRODUCT_URLS_LIST_FILE = SCRAPED_DATA_DIR + "product_urls.txt"

ALL_DATA_JSON = SCRAPED_DATA_DIR + "all_data.json"

PROXY_FILE = ROOT_DIR + 'proxies.txt'
CHECK_PROXY_URL = 'http://dualgrid.com/ping2.php'

CSV_DELIMITER = "|@|"
PRODUCT_PAGE_CHECK_STR = 'name="form4"'

JUNK_ITEMS = {
    "  ", " "
}

ILLEGAL_PSQL_CHARS = ["-", " ", ",", ":", "+", "(", ")", "__"]

NUT_PROPS = {
    "NUTRIENT_": "value",
    "UNIT_NUTRIENT_": "units",
    "DV_NUTRIENT_": "daily_value"
}

DB_NAME = "nut_scraping"
DB_USER_LOGIN = "nut_scraper"
DB_USER_PASSWORD = "mTzHY3FQfgfKGEY7"

STRING_VALUES = ["opinion", "url", "name"]