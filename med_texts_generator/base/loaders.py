from settings import *
from base.classes import *
from base.text_similarity_check import *


class Load(object):
    all_possible_specs = set()
    previously_done_doctors = dict()

    def __init__(self):
        self.specs_intersection_file()
        self.load_done_doctors()
        self.xlsx_input_files()
        self.doctors()

    def specs_intersection_file(self):
        wb = px.load_workbook(SPLITS_TO_SPECS_FILE["file"])
        ws = wb.get_sheet_by_name(SPLITS_TO_SPECS_FILE["sheet"])
        d = defaultdict(list)
        for row in ws.iter_rows():
            for cell in row[:5]:
                cell_color = cell.fill.start_color.index
                cell_a_color = ws['A{}'.format(cell.row)].fill.start_color.index
                if cell_color != COLORS["delimiter"]:
                    if cell.internal_value and cell_color != COLORS["no_gen"]:
                        if cell.column == "A":
                            d["split_name"].append(cell.internal_value)
                        elif cell.column == "B" and cell_a_color != COLORS["no_gen"]:
                            spec_name = cell.internal_value
                            Load.all_possible_specs.add(spec_name)
                            d["main_specs"].append({
                                "name": spec_name,
                                "note": ws['C{}'.format(cell.row)].internal_value
                            })
                        elif cell.column == "D" and cell_a_color != COLORS["no_gen"]:
                            d["secondary_specs"].append({
                                "name": cell.internal_value,
                                "note": ws['E{}'.format(cell.row)].internal_value
                            })
                else:
                    if d:
                        split_name = key_normalize(mode(d["split_name"]))
                        specs_intersection[split_name] = d
                    d = defaultdict(list)

    def xlsx_input_files(self):
        for i, file_path in enumerate(INPUT_XLSX_PATHS):
            Split(file_path, i)

    def doctors(self):
        with open(DOCTORS_JSON_FILE, "r", encoding="utf-8") as f:
            doctors_list = json.loads(f.read())
        all_possible_specs = remove_similar_specs(Load.all_possible_specs)
        doctors_to_generate = 0
        for doctor in doctors_list:
            doc_specs = remove_similar_specs(doctor["our"]["specialty"])
            if len(doc_specs - all_possible_specs) < len(doc_specs):
                doctors_to_generate += 1
        done_doctors = 0
        for i, doc_dict in enumerate(doctors_list):
            if doc_dict['name'] in Load.previously_done_doctors and \
                            "new_info" in Load.previously_done_doctors[doc_dict['name']]["our"] and \
                            len(Load.previously_done_doctors[doc_dict['name']]["our"]["new_info"]) > 3:
                doc_dict = Load.previously_done_doctors[doc_dict['name']]
                # pp(doc_dict)
                Doctor.all_json.append(doc_dict)
                print("Already generated new_info for doctor:", doc_dict["our"]["new_info"])
                Doctor.all_new_info.append(doc_dict["our"]["new_info"])
            else:
                doc = Doctor(doc_dict)
                if doc.dissimilarity:
                    done_doctors += 1
                    report_times = dict()
                    for k, v in Doctor.times.items():
                        report_times[k] = round(sum(v))
                    print(doc.doc_name, doc.doc_specs, "| done:", done_doctors, "| left:",
                          doctors_to_generate - done_doctors,
                          " | d: {}% | cmd: {}%".format(round(doc.dissimilarity), doc.current_dissimilarity))
                    print("attempts:", doc.attempts,
                          " time:", str(int(doc.gen_time)) + " sec" if doc.gen_time/60 < 1
                          else str(round(doc.gen_time/60, 2)) + " min")
                    print("=" * 80)
                    with open(TEXTS_TO_TIME_FILE, "a") as f:
                        f.write(str(done_doctors) + ":" + str(doc.gen_time) + "\n")
                    Load.dump_json_to_file()

    @staticmethod
    def dump_json_to_file():
        json_dump = json.dumps(Doctor.all_json)
        with codecs.open(DOCTORS_JSON_FILE_GEN_TEXT, "w", encoding="utf-8") as f:
            f.write(json_dump)
        with codecs.open(DOCTORS_JSON_FILE_GEN_TEXT + "_backup", "w", encoding="utf-8") as f:
            f.write(json_dump)

    def load_done_doctors(self):
        if not os.path.exists(DOCTORS_JSON_FILE_GEN_TEXT):
            return None
        with open(DOCTORS_JSON_FILE_GEN_TEXT, "r") as f:
            file_content = f.read()
        if len(file_content) > 3 and "[" in file_content:
            try:
                done_doctors_json = json.loads(file_content)
            except:
                done_doctors_json = json.loads(file_content + "]")
            for doctor in done_doctors_json:
                print(doctor["name"])
                Load.previously_done_doctors[doctor["name"]] = doctor
        else:
            try:
                with open(DOCTORS_JSON_FILE_GEN_TEXT + "_backup", "r") as f:
                    file_content = f.read()
                if len(file_content) > 3 and "[" in file_content:
                    try:
                        done_doctors_json = json.loads(file_content)
                    except:
                        done_doctors_json = json.loads(file_content + "]")
                    for doctor in done_doctors_json:
                        print(doctor["name"])
                        Load.previously_done_doctors[doctor["name"]] = doctor
            except:
                pass


