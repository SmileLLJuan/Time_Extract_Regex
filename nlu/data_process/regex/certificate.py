# -*- coding:utf-8 -*-
# @Time: 2021/3/24 10:03
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: certificate_regex.py
import re

import rstr

# from regex.regex_entity import regex_entity
# regex_entity
from nlu.data_process.regex.regex_entity import regex_entity


class certificate(regex_entity):
    def __init__(self):
        #支持前缀匹配
        self.parse_regex="((证件|身份证)(号)?(码)?(:|：|是|为)?)?(11|12|13|14|15|21|22|23|31|32|33|34|35|36|37|41|42|43|44|45|46|50|51|52|53|54|61|62|63|64|65|81|82|83)(\d{4})((19|20)\d{2})(\d{2})?(\d{2})?(\d{3,4})?X?x?"
        self.generate_regex = "(11|12|13|14|15|21|22|23|31|32|33|34|35|36|37|41|42|43|44|45|46|50|51|52|53|54|61|62|63|64|65|81|82|83)(\d{4})((19|20)\d{2})(0[1-9]|1[0-2])([0-2][1-9]|[1-3]0|31)(\d{4}|\d{3}x|\d{3}X)"
        self.describe="身份证号"

    def parse(self,text:str,is_describe=True):
        entitys=[]
        m_iter=re.finditer(self.parse_regex,text)
        for m in m_iter:
            if m:
                entitys.append({
                    "entity":"certificateNumber",
                    "value": m.group(),
                    "start": m.span()[0],
                    "confidence": 0.95,
                    "end": m.span()[1]
                })
        if is_describe:
            for entity in entitys:
                value=entity["value"]
                #匹配汉字
                m=re.match('[\u4e00-\u9fa5]{1,10}(:|：|是|为)?', value)
                if m:
                    #将entity的值中的汉字去掉
                    entity["value"]=re.sub('[\u4e00-\u9fa5]{1,10}(:|：|是|为)?','',value)
                    entity["start"]=entity["start"]+len(m.group())
                    continue
                else:
                    text=text.replace(value,self.describe+value)
        return text,entitys


    def generate(self,is_describe=True):
        format_regex=r'{}'.format(self.generate_regex)
        field_value=rstr.xeger(format_regex)
        if is_describe:
            return self.describe+field_value
        else:
            return field_value

if __name__=="__main__":
    ceri=certificate()
    text,entitys=ceri.parse("44223720220106160X和证件号是140154195910314487的关系")
    print(text)
    print(entitys)


