# -*- coding:utf-8 -*-
# @Time: 2021/3/24 17:25
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: plate_no.py
import random
import re

import rstr

from nlu.data_process.regex.regex_entity import regex_entity


class plate_no(regex_entity):
    def __init__(self):
        # 支持前缀匹配
        self.parse_regex = "(([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Za-z][0-9A-Za-z]{0,6}[挂学警港澳]?)|(无车牌)|(无牌车))"
        self.generate_regex = "[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼](?!IO)[A-Z][DF]?(?!IO)([0-9A-Z]{5})"
        self.describe = "车牌号"

    def parse(self, text: str, is_describe=False):
        entitys = []
        m_iter = re.finditer(self.parse_regex, text)
        for m in m_iter:
            if m:
                start = m.span()[0]
                end = m.span()[1]
                entitys.append({
                    "entity": "plateNo",
                    "value": m.group(),
                    "start": start,
                    "confidence": 0.95,
                    "end": end
                })
        return text, entitys

    def generate(self, is_describe=False):
        i=random.randint(0,9)
        if i < 9:
            format_regex = r'{}'.format(self.generate_regex)
        else:
            format_regex = r'{}'.format(self.generate_regex+"[挂学警港澳]")
        field_value = rstr.xeger(format_regex)
        if is_describe:
            return self.describe + field_value
        else:
            return field_value


if __name__ == "__main__":
    ceri = plate_no()
    text, entitys = ceri.parse("车牌号为新DNPXIZ")
    print(text)
    print(entitys)

    for i in range(100):
        print(ceri.generate(False))