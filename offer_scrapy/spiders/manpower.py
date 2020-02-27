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

class ManpowerSpider(scrapy.Spider):
    name = 'manpower'
    start_urls = ['https://www.manpower.fr/offre-emploi?query=&idZone=1']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(ManpowerSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def start_requests(self):
        for zone in range(1, 99):
            next_link = "https://www.manpower.fr/offre-emploi?query=&idZone={0}".format(zone)
            yield scrapy.Request(next_link, callback=self.parse_specialities)

    def parse_specialities(self,response):
        spec_links = response.xpath('//ul[@class="criteria-list"]//a/@href').extract()
        for  link in spec_links:
            link = response.urljoin(link)
            yield scrapy.Request(link, callback=self.parse_page)

    def parse_page(self,response):
        links_offers=response.xpath('//a[@class="title-link"]//@href').extract()
        for link_offer in links_offers:
            yield scrapy.Request(response.urljoin(link_offer), callback=self.extract_offer_data)
            
    def extract_offer_data(self,response):
        item=OfferscrawlersItem()
        if "offre-non-trouvee" not in response.url:
            item['status']="new"
            item['offerId']=""
            item['companyId']=""
            item['title']=response.xpath('//div[@class="infos-lieu"]/h1/text()').extract_first()
            item['url']=response.url
            item['date']=response.xpath('//b[contains(text(),"Date de")]/parent::div[@class="info-agency"]/text()')[3].extract().strip()
            item['date']=datetime.strptime(item['date'], '%d/%m/%Y')
            item['contractKind']=response.xpath('normalize-space(//b[contains(text(),"Contrat :")]/parent::li/text())').extract_first()
            item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
            item['location']=response.xpath('normalize-space(//b[contains(text(),"Lieu de travail :")]/parent::li/text())').extract_first()
            item['sector']=response.xpath('normalize-space(//b[contains(text(),"%s")]/parent::li/text())'%u"Secteur d'activité :").extract_first()
            item['reference']=response.url.split('/')[-1].strip('.html')
            item['remuneration']=response.xpath('normalize-space(//b[contains(text(),"%s")]/parent::li/text())'%u"Salaire :").extract_first()
            item['company']=response.xpath('//meta[@name="author"]/@content').extract_first().strip(".")
            item['jobKind']="Temps plein"
            item['description'] = u"<br>".join(response.css('article#post-description > div').extract())
            item['description'] = self.crawlerFunction.html2text(item['description'])
            item['skills']=self.crawlerFunction.get_skills(item['description']) 
            item['provider']=self.name
            item['domain']=self.domain
            item['uid']=self.name + '-' + item['reference']    
            yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    