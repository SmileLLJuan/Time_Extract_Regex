# -*- coding:utf-8 -*-
# @Time: 2020/12/8 15:27
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: time_filter.py

'''时间过滤'''
import re

def filter_time(text:str):
    #第零种情况：空
    if not text or not text.strip():
        return True
    #第一种情况：只有单个字
    if text in ["和", "到", "至", "~", "日", "号", "天", "年", "月", "分", "秒","时"]:
        return True
    #第二种情况：一号 二号
    text = re.sub("[0-9一二三四五六七八九十]号","",text)
    if len(text) == 0:
        return True
    return False
