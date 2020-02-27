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

class LejobadequatSpider(scrapy.Spider):
    name = 'lejobadequat'
    start_urls = ['https://www.lejobadequat.com/emplois']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(LejobadequatSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def parse(self, response):
        second_request = response.meta.get('second_request', 0)
        if second_request == 1:
            for offer_link in response.css('article.job a::attr(href)').extract():
                yield scrapy.Request(offer_link, callback=self.extract_offer_data)

        if second_request == 0:
            total_offer = int(response.css('div.blocAccrocheReassuranceWrapper_reassurance_count a span::text').extract_first('').strip())
            total_page = 1
            if total_offer % 12:
                total_page = total_offer / 12
            else:
                total_page = total_offer / 12 + 1
            list_offer_url = 'https://www.lejobadequat.com/emplois/?fwp_load_more={0}'.format(total_page)
            yield scrapy.Request(list_offer_url, meta={'second_request': 1})
            
    def extract_offer_data(self,response):
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('div.pageHeader_secteur + h1::text').extract_first('').strip()
        item['url']=response.url
        item['date']=datetime.now()
        item['contractKind']=response.xpath('//div[contains(@class, "pageHeader_secteur")]/following-sibling::div[contains(@class, "job_meta")]//i[@class="icon-shaking-hands"]/following-sibling::text()').extract_first('').strip()
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=response.xpath('//div[contains(@class, "pageHeader_secteur")]/following-sibling::div[contains(@class, "job_meta")]//i[@class="icon-marker"]/following-sibling::text()').extract_first('').split('(')[0].strip()
        item['sector']=response.css('div.pageHeader_secteur div.job_secteur_infos > div.job_secteur_title::text').extract_first('').strip()
        item['reference']=response.css(u'div.pageHeader_secteur div.job_secteur_ref').extract_first('').split(':')[-1].strip()
        item['remuneration']=''
        item['company']=response.css('div.pageHeader_agenceNavWrapper div.agenceLink_title::text').extract_first('').strip()
        item['jobKind']=self.crawlerFunction.get_job_kind(None)
        item['description'] = u"<br>".join(response.css('div.section.job_content').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    