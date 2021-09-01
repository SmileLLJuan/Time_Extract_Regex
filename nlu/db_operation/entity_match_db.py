# -*- coding:utf-8 -*-
# @Time: 2021/5/12 18:37
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: entity_match_mg.py
import logging

from importers.data_save_fetch import BaseDbManager

logger = logging.getLogger(__name__)


class EntityMatchDb():
    def __init__(self, bot):
        self.project = bot
        self.db = BaseDbManager(project=self.project)
        self.table_name = "entity_match"

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

    def get_match(self):
        '''
        获取所有的match记录
        :return: 记录集合
        '''
        sql = "select entity_name,entity_value,match,type from " + self.table_name
        rows = self.db.select(sql_select=sql)
        return rows

    def get_value_match(self):
        '''
        获取实体识别通过value去match识别的实体
        :return: 记录集合
        '''
        sql = "select entity_name,entity_value,match from " + self.table_name + " where type='value'"
        rows = self.db.select(sql_select=sql)
        return rows

    def get_regex_match(self):
        '''
        获取实体识别通过regex去match的识别的实体
        :return:记录集合
        '''
        sql = "select entity_name,entity_value,match from " + self.table_name + " where type='regex'"
        rows = self.db.select(sql_select=sql)
        return rows

    def del_match(self, match: str, entity_name: list):
        '''
        删除ner的match记录
        :param match: match内容
        :param entity_name: 实体名称
        :return:
        '''
        sql = f"delete from {self.table_name} where "
        if match:
            sql = sql + f"match='{match}' and "
        if len(entity_name) > 0:
            entity_name.append("")
            # delete from entity_match where entity_name in ('color') and true
            sql = sql + f"entity_name in {tuple(entity_name)} and "
        if match or len(entity_name) > 0:
            sql = sql + 'true';
            logger.debug(f"delete ner match and sql is: {sql}")
            return self.db.delete(sql_del=sql)
        else:
            raise ValueError(f"match and entity_name is None.")


if __name__ == "__main__":
    pass
