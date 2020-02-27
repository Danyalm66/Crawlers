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

class BuffaloGrillSpider(scrapy.Spider):
    name = 'buffalo_grill'
    start_urls = ['http://recrutement.buffalo-grill.com/jobsearch/offers']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(BuffaloGrillSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def parse(self, response):
        for offer_link in response.css('ul.mj-offers-list li a.block-link::attr(href)').extract():
            yield scrapy.Request(response.urljoin(offer_link), callback=self.extract_offer_data)

        next_page_url = response.xpath('//ul[@class="pagination-pages"]/li/span/../following-sibling::li[1]/a/@href').extract_first('')
        if next_page_url:
            yield scrapy.Request(response.urljoin(next_page_url))
            
    def extract_offer_data(self,response):
        offer_data = response.css('script[type="application/ld+json"]').extract_first('')
        
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('div.title h1::text').extract_first('').strip()
        item['url']=response.url
        item['date']=offer_data.split('"datePosted":"')[-1].split('T')[0].strip()
        item['date']=datetime.strptime(item['date'], '%Y-%m-%d')
        item['contractKind']='-'.join(response.css('div.matching-criteria ul li > span > span::text').extract())
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=offer_data.split('"addressLocality":"')[-1].split('"')[0].split('(')[0].strip()
        item['sector']=response.xpath('//span[contains(text(), "Secteur :")]/span/text()').extract_first('').strip()
        item['reference']=response.xpath(u'//strong[contains(text(), "Référence :")]/../text()').extract()[-1].strip()
        item['remuneration']=''
        item['company']=offer_data.split('"name":"')[-1].split('"')[0].strip()
        item['jobKind']='-'.join(response.css('div.matching-criteria ul li > span > span::text').extract())
        item['jobKind']=self.crawlerFunction.get_job_kind(item['jobKind'])
        item['description'] = u"<br>".join(response.css('section.company-description, section.job-description, section.profile-description').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills'] = offer_data.split('"skills":"')[-1].split('"')[0].strip()
        item['skills']=self.crawlerFunction.get_skills(item['skills']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    