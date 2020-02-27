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

class PromanEmploiSpider(scrapy.Spider):
    name = 'proman_emploi'
    start_urls = ['https://www.proman-emploi.fr/offres/']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(PromanEmploiSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()

    def parse(self, response):
        for offer_link in response.css('li.col-job-offer > div > div > a[href*="/offres/"]::attr(href)').extract():
            yield scrapy.Request(response.urljoin(offer_link), callback=self.extract_offer_data)

        next_page_url = response.css('ul.wrapper-pagination a.next::attr(href)').extract_first()
        if next_page_url:
            yield scrapy.Request(response.urljoin(next_page_url))

    def extract_offer_data(self,response):
        _xpath1 = '//i[contains(@class, "{0}")]/following-sibling::text()'
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('div.principal-offer h1::text').extract_first('').strip()
        item['url']=response.url
        item['date']=response.xpath(
                        '//span[contains(text(), "Date de publication :")]/following-sibling::text()').extract_first('').strip()
        item['date']=datetime.strptime(item['date'], '%d/%m/%Y')
        item['contractKind']=response.css('li.contract-type::text').extract_first('').strip()
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=response.xpath(_xpath1.format('fa-map-marker')).extract_first('').strip()
        item['sector']=response.xpath(u'//li[contains(text(), "Secteur d\'activité :")]/span/text()').extract_first('').strip()
        item['reference']=response.xpath(u'//li[contains(text(), "Référence")]/text()').extract_first('').split(':')[-1].strip()
        item['remuneration']=''
        item['company']= response.css('meta[name="application-name"]::attr(content)').extract_first('').strip()
        item['jobKind']=response.xpath(_xpath1.format('fa-clock')).extract_first('').strip()
        item['jobKind']=self.crawlerFunction.get_job_kind(None)
        item['description']=u"<br>".join(response.css('div.principal-offer-desc').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    