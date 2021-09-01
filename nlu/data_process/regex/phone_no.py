# -*- coding:utf-8 -*-
# @Time: 2021/3/24 16:56
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: phoneNo.py
import re

import rstr

from nlu.data_process.regex.regex_entity import regex_entity


class phone_no(regex_entity):
    def __init__(self):
        #支持前缀匹配
        self.parse_regex="((电话|手机)(号)?(码)?(:|：|是|为)?)?1\d{10}"
        self.generate_regex = "1(3\d{2}|4[14-9]\d|5([0-35689]\d|7[1-79])|66\d|7[2-35-8]\d|8\d{2}|9[13589]\d)\d{7}$"
        self.describe="手机号"

    def parse(self,text:str,is_describe=True):
        entitys=[]
        m_iter=re.finditer(self.parse_regex,text)
        for m in m_iter:
            if m:
                start = m.span()[0]
                end = m.span()[1]
                #保证前面和后面没有其他的数字
                if start>0:
                    if str.isdigit(text[start-1]):
                        continue
                if end < len(text):
                    if str.isdigit(text[end]):
                        continue
                entitys.append({
                    "entity":"phoneNo",
                    "value": m.group(),
                    "start": start,
                    "confidence": 0.95,
                    "end": end
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
    ceri=phone_no()
    text,entitys=ceri.parse("手机号15258852197和电话号16605174597的关系")
    print(text)
    print(entitys)

    for i in range(10):
        print(ceri.generate())
