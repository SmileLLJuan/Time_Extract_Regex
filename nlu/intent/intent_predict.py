'''
Created on 2020-8-19

@author: zhangjiwei
'''
import os
import logging

from nlu.matcher.intent_matcher import IntentMatcher
from transformers import AutoConfig, BertTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import gc

from utils.url import get_intent_model_dir

logger = logging.getLogger(__name__)


class BertTextIntent(object):
    '''
    classdocs
    '''

    def __init__(self, project="default"):
        self.project = project
        self.model_name_or_path = get_intent_model_dir(self.project)
        self.config = AutoConfig.from_pretrained(self.model_name_or_path)
        self.tokenizer = BertTokenizer.from_pretrained(self.model_name_or_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name_or_path)
        self.classifnlp = pipeline('sentiment-analysis', self.model, self.config, self.tokenizer)

    def predict_classfications(self, text):
        intent_ranking = self.classifnlp(text)
        for intents in intent_ranking:
            logger.debug(intents[0])
        return intent_ranking


intent_model = {}
intent_matcher = {}


def intent_predict(project: str, text):
    '''
    意图分类模型预测
    :param project: 所属项目名称
    :param text: 待预测文本
    :return:
    '''
    intent_rank = []
    if project not in intent_model:
        intent_model[project] = BertTextIntent(project=project)

    bot_id = project.split('.')[0]
    if bot_id not in intent_matcher:
        intent_matcher[bot_id] = IntentMatcher(bot_id=bot_id)

    # intent_matcher
    pro = None if len(project.split('.')) <= 1 else project.split('.')[1]
    matcher_intent_rank = intent_matcher[bot_id].bulk_matcher(text, pro)

    # bert
    bert_intent_rank = intent_model[project].predict_classfications(text)
    for x, y in zip(matcher_intent_rank, bert_intent_rank):
        intent_rank.append(x + y)
    return intent_rank
