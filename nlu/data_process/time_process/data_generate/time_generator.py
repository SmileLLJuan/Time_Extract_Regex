#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/11 18:46
# @Author  : lilijuan
# @File    : time_generator.py
import re
import rstr
import random
def regex_2_str(origin_str,count=1):
    #传入字符串格式${lll}[lll] eg:${((20|19)\d{2}年)?}[year]
    正则表达式=re.findall("\{(\S*?)\}(?=\[.*\])", origin_str)[0]
    实体名称= origin_str.replace(正则表达式, "").replace("{}", "")
    # print("实体类型",实体名称, "实体正则表达式", 正则表达式)
    field_value_list = []
    while len(field_value_list)<count:
        format_regex = r'{}'.format(正则表达式)
        field_value = rstr.xeger(format_regex)
        if len(field_value)>0:
            field_value_list.append(origin_str.replace(正则表达式,field_value).replace("[","(").replace("]",")").replace("{","[").replace("}","]"))
    return field_value_list[random.randint(0, len(field_value_list) - 1)]

def line_regex_generate(line,生成样本个数=50):
    regex_rstr_list = [s for s in line.split("$") if len(s)>0]
    generate_str_list = []
    for i in range(生成样本个数):
        generate_str = ""
        for s in regex_rstr_list:
            generate_str_1 = regex_2_str(s, 3)
            generate_str +=generate_str_1
        if len(generate_str)>0:
            generate_str_list.append(generate_str)
    return generate_str_list

class time():
    def __init__(self):
        with open("/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/time_extract/time_extract_data/time_samples_regex", "r", encoding='utf-8') as f:
            lines = f.readlines()
        lines = [line.replace("\n", "") for line in lines if len(line) > 3]
        self.lines=lines
    def generate(self):
        line=self.lines[random.randint(0, len(self.lines) - 1)]
        generate_str_list=line_regex_generate(line,生成样本个数=3)
        if len(generate_str_list)>0:
            if random.randint(0, 1):
                generate_str_1 = line_regex_generate(line, 生成样本个数=3)[0]
                generate_str_2 = line_regex_generate(line, 生成样本个数=3)[0]
                if len(generate_str_1) > 0 and len(generate_str_2) > 0:
                    generate_str = ["", "从"][random.randint(0, 1)] + generate_str_1 + ["到", "至"][
                        random.randint(0, 1)] + generate_str_2
                    return generate_str
            return generate_str_list[random.randint(0,len(generate_str_list)-1)]
        else:
            return ""


if __name__ == '__main__':
    for i in range(100):
        print(time().generate())
    # print(regex_2_str("{((20|19)\d{2}年)?}[year]",count=1))

