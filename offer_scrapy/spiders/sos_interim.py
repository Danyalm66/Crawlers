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
import re
from datetime import datetime

class SosInterimSpider(scrapy.Spider):
    name = 'sos_interim'
    start_urls = ['http://www.sos-interim.fr/jobs-2/']
    required_fields = ['date', 'title', 'location', 'description', 'contractKind', 'reference', 'company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(SosInterimSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def parse(self, response):
        for offer_link in response.css('.wpjb-column-title > a::attr(href)').getall():
            offer_link = "{0}/".format(response.urljoin(offer_link))
            yield scrapy.Request(offer_link, callback=self.extract_offer_data)

        next_page_url = response.css('.next::attr(href)').get()
        if next_page_url:
            yield scrapy.Request(response.urljoin(next_page_url))

    def extract_offer_data(self,response):
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('h1::text').get('').strip()
        item['url']=response.url
        item['date']=response.xpath(
            u'//*[contains(text(), "Date de publication")]/following-sibling::td/text()').get('').strip()
        if item['date'] != '':
            item['date']=datetime.strptime(item['date'], '%d/%m/%Y')
        else:
            item['date']=datetime.now()
        item['contractKind']=response.xpath(
            u'//*[contains(text(), "Type de contrat")]/following-sibling::td/a/text()').get('').strip()
        item['location']=response.xpath(
            u'//*[contains(text(), "Lieu")]/following-sibling::td/span/text()').get('').strip()
        item['sector']= response.xpath(
            u'//*[contains(text(), "Secteur d\'activite")]/following-sibling::td/a/text()').get('').strip()
        item['reference']= response.url.strip('/').split('/')[-1]
        item['remuneration']= ""
        item['company']= response.xpath(
            u'//*[contains(text(), "Nom de l\'agence")]/following-sibling::td/text()').get('').strip(' (')
        item['jobKind']=self.crawlerFunction.get_job_kind(None)
        item['description'] = u"<br>".join(response.css('.wpjb-info + .wpjb-job-content > *').getall())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description'])
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item
    
    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)