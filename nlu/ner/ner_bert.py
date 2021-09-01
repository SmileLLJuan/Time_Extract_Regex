#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/31 18:52
# @Author  : lilijuan
# @File    : ner_bert.py
import logging
from nlu.utils.ner_token import get_entities_from_token
from transformers import AutoConfig, AutoModelForTokenClassification, BertTokenizer
from transformers import pipeline
from utils.url import get_ner_model_dir

logger = logging.getLogger(__name__)
class BertNer(object):
    def __init__(self, project="default"):
        self.project = project
        # self.model_name_or_path = os.path.join(get_ner_model_dir(self.project),"last_model")
        self.model_name_or_path = get_ner_model_dir(self.project)
        print("model_name_or_path",self.model_name_or_path)
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
