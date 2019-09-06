# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class EbookItem(scrapy.Item):
    # define the fields for your item here like:
    sid = scrapy.Field()
    title = scrapy.Field()
    book_id = scrapy.Field()
    content = scrapy.Field()
    date = scrapy.Field()
    chapter_url = scrapy.Field()
    _id = scrapy.Field()

