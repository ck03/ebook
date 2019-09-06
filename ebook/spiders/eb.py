# -*- coding: utf-8 -*-
import scrapy
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError
from copy import deepcopy
from pymongo import MongoClient
from ebook.items import EbookItem
import re
import datetime as dt
import time


class EbSpider(scrapy.Spider):
    name = 'eb'
    allowed_domains = ['www.zhuishubang.com']
    start_urls = ['https://www.zhuishubang.com/3911/']

    def __init__(self):
        super(EbSpider, self).__init__()
        self.client = MongoClient(host="127.0.0.1", port=27017)
        self.collectionpath = self.client["ebook"]["path"]
        self.collectioninfo = self.client["ebook"]["bookinfo"]
        self.domainname = "https://www.zhuishubang.com"
        self.bookid = "3911"
        self.snum = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "百", "两", "零", "千"]
        self.sint = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
        self.today = dt.date.today()
        self.booktitle = []
        self.checkdb(self.bookid)

    def checkdb(self, bookid):
        dbtitle = self.collectioninfo.find({"book_id": "{}".format(bookid)})
        if dbtitle.count() > 0:
            for t in dbtitle:
                self.booktitle.append(t["title"])
        # print(dbtitle.count())
        # print(self.booktitle)

    def changenum(self, chapternum):
        numlength = 1
        ch = list(chapternum)
        set1 = set(self.snum)
        set2 = set(ch)
        set3 = set1.intersection(set2)
        # print(set3)
        # print(ch)
        if "百" in ch:
            numlength = 3
        if "千" in ch:
            numlength = 4
        else:
            if len(chapternum) == 2 and numlength != 3:
                numlength = 2
            if len(chapternum) == 3 and numlength != 3:
                numlength = 2
        # print(numlength)
        sint = ""
        if len(set3) > 0:
            for i in ch:
                if i == "千" or i == "百":
                    continue
                if i == "零":
                    i = "0"
                if i == "两":
                    i = "2"
                sint += i
            if numlength == 2 and sint[0] == "十":  # 十一
                sint = sint.replace("十", "1")
            if numlength == 3 and len(sint) == 1:  # 三百
                sint += "00"
            if numlength == 3 and len(sint) == 4:  # 九百九十九
                sint = sint.replace("十", "")
            if numlength == 4 and len(sint) == 1:  # 一千
                sint += "000"
            if numlength == 4 and len(sint) == 2:  # 一千一百
                sint += "00"
            if numlength == 4 and len(sint) == 3:  # 一千零三
                sint = sint[0] + "0" + sint[1:]
            if numlength == 4 and len(sint) == 5:  # 一千零一十五
                sint = sint.replace("十", "")
            if numlength == 2 and len(sint) == 3:  # 一十二
                sint = sint.replace("十", "")

            # print(sint)
            rsint = ""
            bolt = False
            for i in list(sint):
                for index, j in enumerate(self.snum):
                    if i == j:
                        rsint += self.sint[index]
                        bolt = True
                        break
                if not bolt:
                    rsint += i
                else:
                    bolt = False
            if rsint == "0":
                rsint = "10"
            # print(rsint)
            return rsint
        else:
            return chapternum

    def parse(self, response):
        print("<ebook>爬蟲開始....")

        # return
        # self.changenum("二十一")
        # return
        li_list = response.xpath("//div[@class='contentDiv']//div[@class='chapterCon']/ul/li")

        for li in li_list:  # TODO 先選幾章來測試
            item = EbookItem()
            item["title"] = li.xpath("./a/text()").extract_first()
            if item["title"] not in self.booktitle:  # 表示尚未下載
                item["chapter_url"] = self.domainname + li.xpath("./a/@href").extract_first()
                sid = re.search("第(.*?)章", item["title"])
                item["sid"] = self.changenum(sid[1]) if sid is not None else "A" + item["chapter_url"].split("/")[-1].split(".")[0]
                item["book_id"] = self.bookid
                item["date"] = str(self.today)
                yield scrapy.Request(
                    item["chapter_url"],
                    errback=self.errback_httpbin,
                    dont_filter=True,
                    callback=self.parse_content,
                    meta={"item": deepcopy(item)}
                )

    def parse_content(self, response):
        item = deepcopy(response.meta["item"])
        content_list = response.xpath("//div[@class='readerDiv']/div[@class='readerCon']/div[@class='articleCon']/p/text()").extract()
        content = []
        for c in content_list:
            c = c.replace("\xa0", "")
            content.append(c)
        item["content"] = content
        yield deepcopy(item)

    def errback_httpbin(self, failure):
        # log all errback failures,
        # in case you want to do something special for some errors,
        # you may need the failure's type
        # print(repr(failure))
        # if isinstance(failure.value, HttpError):
        if failure.check(HttpError):
            # you can get the response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

            # elif isinstance(failure.value, DNSLookupError):
        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

            # elif isinstance(failure.value, TimeoutError):
        elif failure.check(TimeoutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
