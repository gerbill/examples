from settings import *


class Proxy(object):
    all = list()
    alive = list()

    def __init__(self, p_init):
        self.p = p_init
        self.host = self.p[0]
        self.port = self.p[1]
        self.login = self.p[2]
        self.password = self.p[3]
        self.status = 'dead'
        self.proxy_dict = {'http': 'http://{}:{}@{}:{}/'.format(self.login, self.password, self.host, self.port)}
        self.proxy_dict['https'] = self.proxy_dict['http']
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
    def load_and_check():
        Proxy.all = list()
        Proxy.alive = list()
        with open(PROXY_FILE, "r") as f:
            proxies = [p.strip().split(":") for p in f.readlines() if p]
        if not proxies:
            raise EnvironmentError("No proxies in {}".format(PROXY_FILE))
        for p in proxies:
            Proxy(p)
        Proxy.check_all()

    @staticmethod
    def check_all():
        pool = Pool(len(Proxy.all) // 10)
        pool.map(Proxy.check_one, Proxy.all)
        print("{} proxies checked! Alive: {}. Dead: {}".format(
            len(Proxy.all), len(Proxy.alive), len(Proxy.all) - len(Proxy.alive)))
        if len(Proxy.alive) == 0:
            raise EnvironmentError("Cannot continue - no alive proxies!")

    @staticmethod
    def check_one(proxy):
        proxy.check()

    @staticmethod
    def get_random():
        return random.choice(Proxy.alive).proxy_dict

    @staticmethod
    def test_proxies(threads=100):
        Proxy.load_and_check()
        pool = Pool(threads)
        pool.map(Proxy.test_proxies_worker, list(range(threads)))

    @staticmethod
    def test_proxies_worker(w_id):
        test_url = "http://dualgrid.com/ping2.php"
        while True:
            try:
                proxy = Proxy.get_random()
                r = requests.get(test_url, timeout=10, proxies=proxy)
                print("ok")
            except Exception as exc:
                print(exc)


def rget(url, timeout=20, retries=10, use_proxy=True):
    time.sleep(TIMEOUT)
    for i in range(retries):
        try:
            if use_proxy:
                proxy = Proxy.get_random()
                r = requests.get(url, headers=HEADERS, timeout=timeout, proxies=proxy)
                if "You're making too many requests to Yandex Maps API Service" in r.text:
                    print("banned proxy", proxy, url)
            else:
                r = requests.get(url, headers=HEADERS, timeout=timeout)
            return r
        except Exception as exc:
            print("Failed to get", url, exc)
            time.sleep(FAILURE_TIMEOUT)


def get_yandex_geocoder(word, use_proxy=True):
    word = word.lower()
    url = YANDEX_GEOCODER_BASE_URL.format(word)
    json_string = rget(url, use_proxy=use_proxy).text
    geocoder_dict = json.loads(json_string)
    return geocoder_dict


def get_address(word, retries=3):
    try:
        gd = get_yandex_geocoder(word, use_proxy=True)
        found = int(gd['response']['GeoObjectCollection']['metaDataProperty']['GeocoderResponseMetaData']['found'])
        addresses = list()
        if found:
            for obj in gd['response']['GeoObjectCollection']['featureMember']:
                props = obj['GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']['Components']
                province = {prop['name'].lower() for prop in props if prop['kind'] == 'province'}
                if "москва" in province:
                    address = obj['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
                    if address:
                        addresses.append(address)
    except:
        pp(gd, width=300)
        addresses = list()
        time.sleep(FAILURE_TIMEOUT)
    if addresses:
        return " ... ".join(addresses)
    else:
        return ""


def remove_trash_chars(string, trash_chars=TRASH_CHARS, make_lower=True):
    if make_lower:
        string = string.lower()
    for i in range(2):
        for rem, repl in trash_chars.items():
            string = string.replace(rem, repl)
    return string


def get_word_tag(word):
    word = word.lower()
    morph = MORPH.parse(word)[0]
    raw_tag = morph.tag.__str__().split(",")[0].split(" ")[0]
    return raw_tag


def append_to_csv(row_as_list, csv_path, delimiter=";"):
    try:
        row_as_list = [str(cell) for cell in row_as_list]
        row = delimiter.join(row_as_list)
        row = remove_trash_chars(row, trash_chars=TRASH_CHARS_FOR_OUTPUT, make_lower=False)
        with codecs.open(csv_path, "a", encoding="utf-8") as f:
            f.write(row + "\n")
    except Exception as exc:
        print("was unable to write to", csv_path, exc)
