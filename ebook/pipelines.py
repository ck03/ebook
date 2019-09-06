# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient
import json
import time
        #
        # time.sleep(70)
        # tEnd = time.time()  # 計時結束
        # print(tEnd - tStart)

class EbookPipeline(object):
    def __init__(self):
        self.client = MongoClient(host="127.0.0.1", port=27017)
        self.collectionpath = self.client["ebook"]["path"]
        self.collectioninfo = self.client["ebook"]["bookinfo"]
        self.err_log = []
        self.result_dict = {}
        self.starttime = time.time()

    def process_item(self, item, spider):
        print(item["title"])
        try:
            self.collectioninfo.insert_one(item)
        except Exception as e:
            # print("Could not connect to server: %s" % e)
            self.err_log.append("{}寫入失敗".format(item))

        return item

    def close_spider(self, spider):
        if len(self.err_log) > 0:
            self.result_dict["Result"] = self.err_log
            with open("ebook_err_log.json", "w", encoding="utf-8") as f:
                f.write(json.dumps(self.result_dict, ensure_ascii=False, indent=2))
        tEnd = time.time()  # 計時結束
        print("共花費:", tEnd - self.starttime, "秒")
        print("<ebook>爬蟲結束....")
