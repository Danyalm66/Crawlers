# -*- coding: utf-8 -*-
import json
import requests
import itertools
import re
from scrapy.utils.serialize import ScrapyJSONEncoder
from scrapy.conf import settings
from scrapy.exceptions import CloseSpider
import scrapy 
import re
class CrawlersFunctions(object):
    
    def __init__(self):
        pass
        
    def get_skills(self,description):
        skills=['skill']
        return skills   

    def send_data_to_manager(self,stats,crawlerName):
        return

    def get_contract_kind(self, contractKind):
        if contractKind == None or contractKind == '':
            return 'CDI'
        m = re.search(ur'CDI|CDD|Interim|Intérim|Saisonnier|Extra|Stage|VIE|CDIC|Intermittent|Indépendant|Alternance - Apprentissage|Alternance|Apprentissage|Fonction publique', contractKind, re.I)
        if m:
            value = m.group(0)
            if re.search(ur'Alternance|Apprentissage', value, re.I):
                return 'Alternance - Apprentissage'
            if re.search(ur'Interim|Intérim', value, re.I):
                return 'Interim'
            return value
        return 'CDI'

    def get_job_kind(self, jobKind):
        if jobKind is None or jobKind == '':
            return 'Temps plein'

        if re.search(ur'\s+partiel', jobKind, re.I):
            return 'Temps partiel'

        return 'Temps plein'

    def html2text(self, html):
        """
            Convert html to plain text and keep the format
        """
        html = re.sub(r'\s+', ' ', html)
        html = re.sub(r'<(h\d|br|p|tr|li)[^>]*>', u'\n', html, flags=re.I)
        html = re.sub(r'<[^>]+>', '', html)
        return html.strip()