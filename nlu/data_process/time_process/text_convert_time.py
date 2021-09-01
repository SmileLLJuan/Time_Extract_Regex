#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/28 11:05
# @Author  : lilijuan
# @File    : text_convert_time.py
import os
import regex as re
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from dateutil.tz import tz
import traceback
os.environ["CUDA_VISIBLE_DEVICES"] = "1"
NYC = tz.gettz('Asia/Shanghai')
from nlu.data_process.time_process.StringPreHandler import StringPreHandler
from nlu.data_process.time_process.get_time_entities import get_time_entities
from nlu.ner.ner_bert import BertNer
import logging
logger = logging.getLogger(__name__)
def strftime(time, formart="%Y-%m-%d %H:%M:%S"):
    return time.astimezone(NYC).strftime(formart)
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

class TimeStrConvert:
    def __init__(self,project,use_ner=True):
        self.current_time=datetime.now(tz=NYC)
        start_time,end_time=self.current_time,self.current_time
        self.time_ner_model=BertNer(project=project)
        self.use_ner=use_ner

    # def string_get_time(self,text):
    def pre_time_range(self,text):
        time_list = re.split("[到至和~]", text)
        if len(time_list) == 1:
            # 首先获取dic
            dic = self.get_entities(time_list[0])
            self.text=time_list[0]
            start_time,end_time = self.time_entities_transformation(dic)
            # print("1",time_list,dic,start_time,end_time)
        else:
            dic_1 = self.get_entities(time_list[0])
            dic_2 = self.get_entities(time_list[1])
            for key in dic_1.keys():
                if key not in dic_2.keys():
                    dic_2[key] = dic_1[key]
            self.text = time_list[0]
            str_1 = self.time_entities_transformation(dic_1)
            self.text = time_list[1]
            str_2 = self.time_entities_transformation(dic_2)
            start_time,end_time=str_1[0],str_2[1]
            # print("2",time_list,dic_1,dic_2,start_time,end_time)
            # 解决19点到10点 类似问题
            if start_time:
                # 解决夸天的时间段问题
                if str(end_time) < str(start_time):
                    while str(end_time) < str(start_time):
                        end_time = end_time + relativedelta(days=1)
        start_time = strftime(start_time, "%Y-%m-%d %H:%M:%S")
        end_time = strftime(end_time, "%Y-%m-%d %H:%M:%S")
        str_ = start_time + "," + end_time
        return str_
    def pre_process(self,text):
        for k, v in holiday_dict.items():
            if k in text:
                text = re.sub(k, v, text)
        text = StringPreHandler.numberTranslator(text)  # 汉字->数字
        text = re.sub("[\\t\\n]", "", text)  # 删除制表符，不能删除空格
        pattern = "((周|星期)[一二三四五六七天末1-7])"  # 周63点
        match = re.search(pattern, text)
        if match:
            text = re.sub(match.group(), match.group() + " ", text)
        match = re.findall("[上|下](月初|月中|月末|月底)", text)  # 上月初->[上月](month)[月初](half_month)
        if match:
            text = re.sub(match[0], "月{}".format(match[0]), text)
        match = re.findall("[今|本](年终|年末|年尾|年中|年初)", text)  # 今年初->[今年](year)[年初](half_year)
        if match:
            text = re.sub(match[0], "年{}".format(match[0]), text)
        return text
    def get_entities(self,text):
        return get_time_entities(self.time_ner_model,text,use_ner=self.use_ner)
    def time_entities_transformation(self,dic):
        try:
            start_time=datetime.now(tz=NYC)
            end_time=datetime.now(tz=NYC)
            #判断顺序不能变
            if "year" in dic.keys():
                start_time,end_time = self.entity_year_time_range(dic["year"],start_time,end_time)
            if "half_year" in dic.keys():
                start_time,end_time = self.entity_half_year_time_range(dic["half_year"],start_time,end_time)
            if "month" in dic.keys():
                 start_time,end_time = self.entity_month_time_range(dic["month"],start_time,end_time)
            # print(text,"month",start_time,end_time)
            if "half_month" in dic.keys():
                 start_time,end_time = self.entity_half_month_time_range(dic["half_month"],start_time,end_time)
            # print(text,"half_month",start_time,end_time)
            if "week" in dic.keys():
                 start_time,end_time = self.entity_week_time_range(dic["week"],start_time,end_time)
            if "day" in dic.keys() :
                start_time,end_time = self.entity_day_time_range(dic["day"], start_time,end_time)
            if "holiday" in dic.keys():
                start_time, end_time = self.entity_holiday_range(dic["holiday"],start_time,end_time)
            if "mid_day" in dic.keys():
                start_time,end_time =  self.entity_mid_day_time_range(dic["mid_day"],start_time,end_time)
            if "hour" in dic.keys():
                start_time,end_time = self.entity_hour_time_range(dic["hour"],start_time,end_time)
            if "minute" in dic.keys():
                start_time,end_time = self.entity_minutes_time_range(dic["minute"],start_time,end_time)
            if "seconds" in dic.keys():
                start_time,end_time = self.entity_seconds_time_range(dic["seconds"],start_time,end_time)
            return start_time,end_time
        except Exception as e:
            logger.error("time_entities_transformation error :{}".format(e))
            traceback.print_exc()
    def entity_year_time_range(self,entity_value,start_time,end_time):
        if re.search("[今|本]年",entity_value):
            start_time = start_time.replace(year=start_time.year, month=1, day=1, hour=0, minute=0, second=0)
        if "去年" in entity_value:
            start_time = start_time.replace(year=start_time.year - 1, month=1, day=1, hour=0, minute=0, second=0)
        if "前年" in entity_value:
            start_time = start_time.replace(year=start_time.year - 2, month=1, day=1, hour=0, minute=0, second=0)
        end_time=end_time.replace(year=start_time.year,month=12,day=31,hour=23,minute=59,second=59)
        # 过去 3年
        match_2 = re.search("(?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经))[0-9]{1,2}(?=年)|^[0-9]{1,2}(?=年)",self.text)
        match_1 = None
        if match_2:
            start_time = start_time.replace(year=start_time.year - int(match_2.group()), month=1, day=1, hour=0,minute=0, second=0)
            end_time=self.current_time
        else:  # 2021年
            match_1 = re.search("(20|19)\d{2}(?=(年|/-|/.))", entity_value)
            if match_1:
                start_time = start_time.replace(year=int(match_1.group()), month=1, day=1, hour=0, minute=0, second=0)
                end_time = end_time.replace(year=start_time.year , month=12, day=31, hour=23,minute=59, second=59)
            # 2021年左右  2年左右
            suffix_match = re.search("个?(年|月|周|天|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", self.text)
            if suffix_match:
                if suffix_match.group()[-2:] == "左右":
                    if match_1:  # 2021年左右
                        start_time = start_time.replace(year=start_time.year + 1, month=1, day=1, hour=0, minute=0,second=0) - relativedelta(seconds=1)
                        end_time = end_time.replace(year=start_time.year, month=12, day=31, hour=23, minute=59,second=59)
                    if match_2:  # 2年左右
                        start_time = start_time.replace(year=start_time.year - int(match_2.group()), month=1, day=1,hour=0, minute=0, second=0)
                        end_time = self.current_time
        return start_time,end_time
    def entity_half_year_time_range(self,entity_value,start_time,end_time):
        match = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经|^))半年)", self.text)
        if match:# 过去半年
            start_time = start_time.replace(day=1) + relativedelta(months=-6)
            end_time=self.current_time
        if "上半年" in entity_value:
            start_time = start_time.replace(month=1, day=1, hour=0, minute=0, second=0)
            end_time=end_time.replace(month=6,day=30)
        if "下半年" in entity_value:
            start_time = start_time.replace(month=7, day=1, hour=0, minute=0, second=0)
            end_time = end_time.replace(month=12, day=31)
        if "年初" in entity_value:
            start_time = start_time.replace(month=1, day=1, hour=0, minute=0, second=0)
            end_time = end_time.replace(month=4, day=30)
        if "年中" in entity_value:
            start_time = start_time.replace(month=5, day=1, hour=0, minute=0, second=0)
            end_time = end_time.replace(month=8, day=31)
        if re.search("(年终|年底|年末|年尾)", entity_value):
            start_time = start_time.replace(month=9, day=1, hour=0, minute=0, second=0)
            end_time = end_time.replace(month=12, day=31)
        return start_time,end_time
    def entity_month_time_range(self,entity_value,start_time,end_time):
        match = re.search("(本|这|前|上|上上|下|下下)(个)?月", entity_value)
        if match:
            value = 0
            if re.search("(本|这)(个)?月", match.group()):
                value = 0
            if re.search("(前|上)(个)?月", match.group()):
                value = -1
            if re.search("(上上)(个)?月", match.group()):
                value = -2
            if re.search("(下)(个)?月", match.group()):
                value = 1
            if re.search("(下下)(个)?月", match.group()):
                value = 2
            start_time = start_time.replace(day=1, hour=0, minute=0, second=0) + relativedelta(months=value)
            end_time = end_time.replace(day=1, hour=23, minute=59, second=59) + relativedelta(days=-1)
        time_span = False
        match_2 = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经))[0-9]{1,2}|^[0-9]{1,2})(?=个月)",self.text)
        match_1=None
        if match_2:  # 过去3个月
            start_time = start_time.replace(month=start_time.month, day=1, hour=0, minute=0, second=0) - relativedelta(months=int(match_2.group()))
            end_time=self.current_time
        else:  # n月份
            match_1 = re.search("((10|11|12|0?[1-9])(?=(月份?))|(10|11|12|0?[1-9])$)", re.sub("[\-\.\/]","",entity_value))
            if match_1:
                start_time = start_time.replace(month=int(match_1.group()), day=1, hour=0, minute=0, second=0)
                end_time = start_time.replace(day=1, hour=23, minute=59, second=59) + relativedelta(months=+1,days=-1)
        # n个月，与 n月份 区分
        suffix_match = re.search("个?(年|月|月份|周|天|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", self.text)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右":
                if match_1:  # n月份左右
                    start_time = start_time.replace(month=int(match_1.group()), day=1, hour=0, minute=0, second=0)
                    end_time = end_time.replace(month=int(match_1.group()), day=1, hour=0, minute=0,second=0) + relativedelta(months=+1, seconds=-1)
                if match_2:  # n个月左右
                    start_time = start_time.replace(month=start_time.month, day=1, hour=0, minute=0,second=0) - relativedelta(months=int(match_2.group()))
                    end_time = self.current_time
        return start_time,end_time
    def entity_half_month_time_range(self,entity_value,start_time,end_time):
        if re.search("上半个?月",entity_value):
            start_time=start_time.replace(day=1, hour=0, minute=0, second=0)
            end_time=end_time.replace(day=15, hour=23, minute=59, second=59)
        if re.search("上半个?月",entity_value):
            start_time = start_time.replace(day=16, hour=0, minute=0, second=0)
            end_time = end_time.replace(day=1, hour=23, minute=59, second=59)+relativedelta(months=+1,days=-1)
        if re.search("(上旬|月初)", entity_value):
            start_time = start_time.replace(day=1, hour=0, minute=0, second=0)
            end_time = end_time.replace(day=10, hour=23, minute=59, second=59)
        if re.search("(中旬|月中)", entity_value):
            start_time = start_time.replace(day=11, hour=0, minute=0, second=0)
            end_time = end_time.replace(day=20, hour=23, minute=59, second=59)
        if re.search("(下旬|月终|月末|月底|月尾)", entity_value):
            start_time = start_time.replace(day=21, hour=0, minute=0, second=0)
            end_time = end_time.replace(day=1, hour=23, minute=59, second=59)+relativedelta(months=+1,days=-1)
        return start_time,end_time
    def entity_week_time_range(self,entity_value,start_time,end_time):
        match = re.search("(本|这|前|上*|下*)(个)?(周|星期)[1-7]", entity_value)
        if match:
            m = re.search("(?<=(本|这|^)(个)?(周|星期))[1-7]", entity_value)
            if m:  # 这周3 周3
                start_time = start_time.replace(hour=0, minute=0, second=0) + timedelta(days=int(m.group()) - 1 - start_time.weekday())
                end_time=start_time.replace(hour=23, minute=59, second=59)
            m = re.search("上+(?=(个)?(周|星期))", entity_value)  # 上上周4
            if m:  # 上上个星期6
                start_time = start_time - timedelta(days=(7 * len(m.group())))
                end_time=self.current_time
                m = re.search("(?<=[个?(周|星期)])[1-7]", match.group())
                if m:
                    start_time = start_time - timedelta(days=(start_time.weekday() - int(m.group()) + 1))
                    end_time=start_time.replace(hour=23, minute=59, second=59)
            m = re.search("下+(?=(个)?(周|星期))", entity_value)
            if m:  # 下下个周3
                start_time =self.current_time
                end_time=end_time + timedelta(days=(7 * len(m.group())))
                m = re.search("(?<=[个?(周|星期)])[1-7]", match.group())
                if m:
                    end_time = end_time.replace(hour=23,minute=59,second=59) + timedelta(days=(int(m.group()) - end_time.weekday()) - 1)
        # 3周
        match = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经|^))[1-9]{1,2}(?=(个)?(周|星期)))", self.text)  #这里是 text 不是entity_value,注意
        if match:
            start_time = start_time.replace(hour=0, second=0, minute=0) - timedelta(days=7 * int(match.group()))
            end_time=self.current_time
        suffix_match = re.search("个?(年|月|月份|周|星期|天|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", self.text)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右":  # 3周左右
                time_span = True
        return start_time,end_time
    def entity_day_time_range(self,entity_value,start_time,end_time):
        match = re.search("(今|本|昨|前|大前|明|后|大后)儿?天",entity_value)
        if match:
            if re.search("[今|本]儿?天", match.group()):
                start_time = self.current_time.replace(hour=0,minute=0,second=0)
                end_time=self.current_time
            if re.search("昨儿?天", match.group()):
                start_time = self.current_time.replace(hour=0,minute=0,second=0) + timedelta(days=-1)
                end_time = self.current_time
            if re.search("(?<!大)前儿?天", match.group()):
                start_time = self.current_time.replace(hour=0, minute=0, second=0) + timedelta(days=-2)
                end_time = self.current_time
            if re.search("大前儿?天", match.group()):
                start_time = self.current_time.replace(hour=0, minute=0, second=0) + timedelta(days=-3)
                end_time = self.current_time
            if re.search("明儿?天", match.group()):
                start_time=self.current_time
                end_time=self.current_time.replace(hour=0, minute=0, second=0) + timedelta(days=1)
            if re.search("(?<!大)后儿?天", match.group()):
                start_time = self.current_time
                end_time = self.current_time.replace(hour=0, minute=0, second=0) + timedelta(days=2)
            if re.search("大后儿?天", match.group()):
                start_time = self.current_time
                end_time = self.current_time.replace(hour=0, minute=0, second=0) + timedelta(days=3)
        # n天
        match_2 = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经))[0-9]{1,2}|^[0-9]{1,2})(?=[天|日|day])", self.text)
        match_1 = None
        if match_2:
            start_time = start_time.replace(hour=0, minute=0, second=0) - timedelta(days=int(match_2.group()))
            end_time=self.current_time
        else:  # 12号  5月4日
            match_1 = re.search("([012]?[0-9]|30|31)(?=(号))|([012]?[0-9]|30|31)$",entity_value)
            if match_1:
                start_time = start_time.replace(day=int(match_1.group()), hour=0, minute=0, second=0)
                end_time=start_time.replace(hour=23,minute=59,second=59)
        suffix_match = re.search("个?(年|月|月份|周|星期|天|号|日|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", entity_value)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右":  # 3周左右
                if match_1:  # 5月4号左右
                    time_span = False
                if match_2:  # 过去n天左右
                    time_span = True
        return start_time,end_time
    def entity_holiday_range(self,entity_value,start_time,end_time):
        return start_time,end_time
    def entity_mid_day_time_range(self,entity_value,start_time,end_time):
        match = re.search("上午|下午|晌午|中午|午时|早上|晚上|黄昏|深夜|凌晨|傍晚|夜晚|夜里|深夜", entity_value)
        if match:
            for k, v in mid_day_time_dic.items():
                if match.group() in k:
                    start_time = start_time.replace(hour=mid_day_time_dic[k][0], minute=0, second=0)
                    end_time=end_time.replace(hour=mid_day_time_dic[k][1],minute=59,second=59)
        return start_time,end_time
    def entity_hour_time_range(self,entity_value,start_time,end_time):
        # n小时
        match_2 = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经))[0-9]{1,2}|^[0-9]{1,2})(?=(个)?(小时))", self.text)
        match_1 = None
        if match_2:# 过去 3小时
            start_time = start_time.replace(minute=0, second=0) - timedelta(hours=int(match_2.group()))
            end_time=self.current_time
        else:  # 3点
            match_1 = re.search("(1[0-9]|2[0-3]|0?[0-9])(?=(点|时|hour|H|:|：))",entity_value)
            if match_1:
                start_time = start_time.replace(hour=int(match_1.group()), minute=0, second=0)
                if re.search("(下午|晚上|晚上|黄昏|深夜|傍晚|夜晚|夜里|深夜)", self.text):
                    start_time = start_time.replace(minute=0,second=0) + relativedelta(hours=12)
                end_time=end_time.replace(hour=start_time.hour,minute=59,second=59)
        suffix_match = re.search("个?(年|月|月份|周|星期|天|号|日|时|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", self.text)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右":
                if match_1:  # 3点左右
                    time_span=False
                if match_2:  # 过去n小时左右
                    time_span = True
        return start_time,end_time
    def entity_minutes_time_range(self,entity_value,start_time,end_time):
        match_2 = re.search("((?<=(前|过去|过去的|这|近|近这|最近|最近这|曾经|^))[0-9]{1,2})(?=(个)?(分|分钟|minute))", self.text)
        match_1 = None
        if match_2:  # 过去12分钟
            start_time = start_time.replace(second=0) - timedelta(minutes=int(match_2.group()), seconds=0)
            end_time=self.current_time
        else:
            match_1 = re.search("(?<=(：|:|时|点)零?)([1-5][0-9]|0?[0-9])(?=(分|分钟|刻|minute|：|:|))", self.text)
            if match_1:  # 12分
                match_11 = re.search("(?<=(：|:|时|点)零?)([1-5][0-9]|0?[0-9])(?=(刻))", self.text)  # 3点1刻
                if match_11 and int(match_11.group())<5:
                    start_time = start_time.replace(minute=(int(match_1.group())-1)*15, second=0)
                    end_time=end_time.replace(minute=start_time.minute,second=0)+relativedelta(minutes=16,seconds=-1)
                else:
                    start_time = start_time.replace(minute=int(match_1.group()), second=0)
                    end_time=end_time.replace(minute=start_time.minute,second=59)
        suffix_match = re.search("个?(年|月|月份|周|星期|天|号|日|时|小时|时辰|分钟?|秒)[之以]?(前|内|中|左右)", entity_value)
        if suffix_match:
            if suffix_match.group()[-2:] == "左右":
                if match_1:  # 12点12分左右
                    time_span=False
                if match_2:  # 过去n分左右
                    time_span = True
        return start_time,end_time
    def entity_seconds_time_range(self,entity_value,start_time,end_time):
        match_1 = re.search("([1-5][0-9]|0?[0-9])(?=(秒|秒钟|seconds|))", entity_value)
        if match_1:
            start_time = start_time.replace(second=int(match_1.group()))
            end_time=start_time
        return start_time,end_time

if __name__ == '__main__':
    import time
    convert=TimeStrConvert(project="project_time",use_ner=True)
    with open("/mnt/disk1/lilijuan/HK/my_git/Time_Extract_Regex/data/time_texts", "r", encoding='utf-8') as f:
        texts = f.readlines()
    for text in texts:
        if len(text)>3:
            t0=time.time()
            # 预处理：中文转数字，删除特殊符号、某种表述方式转换
            text=convert.pre_process(text)
            print(text,convert.pre_time_range(text),"耗时:{}".format(time.time()-t0),)