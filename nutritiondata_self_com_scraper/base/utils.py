from settings import *


def rget(url, retries=10, timeout=20, check_string=None, use_proxy=False):
    for i in range(retries):
        try:
            if use_proxy:
                proxy = Proxy.get_random()
                r = requests.get(url, headers=HEADERS, timeout=timeout, proxies=proxy)
            else:
                r = requests.get(url, headers=HEADERS, timeout=timeout)
            source = r.text
            if not has_failure(source, check_string):
                return r
            else:
                print("Page didn't pass failure check. See", FAILED_HTMLS_DIR, "for latest failed pages")
        except Exception as exc:
            print("Failed to get", url, exc)
            time.sleep(1)


def x_first(tree, xpath):
    elements = tree.xpath(xpath)
    if len(elements):
        return elements[0].strip()
    else:
        return "None"


def get_category_urls():
    with open(TOP_MENU_FILE, "r") as f:
        ids = [l.strip().split('", "')[1] for l in f.readlines()]
    urls = [BASE_CATEGORY_URL.format(i) for i in ids]
    return urls


def has_failure(source, check_string=None):
    if not check_string:
        return False
    if check_string in source:
        return False
    else:
        with open(FAILED_HTMLS_DIR + str(int(time.time())), "w") as f:
            f.write(source)
        return True


def get_product_pages_urls_from_file():
    if not os.path.isfile(PRODUCT_URLS_LIST_FILE):
        with open(PRODUCT_URLS_LIST_FILE, "w") as f:
            f.write("")
    with open(PRODUCT_URLS_LIST_FILE, "r") as f:
        return [line.strip() for line in f.readlines() if line.strip()]


def save_product_pages_urls_to_file(urls_list):
    former_urls = get_product_pages_urls_from_file()
    urls = former_urls + urls_list
    urls = sorted(list(set(urls)))
    with open(PRODUCT_URLS_LIST_FILE, "w") as f:
        f.write("\n".join(urls))


def load_csv_with_htmls():
    with open(HTML_DATA_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if CSV_DELIMITER in line and PRODUCT_PAGE_CHECK_STR in line:
                line = line.split(CSV_DELIMITER)
                yield line


def clean_column_name(string):
    string = string.lower()
    for char in ILLEGAL_PSQL_CHARS:
        for i in range(2):
            string = string.replace(char, "_")
    return string


class Proxy(object):
    all = list()
    alive = list()

    def __init__(self, p_init):
        self.p = p_init
        self.host = self.p[2]
        self.port = self.p[3]
        self.login = self.p[0]
        self.password = self.p[1]
        self.status = 'dead'
        self.proxy_dict = {'http': 'http://{}:{}@{}:{}/'.format(self.login, self.password, self.host, self.port)}
        Proxy.all.append(self)

    def check(self, timeout=3, retries=3):
        for i in range(retries):
            try:
                r = requests.get(CHECK_PROXY_URL, timeout=timeout, proxies=self.proxy_dict)
                if "welcome to dualgrid" in r.text:
                    self.status = 'alive'
                    Proxy.alive.append(self)
                else:
                    self.status = 'dead'
                return None
            except Exception as exc:
                print(exc)
                pass
            self.status = 'dead'

    @staticmethod
    def load():
        with open(PROXY_FILE, "r") as f:
            proxies = [p.strip().split(":") for p in f.readlines() if p]
        for p in proxies:
            Proxy(p)

    @staticmethod
    def check_all():
        pool = Pool(len(Proxy.all))
        result = pool.map(Proxy.check_one, Proxy.all)
        print("{} proxies checked! Alive: {}. Dead: {}".format(
            len(Proxy.all), len(Proxy.alive), len(Proxy.all) - len(Proxy.alive)))

    @staticmethod
    def check_one(proxy):
        proxy.check()

    @staticmethod
    def get_random():
        return random.choice(Proxy.alive).proxy_dict








