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
from urlparse import urlparse
from datetime import datetime

class ServaSpider(scrapy.Spider):
    name = 'serva'
    start_urls = ['http://www.servagroupe-emploi.fr/']
    required_fields = ['date', 'title', 'location', 'description', 'contractKind', 'reference', 'company']


    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ServaSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction = CrawlersFunctions()

    def parse(self, response):
        urls=response.css('a.fancybox::attr(href)').extract()

        for url in urls:
            yield scrapy.Request(url, callback=self.info_page)


    def info_page(self,response):
        item = OfferscrawlersItem()
        item['status'] =   response.xpath('//*[contains(text(),"Statut")]/span/text()').extract_first()
        item['offerId'] = ""
        item['companyId'] = ""
        item['title'] = response.css('h1::text').extract_first()
        item['url'] = response.url
        item['date'] = response.css('.soustitre::text').extract_first().split('le')[1].strip()
        item['contractKind'] =''
        l = ''
        for j in response.css('.fonction_contact > p:nth-child(1)::text').extract():
            l+=j
        item['location'] = l
        item['sector'] = response.css('.infoTechnique > li:nth-child(1) > span:nth-child(1)::text').extract_first()
        item['reference'] =  response.css('.soustitre::text').extract_first().split('-')[0].split('.')[1].strip()
        item['remuneration'] = ''
        item['company'] =''
        for i in response.css('.infoContact > h3:nth-child(1)::text').extract():
            if len(i.strip()) > 0:
                item['company'] = i.strip()
        item['jobKind'] = self.crawlerFunction.get_job_kind(None)
        desc = ''
        for i in response.css('.offre > p::text').extract():
            desc+=i
        item['description'] = desc
        item['skills'] = self.crawlerFunction.get_skills(item['description'])
        item['provider'] = self.name
        item['domain'] = self.domain
        item['uid'] = self.name + '-' + item['reference']
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)