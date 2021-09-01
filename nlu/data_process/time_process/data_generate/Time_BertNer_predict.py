#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/12 9:25
# @Author  : lilijuan
# @File    : Time_BertNer_predict.py
import shutil
import os
import regex as re
from nlu.ner.ner_predict import BertNer
from llj_test.time_extract.time_extract_ner.Time_BertNer_train import data
project=data['project']
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from dateutil.tz import tz
NYC = tz.gettz('Asia/Shanghai')
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
holiday_dict={"双十一":"11月11日",
              "双11":"11月11日",
              "双12":"12月12日",
              "双十二":"12月12日",
              "十一":"10月1日",
              "五一":"5月1日",
              "元旦":"1月1日",
              "情人节":"2月14日",
              "妇女节":"3月8日",
              "植树节":"3月12日",
              "白色情人节":"3月14日",
              "国际消费者权益日":"3月15日",
              "愚人节":"4月1日",
              "清明节":"4月5日",
              "劳动节":"5月1日",
              "青年节":"5月4日",
              "儿童节":"6月1日",
              "全国爱眼日":"6月6日",
              "中国人民抗日战争纪念日":"7月7日",
              "建军节":"8月1日",
              "国际青年节":"8月2日",
              "教师节":"9月10日",
              "国庆节":"10月1日",
              "万圣节":"10月31日",
              "世界足球日":"12月9日",
              "平安夜": "12月24日",
              "圣诞节":"12月25日",
              }



def process_timedelta(start_timedelta, end_timedelta,current_time=datetime.now(tz=NYC)):
    # start_timedelta 处理
    a=[(i,k) for i,(k,v) in enumerate(start_timedelta.items()) if v!=-1]
    最小时间单位=a[-1]if len(a)>0 else [0,"year"]
    # 最小时间单位 = [(i, k) for i, (k, v) in enumerate(start_timedelta.items()) if v != -1][-1]
    # print(list(timedelta.items())[:最小时间单位[0]+1],"*",最小时间单位,"*",list(timedelta.items())[最小时间单位[0]+1:])
    for k, v in list(start_timedelta.items())[:最小时间单位[0] + 1]:
        if v == -1:
            start_timedelta[k] = eval("current_time.{}".format(k))
    for k, v in list(start_timedelta.items())[最小时间单位[0] + 1:]:
        if k == "month":
            start_timedelta[k] = 1
        if k == "day":
            start_timedelta[k] = 1
        if k == "hour":
            start_timedelta[k] = 0
        if k == "minute":
            start_timedelta[k] = 0
        if k == "second":
            start_timedelta[k] = 0
    # end_timedelta 处理
    a = [(i, k) for i, (k, v) in enumerate(end_timedelta.items()) if v != -1]
    最小时间单位 = a[-1] if len(a) > 0 else [0, "year"]
    for k, v in list(end_timedelta.items())[:最小时间单位[0] + 1]:
        if v == -1:
            end_timedelta[k] = start_timedelta[k]
        else:
            if k == 'hour' and (start_timedelta["day"] > end_timedelta["day"] or start_timedelta["day"] == end_timedelta["day"]) and \
                    start_timedelta[k] > end_timedelta[k]:  # 3月晚上11点到凌晨5点
                end_timedelta['day'] = (current_time.replace(year=end_timedelta['year'], month=end_timedelta['month'],
                                                             day=end_timedelta['day']) + relativedelta(days=+1)).day

    for k, v in list(end_timedelta.items())[最小时间单位[0] + 1:]:
        if k == "month":
            end_timedelta[k] = 12
        if k == "day":
            _ = current_time.replace(year=end_timedelta['year'], month=end_timedelta["month"], day=1, hour=0,minute=0, second=1) + relativedelta(months=+1, days=-1, seconds=-1)
            end_timedelta['year'] = _.year
            end_timedelta['month'] = _.month
            end_timedelta[k] = _.day
        if k == "hour":
            end_timedelta[k] = 23
        if k == "minute":
            end_timedelta[k] = 59
        if k == "second":
            end_timedelta[k] = 59
    return start_timedelta, end_timedelta