class Split(object):

    def __init__(self, file_path, i):
        self.file_path = file_path
        self.file_name = INPUT_XLSX_FILE_NAMES[i]
        self.split_name = key_normalize(self.file_name.split(".")[0])
        self.all_sentences = list()
        self.all_specializations = defaultdict(list)
        self.all_spec_sentences = defaultdict(list)
        self.children = True
        self.paragraph_length = random.randrange(3, 7)
        if self.split_name in specs_intersection:
            self.main_specs = set(
                [key_normalize(spec["name"]) for spec in specs_intersection[self.split_name]["main_specs"]])
            self.secondary_specs = set(
                [key_normalize(spec["name"]) for spec in specs_intersection[self.split_name]["secondary_specs"]])
            self.main_specs = remove_similar_specs(self.main_specs)
            self.secondary_specs = remove_similar_specs(self.secondary_specs)
        else:
            self.main_specs = set()
            self.secondary_specs = set()
        self.wb = px.load_workbook(self.file_path)
        self.load_sentences()
        self.load_specializations()
        self.load_spec_sentences()
        if self.main_specs:
            all_splits[self.split_name] = self

    def load_sentences(self):
        sheet_name = "Краткий параграф"
        if sheet_name not in self.wb.get_sheet_names():
            return None
        ws = self.wb.get_sheet_by_name(sheet_name)
        ws.append([""])
        rows = list(ws.iter_rows())
        data_dict = defaultdict(list)
        for row in rows:
            for cell in row:
                cell_color = cell.fill.start_color.index
                if cell.column == "A" and cell.internal_value:
                    category = cell.internal_value.lower()
                    category = category.replace(", ", ",").replace(" ", "+")
                    data_dict["category"].append(category)
                elif cell.column == "B" and cell.internal_value:
                    data_dict["note"].append(cell.internal_value.lower())
                else:
                    if all(c != cell_color for c in COLORS["no_fill"]) and cell.internal_value:
                        data_dict["parts" + "|" + cell.column].append(cell.internal_value)
                if any(c == cell_color for c in COLORS["no_fill"]) \
                        and not cell.internal_value and cell.column == "D":
                    if 'parts|C' in data_dict:
                        self.all_sentences.append(Sentence(data_dict=data_dict))
                        data_dict = defaultdict(list)

    def generate_sentences(self, doc_specs):
        sentences = get_allowed_sentences(self.all_sentences, doc_specs, self.split_name)
        if not sentences:
            sentences = self.all_sentences
        priority_cats = copy.deepcopy(PRIORITY_CATS)
        random.shuffle(priority_cats)
        random.shuffle(sentences)
        used_cats = set()
        paragraph = list()
        paragraph_cats = list()
        for priority_cat in priority_cats:
            got_sentence = False
            if any(priority_cat in cat for cat in used_cats) or any(priority_cat in cat for cat in paragraph_cats):
                pass
            else:
                for sentence in sentences:
                    if got_sentence:
                        break
                    if not cat_is_used(priority_cat, used_cats) and priority_cat in sentence.category:
                        # for i in range(1000):
                        if self.children:
                            paragraph.append(add_cat(sentence.category, sentence.random_sentence()))
                            got_sentence = True
                            # break
                        else:
                            if not sentence.children:
                                paragraph.append(add_cat(sentence.category, sentence.random_sentence()))
                                got_sentence = True
                                # break
                        paragraph_cats.append(sentence.category)
                        used_cats.add(sentence.category)
                        used_cats.add(priority_cat)
        # counter = 0
        # while len(paragraph) < self.paragraph_length:
        #     counter += 1
        #     if counter > 3:
        #         print("breaking by counter")
        #         break
        # sentence = get_random_choice(self.all_sentences)
        random.shuffle(self.all_sentences)
        for sentence in self.all_sentences:
            if not cat_is_used(sentence.category, used_cats) and all(p_cat not in sentence.category for p_cat in priority_cats):
                if self.children:
                    paragraph.append(add_cat(sentence.category, sentence.random_sentence()))
                else:
                    if not sentence.children:
                        paragraph.append(add_cat(sentence.category, sentence.random_sentence()))
                used_cats.add(sentence.category)
                paragraph_cats.append(sentence.category)
            if len(paragraph) >= self.paragraph_length:
                break
        return remove_junk(" ".join(paragraph))

    def load_specializations(self):
        sheet_name = "Специализация"
        if sheet_name not in self.wb.get_sheet_names():
            return None
        ws = self.wb.get_sheet_by_name(sheet_name)
        ws.append([""])
        rows = list(ws.iter_rows())
        data_dict = defaultdict(list)
        entries = defaultdict(list)
        entries_counter = 0
        for i, row in enumerate(rows):
            for cell in row:
                cell_color = cell.fill.start_color.index
                if cell.column == "A" and cell.internal_value:
                    data_dict["spec_type"].append(cell.internal_value.lower())
                elif cell_color == COLORS["entry"]:
                    entries[(entries_counter, cell.column)].append(cell.internal_value)
                elif cell.column == "C" and not cell.internal_value:
                    if i > 0 and rows[i - 1][2].fill.start_color.index == COLORS["entry"]:
                        entries_counter += 1
                elif cell_color == COLORS["spec_cat"]:
                    data_dict["spec_cat"].append(cell.internal_value)
                elif all(c != cell_color for c in COLORS["no_fill"]) and cell.column != "A" and cell.column != "B":
                    data_dict[("part", cell.column)].append(cell.internal_value)
                elif cell.column == "A" and any(c == cell_color for c in COLORS["no_fill"]):
                    if data_dict:
                        data_dict["entries"] = entries
                        spec_type = key_normalize(mode(data_dict['spec_type']))
                        self.all_specializations[spec_type].append(Specialization(data_dict))
                    data_dict = defaultdict(list)
                    entries = defaultdict(list)
                    entries_counter = 0

    def generate_specialization(self):
        if not self.all_specializations:
            return ""
        main_specs = list(copy.deepcopy(self.main_specs))
        random.shuffle(main_specs)
        spec_types = None
        for s in main_specs:
            try:
                spec_types = min_max_types(s)
                break
            except:
                pass
        if not spec_types:
            print("no valid spec", main_specs)
            return ""
        paragraph = list()
        for t in spec_types:
            if key_normalize(t[0]) not in self.all_specializations:
                continue
            spec_obj = get_random_choice(self.all_specializations[key_normalize(t[0])])
            text = spec_obj.generate(t[1])
            text_str = remove_junk(text[0]) + "\n" + "\n".join([remove_junk(item) for item in text[1]])
            paragraph.append(text_str)
        return " ".join(paragraph)

    def load_spec_sentences(self):
        sheet_name = "Специализация - предложения"
        if sheet_name not in self.wb.get_sheet_names():
            return None
        ws = self.wb.get_sheet_by_name(sheet_name)
        ws.append([""])
        rows = list(ws.iter_rows())
        data_dict = defaultdict(list)
        for row in rows:
            for cell in row:
                cell_color = cell.fill.start_color.index
                if cell.column == "A" and cell.internal_value:
                    category = cell.internal_value.lower()
                    category = category.replace(", ", ",").replace(" ", "+")
                    data_dict["spec_type"].append(category)
                elif cell.column == "B" and cell.internal_value:
                    data_dict["note"].append(cell.internal_value.lower())
                else:
                    if all(c != cell_color for c in COLORS["no_fill"]) and cell.internal_value:
                        data_dict[(cell.column, "parts")].append(cell.internal_value)
                if any(c == cell_color for c in COLORS["no_fill"]) \
                        and not cell.internal_value and cell.column == "D":
                    if ("C", "parts") in data_dict:
                        spec_type = key_normalize(mode(data_dict['spec_type']))
                        self.all_spec_sentences[spec_type].append(SpecSentence(data_dict))
                        data_dict = defaultdict(list)

    def generate_spec_sentences(self):
        if not self.all_spec_sentences:
            return ""
        main_specs = list(copy.deepcopy(self.main_specs))
        random.shuffle(main_specs)
        types = None
        for spec in main_specs:
            try:
                types = min_max_spec_sentence(spec)
                break
            except:
                pass
        if not types:
            return ""
        paragraph = list()
        for t in types:
            if key_normalize(t[0]) not in self.all_spec_sentences:
                continue
            spec_obj = get_random_choice(self.all_spec_sentences[key_normalize(t[0])])
            text = spec_obj.generate()
            paragraph.append(text)
        return " ".join(paragraph)


