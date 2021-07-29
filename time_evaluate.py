#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/7/26 13:47
# @Author  : lilijuan
# @File    : time_evaluate.py
import os,sys
import time
from datetime import datetime
from dateutil import tz
NYC = tz.gettz('Asia/Shanghai')
import json
import pandas as pd

with open("./data/time_texts", "r", encoding='utf-8') as f:
    texts=f.readlines()
print(len(texts),texts)

baseDate = datetime.now(tz=NYC)
baseDate = time.strftime('%Y-%m-%d %H:00:00', time.localtime())
print(baseDate)
def TimeNormalizer_evaluate():
    from app.TimeNormalizer import TimeNormalizer  # 引入包
    tn = TimeNormalizer()
    for text in texts:
        time_parse=tn.parse(target=text, timeBase=baseDate)
        print(time_parse, text.replace("\n", ""))

def result_wirte(pd_results,file):
    file_name = file.split("/")[-1:][0]
    file_dir=file.replace(file_name,'')
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    pd_results.to_csv(file,encoding="utf8",index=False,columns=["texts","results"])


if __name__ == '__main__':
    print(sys.path)
    TimeNormalizer_evaluate()
    pass

