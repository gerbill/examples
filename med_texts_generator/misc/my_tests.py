from settings import *


output_doctors_json = "../output_data/doctors.json"
doctors_with_texts_json = "temp_data/doctors.json"
doctors_output_texts = "temp_data/doctors.txt"


def load_json_file(json_file):
    with open(json_file, "r") as f:
        json_file_data = json.loads(f.read())
    return json_file_data


def show_nth_element_in_json(json_file_path, el_num=11):
    doc_json = load_json_file(json_file_path)
    for doc in doc_json:
        print(doc["name"], doc["our"]["specialty"], doc["our"]["new_info"])
    # for doc in doc_json[el_num - 1:el_num]:
    #     pp(doc, width=1000)


def print_doctors_texts(file_path):
    with open(doctors_output_texts, "w") as f:
        f.write("")
    json_data = load_json_file(file_path)
    for doctor in json_data:
        doc_name = doctor["name"]
        doc_spec = doctor["our"]["specialty"]
        doc_gen_text = doctor["our"]["new_info"]
        if doc_gen_text:
            with open(doctors_output_texts, "a") as f:
                f.write(doc_name + " [" + ", ".join(doc_spec) + "] " + doc_gen_text + "\n")


# print_doctors_texts(doctors_with_texts_json)
print_doctors_texts(output_doctors_json)
