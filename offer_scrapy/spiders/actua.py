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

class ActuaSpider(scrapy.Spider):
    name = 'actua'
    start_urls = ['http://www.actua.fr/index.php?option=com_page&page=offres.list&Itemid=6']
    required_fields=['date','title','location','description','contractKind','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }

    header_post = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    }

    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(ActuaSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    
    def build_search(self, page):
        formdata = {
            'limit': '30',
            'limitstart': str(page * 30),
            'search': '',
            'dep': '0',
        }
        url = 'http://www.actua.fr/index.php?option=com_page&page=offres.list'
        return scrapy.FormRequest(url, formdata=formdata, callback=self.parse_page, 
            headers=self.header_post, meta={'page': page})

    def parse(self, response):
        yield self.build_search(0)

    def parse_page(self, response):
        offers = response.css('form[name="adminForm"] > table.adminlist tr td:nth-child(2) a ::attr(href)').extract()
        for offer_link in offers:
            yield scrapy.Request(response.urljoin(offer_link), callback=self.extract_offer_data)

        if len(offers) > 0:
            page = response.meta.get('page', 0) + 1
            yield self.build_search(page)

    def extract_offer_data(self,response):
        _xpath = u'//td[contains(text(), "{0}")]/following-sibling::td/text()'
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('div#corps > h2::text').extract_first('').strip()
        item['title'] = re.sub(r'\s+', ' ', item['title'])
        item['url']=response.url
        item['date']=response.xpath(_xpath.format(u'Date de début de mission :')).extract_first('').strip()
        item['date']=datetime.strptime(item['date'], '%d/%m/%Y')
        item['contractKind']=self.crawlerFunction.get_contract_kind(None)
        item['location']=response.xpath(_xpath.format('Lieu de mission:')).extract_first('').strip()
        item['sector']=''
        item['reference']= response.css('input[name="id"]::attr(value)').extract_first('').strip()
        item['remuneration']=''
        item['company']= response.xpath(_xpath.format('Nom :')).extract_first('').strip()
        item['jobKind']=self.crawlerFunction.get_job_kind(None)
        item['description'] = u"<br>".join(response.css('div#corps table[width="100%"]').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)     