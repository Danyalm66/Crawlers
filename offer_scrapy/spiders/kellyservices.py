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

class KellyservicesSpider(scrapy.Spider):
    name = 'kellyservices'
    start_urls = ['https://jobs.kellyservices.fr/']
    required_fields=['date','title','location','description','contractKind','sector','reference','company']
    
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT" : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY" : False
    }

    header_post = {
        'Accept': 'application/xml, text/xml, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Faces-Request': 'partial/ajax',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
    }
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
      spider = super(KellyservicesSpider, cls).from_crawler(crawler, *args, **kwargs)
      crawler.signals.connect(spider.spider_closed, signals.spider_closed)
      return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction=CrawlersFunctions()  

    def build_search(self, offset):
        formdata = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'searchForm:resultTable',
            'javax.faces.partial.execute': 'searchForm:resultTable',
            'javax.faces.partial.render': 'searchForm:resultTable',
            'searchForm:resultTable': 'searchForm:resultTable',
            'searchForm:resultTable_pagination': 'true',
            'searchForm:resultTable_first': str(offset),
            'searchForm:resultTable_rows': '10',
            'searchForm:resultTable_encodeFeature': 'true',
            'searchForm': 'searchForm',
            'javax.faces.ViewState': '3951018569048023082:4601472914472834437',
        }
        url = 'https://jobs.kellyservices.fr/index.xhtml'
        return scrapy.FormRequest(url, formdata=formdata, callback=self.parse_page, 
            headers=self.header_post, meta={'offset': offset})

    def parse(self, response):
        yield self.build_search(0)

    def parse_page(self, response):
        body_res = '<html><body><table><tr {0}</tr></table></body></html>'.format(response.body.split('[CDATA[<tr')[-1].split('</tr>]]')[0].strip())
        response = response.replace(body=body_res)
        offers = response.css('a[href*="/jobOrderDetail"]::attr(href)').extract()
        for offer_link in offers:
            yield scrapy.Request(response.urljoin(offer_link), callback=self.extract_offer_data)
        
        if len(offers) > 0:
            offset = response.meta.get('offset') + 10
            yield self.build_search(offset)

    def extract_offer_data(self,response):
        _xpath = u'//label[contains(text(), "{0}")]/following-sibling::text()'
        item=OfferscrawlersItem()
        item['status']="new"
        item['offerId']=""
        item['companyId']=""
        item['title']=response.css('span.m-job-order-fields-header::text').extract_first('').strip()
        item['title']=re.sub(r'\s+', ' ', item['title'])
        item['url']=response.url
        item['date']=response.xpath(_xpath.format('Date de publication')).extract_first('').split(' le ')[-1].strip()
        item['date']=datetime.strptime(item['date'], '%d/%m/%y')
        item['contractKind']=response.xpath(_xpath.format('Type:')).extract_first('').strip()
        item['contractKind']=self.crawlerFunction.get_contract_kind(item['contractKind'])
        item['location']=response.xpath(_xpath.format(u'Où:')).extract_first('').strip()
        item['sector']=response.xpath(_xpath.format(u'Catégorie:')).extract_first('').strip()
        item['reference']=response.xpath(_xpath.format(u'Numéro  du poste')).extract_first('').strip()
        item['remuneration']=response.xpath('//b[contains(text(), "Salaire")]/following-sibling::text()[1]').extract_first('').split(':')[-1].strip()
        item['company']= 'Kelly Services'
        item['jobKind']=response.xpath(_xpath.format('Taux d\'occupation')).extract_first('').strip()
        item['jobKind']=self.crawlerFunction.get_job_kind(item['jobKind'])
        item['description'] = u"<br>".join(response.css('div.m-job-order-description > p').extract())
        item['description'] = self.crawlerFunction.html2text(item['description'])
        item['skills']=self.crawlerFunction.get_skills(item['description']) 
        item['provider']=self.name
        item['domain']=self.domain
        item['uid']=self.name + '-' + item['reference']    
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)    