from settings import *
from base.utils import *
from base.classes import *

if __name__ == '__main__':
    # CategoryPage.scrape_all()  # scraped! Results in scraped_data/product_urls.txt
    # ProductPage.scrape_all()  # scraped! Results in scraped_data/htmls.csv
    DataExtractor.extract_all()
    with open(ALL_DATA_JSON, "w") as f:
        f.write(json.dumps(DataExtractor.all_data))
    pass