class Doctor(object):
    all = list()
    all_json = list()
    all_new_info = list()
    used_names = set()
    times = defaultdict(list)
    sim_specs = load_similar_specs()

    def __init__(self, doc_dict):
        self.current_dissimilarity = copy.deepcopy(MINIMAL_DISSIMILARITY)
        self.doc_dict = doc_dict
        self.start_dissim_change_time = time.time()
        self.attempts = 0
        self.gen_time = 0
        self.doc_name = self.doc_dict["our"]["name"]
        self.doc_dict["our"]["new_info"] = ""
        if "принимает детей" in self.doc_dict["our"]["info"].lower():
            self.children = True
            self.doc_dict["our"]["admit_children"] = True
        else:
            self.children = False
        if isinstance(self.doc_dict["our"]["specialty"], str):
            self.doc_specs = [self.doc_dict["our"]["specialty"].lower()]
        else:
            self.doc_specs = [d.lower() for d in self.doc_dict["our"]["specialty"]]
        self.doc_specs = set([key_normalize(spec) for spec in self.doc_specs])
        self.doc_specs = remove_similar_specs(self.doc_specs)
        self.good_splits = list()
        self.good_splits_names = list()
        self.get_good_splits_names()
        self.generated_texts = list()
        self.dissimilarity = None
        if self.good_splits_names:
            self.get_split_objects()
        if self.good_splits:
            split = get_random_choice(self.good_splits)
            start_time = time.time()
            while not self.dissimilarity:
                self.new_info = split.generate_sentences(self.doc_specs)
                self.new_info = self.new_info.replace("(ФИО)", self.doc_name)
                self.dissimilarity = self.check_dissimilarity()
                self.attempts += 1
            self.gen_time = time.time() - start_time
            Doctor.all_new_info.append(self.new_info)
            self.doc_dict["our"]["new_info"] = self.new_info
            self.specialization_block = split.generate_specialization()
            spec_sent_block = split.generate_spec_sentences()
            if spec_sent_block:
                self.specialization_block += "\n" + spec_sent_block
            self.doc_dict["our"]["specialization_block"] = self.specialization_block
            # print(self.new_info)
            # print(self.specialization_block)
            # print("="*200)
        Doctor.all.append(self)
        Doctor.all_json.append(self.doc_dict)

    def check_dissimilarity(self, shingle_length=5):
        current_time = time.time()
        all_texts = " ".join(Doctor.all_new_info)
        if len(all_texts) < shingle_length + 1:
            return 100
        if self.new_info:
            dissimilarity = compute_similarity(self.new_info, all_texts, shingle_length=shingle_length)
            if dissimilarity > self.current_dissimilarity:
                return dissimilarity
            else:
                if current_time - self.start_dissim_change_time > DISSIM_CHANGE_TIME:
                    if self.current_dissimilarity > ABS_MINIMAL_DISSIMILARITY:
                        self.current_dissimilarity -= 1
                        self.start_dissim_change_time = time.time()

    def get_good_splits_names(self):
        doc_specs = self.doc_specs
        good_splits = list()
        for k, v in all_splits.items():
            original_doc_specs = copy.deepcopy(doc_specs)
            div_is_good = True
            split_main_specs = set(v.main_specs)
            if len(original_doc_specs - split_main_specs) == len(original_doc_specs):
                div_is_good = False
            # if len(original_doc_specs - v.secondary_specs) == len(original_doc_specs):
            #     div_is_good = False
            if div_is_good:
                good_splits.append(k)
        self.good_splits_names = good_splits

    def get_split_objects(self):
        for split_name in self.good_splits_names:
            if split_name in all_splits:
                self.good_splits.append(all_splits[split_name])
