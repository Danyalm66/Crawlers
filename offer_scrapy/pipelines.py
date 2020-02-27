# -*- coding: utf-8 -*-

from scrapy.conf import settings
from scrapy.exceptions import DropItem
import sys
import re
from datetime import datetime

class OfferscrawlersPipeline(object):
    name="pipeline"
    __collection = None
    
    required_fields = ['date', 'title', 'location', 'description', 'contractKind']
    
    def process_item(self, item, spider):
        ################# check requierd  fields ############################################################
        item['contractKind'] = OfferscrawlersPipeline.get_contract_kind(item['contractKind'])
        
        #####################################################################################################

        ################# check requierd  fields ############################################################
        if hasattr(spider, 'required_fields'):
            required_fields = spider.required_fields
        else:
            required_fields = self.required_fields
        
        missDataFields = []
        for field in required_fields:
            if item[field] == None or item[field] == "" or item[field] == []:
                missDataFields.append(field)
        if len(missDataFields) > 0:
            missing_values=",".join(str(x) for x in missDataFields)
            raise DropItem("Missing required fields {0}!".format(missing_values))
        
        # check date is datetime string if set
        if 'date' in item and not isinstance(item['date'], datetime):
            raise DropItem("Date must be datetime not string {0}".format(item['date']))
        # verify jobKind
        if 'jobKind' in item and not (item['jobKind'] == 'Temps plein' or item['jobKind'] == 'Temps partiel'):
            raise DropItem("jobKind must be Temps plein or Temps partiel - {0}".format(item['jobKind']))

        # Add created_at, updated_at
        item['created_at'] = item['updated_at'] = datetime.now()
        #####################################################################################################   
        return item

    @classmethod
    def get_contract_kind(cls, contractKind):
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