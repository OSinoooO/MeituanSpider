# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient
from .items import MeishiCommentItem, MeishiInfoItem


class MeishiPipeline(object):
    """保存美食商家及评论信息"""

    def __init__(self):
        self.client = MongoClient()

    def process_item(self, item, spider):
        if isinstance(item, MeishiInfoItem):
            collection = self.client['MeiTuan']['meishi_info']
            if not collection.find_one({'poiId': item['poiId']}):  # 数据去重
                collection.insert_one(item)
                return item

        if isinstance(item, MeishiCommentItem):
            collection = self.client['MeiTuan']['meishi_comment']
            if not collection.find_one({'poiId': item['poiId'], 'publishDate': item['publishDate'], 'comment': item['comment']}):
                collection.insert_one(item)
                return item

    def close_spider(self, spider):
        self.client.close()



