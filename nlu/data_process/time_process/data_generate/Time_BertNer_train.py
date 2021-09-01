#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/19 14:24
# @Author  : lilijuan
# @File    : Time_BertNer_train.py
import shutil
import os,re
from nlu.intent.intent_train import BertIntent
from nlu.status import NluTrainStatus
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
data={
    "text": "start",
    "bot_id":"robot20210809",
    # "project": "IOT21_yunyao.cmd_dm",
    "project": "project_time",
    # "train_data": "/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/data/default/nlu.md",
    # "train_data": "/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/data/time_extract_data/time_samples.md",
    "train_data": "/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/time_extract/time_extract_data/time.md",
    "train_kind": 0,
    "train_parameter": [
        {
            "model_type": "ner",
            "num_train_epochs": 2,
            "model_name_or_path": "albert_chinese_base",
            "per_gpu_train_batch_size": 16
        },
        {
            "model_type": "intent",
            "num_train_epochs": 10,
            "model_name_or_path": "albert_chinese_base",
            "per_gpu_train_batch_size": 64
        }
    ]
}
to_bot_id=data['project']
project=data['project']
train_data=data['train_data']
train_kind=data['train_kind']
train_status = NluTrainStatus(project=project, train_kind=train_kind)
train_parameter=data['train_parameter']

def ner_train():
    from nlu.ner.ner_train import BertNer
    ner = BertNer()
    ner.train(project=project, train_data=train_data, train_status=train_status, train_parameter_total=train_parameter)
if __name__ == '__main__':
    ner_train()