# -*- coding: utf-8 -*-
import scrapy
import re
import time
import json
import logging
from ..items import MeishiCommentItem, MeishiInfoItem
from copy import deepcopy
from scrapy_redis.spiders import RedisSpider
from ..settings import CITY


class MeishiSpider(RedisSpider):
    name = 'meishi'
    allowed_domains = ['meituan.com']
    # start_urls = ['https://meishi.meituan.com/i/?ci=45&stid_b=1&cevent=imt/homepage/category1/1']
    redis_key = 'meishi:start_urls'

    def parse(self, response):
        uuid = re.findall(r'"uuid":"(.*?)"', response.body.decode(), re.S)[0]

        city_id_list = []
        with open('MeituanSpider/spiders/data/meishi_city.json') as f:
            ret_list = json.load(f)
            for ret in ret_list:
                city_id_list.append(ret['id'])

        list_url = 'https://meishi.meituan.com/i/api/channel/deal/list'
        headers = {
            'x-requested-with': 'XMLHttpRequest',
            'Referer': 'https://meishi.meituan.com/i/?ci=30&stid_b=1&cevent=imt%2Fhomepage%2Fcategory1%2F1',
        }

        for city in CITY:
            if re.findall(r'\d+', str(city)):
                if city in city_id_list:
                    ci = city
                else:
                    print('目标城市（或城市ID）无效：{}'.format(city))
                    continue
            else:
                with open('MeituanSpider/spiders/data/meishi_city.json') as f:
                    city_id = re.findall(r'{"id": (\d+), "name": "%s"}' % city, f.read(), re.S)
                    if city_id:
                        ci = city_id[0]
                    else:
                        print('目标城市（或城市ID）无效：{}'.format(city))
                        continue

            cookies = {
                'uuid': uuid,
                'ci': ci  # 城市代号
            }

            data = {
                "app": "",
                "areaId": '0',  # 区域id
                "cateId": '1',
                "deal_attr_23": "",
                "deal_attr_24": "",
                "deal_attr_25": "",
                "limit": '50',  # 每次获取数据的个数
                "lineId": '0',
                "offset": '0',  # 获取数据的坐标
                "optimusCode": '10',
                "originUrl": "http://meishi.meituan.com/i/?ci={}&stid_b=1&cevent=imt%2Fhomepage%2Fcategory1%2F1".format(
                    ci),
                "partner": '126',
                "platform": '3',
                "poi_attr_20033": "",
                "poi_attr_20043": "",
                "riskLevel": '1',
                "sort": "default",
                "stationId": '0',
                "uuid": uuid,
                "version": "8.2.0"
            }

            # 解析区域代号
            area_list = re.findall(r'"areaObj":(.*?),"subAreaList"', response.body.decode(), re.S)[0]
            area_id_list = re.findall(r'"id":(\d+),.*?"count":\d+', area_list, re.S)
            count_list = re.findall(r'"id":\d+,.*?"count":(\d+)', area_list, re.S)
            for area_id in area_id_list[:1]:
                count = count_list[area_id_list.index(area_id)]
                yield scrapy.FormRequest(
                    url=list_url,
                    formdata=data,
                    cookies=cookies,
                    headers=headers,
                    callback=self.parse_item,
                    meta={
                        'data': deepcopy(data),
                        'cookies': cookies,
                        'headers': headers,
                        'count': deepcopy(count),
                        'area_id': deepcopy(area_id),
                        'url': deepcopy(list_url)
                    },
                    dont_filter=True
                )

    def parse_item(self, response):  # 提取商家信息
        data = response.meta['data']
        area_id = response.meta['area_id']
        data['areaId'] = str(area_id)
        cookies = response.meta['cookies']
        count = response.meta['count']
        headers = response.meta['headers']
        print('areaId:', data['areaId'], ', offset:', data['offset'], ', count:', count)
        ret = json.loads(response.body)
        # 判断是否请求成功
        try:
            if ret['status'] == 0:
                # 判断是否存在数据
                if ret['data']['poiList']['totalCount'] != 0:
                    info_list = ret['data']['poiList']['poiInfos']
                    for info in info_list:
                        item = MeishiInfoItem()
                        item["avgPrice"] = info['avgPrice']
                        item["avgScore"] = info['avgScore']
                        item["cateName"] = info['cateName']
                        item["channel"] = info['channel']
                        item["showType"] = info['showType']
                        item["frontImg"] = info['frontImg']
                        item["lat"] = info['lat']
                        item["lng"] = info['lng']
                        item["name"] = info['name']
                        item["poiId"] = info['poiid']
                        item["areaName"] = info['areaName']
                        item["iUrl"] = info['iUrl']
                        item["ctPoi"] = info['ctPoi']
                        # 更多信息
                        detail_url = 'https://meishi.meituan.com/i/poi/{}?ct_poi={}'.format(item['poiId'], item['ctPoi'])
                        detail_headers = {
                            'Referer': 'https://meishi.meituan.com/i/?ci=45&stid_b=1&cevent=imt%2Fhomepage%2Fcategory1%2F1',
                        }
                        yield scrapy.Request(
                            url=detail_url,
                            callback=self.parse_detail_item,
                            headers=detail_headers,
                            meta={'item': deepcopy(item), 'headers': detail_headers, 'url': detail_url},
                        )

                        # # 请求评论页(如不需要评论信息请注释此部分)
                        # comment_headers = {
                        #     'Referer': 'https://meishi.meituan.com/i/poi/{}?ct_poi={}'.format(item['poiId'], item['ctPoi']),
                        #     'Host': 'i.meituan.com'
                        # }
                        # comment_url = 'https://i.meituan.com/poi/{}/feedbacks'.format(item['poiId'])
                        # yield scrapy.Request(
                        #     url=comment_url,
                        #     headers=comment_headers,
                        #     cookies=cookies,
                        #     callback=self.parse_comment,
                        #     meta={'headers': comment_headers}
                        # )

                    # 请求下一页
                    offset = int(data['offset'])
                    offset += 50
                    if offset < int(count):
                        data['offset'] = str(offset)
                        yield scrapy.FormRequest(
                            url=response.url,
                            formdata=data,
                            headers=headers,
                            cookies=cookies,
                            callback=self.parse_item,
                            meta={
                                'data': data,
                                'cookies': cookies,
                                'headers': headers,
                                'count': count,
                                'area_id': area_id,
                                'url': deepcopy(response.url)
                            },
                            dont_filter=True
                        )
            else:
                # 重新请求
                logging.debug('重新请求：' + response.url + '[offset={}]'.format(data['offset']))
                yield scrapy.FormRequest(
                    url=response.url,
                    formdata=data,
                    headers=headers,
                    cookies=cookies,
                    callback=self.parse_item,
                    meta={
                        'data': data,
                        'cookies': cookies,
                        'headers': headers,
                        'count': count,
                        'area_id': area_id,
                        'url': deepcopy(response.url)
                    },
                    dont_filter=True
                )
        except:
            # TODO: 验证码处理（以下为临时处理办法，可接入打码平台或自己破解 - -）
            url = response.meta['url']
            print('出现验证码！url:', url)
            time.sleep(20)  # 登陆网站手动输入验证码
            # 重新请求
            yield scrapy.FormRequest(
                url=url,
                formdata=data,
                headers=headers,
                cookies=cookies,
                callback=self.parse_item,
                meta={
                    'data': data,
                    'cookies': cookies,
                    'headers': headers,
                    'count': count,
                    'area_id': area_id,
                    'url': deepcopy(url)
                },
                dont_filter=True
            )

    def parse_detail_item(self, response):  # 提取更多信息
        item = response.meta['item']
        headers = response.meta['headers']
        try:
            ret = re.findall(r'"pvLab"(.*?)"originUrl"', response.body.decode(), re.S)[0]
            item['wifi'] = re.findall(r'"wifi":(.*?),', ret, re.S)[0]
            item['addr'] = re.findall(r'"addr":"(.*?)",', ret, re.S)[0]
            item['phone'] = re.findall(r'"phone":"(.*?)",', ret, re.S)[0]
            yield item
        except:
            # TODO: 验证码处理（以下为临时处理办法，可接入打码平台或自己破解 - -）
            detail_url = response.meta['url']
            print('出现验证码！url:', detail_url)
            time.sleep(20)  # 登陆网站手动输入验证码
            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail_item,
                headers=headers,
                meta={'item': item, 'headers': headers, 'url': detail_url},
            )

    def parse_comment(self, response):  # 提取评论数据
        comment_info_list = response.xpath('//dd[@class="dd-padding"]')
        if len(comment_info_list):
            for comment_info in comment_info_list:
                item = MeishiCommentItem()
                item['poiId'] = re.findall(r'/(\d+)/', response.url)[0]
                item['avatar'] = comment_info.xpath('//div[@class="imgbox"]/@data-src').extract_first()
                item['userName'] = comment_info.xpath('.//weak[@class="username"]/text()').extract_first()
                item['star'] = len(comment_info.xpath('.//i[@class="text-icon icon-star"]').extract())
                item['publishDate'] = comment_info.xpath('.//weak[@class="time"]/text()').extract_first()
                item['comment'] = ''.join([i.strip() for i in comment_info.xpath('.//div[@class="comment"]//p//text()').extract()])
                item['comment_imgs'] = comment_info.xpath('.//div[@class="pics"]/span/@data-src').extract()
                yield item

            # 翻页
            if len(re.findall(r'/page_\d+', response.url)):
                page = re.findall(r'/page_(\d+)', response.url)[0]
                next_url = re.sub(r'/page_(\d+)', '/page_' + str(int(page) + 1), response.url)
            else:
                next_url = response.url + '/page_2'
            headers = response.meta['headers']
            yield scrapy.Request(
                url=next_url,
                headers=headers,
                callback=self.parse_comment,
                meta={'headers': headers}
            )



