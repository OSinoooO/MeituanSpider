# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import scrapy


class MeishiInfoItem(scrapy.Item):  # 美食商家信息
    _id = scrapy.Field()
    avgPrice = scrapy.Field()
    avgScore = scrapy.Field()
    cateName = scrapy.Field()
    channel = scrapy.Field()
    showType = scrapy.Field()
    frontImg = scrapy.Field()
    lat = scrapy.Field()
    lng = scrapy.Field()
    name = scrapy.Field()
    poiId = scrapy.Field()
    areaName = scrapy.Field()
    iUrl = scrapy.Field()
    ctPoi = scrapy.Field()
    wifi = scrapy.Field()
    addr = scrapy.Field()
    phone = scrapy.Field()


class MeishiCommentItem(scrapy.Item):  # 美食评论信息
    _id = scrapy.Field()
    poiId = scrapy.Field()
    avatar = scrapy.Field()
    userName = scrapy.Field()
    star = scrapy.Field()
    publishDate = scrapy.Field()
    comment = scrapy.Field()
    comment_imgs = scrapy.Field()