def ner_predict(current_time=datetime.now(tz=NYC)):
    from nlu.data_process.time_process.convert_time_str import TimeStrConvert
    from llj_test.time_extract.time_extract_ner.get_time_entities import get_time_entities
    convert = TimeStrConvert()
    with open("../time_extract_data/time_texts", "r", encoding='utf-8') as f:
        texts = f.readlines()
    texts=[text.replace("\n","")for text in texts if len(text)>3]
    # print(len(texts), texts)
    ner_model={}
    ner_model[project] = BertNer(project=project)
    for text in texts:
        text=ner_predict_preprocess(text)
        text_list = re.split("[到至和~]", text)
        if len(text_list)>1:
            entities1 = get_time_entities(ner_model[project], text_list[0])
            entities2 = get_time_entities(ner_model[project], text_list[1])
            for key in entities1.keys():
                if key not in entities2.keys():
                    entities2[key] = entities1[key]
            str_1 = convert.pre_time_transformation(entities1)
            str_2 = convert.pre_time_transformation(entities1)
            str = str_1[1].split(",")[0] + "," + str_2[1].split(",")[1]
            print(str)

        else:
            entities = get_time_entities(ner_model[project], text)
            str=convert.pre_time_transformation(entities)
            print(text,entities,str)

            # for t in text_list:
            #
            #     text_time_list.append((timestamp,start_timedelta,end_timedelta))
            #     # print("??",t,timestamp,start_timedelta,end_timedelta,entities)
            # start_timedelta_1 = text_time_list[0][1]
            # end_timedelta_1 = text_time_list[0][2]
            # start_timedelta_2 = text_time_list[-1][1]
            # end_timedelta_2 = text_time_list[-1][2]
            #
            # start_timedelta= dict([(k, v) if v != -1 else ((k, end_timedelta_1[k]) if end_timedelta_1[k] != -1 else (k, -1)) for k, v in start_timedelta_1.items()])
            # end_timedelta = dict([(k, v) if v != -1 else ((k, start_timedelta_2[k]) if start_timedelta_2[k] != -1 else (k, -1)) for k, v in end_timedelta_2.items()])
            # print("$$",text,start_timedelta,end_timedelta)
        # else: #
        #     entities = get_time_entities(ner_model, text)
        #     timestamp,start_timedelta,end_timedelta = entities_time_transformation(text, entities)
        #     print("$$",text,entities,start_timedelta,end_timedelta)
        #
        # start_timedelta,end_timedelta=process_timedelta(start_timedelta,end_timedelta)
        # set_time=lambda x:current_time.replace(year=x['year'],month=x['month'],day=x['day'],hour=x['hour'],minute=x['minute'],second=x['second'],)
        # start_time=set_time(start_timedelta)
        # end_time=set_time(end_timedelta)
        #
        # print("##",text,start_time,end_time)



mid_day_time_dic = {"(上午|晌午)":[6,11],
                   "(下午)":[12,18],
                   "(中午)":[11,13],
                   "(晚上|夜晚|夜里)":[18,23],
                   "(早上|早晨)":[6,9],
                   "(凌晨)":[1,5],
                   "(傍晚)":[15,17],
                   "(黄昏)":[17,19],
                   "(深夜)":[21,23]
                   }

