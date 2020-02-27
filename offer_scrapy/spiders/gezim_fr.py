# -*- coding: utf-8 -*-
import scrapy
import logging
from offer_scrapy.items import OfferscrawlersItem
from scrapy import signals
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import FormRequest
from  offer_scrapy.commonfunctions import CrawlersFunctions
import json
import re
from urlparse import urlparse
from datetime import datetime

class GezimFrSpider(scrapy.Spider):
    name = 'gezim-fr'
    start_urls = ['https://www.gezim.fr/toutes-les-offres//']
    required_fields = ['date', 'title', 'location', 'description', 'contractKind', 'reference', 'company']

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY": False
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(GezimFrSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction = CrawlersFunctions()

    def parse(self, response):
        all_urls=response.css('.list-offres > div> div> div > div> div > div > h2 > a::attr(href)').getall()
        for url in all_urls:
            yield scrapy.Request(url, callback=self.extract_offer_data)
        next_page_url=response.css('.next::attr(href)').get('')
        if next_page_url:
            yield scrapy.Request(next_page_url)

    def extract_offer_data(self,response):
        item = OfferscrawlersItem()
        item['status'] = "new"
        item['offerId'] = ""
        item['companyId'] = ""
        item['title'] = response.css('h1::text').get('').strip()
        item['title'] = re.sub(r'\s+', ' ', item['title'])
        item['url'] = response.url
        item['date'] = response.css('.soustitre::text').get('').split(' le ', 1)[-1].strip()
        if item['date'] != '' and '20' in item['date']:
            item['date'] = datetime.strptime(item['date'].encode('utf-8'), '%d %B %Y')
        else:
            item['date'] = datetime.now()
        item['contractKind'] = response.css('.info > ul:nth-child(1) > li:nth-child(1)::text').get('')
        item['location'] = response.css('.col-md-8 > ul:nth-child(1) > li:nth-child(2)::text').get('').strip()
        item['sector'] = ''
        item['reference'] = response.css('.col-md-8 > ul:nth-child(1) > li:nth-child(3)::text').get('').strip()
        item['remuneration'] = ''
        item['company'] = response.css('.info > ul:nth-child(1) > li:nth-child(3)::text').get('')
        item['jobKind'] = self.crawlerFunction.get_job_kind(None)
        item['description'] =u'<p>'.join(response.css('.entry-content').getall())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills'] = self.crawlerFunction.get_skills(item['description'])
        item['provider'] = self.name
        item['domain'] = self.domain
        item['uid'] = self.name + '-' + item['reference']
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(), self.name)

