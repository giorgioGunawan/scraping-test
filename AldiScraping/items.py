# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class AldiscrapingItem(scrapy.Item):
    product_title = scrapy.Field()
    product_image = scrapy.Field()
    product_category = scrapy.Field()
    product_price = scrapy.Field()
    product_ppu = scrapy.Field()
    product_packsize = scrapy.Field()
    pass
