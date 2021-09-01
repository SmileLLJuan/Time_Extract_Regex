#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/27 16:40
# @Author  : lilijuan
# @File    : get_time_entities.py
import regex as re
year_regex = "(?P<year>([今本去前]年|(((20|19)\d{2})|((二零|一九)[零一二三四五六七八九]{2}))[年\-/.]|((最)?(这|近|前|过去|曾经)?(这)?([一二三四五六七八九十两1-9]{1,2}))年)[之以]?(前|内|中|左右)?)?"
half_year_regex = "(?P<half_year>(((((最)?(这|近|前|过去|曾经)(这)?)|(上|下))半年[之以]?(前|内|中)?)|(年终|年末|年尾|年中|年初)))?"
month_regex = "(?P<month>(((这|前|近|过去|去|曾经)?([1-9]{1,2})个?)|([这上本前]个?)|((0?[1-9]|1[0-2])))[月\-/.](份)?[之以]?(前|内|左右|末|初|中)?|(?<=(20|19)\d{2}[年|/.|/-])(1[0-2]|0?[1-9])?)?"
half_month_regex="(?P<half_month>((((这|近|前|过去|曾经)(这)?)|(上|下)|)半(个)?月[之以]?(前|内|中)?|(上旬|下旬|中旬)|(月初|月末|月中)))?"
week_regex = "(?P<week>(前|这|过去|近|去|曾经)?((上*|下*|这|本)个?(周|星期)+[1-7]?|[0-9]{1,2}个?(周|星期))[之以]?(前|内|中|左右)?)?"
# day_regex = "(?P<day>(((前|过去|这|近|近这|最近|最近这|曾经)([半1-9]{1,2}))|[今昨前]|([012]?[0-9]|30|31))(天|日|号| )[之以]?(前|内|左右)?)?"
day_regex = "(?P<day>(((前|过去|这|近|近这|最近|最近这|曾经)([半1-9]{1,2}))|[今昨前]|([012]?[0-9]|30|31))(天|日|号| )[之以]?(前|内|左右)?|(?<=(20|19)\d{2}[年|/.|/-](1[0-2]|0?[1-9])[月|/.|/-])(3[1-2]|[1-2][1-9]|0?[1-9])?)?"
mid_day_regex = "(?P<mid_day>(上午|下午|晌午|中午|午时|早上|晚上|黄昏|深夜|凌晨|傍晚|夜晚|夜里|深夜)?)?"
hour_regex = "(?P<hour>(上|前|过去|去|近|曾经)?(([半0-9]{1,2})个?小?(时|时辰)|([0-9]|1[0-9]|2[0-3])(点|时|：|:))([之以]?(前|内|中|左右|整|半)?))?"
minute_regex = "(?P<minute>(((前|过去|近|曾经)?([0-9]{1,2}))|([0-9]|[1-5][0-9]))(分|分钟|：|:| )[之以]?(前|内|中|左右)?|(?<=(时|点|(2[0-3]|1[0-9]|0?[1-9]:)))([1-5][0-9]|0?[1-9]))?"
seconds_regex = "(?P<seconds>(((前|过去|近|曾经)?([0-9]{1,2}))|([0-9]|[1-5][0-9]))(秒|秒钟| )[之以]?(前|内|中)?|(?<=(分|((2[0-3]|1[0-9]|0?[1=9]):([1-5][0-9]|0?[1-9]):)))([1-5][0-9]|0?[0-9]))?"
holiday_regex="(?P<holiday>(十一|五一|劳动节|国庆节|元旦|妇女节|平安夜|圣诞节|万圣节|情人节|植树节|青年节|护士节|儿童节|建党节|建军节|双十一|双十二)?)?"
time_regex_str =year_regex+half_year_regex+month_regex+half_month_regex+week_regex+day_regex+holiday_regex+mid_day_regex+hour_regex+minute_regex+seconds_regex
def get_entity_by_regex(text):
    entities = {}
    match = re.finditer(time_regex_str, text)
    for m in match:
        mdic = m.groupdict()
        for m2 in mdic:
            if mdic[m2]:
                entities[m2] = mdic[m2]
    return entities

def get_time_entities(time_ner_model,text,use_ner=False):
    if use_ner:
        bert_entities = time_ner_model.process_transformer_entities(text)
        # print("bert_entities",bert_entities)
        # 相邻 相同实体合并  相邻实体合并，相同实体保留一个
        entities = {}
        for e in bert_entities[0]:
            if e['entity'] in entities:
                if e['value'] == entities[e['entity']]['value']:
                    continue
                else:
                    if e['start'] == entities[e['entity']]['end']:  #一个实体拆分成了两个
                        new_entity = {"value": entities[e['entity']]['value'] + e['value'],
                                      "confidence": (entities[e['entity']]['confidence'] + e['confidence']) / 2,
                                      "start": entities[e['entity']]['start'],
                                      "end": e['end']}
                        entities[e['entity']] = new_entity
            else:
                entities[e['entity']] = {"value": e['value'], "confidence": e['confidence'], 'start': e['start'],"end": e['end']}
        entities=dict([(k,v['value']) for k,v in entities.items()])
    regex_entities = get_entity_by_regex(text)
    if use_ner:
        for k,v in regex_entities.items():
            if (v!=None and v!="") and k not in entities:
                entities[k] = v
            else:
                continue
    else:
        entities=regex_entities
    return entities


if __name__ == '__main__':
    from nlu.ner.ner_predict import BertNer
    from llj_test.time_extract.time_extract_ner.Time_BertNer_train import data
    from llj_test.time_extract.time_extract_ner.time_text_process import ner_predict_preprocess
    project = data['project']
    ner_model={}
    ner_model[project] = BertNer(project=project)
    with open("../../../llj_test/time_extract/time_extract_data/time_texts", "r", encoding='utf-8') as f:
        texts = f.readlines()
    # texts=["上上周2","上上周","下周","周3","下d周","上周星期2 下午2点","上星期2"]
    for text in texts:
        text=ner_predict_preprocess(text)
        # match = re.search("(前|这|过去|近|去|曾经)?([0-9]{1,2}个(周|星期)|(上*|下|这|本)(周|星期)[1-7]?)[之以]?(前|内|中|左右)?",text)
        # print(text,match)
        if len(text)>1:
            text_list=re.split("[到至和~]", text)
            for t in text_list:
                print(t,get_time_entities(ner_model[project],t,use_ner=False))

