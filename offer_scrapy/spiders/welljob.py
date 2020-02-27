# -*- coding: utf-8 -*-
import scrapy
import logging
from urlparse import urlparse
from offer_scrapy.items import OfferscrawlersItem
from scrapy import signals
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import FormRequest
from  offer_scrapy.commonfunctions import CrawlersFunctions
import json
from urlparse import urlparse
from datetime import datetime
import re
import math

class WelljobSpider(scrapy.Spider):
    name = 'welljob'
    start_urls = ['https://www.welljob.fr/rechercher?what=&where=']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(WelljobSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def parse(self, response):
        second_request = response.meta.get('second_request', 0)
        if second_request == 1:
            for offer_link in response.css('div.annonce-search > a::attr(href)').extract():
                yield scrapy.Request(offer_link, callback=self.extract_offer_data)
        else:
            total_offer = int(response.css('div.annonce-result h3 span::text').extract_first('').strip())
            total_page = int(math.ceil(total_offer / 15))
            list_offer_url = 'https://www.welljob.fr/rechercher?type=&category_id=&city=&place_id=&what=&where=&page={0}'.format(total_page)
            yield scrapy.Request(list_offer_url, meta={'second_request': 1})

    def extract_offer_data(self,response):
        _xpath = u'//i[contains(@class, "{0}")]/following-sibling::text()'
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('div.annonce-content h1::text').extract_first('').strip()
        item['url']=response.url
        item['date']=response.xpath(_xpath.format('fa-calendar-alt')).extract_first('').strip()
        item['date']=datetime.strptime(item['date'], '%d/%m/%Y')
        item['contractKind']=response.xpath(_xpath.format('fa-tags')).extract_first('').strip()
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=response.xpath(_xpath.format('fa-map-marker-alt')).extract_first('').strip()
        item['sector']=response.xpath(_xpath.format('fa-folder-open')).extract_first('').strip()
        item['reference']=response.css('p.annonce-reference::text').extract_first('').split(':')[-1].strip()
        item['remuneration']=response.xpath(_xpath.format('fa-euro-sign')).extract_first('').strip()
        item['company']= response.css('div.annonce-information h2::text').extract_first('').strip()
        item['jobKind']=self.crawlerFunction.get_job_kind(None)
        item['description']=u"<br>".join(response.xpath('//h2[contains(text(), "A propos du poste")]/../following-sibling::div[1]').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    