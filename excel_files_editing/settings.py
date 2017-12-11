import openpyxl as px
import pymorphy2
import requests
import random
import codecs
import json
import time
import os
from pprint import pprint as pp
from collections import defaultdict
from multiprocessing.dummy import Pool


THREADS_NUM = 10
TIMEOUT = 0.1
FAILURE_TIMEOUT = 0.1


ROOT_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
INPUT_FILES_DIR = ROOT_DIR + "input_files/"
OUTPUT_FILES_DIR = ROOT_DIR + "output_files/"

INPUT_FILE = INPUT_FILES_DIR + "2.xlsx"
OUTPUT_WORDS_CSV = OUTPUT_FILES_DIR + "words.csv"
OUTPUT_SP_CSV = OUTPUT_FILES_DIR + "sp.csv"
OLD_OUTPUT_FILE = OUTPUT_FILES_DIR + "old/words.csv"

MORPH = pymorphy2.MorphAnalyzer()

PROXY_FILE = ROOT_DIR + "proxies2.txt"
CHECK_PROXY_URL = "http://dualgrid.com/ping2.php"

WORD_TAGS = {
    'CONJ': 'Союз',
    'NOUN': 'Существительное',
    'ADJF': 'Прилагательное',
    'NUMR': 'Числительное',
    'VERB': 'Глагол',
    'ADVB': 'Наречие',
    'PREP': 'Предлог',
    'PRCL': 'Частица',
    'INFN': 'Связка',
    'LATN': 'Латиница',
    'UNKN': 'Неопределено'
}

TRASH_TAGS = {'NUMR', 'PRCL', 'INFN', 'CONJ', 'UNKN', 'LATN', 'PREP'}
TRASH_CHARS = {
    "[": " ",
    "]": " ",
    ";": ",",
    "  ": " "
}

TRASH_CHARS_FOR_OUTPUT = {
    "[": " ",
    "]": " ",
    "  ": " "
}

COMMERCE_WORDS = {
    'где',
    'сделать',
    'купить',
    'цена',
    'стоимость',
    'записать',
    'записаться',
    'прием'
}

NAME_TYPES = ["last_name", "first_name", "middle_name"]


HEADERS = {
    'ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'ACCEPT_ENCODING': 'gzip, deflate, br',
    'ACCEPT_LANGUAGE': 'en-US,en;q=0.8,ru;q=0.6',
    'CONNECTION': 'keep-alive',
    'UPGRADE_INSECURE_REQUESTS': "1",
    'USER_AGENT': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
}


YANDEX_GEOCODER_BASE_URL = "https://geocode-maps.yandex.ru/1.x/?format=json&geocode={}"

WORD_OUTPUT_COLUMNS = ["tag"] + NAME_TYPES + ["is_geo", "address"]

SEARCH_PHRASE_OUTPUT_COLUMNS = ["sp", "if_commerce"] + NAME_TYPES + ["is_geo", "addresses"]