def entities_time_transformation(text,entities):   #entities 字典转化成 时间表示
    current_time=datetime.now(tz=NYC)
    timestamp=current_time
    start_timedelta={"year":-1,"month":-1,"day":-1,"hour":-1,"minute":-1,"second":-1}
    end_timedelta={"year":-1,"month":-1,"day":-1,"hour":-1,"minute":-1,"second":-1}
    ## 绝对时间 & 相对时间 处理
    time_span=False
    #year
    if "year" in entities:
        value=0  # 今年|本年
        if "去年" in entities['year']['value']:
            value=1
        if "前年" in entities['year']['value']:
            value=2
        timestamp=timestamp.replace(year=timestamp.year-value,month=1,day=1,hour=0,minute=0,second=0)
        # 过去 3年
        match_2 = re.search("(?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经))[0-9]{1,2}(?=年)|^[0-9]{1,2}(?=年)",entities['year']['value'])
        match_1=None
        if match_2:
            timestamp = timestamp.replace(year=timestamp.year - int(match_2.group()), month=1, day=1, hour=0,minute=0, second=0)
            time_span=True
        else:#2021年
            match_1=re.search("(20|19)\d{2}(?=年)",entities['year']['value'])
            if match_1:
                timestamp = timestamp.replace(year=int(match_1.group()), month=1, day=1, hour=0, minute=0, second=0)
                time_span=False
        # 2021年左右  2年左右
        suffix_match = re.search("个?(年|月|周|天|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", text)
        if suffix_match:
            if suffix_match.group()[-2:]=="左右":
                if match_1:#2021年左右
                    timestamp = timestamp.replace(year=timestamp.year + 1, month=1, day=1, hour=0, minute=0,second=0) - relativedelta(seconds=1)
                    time_span=False
                if match_2:#2年左右
                    time_span = True
        start_timedelta['year'] = timestamp.year
        end_timedelta['year'] = current_time.year if time_span else timestamp.year

        # print("year",entities['year']['value'],timestamp,end_time)
    if "half_year" in entities:
        #过去半年
        match = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经|^))半年)",entities['half_year']['value'])
        if match:
            timestamp = timestamp.replace(day=1)+relativedelta(months=-6)
            start_timedelta['month'], start_timedelta['day'] = timestamp.month, 1
            end_timedelta['month'], end_timedelta['day'] = current_time.month,current_time.day
        if "上半年" in entities['half_year']['value']:
            timestamp = timestamp.replace(month=1, day=1, hour=0, minute=0, second=0)
            start_timedelta['month'],start_timedelta['day']=1,1
            end_timedelta['month'],end_timedelta['day']=6,30
        if "下半年" in entities['half_year']['value']:
            timestamp = timestamp.replace(month=7, day=1, hour=0, minute=0, second=0)
            start_timedelta['month'], start_timedelta['day'] =7, 1
            end_timedelta['month'], end_timedelta['day'] = 12, 31
        if "年初" in entities['half_year']['value']:
            timestamp = timestamp.replace(month=1, day=1, hour=0, minute=0, second=0)
            start_timedelta['month'], start_timedelta['day'] = 1, 1
            end_timedelta['month'], end_timedelta['day'] = 4, 30
        if "年中" in entities['half_year']['value']:
            timestamp = timestamp.replace(month=5, day=1, hour=0, minute=0, second=0)
            start_timedelta['month'], start_timedelta['day'] = 5, 1
            end_timedelta['month'], end_timedelta['day'] = 8, 31
        if re.search("(年终|年底|年末|年尾)",entities['half_year']['value']):
            timestamp = timestamp.replace(month=9, day=1, hour=0, minute=0, second=0)
            start_timedelta['month'], start_timedelta['day'] = 9, 1
            end_timedelta['month'], end_timedelta['day'] = 12, 31
        # print("half_year",entities['half_year']['value'],start_time,end_time)

    if "month" in entities:
        match=re.search("(本|这|前|上|上上|下|下下)(个)?月",entities['month']['value'])
        if match:
            value=0
            if re.search("(本|这)(个)?月",match.group()):
                value=0
            if re.search("(前|上)(个)?月",match.group()):
                value=-1
            if re.search("(上上)(个)?月",match.group()):
                value = -1
            if re.search("(下)(个)?月",match.group()):
                value = 1
            if re.search("(下下)(个)?月",match.group()):
                value = 2
            timestamp = timestamp.replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=value, seconds=-1)
        time_span=False
        match_2 = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经))[0-9]{1,2}|^[0-9]{1,2})(?=个月)",entities['month']['value'])
        if match_2: #过去3个月
            timestamp = timestamp.replace(month=timestamp.month, day=1, hour=0, minute=0, second=0) - relativedelta(months=int(match_2.group()))
            time_span=True
        else:#n月份
            match_1 = re.search("((10|11|12|0?[1-9])(?=(月份?))|(10|11|12|0?[1-9])$)", entities['month']['value'])
            if match_1:
                timestamp = timestamp.replace(month=int(match_1.group()), day=1, hour=0, minute=0, second=0)
                time_span = False
        #n个月，与 n月份区分
        suffix_match = re.search("个?(年|月|月份|周|天|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", text)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右" and suffix_match.span()[0]+1==entities['month']['end']:
                if match_1:#n月份左右
                    timestamp = timestamp.replace(day=1, hour=0, minute=0,second=0)+relativedelta(months=1,seconds=-1)
                    time_span = False
                if match_2: #n个月左右
                    timestamp = timestamp.replace(month=int(match_2.group()),day=1, hour=0, minute=0,second=0)
                    time_span = True
                    # return datetime.strftime(start_time, "%Y-%m-%d %H:%M:%S"), datetime.strftime(end_time,"%Y-%m-%d %H:%M:%S")
        start_timedelta["month"] = timestamp.month
        end_timedelta["month"] = current_time.month if time_span else timestamp.month
        # print("month",entities['month']['value'],start_time,end_time)


    if "half_month" in entities:
        if re.search("上半个?月",entities['half_month']['value']):
            timestamp = timestamp.replace(day=1, hour=0, minute=0, second=0)
            start_timedelta['day'] = 1
            end_timedelta['day'] = 15
        if re.search("上半个?月",entities['half_month']['value']):
            timestamp = timestamp.replace(day=16, hour=0, minute=0, second=0)
            start_timedelta['day'] = 16
            end_timedelta['day'] = (timestamp.replace(month=(timestamp.month+1),day=1,hour=0,minute=0,second=0)-timedelta(seconds=1)).day
        if re.search("(上旬|月初)", entities['half_month']['value']):
            timestamp = timestamp.replace(day=1, hour=0, minute=0, second=0)
            start_timedelta['day'] = 1
            end_timedelta['day'] =10
        if re.search("(中旬|月中)", entities['half_month']['value']):
            timestamp = timestamp.replace(day=11, hour=0, minute=0, second=0)
            start_timedelta['day'] = 11
            end_timedelta['day'] = 20
        if re.search("(下旬|月终|月末|月底|月尾)", entities['half_month']['value']):
            timestamp = timestamp.replace(day=21, hour=0, minute=0, second=0)
            start_timedelta['day'] = 21
            end_timedelta['day'] = (timestamp.replace(month=(timestamp.month+1),day=1,hour=0,minute=0,second=0)-timedelta(seconds=1)).day

        # print("half_month",entities['half_month']['value'],start_time,end_time)

    if "week" in entities:
        time_span=True
        match = re.search("(本|这|前|上*|下*)(个)?(周|星期)[1-7]", entities['week']['value'])
        if match:
            m = re.search("(?<=(本|这|^)(个)?(周|星期))[1-7]", entities['week']['value'])
            if m:  # 这周3 周3
                timestamp = timestamp.replace(hour=0, minute=0, second=0) + timedelta(days=int(m.group()) - 1 - timestamp.weekday())
                time_span=True
            m = re.search("上+(?=(个)?(周|星期))", entities['week']['value'])  #上上周4
            if m:   #上上个星期6
                timestamp = timestamp - timedelta(days=(7 * len(m.group())))
                m = re.search("(?<=[个?(周|星期)])[1-7]", match.group())
                if m:
                    timestamp = timestamp - timedelta(days=(timestamp.weekday() - int(m.group()) + 1))
                    time_span = False
            m = re.search("下+(?=(个)?(周|星期))", entities['week']['value'])
            if m:  #下下个周3
                timestamp = timestamp + timedelta(days=(7 * len(m.group())))
                m = re.search("(?<=[个?(周|星期)])[1-7]", match.group())
                if m:
                    timestamp = timestamp + timedelta(days=(int(m.group()) - timestamp.weekday()) - 1)
                    time_span = False
        #3周
        match = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经|^))[1-9]{1,2}(?=(个)?(周|星期)))", entities['week']['value'])
        if match:
            timestamp = timestamp.replace(hour=0,second=0,minute=0) - timedelta(days=7 * int(match.group()))
        suffix_match = re.search("个?(年|月|月份|周|星期|天|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", text)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右" and suffix_match.span()[0]+1==entities['week']['end']: #3周左右
                time_span=True
                # return datetime.strftime(start_time, "%Y-%m-%d %H:%M:%S"), datetime.strftime(end_time,"%Y-%m-%d %H:%M:%S")
        start_timedelta['year'] = timestamp.year
        start_timedelta['month'] = timestamp.month
        start_timedelta['day'] = timestamp.day
        if time_span:
            end_timedelta['year'] = current_time.year
            end_timedelta['month'] = current_time.month
            end_timedelta['day'] = current_time.day
        else:
            end_timedelta['year'] = timestamp.year
            end_timedelta['month'] = timestamp.month
            end_timedelta['day'] = timestamp.day
        # print("week",entities['week']['value'],start_time,end_time)

    if "day" in entities:
        time_span=False
        match = re.search("(今|本|昨|前|大前|明|后|大后)儿?天", entities['day']['value'])
        if match:
            if re.search("[今|本]儿?天", match.group()):
                timestamp = current_time.replace(month=current_time.month, day=current_time.day)
            if re.search("昨儿?天", match.group()):
                timestamp = current_time + timedelta(days=-1)
            if re.search("(?<!大)前儿?天", match.group()):
                timestamp = current_time + timedelta(days=-2)
            if re.search("大前儿?天", match.group()):
                timestamp = current_time + timedelta(days=-3)
            if re.search("明儿?天", match.group()):
                timestamp = current_time + timedelta(days=1)
            if re.search("(?<!大)后儿?天", match.group()):
                timestamp = current_time + timedelta(days=2)
            if re.search("大后儿?天", match.group()):
                timestamp = current_time + timedelta(days=3)
        #n天
        match_2 = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经))[0-9]{1,2}|^[0-9]{1,2})(?=[天|day])", text)
        match_1=None
        if match_2:
            timestamp = timestamp.replace(hour=0,minute=0,second=0)-timedelta(days=int(match_2.group()))
            time_span = True
        else:# 12号  5月4日
            match_1 = re.search("([012]?[0-9]|30|31)(?=(号|日))|([012]?[0-9]|30|31)$", entities['day']['value'])
            if match_1:
                timestamp = timestamp.replace(day=int(match_1.group()), hour=0, minute=0, second=0)
        suffix_match = re.search("个?(年|月|月份|周|星期|天|号|日|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", text)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右" and suffix_match.span()[0]+1==entities['day']['end']:  # 3周左右
                if match_1:#5月4号左右
                    timestamp = timestamp.replace(hour=0, minute=0,second=0)+relativedelta(days=1,seconds=-1)

                if match_2:#过去n天左右
                    time_span = True
        start_timedelta['day'] = timestamp.day
        end_timedelta['day'] = current_time.day if time_span else timestamp.day
        # print("day",entities['day']['value'],start_time,end_time)

    if "mid_day" in entities:
        match=re.search("上午|下午|晌午|中午|午时|早上|晚上|黄昏|深夜|凌晨|傍晚|夜晚|夜里|深夜",entities['mid_day']['value'])
        if match:
            for k, v in mid_day_time_dic.items():
                if match.group() in k:
                    timestamp = timestamp.replace(hour=mid_day_time_dic[k][0], minute=0, second=0)
                    start_timedelta['hour']=mid_day_time_dic[k][0]
                    end_timedelta['hour']=mid_day_time_dic[k][1]
        # print("mid_day",entities['mid_day']['value'],start_time,end_time)

    if "hour" in entities:
        time_span=False
        # n小时
        match_2 = re.search("((?<=[前|过去|过去的|这|近|近这|最近|最近这|曾经])[0-9]{1,2}|^[0-9]{1,2})(?=(个)?(小时))", text)
        match_1=None
        if match_2:
            timestamp = timestamp.replace(minute=0, second=0) - timedelta(hours=int(match_2.group()), minutes=0,seconds=0)
            time_span = True
        else:# 3点
            match_1=re.search("(1[0-9]|2[0-3]|0?[0-9])(?=(点|刻|时|hour|H|:|：))",entities['hour']['value'])
            if match_1:
                timestamp = timestamp.replace(hour=int(match_1.group()), minute=0, second=0)
                if "mid_day" in entities and re.search("(下午|晚上|晚上|黄昏|深夜|傍晚|夜晚|夜里|深夜)",entities['mid_day']['value']):
                    timestamp = timestamp+relativedelta(hours=12)
        suffix_match = re.search("个?(年|月|月份|周|星期|天|号|日|时|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)",text)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右" and suffix_match.span()[0]+1==entities['hour']['end']:
                if match_1:  #3点左右
                    timestamp = timestamp.replace(minute=0, second=0) + relativedelta(hours=1, seconds=-1)
                if match_2:  # 过去n小时左右
                    time_span = True
        start_timedelta['hour'] = timestamp.hour
        end_timedelta['hour'] =current_time.hour if time_span else timestamp.hour
        # print("hour",entities['hour']['value'],start_time,end_time)

    if "minute" in entities:
        time_span=False
        match_2 = re.search("((?<=[前|过去|过去的|这|近|近这|最近|最近这|曾经|^])[0-9]{1,2})(?=(个)?(分|分钟|minute))", text)
        match_1=None
        if match_2:  # 过去12分钟
            timestamp = timestamp.replace(second=0) - timedelta(minutes=int(match_2.group()), seconds=0)
            time_span=True
        else:
            match_1 = re.search("(?<=点零?)([1-5][0-9]|0?[0-9])(?=(分|分钟|minute|：|:|))", text)
            if match_1:  #12分
                timestamp = timestamp.replace(minute=int(match_1.group()),second=0)
        # match_2 = re.search("((?<=[前|过去|过去的|这|近|近这|最近|最近这|曾经])[0-9]{1,2}|^[0-9]{1,2})(?=(个)?(分|分钟|minute))",entities['hour']['value'])
        suffix_match = re.search("个?(年|月|月份|周|星期|天|号|日|时|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", text)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右" and suffix_match.span()[0]+1==entities['minute']['end']:
                if match_1:  # 12点12分左右
                    timestamp = timestamp.replace(second=0) + relativedelta(minutes=1, seconds=-1)
                if match_2:  # 过去n分左右
                    time_span=True
        start_timedelta['minute'] = timestamp.minute
        end_timedelta['minute'] = current_time.minute  if time_span else timestamp.minute
        print(timestamp,start_timedelta,end_timedelta)
        # print("minute",entities['minute']['value'],start_time,end_time)


    if "seconds" in entities:
        match_1 = re.search("([1-5][0-9]|0?[0-9])(?=(秒|秒钟|seconds|))", entities['seconds']['value'])
        if match_1:
            timestamp = timestamp.replace(second=int(match_1.group()))
            start_timedelta['second'] = timestamp.second
            end_timedelta['second'] = timestamp.second
        # print("seconds",entities['seconds']['value'],start_time,end_time)

    return timestamp,start_timedelta,end_timedelta
    # return datetime.strftime(start_time,"%Y-%m-%d %H:%M:%S"),datetime.strftime(end_time,"%Y-%m-%d %H:%M:%S")

def get_entity_by_regex(text):
    from llj_test.time_extract.time_extract_ner.time_entities_define import time_regex_str
    match = re.finditer(time_regex_str, text)
    regex_entities = [m.groupdict() for m in match][0] #只获取第一个吧
    return regex_entities
if __name__ == '__main__':

    ner_predict()
    pass