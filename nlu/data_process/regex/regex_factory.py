# -*- coding:utf-8 -*-
# @Time: 2021/3/30 10:26
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: regex_factory.py
import logging

from nlu.data_process.regex.certificate import certificate
from nlu.data_process.regex.phone_no import phone_no
from nlu.data_process.regex.plate_no import plate_no
from nlu.data_process.regex.time import time
# from llj_test.time_extract.time_data_generate.time_generator import time
from nlu.data_process.regex.time_span import TimeSpan

logger = logging.getLogger(__name__)
class InnerRegexMatcher():
    def __init__(self):
        self.phone_no=phone_no()
        self.certificate=certificate()
        self.plate_no=plate_no()
        self.time=time()
        self.time_span = TimeSpan()

    def parse(self,text):
        text,entities_1 = self.certificate.parse(text)
        text,entities_2=self.phone_no.parse(text)
        text,entities_3=self.plate_no.parse(text)
        text,entities_4=self.time.parse(text)
        text,entities_5=self.time_span.parse(text)
        entities_1.extend(entities_2)
        entities_1.extend(entities_3)
        entities_1.extend(entities_4)
        entities_1.extend(entities_5)
        return text,entities_1

    def generater(self,filed_name:str,need_recognize=False):
        filed_value=''
        if "certificateNumber" == filed_name:
            filed_value=self.certificate.generate()
        elif "plateNo" == filed_name:
            filed_value=self.plate_no.generate()
        elif "phoneNo" == filed_name:
            filed_value=self.phone_no.generate()
        elif "collectTime" == filed_name:
            filed_value=self.time.generate()
        elif "time_span" == filed_name:
            filed_value=self.time_span.generate()
        else:
            logger.error("There is not contain the regex :"+filed_name)
        if need_recognize:
            fieldVal = f'[{filed_value}]({filed_name})'
            return fieldVal
        else:
            return filed_value



