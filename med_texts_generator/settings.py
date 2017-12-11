import os
import json
import copy
import time
import random
import codecs
import pymorphy2
import openpyxl as px
from statistics import mode
from itertools import product
from pprint import pprint as pp
from collections import defaultdict
from openpyxl.utils import column_index_from_string


# Укажите входные файлы в виде: "тип_доктора": "название_файла.xlsx"
# "тип_доктора" должен совпадать с типом доктора в doctors.json файле в поле "our">"specialty">"name"
INPUT_XLSX_FILES = {
    'стоматолог': "dentists.xlsx",
    'маммолог': 'mammalogists.xlsx',
    'дерматолог': 'dermatologists.xlsx',
    'гинеколог': 'gynecologists.xlsx',
    'гастроэнтеролог': 'Гастроэнтерологи разбивка.xlsx',
    'иммунолог': 'Иммунологи Разбивка.xlsx',
    'отоларинголог': 'Отоларингологи Разбивка.xlsx',
    'уролог': 'Урологи разбивка.xlsx',
    'проктолог': 'Проктологи Разбивка.xlsx',
    'флеболог': 'Флебологи разбивка.xlsx',
    'кардиолог': 'Кардиолог Разбивка.xlsx',
}

MINIMAL_DISSIMILARITY = 80
ABS_MINIMAL_DISSIMILARITY = 0
DISSIM_CHANGE_TIME = 30

ROOT_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"
INPUT_DATA_DIR = ROOT_DIR + "input_data/"
SPLITS_DIR = INPUT_DATA_DIR + "xlsx_splits/"
SPLITS_TO_SPECS_FILE = {
    "file": INPUT_DATA_DIR + "Пересечение специализаций.xlsx",
    "sheet": "ГОТОВОЕ ГЕНЕРАЦИЯ"
}
SIMILAR_SPECS_XLSX = INPUT_DATA_DIR + "Пересечение специализаций.xlsx"
ALL_TEXTS_FILE = INPUT_DATA_DIR + "texts.txt"
OBJECTS_JSON_FILE = INPUT_DATA_DIR + "objects.json"
USED_SENTENCES_FILE = INPUT_DATA_DIR + "used_sentences.txt"
DOCTORS_JSON_FILE = INPUT_DATA_DIR + "doctors.json"

OUTPUT_DATA_DIR = "output_data/"
DOCTORS_JSON_FILE_GEN_TEXT = OUTPUT_DATA_DIR + "doctors.json"

INPUT_XLSX_FILE_NAMES = os.listdir(SPLITS_DIR)
INPUT_XLSX_PATHS = [SPLITS_DIR + file for file in INPUT_XLSX_FILE_NAMES]


PRIORITY_CATS = [
    "услуги",
    "методы",
    "заболевания"
]

THINGS_TO_REPLACE = {
    "\n": " ",
    "\t": " ",
    "  ": " ",
    "::": ":",
    "..": "."
}

COLORS = {
    "spec_type": "FF00FFFF",
    "entry": "FFFF0000",
    "spec_cat": "FFD9D2E9",
    "no_color": "00000000",
    "no_fill": ["FFFFFFFF", "00000000"],
    "delimiter": "FF00FFFF",
    "no_gen": "FFFF0000"
}

# Эти фразы нельзя сочетать (указываются в xlsx файле во вкладке "Аннотация"
NO_MIX = {
    "хирургия (общее)": [i.lower() for i in [
        "Удаление", "Имплантация и протезирование", "Пластика", "Удаление кист"
    ]],
    "терапевтическая стоматология": [i.lower() for i in [
        "Восстановление и реставрация",  "Профессиональная гигиена", "Отбеливание зубов",
        "Профилактика (герметизация фиссур и ремотерпаия)",  "Лечение корневых каналов", "Пародонтология"
    ]]
}

# Возможные комбинации категорий специализаций. Указывается в xlsx файле во вкладе "Аннотация"
MIN_MAX_QUANTITY = {
    "стоматолог": [[
        ("заболевания", 3, 5),
        ("методы", 3, 5),
        ("другое", 1, 1)
    ], [
        ("заболевания", 3, 5),
        ("услуги", 3, 5),
        ("другое", 1, 1)
    ]],
    "маммолог": [[
        ("заболевания", 3, 5),
        ("услуги", 3, 5),
        ("методы", 3, 5),
        ("другое", 1, 2)
    ], [
        ("заболевания", 3, 5),
        ("методы", 3, 5),
        ("другое", 1, 3)
    ], [
        ("заболевания", 3, 5),
        ("услуги", 3, 5),
        ("другое", 1, 3)
    ]],
    "дерматолог": [[
        ("заболевания", 3, 5),
        ("услуги", 4, 5),
    ]],
    "гинеколог": [[
        ("заболевания", 3, 3),
        ("услуги", 3, 4)
    ]],
    "гастроэнтеролог": [[
        ("заболевания", 3, 3),
        ("методы", 3, 3)
    ]],
    "иммунолог": [[
        ("заболевания", 3, 3),
        ("методы", 3, 3)
    ]],
    "отоларинголог": [[
        ("заболевания", 3, 4),
        ("услуги", 3, 4),
        ("методы", 2, 3)
    ]],
    "уролог": [[
        ("услуги", 3, 4),
        ("заболевания", 4, 5),
        ("методы", 2, 3)
    ]],
    "проктолог": [[
        ("лечение", 2, 2),
        ("диагностика", 1, 2),
        ("дополнительно", 3, 4),
        ("другие+навыки", 4, 5),
        ("заболевания", 2, 3)
    ]],
    "флеболог": [[
        ("заболевания", 3, 5),
        ("услуги", 5, 7),
    ]],
    "кардиолог": [[
        ("заболевания", 3, 3),
        ("услуги", 3, 3),
        ("методы", 3, 3)
    ], [
        ("заболевания", 4, 4),
        ("услуги", 4, 4),
    ], [
        ("заболевания", 4, 4),
        ("методы", 3, 3),
    ]]
}


MIN_MAX_SPEC_SENTENCE = {
    "проктолог": [
        ("диагностика", 1, 1, True),
        ("лечение", 1, 1, True),
        ("дополнительно", 2, 2, False),
        ("другие навыки", 3, 3, False),
        ("заболевания", 1, 1, False)
    ]
}


# Заполняется методом Load.specs_intersection_file()
specs_intersection = dict()

# Заполняется классом Split
all_splits = dict()

morph = pymorphy2.MorphAnalyzer()

TEXTS_TO_TIME_FILE = ROOT_DIR + "misc/texts_to_time.txt"
