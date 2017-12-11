from settings import *
from base.utils import *

for tup in load_csv_with_htmls():
    source = tup[1]
    tree = html.fromstring(source)
    header = tree.xpath('//div[@class="facts-heading"]/text()')
    print(header)