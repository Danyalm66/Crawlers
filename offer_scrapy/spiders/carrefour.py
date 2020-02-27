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

class CarrefourSpider(scrapy.Spider):
    name = 'carrefour'
    start_urls = ['https://recrute.carrefour.fr/liste-des-offres']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(CarrefourSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse_page)

    def parse_page(self,response):
        for href in response.css('div.job-offer-content a.job-offer-desc-title::attr(href)').extract():
            yield scrapy.Request(response.urljoin(href), callback=self.extract_offer_data)

        for next_url in response.css('ul.pagination li.next a::attr(href)').extract():
            yield scrapy.Request(response.urljoin(next_url), callback=self.parse_page)
            break
            
    def extract_offer_data(self,response):
        item=OfferscrawlersItem()
        if "offre-non-trouvee" not in response.url:
            item['status']="new"
            item['offerId']=""
            item['companyId']=""
            item['title']=response.css('h1.job-offer-intro-title::text').extract_first('').strip()
            item['url']=response.url
            item['date']=response.xpath('//div[contains(text(), "%s")]/span[@class="label-desc-txt"]/text()' %u"Publiée le").extract_first('').strip()
            item['date']=datetime.strptime(item['date'], '%d/%m/%y')
            item['contractKind']=response.css('div.contrat-type span.type-txt::text').extract_first('')
            item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
            item['location']=response.css('div.contrat-place span.type-txt-place::text').extract_first('').strip()
            item['sector']=''
            item['reference']=response.url.split('/offre/')[-1].split('-')[0].strip()
            item['remuneration']=''
            item['company']=response.css('section#job-place h1.article-title::text').extract_first('').strip()
            item['jobKind']=response.css('div.contrat-type span.type-txt::text').extract_first('').strip()
            item['jobKind']=self.crawlerFunction.get_job_kind(item['jobKind'])
            item['description'] = u"<br>".join(response.css('div.desc-content').extract())
            item['description'] = self.crawlerFunction.html2text(item['description'])
            item['skills']=self.crawlerFunction.get_skills(item['description']) 
            item['provider']=self.name
            item['domain']=self.domain
            item['uid']=self.name + '-' + item['reference']    
            yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    