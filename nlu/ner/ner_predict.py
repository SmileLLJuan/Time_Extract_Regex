'''
Created on 2020-8-7

@author: zhangjiwei
'''
import logging
import os

from nlu.matcher.entity_matcher import EntityMatcher
from nlu.utils.ner_remove import _remove_include_entities
from nlu.utils.ner_token import get_entities_from_token
from transformers import AutoConfig, AutoModelForTokenClassification, BertTokenizer
from nlu.data_process.time_process.custom_time_regrex_parse import CustomTimeParse
from transformers import pipeline
from utils.url import get_ner_model_dir

logger = logging.getLogger(__name__)


class BertNer(object):
    def __init__(self, project="default"):
        self.project = project
        # self.model_name_or_path = os.path.join(get_ner_model_dir(self.project),"last_model")
        self.model_name_or_path = get_ner_model_dir(self.project)
        self.config = AutoConfig.from_pretrained(self.model_name_or_path)
        self.tokenizer = BertTokenizer.from_pretrained(self.model_name_or_path)
        self.model = AutoModelForTokenClassification.from_pretrained(self.model_name_or_path)
        self.nlp = pipeline('ner', self.model, self.config, self.tokenizer, ignore_labels=[])

    def process_transformer_entities(self, message_text):
        '''
        基于bert进行token标签的识别和实体名称的合成
        :param message_text: 待识别文字
        :return:
        '''
        all_entities = []
        # 实体预测
        all_tokens = self.nlp(message_text)
        logger.info(f'Bert predict the token labels is:\n {all_tokens}')
        for token in all_tokens:
            entities = get_entities_from_token(token)
            all_entities.append(entities)
        return all_entities


# bert处理
ner_model = {}
# matcher处理
ner_matcher = {}
# 时间处理方法
time_parse_dic = {}


def bulk_ner_predict(project, texts):
    '''

    :param project:
    :param text:
    :return:
    '''
    if project not in ner_model:
        ner_model[project] = BertNer(project=project)
    bot_id = project.split('.')[0]
    if bot_id not in ner_matcher:
        ner_matcher[bot_id] = EntityMatcher(bot_id=bot_id)
    if project not in time_parse_dic:
        time_parse_dic[project] = CustomTimeParse(project=project)

    entities = []
    # 1.基于内置正则识别
    texts, matcher_entities = ner_matcher[bot_id].bulk_matcher(texts)
    logger.info("matcher::{0}".format(matcher_entities))
    # 2. bert模型识别
    bert_entities = ner_model[project].process_transformer_entities(texts)
    logger.info("bert::{0}".format(bert_entities))
    for x, y in zip(matcher_entities, bert_entities):
        entities.append(x + y)

    # # 3.移出包含实体
    entities = [_remove_include_entities(entity) for entity in entities]
    logger.info("parse_entity_component,移出包含实体::{0}".format(entities))
    #
    # # 4.几个时间有关特殊处理
    entities = [time_parse_dic[project].special_field_process(entity) for entity in entities]
    logger.info("parse_entity_component,时间有关特殊处理::{0}".format(entities))
    # 5.返回
    return texts, entities

if __name__ == '__main__':
    project = "default"
    texts = ["黑ddjh5ei港的拥有者", "请查找非出租屋筒子楼", "搜索设备图书馆2", "查询本个月30号凌晨13时零分31秒钟以内仪丰快捷宾馆分局辅助接警", "上个月10号凌晨4点西兴派出所接警",
             "请找一下泽楚路37", "请检索驾驶人员", "查下副驾驶上坐着的是谁", "查下今天上午12点海康威视东南门驶过的红色奥迪车"]
    texts, entities=bulk_ner_predict(project=project, texts=texts)
    for text,entity in zip(texts,entities):
        print(text,entity)
