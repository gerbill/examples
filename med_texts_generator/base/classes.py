from settings import *
from base.utils import *


class Sentence(object):

    def __init__(self, data_dict=None):
        self.category = ""
        self.note = ""
        self.parts = []
        self.usage_counter = 0
        self.possible_sentences_number = 0
        self.children = False
        if data_dict:
            self.data_dict = data_dict
            self.load_from_data_dict()
        if "детей" in self.note.lower():
            self.children = True

    def load_from_data_dict(self):
        self.category = mode(self.data_dict['category']).lower()
        if self.data_dict['note']:
            self.note = mode(self.data_dict['note'])
        list_of_parts = list()
        for k, v in self.data_dict.items():
            if "parts" in k:
                list_of_parts.append((k.replace("parts|", ""), v))
        for parts in sorted(list_of_parts):
            self.parts.append(parts[1])

    def get_data_dict(self, reset_usage_counters=False):
        usage_counter = self.usage_counter
        if reset_usage_counters:
            usage_counter = 0
        return {
            "category": self.category,
            "note": self.note,
            "parts": self.parts,
            "usage_counter": usage_counter,
            "pediatrician": self.children}

    def random_sentence(self):
        random_sentence_list = list()
        for part in self.parts:
            random_sentence_list.append(get_random_choice(part))
        sentence = " ".join([str(s) for s in random_sentence_list])
        sentence = remove_junk(sentence)
        return sentence

    def get_all_possible_sentences(self):
        with codecs.open(ALL_TEXTS_FILE, "a", encoding="utf-8") as f:
            for combination in product(*self.parts):
                self.possible_sentences_number += 1
                sentence = " ".join(combination)
                sentence = remove_junk(sentence)
                f.write(self.category + "|" + sentence + "\n")


class Specialization(object):

    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.spec_type = ""
        self.entries = self.data_dict["entries"]
        self.spec_parts = list()
        self.spec_cats = list()
        self.load_from_data_dict()

    def load_from_data_dict(self):
        self.spec_type = mode(self.data_dict['spec_type']).lower().replace(" ", "")
        for i in self.data_dict['spec_cat']:
            # print(i.lower())
            pass
        self.spec_cats = [i.lower() for i in self.data_dict['spec_cat']]
        parts_raw = defaultdict(list)
        for k, v in self.data_dict.items():
            if isinstance(k, tuple) and k[0] == 'part':
                for item in v:
                    parts_raw[column_index_from_string(k[1])].append(item)
        for i, part in enumerate(sorted(parts_raw.items())):
            self.spec_parts.append([self.spec_cats[i], [remove_junk(p) for p in part[1] if p]])
        raw_entries = [[] for i in range(100)]
        for i, entry in enumerate(sorted(self.entries.items())):
            raw_entries[entry[0][0]].append([e for e in entry[1] if e])
        raw_entries = [item for item in raw_entries if item]
        self.entries = raw_entries

    def generate(self, text_quantity):
        # Generate entry text
        entry = list()
        if self.entries:
            for e in get_random_choice(self.entries):
                if e:
                    entry.append(get_random_choice(e))
        entry = " ".join(entry)
        # Generate specializations text
        spec_parts = copy.deepcopy(self.spec_parts)
        random.shuffle(spec_parts)
        specs = list()
        inv_no_mix = dict()
        for k, v in NO_MIX.items():
            for item in v:
                inv_no_mix[item] = k
        for i in range(100):
            if len(specs) < text_quantity and len(spec_parts) > 0:
                spec_parts_list = spec_parts.pop()
                if spec_parts_list[0].lower() in NO_MIX:
                    if any(c not in [s[0] for s in specs] for c in NO_MIX[spec_parts_list[0]]):
                        specs.append(spec_parts_list)
                elif spec_parts_list[0] in inv_no_mix:
                    if any(c not in [s[0] for s in specs] for c in inv_no_mix[spec_parts_list[0]]):
                        specs.append(spec_parts_list)
                else:
                    specs.append(spec_parts_list)
            else:
                break
        final_specs = [get_random_choice(s[1]) for s in specs]
        return remove_junk(entry).strip(), [remove_junk(s).strip() for s in final_specs]


class SpecSentence(object):

    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.spec_type = ""
        self.entries = self.data_dict["entries"]
        self.spec_parts = list()
        self.load_from_data_dict()

    def load_from_data_dict(self):
        self.spec_type = mode(self.data_dict['spec_type']).lower().replace(" ", "")
        parts_from_dict = [(k, v) for k, v in self.data_dict.items() if isinstance(k, tuple)]
        for k, v in sorted(parts_from_dict):
            if k[1] == "parts":
                self.spec_parts.append(v)

    def generate(self):
        spec_sentence = ""
        for part in self.spec_parts:
            spec_sentence += " " + get_random_choice(part)
        spec_sentence = remove_junk(spec_sentence)
        if "." not in spec_sentence:
            spec_sentence += "."
        return remove_junk(spec_sentence)
