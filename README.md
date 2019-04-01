# MeituanSpider
美团爬虫，基于scrapy_redis,学习使用，请勿用于商业用途。（目前实现板块：美食板块）


## 美食板块
根据地点爬取美食板块所有商家信息，保存至mongoDB数据库
### 配置信息
- CITY: 爬取的城市，列表类型，可传入城市名或城市id。 (城市名与id对应关系文件：spiders/data/meishi_city.json)
- LOG_LEVEL: 设置日志等级，自定义。
- SCHEDULER_PERSIST: 传入True设置爬虫为增量爬虫，否则False。 
- REDIS_URL: 连接redis数据库的地址。
- DOWNLOAD_DELAY: 设置请求的时间间隔，默认2.2秒到2.6秒之间，可自行调整。

其他设置请参考scrapy官方文档。

### 版本信息
python (3.6.3)<br>
Scrapy (1.5.1)<br>
scrapy-redis (0.6.8)<br>
pymongo (3.7.1)

### 启动
首次启动需要向 redis_key 中传入起始 url

redis 数据库中：
```
select 0
lpush meishi_start_urls https://meishi.meituan.com/i/?ci=45&stid_b=1&cevent=imt/homepage/category1/1
```
终端运行爬虫：
```
scrapy crawl meishi
```

### 注意事项
- 保存的信息分为两大块：商家信息和评论信息。

    评论信息默认不爬取（分布式可以开启，本人就一台电脑，速度太慢- -），如需开启爬取评论信息功能将相关代码注释取消即可。
 
- 爬取过程中可能出现验证码。

    目前处理方式为手动验证：<br>
    - 验证码出现后程序暂停20秒，打开出现验证码的url，手动输入验证

    有条件的话建议处理方式：
    - 接入打码平台
    - 使用代理
