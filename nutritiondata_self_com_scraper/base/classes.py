from settings import *
from base.utils import *


class CategoryPage(object):
    all = dict()

    def __init__(self, base_url):
        self.base_url = base_url
        self.all_urls = list()
        self.product_pages_urls = list()
        self.sources = dict()
        self.results_num = 0
        self.pages = 1
        self.get_data()
        CategoryPage.all[self.base_url] = self
        save_product_pages_urls_to_file(self.product_pages_urls)

    def get_data(self):
        first_page_source = rget(self.base_url).text
        tree = html.fromstring(first_page_source)
        self.sources[self.base_url] = first_page_source
        try:
            self.results_num = int(re.findall(r'\d+', x_first(tree, '//h2[@class="resultCount"]/text()'))[0])
        except Exception as exc:
            print("Couldn't get results num on page", self.base_url, exc)
        if self.results_num:
            self.pages = self.results_num // 50 + 1
        if self.pages > 1:
            for i in range(2, self.pages + 1):
                self.all_urls.append(self.base_url.replace(".html", "-{}.html".format(i)))
        for url in self.all_urls:
            source = rget(url, check_string='class="menuaddOptions"').text
            self.sources[url] = source
            time.sleep(0.5)
        for source in self.sources.values():
            tree = html.fromstring(source)
            product_pages_urls = tree.xpath('//td[@class="note2"]/a/@href')
            product_pages_urls = [ROOT_URL + url for url in product_pages_urls]
            self.product_pages_urls = self.product_pages_urls + product_pages_urls

    @staticmethod
    def scrape_all():
        category_pages_urls = get_category_urls()
        for url in category_pages_urls:
            print("Scraping", url)
            CategoryPage(url)


class ProductPage(object):
    all = dict()
    all_urls = list()

    def __init__(self, url):
        self.url = url
        self.source = rget(self.url, use_proxy=True, check_string=PRODUCT_PAGE_CHECK_STR).text.replace("\n", " ")
        self.source = self.source.replace("  ", " ").replace("  ", " ")
        with open("sample.html", "w") as f:
            f.write(self.source)
        self.save_source_to_file()

    def save_source_to_file(self):
        with open(HTML_DATA_FILE, "a") as f:
            f.write(self.url + CSV_DELIMITER + self.source + "\n")

    @staticmethod
    def scrape_all():
        Proxy.load()
        Proxy.check_all()
        ProductPage.all_urls = get_product_pages_urls_from_file()
        threads = len(Proxy.all) // 3
        pool = Pool(threads)
        result = pool.map(ProductPage.worker, range(threads))

    @staticmethod
    def worker(worker_id):
        while len(ProductPage.all_urls) > 0:
            url = ProductPage.all_urls.pop()
            print("Scraping Product Page:", url, " | Left:", len(ProductPage.all_urls))
            ProductPage(url)


class DataExtractor(object):
    all_data = list()

    def __init__(self, url, source):
        self.url = url
        self.source = source
        self.tree = html.fromstring(self.source)
        self.nutrients_raw_data = self.get_nutrients_raw_data()
        self.nutrients_ids = dict()
        self.get_nutrients_ids()
        self.nutrients_data = dict()
        self.set_nutrients_data()
        self.data = dict()
        self.extract_data()
        # pp(self.nutrients_data, width=300)
        DataExtractor.all_data.append(self.nutrients_data)
        print(len(DataExtractor.all_data))


    def extract_data(self):
        tree = self.tree
        d = dict()
        d["name"] = x_first(tree, '//div[@class="facts-heading"]/text()')
        d["url"] = self.url
        d["Fullness Factor"] = x_first(tree, '//span[@class="box_7"]/text()')
        d["ND Rating"] = x_first(tree, '//span[@class="box_8"]/text()')
        d["Carbs"] = x_first(tree, '//td[@class="carbs"]/text()').replace("%", "")
        d["Fats"] = x_first(tree, '//td[@class="fats"]/text()').replace("%", "")
        d["Protein"] = x_first(tree, '//td[@class="protein"]/text()').replace("%", "")
        stars = tree.xpath('//div[@class="rating_on"]/@style')
        stars = [re.search(r'\d+', s).group() for s in stars]
        d["Weight loss"] = stars[0]
        d["Optimum health"] = stars[1]
        d["Weight gain"] = stars[2]
        d["Opinion"] = tree.xpath('//div[@class="opinion_description"]/p')[0].text_content()
        d["Estimated Glycemic Load"] = self.nutrients_raw_data["SCORE_ESTIMATED_GLYCEMIC_LOAD"]
        d["Completeness Score"] = x_first(
            tree, '//fieldset[@id="nutrient-balance-container"]//div[@class="box_PQI"]/text()')
        d["Amino Acid Score"] = x_first(
            tree, '//fieldset[@id="nutrient-balance-container"]//div[@class="box_PQI"]/text()')
        for k, v in d.items():
            self.nutrients_data[k] = v

    def get_nutrients_raw_data(self):
        nutrients_data = re.findall(r'foodNutrients = {([^{}]*)};', self.source)[0]
        nutrients_data = [[item.replace('"', '') for item in el.strip().split(":")] for el in
                          nutrients_data.split('", ')]
        nutrients_data = [el for el in nutrients_data]
        nutrients_data_dict = dict()
        for item in nutrients_data:
            nutrients_data_dict[item[0]] = item[1]
        return nutrients_data_dict

    def get_nutrients_ids(self):
        tree = self.tree
        for row in tree.xpath(r'.//div[@class="clearer"]'):
            name = x_first(row, r'.//div[@class="nf1 left"]/text()')
            if not name:
                name = x_first(row, r'.//div[@class="nf1 left"]//span[@class="indented"]/text()')
            nutrient_id = x_first(row, r'.//div[@class="nf2 left"]/span/@id').replace("NUTRIENT_", "")
            self.nutrients_ids[name] = nutrient_id

    def set_nutrients_data(self):
        for name, nut_id in self.nutrients_ids.items():
            nut_values = dict()
            for raw_name, hr_name in NUT_PROPS.items():
                nut_value_name = raw_name + nut_id
                if nut_value_name in self.nutrients_raw_data:
                    value = self.nutrients_raw_data[nut_value_name]
                    if value == '~':
                        value = None
                    nut_values[hr_name] = value
                else:
                    nut_values[hr_name] = None
            self.nutrients_data[name] = nut_values

    # def set_nutrients_data(self):
    #     for name, nut_id in self.nutrients_ids.items():
    #         nut_values = dict()
    #         for raw_name, hr_name in NUT_PROPS.items():
    #             nut_value_name = raw_name + nut_id
    #             if nut_value_name in self.nutrients_raw_data:
    #                 nut_values[hr_name] = self.nutrients_raw_data[nut_value_name].replace("%", "")
    #                 if nut_value_name[:10] == "NUTRIENT_" and nut_values[hr_name] == '~':
    #                     nut_values[hr_name] = -1
    #             else:
    #                 if "DV_NUTRIENT_" in nut_value_name or nut_value_name[:10] == "NUTRIENT_":
    #                     nut_values[hr_name] = -1
    #                 else:
    #                     nut_values[hr_name] = None
    #         for nv_name, nv_value in nut_values.items():
    #             self.nutrients_data[name + "_" + nv_name] = nv_value

    @staticmethod
    def extract_all():
        for tup in load_csv_with_htmls():
            DataExtractor(tup[0], tup[1])
