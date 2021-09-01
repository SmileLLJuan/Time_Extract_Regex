# -*- coding:utf-8 -*-
# @Time: 2021/5/13 16:00
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: intent_matcher.py
import re

from nlu.db_operation.intent_match_db import IntentMatchDb


class IntentMatcher():
    def __init__(self, bot_id='default'):
        self._project = bot_id
        self._db = IntentMatchDb(project=self._project)

    def value_matcher(self, text: str, rows):
        '''
        处理value型的匹配
        :param text: 带分析文本
        :param rows: value型的match记录
        :return:
        '''
        intent_rank = []
        for row in rows:
            intent_name, match = row
            index = text.find(match)
            if index != -1:
                intent = {}
                intent["name"] = intent_name
                intent["confidence"] = 0.9
                intent_rank.append(intent)
        return intent_rank

    def regex_matcher(self, text: str, rows):
        '''
        处理正则类型的匹配问题
        :param text: 待分析文本
        :param rows: regex类型的匹配记录
        :return:
        '''
        intent_rank = []
        for row in rows:
            intent_name, match = row
            m = re.search(match, text)
            if m:
                intent = {}
                intent["name"] = intent_name
                intent["confidence"] = 0.9
                intent_rank.append(intent)
        return intent_rank

    def matcher(self, text, project):
        '''
        意图匹配库意图识别
        :param text: 待分析文本
        :return:
        '''
        intent_rank = []
        value_rows = self._db.get_value_match(project)
        intent_rank.extend(self.value_matcher(text, value_rows))

        regex_rows = self._db.get_regex_match(project)
        intent_rank.extend(self.regex_matcher(text, regex_rows))

        return intent_rank

    def bulk_matcher(self, texts, project):
        '''
        意图匹配库意图识别
        :param text: 待分析文本
        :return:
        '''
        intents = []
        for text in texts:
            intents.append(self.matcher(text=text, project=project))
        return intents


