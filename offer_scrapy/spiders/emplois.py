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

class EmploisSpider(scrapy.Spider):
    name = 'emplois'
    start_urls = ['https://emplois.lidl.fr/fr/Offres-d-emploi.htm']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(EmploisSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def parse(self, response):
        for offer_link in response.css('a.link-vacancy::attr(href)').extract():
            yield scrapy.Request(response.urljoin(offer_link), callback=self.extract_offer_data)

        for next_page_url in response.css('nav.pagination a[rel="next"]::attr(href)').extract():
            if next_page_url:
                yield scrapy.Request(response.urljoin(next_page_url))

    def extract_offer_data(self,response):
        _xpath = u'//td[contains(text(), "{0}")]/following-sibling::td/text()'
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('section.apply-online-box div.inner h1::text').extract_first('').strip()
        item['title']=re.sub(r'\s+', ' ', item['title'])
        item['url']=response.url
        temp_arr=[x for x in response.css('section.apply-online-box div.inner > ul > li::text').extract() if re.sub(r'\d{2}.\d{2}.\d{4}', '', x).strip() == '']
        item['date']=datetime.strptime(temp_arr[0], '%d.%m.%Y') if len(temp_arr) > 0 else datetime.now()
        item['contractKind']=response.xpath(_xpath.format('Type de contrat:')).extract_first('').strip()
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=response.xpath(_xpath.format('Lieu:')).extract_first('').strip()
        item['sector']=response.css('section.apply-online-box div.inner > ul > li:nth-child(2)::text').extract_first('').strip()
        item['reference']=response.xpath(_xpath.format(u'Référence de l\'offre:')).extract_first('').strip()
        item['remuneration']=''
        item['company']= 'emplois.lidl.fr'
        item['jobKind']=self.crawlerFunction.get_job_kind(None)
        item['description']=u"<br>".join(response.css('section.vacancy-page div.vacancy-features ul li, section.vacancy-page div.inner > p').extract())
        item['description']=re.sub(r'<!--(.*?)-->', '', item['description'])
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    