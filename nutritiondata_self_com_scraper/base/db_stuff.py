from settings import *

conn_params = "dbname='nut_scraping' user='postgres' host='localhost' password='postgres'"


def create_table():
    columns_list_file = "../db_columns.json"
    with open(columns_list_file, "r") as f:
        columns_list = json.loads(f.read())
    conn = psycopg2.connect(conn_params)
    cur = conn.cursor()
    columns_str = ""
    for k, v in columns_list.items():
        if v == "str":
            columns_str = columns_str + "_" + k + " VARCHAR (200), "
        else:
            columns_str = columns_str + "_" + k + " INT, "

    sql = "CREATE TABLE test ({});".format(columns_str)
    sql = sql.replace(", )", ")")
    print(sql)
    cur.execute(sql)
    conn.commit()
    conn.exit()


def insert_row(data_dict):
    conn = psycopg2.connect(conn_params)
    cur = conn.cursor()