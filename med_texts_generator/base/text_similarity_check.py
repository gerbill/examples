import re
import json
import codecs
import pymorphy2
import openpyxl as px
from nltk import ngrams
from copy import deepcopy
from pprint import pprint as pp


morph = pymorphy2.MorphAnalyzer()
norm_cache = dict()


class MyShingledText(object):

    def __init__(self, text, shingle_length=5):
        split_text = text.split()
        if len(split_text) < shingle_length:
            raise ValueError('input text is too short for specified shingle length of {}'.format(shingle_length))
        self.shingles = list()
        for shingle in ngrams(split_text, shingle_length):
            min_value = ' '.join(shingle)
            self.shingles.append(min_value)

    def similarity(self, other_shingled_text):
        return len(set(self.shingles).intersection(set(other_shingled_text.shingles))) / len(set(self.shingles))


def compute_similarity(t1, t2, shingle_length=4):
    ts1 = MyShingledText(t1, shingle_length=shingle_length)
    ts2 = MyShingledText(t2, shingle_length=shingle_length)
    return 100 - ts1.similarity(ts2) * 100


def norm_and_clean(text):
    text = re.sub('[^\w\d\s]', '', text).lower()
    for stop_word in stop_words:
        text = text.replace(" " + stop_word + " ", " ")
    text = text.split()
    text = [word for word in text if len(word) > 2]
    norm_text = []
    for word in text:
        if word not in norm_cache:
            norm_word = morph.parse(word)[0].normal_form
            norm_cache[word] = norm_word
        norm_text.append(norm_cache[word])
    return " ".join(norm_text)


def load_text_from_json_file(file_name):
    with codecs.open(file_name, "r", encoding="utf-8") as f:
        data = json.loads(f.read())
    # pp(data, width=1000)
    texts = dict()
    # for item in data:
    #     text_fields = ['education', 'extra_education', 'info']
    #     text_url = item['url']
    #     text = " ".join([item[tf] for tf in text_fields])
    #     texts[text_url] = norm_and_clean(text)

    counter = 0
    for item in data:
        try:
            if len(item['new_info']) < 5 and len(item['info']) < 5 and "docdoc" not in item['url']:
                continue
            if "docdoc" in item['url'] and len(item['info']) > 5:
                text_fields = ['info']
                text_url = item['url']
                text = " ".join([item[tf] for tf in text_fields])
                texts[text_url] = norm_and_clean(text)
                counter += 1
                if counter > 2000:
                    break
        except Exception as exc:
            print(exc)
    return texts


stop_words = ('это', 'как', 'так',
              'и', 'в', 'над',
              'к', 'до', 'не',
              'на', 'но', 'за',
              'то', 'с', 'ли',
              'а', 'во', 'от',
              'со', 'для', 'о',
              'же', 'ну', 'вы',
              'бы', 'что', 'кто',
              'он', 'она', 'или',  '  ', '  ')


def create_xlsx_from_json(json_file_name):
    texts = load_text_from_json_file(json_file_name)
    wb = px.Workbook()
    ws = wb.active
    headers = ['url', '3.s (%)', '4.s (%)', '5.s (%)']
    ws.append(headers)
    total_length = len(texts.items())
    for i, this_text in enumerate(texts.items()):
        print(i, total_length - i, this_text)
        texts_without_this_text = deepcopy(texts)
        del texts_without_this_text[this_text[0]]
        texts_without_this_text = " ".join([text[1] for text in texts_without_this_text.items()])
        row = [this_text[0]]
        for j in range(3, 6):
            row.append(round(compute_similarity(this_text[1], texts_without_this_text, shingle_length=j), 2))
        ws.append(row)
    wb.save(json_file_name.split(".")[0] + ".docdoc_dissimilarities.xlsx")


def general_dissimilarities_report(json_files_list):
    all_texts = dict()
    for json_file_name in json_files_list:
        texts = load_text_from_json_file(json_file_name)
        for k, v in texts.items():
            all_texts[k] = v

    wb = px.Workbook()
    ws = wb.active
    headers = ['3.s (%)', '4.s (%)', '5.s (%)', 'text']
    ws.append(headers)
    total_length = len(all_texts.items())
    for i, this_text in enumerate(all_texts.items()):
        print(i, total_length - i, this_text)
        texts_without_this_text = deepcopy(all_texts)
        del texts_without_this_text[this_text[0]]
        texts_without_this_text = " ".join([text[1] for text in texts_without_this_text.items()])
        row = []
        for j in range(3, 6):
            row.append(round(compute_similarity(this_text[1], texts_without_this_text, shingle_length=j), 2))
        row.append(this_text[1])
        ws.append(row)
    wb.save("general_docdoc_dissimilarities_2.xlsx")


if __name__ == '__main__':
    general_dissimilarities_report(["./files/doctors.json"])
