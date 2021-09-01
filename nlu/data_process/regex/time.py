# -*- coding:utf-8 -*-
# @Time: 2021/5/13 11:21
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: time.py
from nlu.data_process.regex.regex_entity import regex_entity
from nlu.data_process.time_process.generator_time import TimeGenderator
from nlu.data_process.time_process.time_regex import recognition


class time(regex_entity):
    def __init__(self):
        self.genertor = TimeGenderator()

    def parse(self, text: str, is_describe=False):
        entitys = []
        result = recognition(text)
        if result:
            entity = "collectTime"
            value = result[0].group()
            start = result[0].span()[0]
            end = result[0].span()[1]
            for index in range(1, len(result)):
                if result[index]:
                    # 时间实体过滤
                    value = value + result[index].group()
                    # end=result[index].span()[1]
            if text.__contains__("出生") or text.__contains__("生日"):
                entity = "birthday"
            entitys.append({
                "entity": entity,
                "value": value,
                "start": start,
                "confidence": 0.9,
                "end": end,
            })
        return text, entitys

    def generate(self, is_describe=False):
        return self.genertor.get_time_value(False)


if __name__ == "__main__":
    time = time()
    text, entity = time.parse('搜一九九八年十二月三十一日23时五十九分红旺日租白色明瑞RS车')
    print(f'{text} contains time entity is {entity}')
    print([time.generate() for i in range(10)])
