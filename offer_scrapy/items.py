# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class OfferscrawlersItem(scrapy.Item):
    # name = scrapy.Field()
    date=scrapy.Field()
    title=scrapy.Field()
    location=scrapy.Field()
    contractKind=scrapy.Field()
    company=scrapy.Field()
    companyId=scrapy.Field()
    description=scrapy.Field()
    remuneration=scrapy.Field()
    url=scrapy.Field()
    reference=scrapy.Field()
    offerId=scrapy.Field()
    status=scrapy.Field()
    provider=scrapy.Field()
    domain=scrapy.Field()
    uid=scrapy.Field()
    sector=scrapy.Field()
    jobKind=scrapy.Field()
    skills=scrapy.Field()
    uid=scrapy.Field()
    domain=scrapy.Field()
    descriptionPlus=scrapy.Field()
    chunk=scrapy.Field()
    created_at=scrapy.Field()
    updated_at=scrapy.Field()