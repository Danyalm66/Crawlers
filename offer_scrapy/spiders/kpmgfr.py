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

class KpmgfrSpider(scrapy.Spider):
    name = 'kpmgfr'
    start_urls = ['https://kpmgfr.referrals.selectminds.com/etudiants/jobs/search', 
                  'https://kpmgfr.referrals.selectminds.com/jeunesdiplomes/jobs/search',
                  'https://kpmgfr.referrals.selectminds.com/experimentes/jobs/search']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }

    page_url_dict = {
        'https://kpmgfr.referrals.selectminds.com/etudiants/jobs/search': 1,
        'https://kpmgfr.referrals.selectminds.com/jeunesdiplomes/jobs/search': 1,
        'https://kpmgfr.referrals.selectminds.com/experimentes/jobs/search': 1
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(KpmgfrSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def parse(self, response):
        for offer_link in response.css('a.job_link::attr(href)').extract():
            yield scrapy.Request(offer_link, callback=self.extract_offer_data)

        if (len(response.css('a.job_link::attr(href)').extract()) > 0):
            key = response.url.split('/search')[0].strip() + '/search'
            self.page_url_dict[key] += 1
            next_page_url = response.url.split('/page')[0] + '/page{0}'.format(self.page_url_dict.get(key))
            if next_page_url:
                yield scrapy.Request(next_page_url)
            
    def extract_offer_data(self,response):
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('div.content_header h1.title::text').extract_first('').strip()
        item['url']=response.url
        item['date']=datetime.now()
        item['contractKind']=''
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=response.xpath('//h4[@class="primary_location"]/a/span/following-sibling::text()').extract_first('').strip()
        item['sector']=response.css('dl.field_category dd span::text').extract_first('').strip()
        item['reference']=response.url.split('-')[-1].strip()
        item['remuneration']=''
        item['company']= response.css('meta[property="og:site_name"]::attr(content)').extract_first('').strip()
        item['jobKind']=''
        item['jobKind']=self.crawlerFunction.get_job_kind(item['jobKind'])
        item['description'] = u"<br>".join(response.css('div.job_description').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    