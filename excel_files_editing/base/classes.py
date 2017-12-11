from settings import *
from base.utils import *


class Word(object):
    all = dict()
    headers = list()
    word_to_address_old = dict()
    word_to_addresses = dict()
    words_rows_generator = None
    used_strings = set()

    def __init__(self, row):
        self.row = row
        self.name = str(row[0]).lower()
        self.raw_tag = get_word_tag(self.name)
        if self.raw_tag in WORD_TAGS:
            self.tag = WORD_TAGS[self.raw_tag]
        else:
            self.tag = WORD_TAGS['UNKN']
        for nt in NAME_TYPES:
            if self.name in FIO.all and nt == FIO.all[self.name]:
                self.__dict__[nt] = self.name
            else:
                self.__dict__[nt] = " "
        if self.name in Word.word_to_addresses:
            self.address = Word.word_to_addresses[self.name]
        elif self.raw_tag not in TRASH_TAGS:
            self.address = get_address(self.name)
            if self.address:
                Word.word_to_addresses[self.name] = self.address
        else:
            self.address = ""
        if self.address:
            self.is_geo = True
        else:
            self.is_geo = False
        Word.all[self.name] = self
        self.output_row()

    def output_row(self):
        for col in WORD_OUTPUT_COLUMNS:
            self.row.append(self.__dict__[col])
        append_to_csv(self.row, OUTPUT_WORDS_CSV)
        print(self.row)


class SearchPhrase(object):
    all = list()
    headers = list()
    sp_rows_generator = None

    def __init__(self, sp):
        self.row = list()
        self.sp = sp.lower()
        self.words_set = set(self.sp.split(" "))
        SearchPhrase.all.append(self)
        if any(com_word.lower() in self.sp for com_word in COMMERCE_WORDS):
            self.if_commerce = True
        else:
            self.if_commerce = False
        common_names = self.words_set & FIO.all_set
        if len(common_names) > 0:
            for name in common_names:
                for nt in NAME_TYPES:
                    if FIO.all[name] == nt:
                        self.__dict__[nt] = name
                    else:
                        self.__dict__[nt] = ""
        else:
            for nt in NAME_TYPES:
                self.__dict__[nt] = ""
        self.is_geo = False
        self.addresses = ""
        self.get_addresses()
        if self.addresses:
            self.is_geo = True
        self.output_row()

    def get_addresses(self):
        addresses = list()
        for word in self.words_set:
            word = word.lower()
            raw_tag = get_word_tag(word)
            if raw_tag in TRASH_TAGS:
                continue
            if word in Word.word_to_addresses:
                word_address = Word.word_to_addresses[word]
            else:
                word_address = get_address(word)
            if word_address:
                addresses.append(word_address)
        self.addresses = " | ".join(addresses)

    def output_row(self):
        for col in SEARCH_PHRASE_OUTPUT_COLUMNS:
            self.row.append(self.__dict__[col])
        append_to_csv(self.row, OUTPUT_SP_CSV)
        print(self.row)


class FIO(object):
    all = dict()
    all_set = set()
