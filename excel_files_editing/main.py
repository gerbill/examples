from settings import *
from base.utils import *
from base.classes import *


def worker_words(worker_id):
    while True:
        try:
            row = next(Word.words_rows_generator)
            if len(row) > 0 and row[0].internal_value:
                if row[0].internal_value not in Word.used_strings:
                    Word([cell.internal_value for cell in row[:8]])
                    Word.used_strings.add(row[0].internal_value)
            time.sleep(random.random()/10)
        except StopIteration:
            print("worker_words #{} has finished its task. Closing...".format(str(worker_id)))
            return None
        except ValueError as exc:
            print(exc)
            time.sleep(random.random())


def worker_sp(worker_id):
    while True:
        try:
            row = next(SearchPhrase.sp_rows_generator)
            if len(row) > 0 and row[0].internal_value:
                SearchPhrase(row[0].internal_value)
            time.sleep(TIMEOUT)
        except StopIteration:
            print("worker_sp #{} has finished its task. Closing...".format(str(worker_id)))
            return None


def load_old_addresses():
    with codecs.open(OLD_OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().split(";")
            Word.word_to_addresses[line[0]] = line[-1]


def load_input_xlsx(input_xlsx):
    Proxy.load_and_check()
    wb = px.load_workbook(input_xlsx)
    used_strings = set()

    # Get FIOs
    ws = wb.get_sheet_by_name("ФИО")
    for i, row in enumerate(list(ws.iter_rows())):
        if i == 0:
            continue
        if len(row) > 0 and row[0]:
            for cell_tup in zip(row[:3], NAME_TYPES):
                if cell_tup[0].internal_value and cell_tup[0].internal_value not in used_strings:
                    FIO.all[cell_tup[0].internal_value.lower()] = cell_tup[1]
                    FIO.all_set.add(cell_tup[0])
                    used_strings.add(cell_tup[0].internal_value)

    # Get Words
    # ws = wb.get_sheet_by_name("Слова")
    # Word.words_rows_generator = ws.iter_rows()
    # next(Word.words_rows_generator)
    # pool = Pool(THREADS_NUM)
    # pool.map(worker_words, list(range(THREADS_NUM)))

    # Get SearchPhrases
    ws = wb.get_sheet_by_name("ПЗ")
    SearchPhrase.sp_rows_generator = ws.iter_rows()
    next(SearchPhrase.sp_rows_generator)
    pool = Pool(THREADS_NUM)
    pool.map(worker_sp, list(range(THREADS_NUM)))


if __name__ == '__main__':
    load_old_addresses()
    load_input_xlsx(INPUT_FILE)
