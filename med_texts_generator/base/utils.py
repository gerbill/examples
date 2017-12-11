from settings import *


def remove_junk(string):
    for i in range(2):
        for old, new in THINGS_TO_REPLACE.items():
            string = string.replace(old, new)
    return string


def key_normalize(string):
    string = string.replace("+", "").lower()
    string = remove_junk(string)
    new_string = list()
    for word in string.split(" "):
        if word:
            word = morph.parse(word)[0].normal_form
            new_string.append(word)
    return " ".join(new_string)


def remove_similar_specs(specs):
    new_specs = set()
    for spec in specs:
        if spec in similar_specs:
            new_specs.add(similar_specs[spec])
        else:
            new_specs.add(spec)
    return new_specs


def load_similar_specs():
    wb = px.load_workbook(SIMILAR_SPECS_XLSX)
    ws = wb.get_sheet_by_name("Специализации врачей")
    similar_specs = dict()
    for row in ws.iter_rows():
        sim_specs = list()
        cell_iv_a = ""
        for cell in row:
            cell_iv = cell.internal_value
            if cell.column == "A":
                sim_specs.append(cell_iv)
                cell_iv_a = cell_iv
            if cell.column == "B":
                if cell_iv:
                    sim_specs.append(cell_iv)
                else:
                    sim_specs.append(cell_iv_a)
        similar_specs[key_normalize(sim_specs[0])] = sim_specs[1]
    return similar_specs


similar_specs = load_similar_specs()


def add_to_used_sentences(sentence):
    with codecs.open(USED_SENTENCES_FILE, "a", encoding="utf-8") as f:
        f.write(sentence + "\n")


def clear_used_sentences_file():
    with codecs.open(USED_SENTENCES_FILE, "w", encoding="utf-8") as f:
        f.write("")


def add_cat(cat, sentence, add=False):
    add_to_used_sentences(sentence)
    if add:
        cat_to_add = "[" + cat + "] "
        return cat_to_add + sentence
    else:
        return sentence


def cat_is_used(cat, used_cats):
    used_cats = {c.replace(",", "+") for c in used_cats}
    used_cats_split = set()
    for c in used_cats:
        for word in c.split("+"):
            used_cats_split.add(word)
    if any(word in used_cats_split for word in cat.split("+")):
        return True
    else:
        # print(used_cats, cat)
        return False


def min_max_types(doc_type):
    mm = get_random_choice(MIN_MAX_QUANTITY[doc_type])
    types = list()
    for t in mm:
        my_range = random.randrange(t[1], t[2] + 1)
        types.append((t[0], my_range))
    return types


def min_max_spec_sentence(doc_type):
    types = list()
    for item in MIN_MAX_SPEC_SENTENCE[doc_type]:
        if item[-1]:
            types.append((item[0], random.randrange(item[1], item[2] + 1)))
        else:
            item = get_random_choice([i for i in MIN_MAX_SPEC_SENTENCE[doc_type] if not i[-1]])
            types.append((item[0], random.randrange(item[1], item[2] + 1)))
    return types


def get_random_choice(list_to_choose_from):
    true_random_index = random.SystemRandom().randint(0, len(list_to_choose_from) - 1)
    return list_to_choose_from[true_random_index]


def get_allowed_sentences(sentences, doc_specs, split_name):
    if frozenset(doc_specs) in allowed_sentences_cache:
        return allowed_sentences_cache[frozenset(doc_specs)]
    allowed_sentences = list()
    if split_name in specs_intersection:
        si = specs_intersection[split_name]
        try:
            si.pop("split_name")
        except:
            pass
        for spec_type, spec_list in si.items():
            notes = {i["note"] for i in spec_list}
            for sentence_obj in sentences:
                if sentence_obj.note and sentence_obj.note in notes:
                    allowed_sentences.append(sentence_obj)
                elif not sentence_obj.note:
                    allowed_sentences.append(sentence_obj)
        allowed_sentences_cache[frozenset(doc_specs)] = allowed_sentences
        return allowed_sentences


allowed_sentences_cache = dict()
