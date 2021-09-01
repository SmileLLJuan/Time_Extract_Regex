# -*- coding:utf-8 -*-
# @Time: 2021/7/27 15:25
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: time_span.py
import re

import rstr

from nlu.data_process.regex.regex_entity import regex_entity
from nlu.data_process.time_process.convert_time_str import convertChineseDigitsToArabic


class TimeSpan(regex_entity):
    def __init__(self):
        # 支持前缀匹配
        self.parse_regex = "(前进|快进|后退|倒退|回退|快退)[0-9一二三四五六七八九]{1,3}(秒|分|分钟|小时)"
        self.generate_regex = "(前进|快进|后退|倒退|回退|快退)[0-9一二三四五六七八九]{1,3}(秒|分|分钟|小时)"
        self.describe = ""

    def _time_span_oper(self,time_span:str):
        m = re.match("[0-9一二三四五六七八九]{1,3}",time_span)
        if not m:
            return None
        value = m.group()
        value_len = len(value)
        if not str.isdigit(value):
            value = convertChineseDigitsToArabic(value)

        if time_span.endswith("分") or time_span.endswith("分钟"):
            value = int(value)*60
        elif time_span.endswith("小时"):
            value = int(value)*60*60
        return value,value_len

    def parse(self, text: str, is_describe=False):
        entitys = []
        m_iter = re.finditer(self.parse_regex, text)
        for m in m_iter:
            if m:
                value = m.group()
                p_m = re.search("(前进|快进|后退|倒退|回退|快退)",value)
                if p_m:
                    start_index = text.index(p_m.group())
                    value_len = len(p_m.group())
                    entitys.append({
                        "entity": "play_type",
                        "value": p_m.group(),
                        "start": start_index,
                        "confidence": 0.95,
                        "end": start_index + value_len
                    })
                time_span_m = re.search("[0-9一二三四五六七八九]{1,3}(秒|分|分钟|小时)",value)
                if time_span_m:
                    start_index = text.index(time_span_m.group())
                    value,value_len = self._time_span_oper(time_span_m.group())
                    entitys.append({
                        "entity": "time_span",
                        "value": value,
                        "start": start_index,
                        "confidence": 0.95,
                        "end": start_index + len(time_span_m.group())
                    })
        return text, entitys

    def generate(self, is_describe=False):
        field_value = rstr.xeger(self.generate_regex)
        if is_describe:
            return self.describe + field_value
        else:
            return field_value


if __name__ == "__main__":
    ceri = TimeSpan()
    text, entitys = ceri.parse("第三号屏幕前进1小时")
    print(text)
    print(entitys)