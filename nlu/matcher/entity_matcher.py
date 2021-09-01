# -*- coding:utf-8 -*-
# @Time: 2021/5/13 10:00
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: entity_match.py
import re

from nlu.data_process.regex.regex_factory import InnerRegexMatcher
from nlu.db_operation.entity_match_db import EntityMatchDb


class EntityMatcher():
    def __init__(self, bot_id='default'):
        self._project = bot_id
        self._db = EntityMatchDb(bot=self._project)
        self._iregex = InnerRegexMatcher()

    def value_matcher(self, text: str, rows):
        '''
        基于value识别实体
        :param text: 文本
        :param rows: match 集合
        :return: entity
        '''
        entities = []
        for row in rows:
            entity_name, entity_value, match = row
            index = text.find(match)
            if index != -1:
                entity = {
                    "entity": entity_name,
                    "value": entity_value if entity_value else match,
                    "start": index,
                    "end": index + len(match),
                    "confidence": 1
                }
                entities.append(entity)
        return entities

    def regex_matcher(self, text, rows):
        '''
        基于正则识别实体
        :param text: 文本
        :param rows: 正则记录集合
        :return:
        '''
        entities = []
        for row in rows:
            entity_name, entity_value, match = row
            m = re.search(match, text)
            if m:
                entity = {
                    "entity": entity_name,
                    "value": entity_value if entity_value else m.group(),
                    "start": m.start(),
                    "end": m.end(),
                    "confidence": 1
                }
                entities.append(entity)
        return entities

    def matcher(self, text):
        '''
        通过对识别库中的配置进行实体识别
        :param text: 识别文本
        :return: entity集合
            entity = {"entity": string_id,
                  "value": span.text,
                  "start": doc[start].idx,
                  "confidence": 0.9,
                  "end": doc[start].idx + len(span.text)}
        '''
        entities = []
        value_rows = self._db.get_value_match()
        entities.extend(self.value_matcher(text, value_rows))
        regex_rows = self._db.get_regex_match()
        entities.extend(self.regex_matcher(text, regex_rows))
        text, entitie_regex = self._iregex.parse(text)
        entities.extend(entitie_regex)
        return text, entities

    def bulk_matcher(self, texts):
        '''
        通过对识别库中的配置进行实体识别
        :param text: 识别文本
        :return: entity集合
            entity = {"entity": string_id,
                  "value": span.text,
                  "start": doc[start].idx,
                  "confidence": 0.9,
                  "end": doc[start].idx + len(span.text)}
        '''
        all_entities = []
        all_text = []
        for text in texts:
            text, entities = self.matcher(text=text)
            all_entities.append(entities)
            all_text.append(text)
        return all_text, all_entities
