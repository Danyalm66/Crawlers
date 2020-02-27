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
import locale

class WalterspeopleSpider(scrapy.Spider):
    name = 'walterspeople'
    start_urls = ['https://www.walterspeople.fr/offres-d-emploi.html?q=']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(WalterspeopleSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  
        # locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

    def parse(self, response):
        for offer_link in response.css('div.search-result div.search-result-readmore a::attr(href)').extract():
            yield scrapy.Request(response.urljoin(offer_link), callback=self.extract_offer_data)

        next_page_url = response.css('div.searchResults-pagination li.is-active + li a::attr(href)').extract_first()
        if next_page_url:
            yield scrapy.Request(response.urljoin(next_page_url))

    def extract_offer_data(self,response):
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('div.job-advert-title h2::text').extract_first('').strip()
        item['url']=response.url
        item['date']=response.css('p.job-advert-attribute-date-posted span.job-advert-attribute-value::text').extract_first('').strip()
        # item['date']=datetime.strptime(item['date'], '%d %B %Y')
        item['contractKind']=self.crawlerFunction.get_contract_kind(None)
        item['location']=response.css('p.job-advert-attribute-location span.job-advert-attribute-value::text').extract_first('').strip()
        item['sector']=''
        item['reference']=response.css('p.job-advert-attribute-jobref span.job-advert-attribute-value::text').extract_first('').split(':')[-1].strip()
        item['remuneration']=response.xpath('//span[contains(text(), "Salaire")]/following-sibling::span/text()').extract_first('').strip()
        item['company']= 'Walters People'
        item['jobKind']=self.crawlerFunction.get_job_kind(None)
        item['description']=u"<br>".join(response.css('div[itemprop="description"]').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    