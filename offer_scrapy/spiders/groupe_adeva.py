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
import locale

class GroupeAdevaSpider(scrapy.Spider):
    name = 'groupe_adeva'
    start_urls = ['https://www.groupe-adeva.fr/offres/rechercher/']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }

    header_post = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(GroupeAdevaSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  
        # locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")

    def parse(self, response):
        extract_item = response.meta.get('extract_item', 0)
        if extract_item == 1:
            for offer_link in response.css('ul[class*="emploi-item"] a::attr(href)').extract():
                yield scrapy.Request(response.urljoin(offer_link), callback=self.extract_offer_data)
        else:
            formdata = {
                'search': '',
                'button': 'Rechercher'
            }
            yield scrapy.FormRequest(response.url, formdata=formdata, 
                headers=self.header_post, meta={'extract_item': 1})

    def extract_offer_data(self,response):
        _xpath = u'//span[contains(text(), "{0}")]/following-sibling::text()'
        _xpath_1 = u'//strong[contains(text(), "{0}")]/following-sibling::text()'
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('div#emploi-header h1::text').extract_first('').strip()
        item['title']=re.sub(r'\s+', ' ', item['title'])
        item['url']=response.url
        item['date']=response.xpath(_xpath.format('Date de parution :')).extract_first('').strip()
        # item['date']=datetime.strptime(item['date'], '%d %B %Y')
        item['contractKind']=response.xpath(_xpath_1.format('Type de contrat :')).extract_first('').strip()
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=response.xpath(_xpath_1.format('Lieu :')).extract_first('').strip()
        item['sector']=response.css('div#emploi-header span.icon-wrap span::text').extract_first('').strip()
        item['reference']=response.xpath(_xpath.format(u'Référence :')).extract_first('').strip()
        item['remuneration']=response.xpath(_xpath_1.format(u'Salaire :')).extract_first('').strip()
        item['company']= 'groupe-adeva.fr'
        item['jobKind']=self.crawlerFunction.get_job_kind(None)
        item['description'] = u"<br>".join(response.css('div#emploi-content').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    