import scrapy
import collections
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

class GenyInterimSpider(scrapy.Spider):
    name = 'geny-interim'
    start_urls = ['http://www.geny-interim.com/offres.html/']
    required_fields = ['date', 'title', 'location', 'description', 'contractKind', 'reference', 'company']

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "USER_AGENT": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
        "ROBOTSTXT_OBEY": False
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(GenyInterimSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signals.spider_closed)
        return spider

    def __init__(self, *args, **kwargs):
        parsed_uri = urlparse(self.start_urls[0])
        self.domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        self.crawlerFunction = CrawlersFunctions()

    def parse(self, response):
        urls=response.css('div.featured-box > div > div> div> a::attr(href)').extract()
        for url in urls:
            yield scrapy.Request(url, callback=self.info_page)
        next_page_url = response.css('a.page::attr(href)').extract()

        for x in [item for item, count in collections.Counter(next_page_url).items() if count > 1]:
            yield scrapy.Request(x)




    def info_page(self,response):
        item = OfferscrawlersItem()
        item['status'] = "new"
        item['offerId'] = ""
        item['companyId'] = ""
        item['title'] = response.css('.two-thirds > div > div > div >h1::text').get("")
        item['url'] = response.url
        item['date'] = response.xpath('//*[contains(text(), "Date de")]/following-sibling::dd/text()').extract_first().replace('.','/')

        item['contractKind'] = response.xpath('//*[contains(text(), "Contrat ")]/following-sibling::dd/text()').extract_first()
        item['location'] =  response.xpath('//*[contains(text(), "Lieu")]/following-sibling::dd/text()').extract_first()
        item['sector'] = response.xpath('//*[contains(text(), "Secteur d\'activit")]/following-sibling::dd/text()').extract_first()
        item['reference'] = response.url.strip('/').split('/')[-1]
        item['remuneration'] = response.css('.shortcode-unorderedlist > dl > dd:nth-child(14)::text').extract_first()
        item['company'] =''
        item['jobKind'] = self.crawlerFunction.get_job_kind(None)
        desc = ""
        for i in response.css('.two-thirds > div > div > div > strong > p').extract():
            desc += i
        item['description'] = desc
        item['skills'] = self.crawlerFunction.get_skills(item['description'])
        item['provider'] = self.name
        item['domain'] = self.domain
        item['uid'] = self.name + '-' + item['reference']
        yield item

    def spider_closed(self, spider):
        self.crawlerFunction.send_data_to_manager(self.crawler.stats.get_stats(),self.name)