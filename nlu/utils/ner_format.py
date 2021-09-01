# -*- coding:utf-8 -*-
# @Time: 2021/5/13 15:36
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: ner_format.py
from utils.nlu_config import NluConfig

nlu_config_dict = {}

'''将驼峰式修改为下划线连接'''


def rename_(key: str):
    new_word = ""
    for char in key:
        if not char.islower() and char.isalpha():
            new_word += "_" + char.lower()
        else:
            new_word += char
    return new_word


def format_entity_name(all_entity, project="default"):
    if not project in nlu_config_dict.keys():
        nlu_config_dict[project] = NluConfig(project)
    # 获取配置
    format_value = nlu_config_dict[project].get_value("entity.format", 0)
    if format_value == '1':
        for entities in all_entity:
            for entity in entities:
                entity["entity"] = rename_(entity["entity"])
