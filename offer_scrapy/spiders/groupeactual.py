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

class GroupeactualSpider(scrapy.Spider):
    name = 'groupeactual'
    start_urls = ['https://www.groupeactual.eu/offre-emploi?adresse=']
    required_fields=['date','title','location','description','contractKind','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }

    token = None
    header_post = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        'x-csrf-token': '',
        'x-requested-with': 'XMLHttpRequest',
    }

    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(GroupeactualSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    
    def build_search(self, page):
        formdata = {
            '_token': self.token,
            'limit': '',
            'order': '',
            'adresse': '',
            'google_adresse': '',
            'distance': '30',
            'remunerations': '10000;100000',
            'page': str(page),
        }
        url = 'https://www.groupeactual.eu/offre-emploi/search'
        return scrapy.FormRequest(url, formdata=formdata, callback=self.parse_page, 
            headers=self.header_post, meta={'page': page})

    def parse(self, response):
        self.token = response.css('meta[name="csrf-token"]::attr(content)').extract_first('').strip()
        self.header_post['x-csrf-token'] = self.token

        yield self.build_search(1)

    def parse_page(self, response):
        offers = response.css('div.actual-shadow::attr(onclick)').extract()
        for offer_link in offers:
            offer_link = offer_link.split("document.location.href='")[-1].split("'")[0].strip()
            offer_link = offer_link.split('?')[0]
            yield scrapy.Request(offer_link, callback=self.extract_offer_data)
        
        if len(offers) > 0:
            page = response.meta.get('page', 1) + 1
            yield self.build_search(page)

    def extract_offer_data(self,response):
        _xpath = '//p[contains(@class, "hero-details")]/span/i[contains(@class, "{0}")]/following-sibling::text()'
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('h2.annonce-titre::text').extract_first('').strip()
        item['title'] = re.sub(r'\s+', ' ', item['title'])
        item['url']=response.url
        item['date']=response.xpath(u'//p[contains(text(), "Publi")]/text()').extract_first('').split(' le ')[-1].strip()
        item['date']=datetime.strptime(item['date'], '%d/%m/%Y')
        item['contractKind']=response.xpath(
            _xpath.format('fa-suitcase')).extract_first('').strip()
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=response.xpath(
            _xpath.format('fa-map-marker')).extract_first('').strip()
        item['sector']=''
        item['reference']= response.css('[property="og:url"]::attr(content)').extract_first('').split('-')[-1]
        item['remuneration']=response.xpath(
            _xpath.format("fa-euro-sign")).extract_first('').strip()
        item['company']= response.css('span.agency-name::text').extract_first('').strip()
        item['jobKind']=response.xpath(
            _xpath.format("fa-clock")).extract_first('').strip()
        item['jobKind']=self.crawlerFunction.get_job_kind(item['jobKind'])
        item['description'] = u"<br>".join(response.css('article.wrap').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)     