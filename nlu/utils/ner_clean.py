# -*- coding:utf-8 -*-
# @Time: 2021/5/13 15:01
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: ner_clean.py
import re
from zhon import hanzi
import string

from utils.nlu_config import NluConfig

punctuation_regex=r'['+string.punctuation+hanzi.punctuation+']'
nlu_config_dic={}

def clean(project,text):
    # to filter the Ai ya
    if project not in nlu_config_dic:
        nlu_config_dic[project] = NluConfig(project)
    ai_ya = nlu_config_dic[project].get_value("ai_ya", "啊哦吧哎呀")
    ya = r'[' + ai_ya + ']'
    text = re.sub(ya, '', text)
    # 去掉空格
    text = ''.join(text.split())
    # 去掉所有的符号
    text = re.sub(punctuation_regex, '', text)
    return text