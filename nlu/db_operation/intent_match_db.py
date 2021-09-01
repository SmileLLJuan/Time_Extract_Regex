# -*- coding:utf-8 -*-
# @Time: 2021/5/12 18:47
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: intent_match_db.py
import logging

from importers.data_save_fetch import BaseDbManager

logger = logging.getLogger(__name__)


class IntentMatchDb():
    def __init__(self, project="default"):
        self.project = project
        self.db = BaseDbManager(project=project)
        self.table_name = 'intent_match'

    def inserts(self, records: list):
        '''
        实体识别模式匹配库更新
        :param project: 所属项目名称
        :param records: 更新记录
        :return:
        '''

        if len(records) == 0:
            return
        fields = list(records[0].keys())
        fields = '(' + ','.join(fields) + ')'
        values = ['?' for i in range(len(records[0]))]
        values = '(' + ','.join(values) + ')'
        inserts = []

        for record in records:
            inserts.append(tuple(record.values()))

        sql_insert = "REPLACE into " + self.table_name + " " + fields + " VALUES" + values
        logger.debug("update the entity_match the sql is :" + sql_insert)
        self.db.insert_many(sql_insert, inserts)

    def get_value_match(self, project):
        '''
        获取实体识别通过value去match识别的实体
        :return: 记录集合
        '''
        if project:
            sql = f"select intent_name,match from " + self.table_name + f" where type='value' and project='{project}'"
        else:
            sql = "select intent_name,match from " + self.table_name + " where type='value'"
        rows = self.db.select(sql_select=sql)
        return rows

    def get_regex_match(self, project):
        '''
        获取实体识别通过regex去match的识别的实体
        :return:记录集合
        '''
        if project:
            sql = "select intent_name,match from " + self.table_name + f" where type='regex' and project='{project}'"
        else:
            sql = "select intent_name,match from " + self.table_name + " where type='regex'"
        rows = self.db.select(sql_select=sql)
        return rows

    def del_match(self, match, intent_name: list):
        '''
        删除intent match匹配库
        :param match:
        :param intent_name:
        :return:
        '''
        sql = f"delete from {self.table_name} where "
        if match:
            sql = sql + f"match='{match}' and "
        if len(intent_name) > 0:
            intent_name.append("")
            sql = sql + f"intent_name in {tuple(intent_name)} and "
        if match or len(intent_name) > 0:
            sql = sql + f"1"
            logger.debug(f"delete intent match record, sql is :{sql}")
            return self.db.delete(sql_del=sql)
        else:
            raise ValueError(f"match and intent_name is None.")
