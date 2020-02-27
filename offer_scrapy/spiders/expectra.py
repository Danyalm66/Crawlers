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

class ExpectraSpider(scrapy.Spider):
    name = 'expectra'
    start_urls = ['https://www.expectra.fr/recherche_offres/all/']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(ExpectraSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def parse(self, response):
        for offer_link in response.css('li.item h2 a::attr(href)').extract():
            yield scrapy.Request(offer_link, callback=self.extract_offer_data)

        next_page_url = response.css('a.nextrandstad::attr(href)').extract_first('')
        if next_page_url:
            yield scrapy.Request(response.urljoin(next_page_url))
            
    def extract_offer_data(self,response):
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('div.offer-title h1::text').extract_first('').strip()
        item['url']=response.url
        item['date']=response.xpath(u'//p[contains(text(), "publiée")]/text()').extract_first('').split(' le ')[-1].strip()
        # date value: 17 avril 2019
        # item['date']=datetime.strptime(item['date'], '%d %B %Y')
        item['contractKind']=response.xpath('//*[contains(text(), "Type du contrat")]/following-sibling::text()').extract_first('').strip()
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=response.xpath('//*[contains(text(), "Lieu de travail")]/following-sibling::text()').extract_first('').split('(')[0].strip()
        item['sector']=response.xpath(u'//*[contains(text(), "Secteur ")]/following-sibling::text()').extract_first('').strip()
        item['reference']=response.url.split('/offre/')[-1].split('/')[0].strip()
        item['remuneration']=response.xpath('//div[@class="offer-resume"]//*[contains(text(), "Salaire")]/following-sibling::text()').extract_first('').strip()
        item['company']=response.css('.widget-offer-agency h2::text').extract_first('').strip()
        item['jobKind']=''
        item['jobKind']=self.crawlerFunction.get_job_kind(item['jobKind'])
        item['description'] = u"<br>".join(response.css('div.offer-rte').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    