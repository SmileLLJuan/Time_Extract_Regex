# -*- coding:utf-8 -*-
# @Time: 2020/10/15 11:06
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: convert_time_str.py
import sys
from datetime import datetime, timedelta
import logging
import re
import calendar
import traceback
from dateutil.relativedelta import relativedelta
from dateutil.tz import tz
#
# from time_process.time_regex import time_regex_str
from nlu.data_process.time_process.time_regex import time_regex_str

NYC = tz.gettz('Asia/Shanghai')
logger = logging.getLogger(__name__)
chs_arabic_map = {u'零': 0, u'一': 1, u'二': 2, u'三': 3, u'四': 4,
                  u'五': 5, u'六': 6, u'七': 7, u'八': 8, u'九': 9,
                  u'十': 10, u'百': 100, u'千': 10 ** 3, u'万': 10 ** 4,
                  u'〇': 0, u'壹': 1, u'贰': 2, u'叁': 3, u'肆': 4,
                  u'伍': 5, u'陆': 6, u'柒': 7, u'捌': 8, u'玖': 9,
                  u'拾': 10, u'佰': 100, u'仟': 10 ** 3, u'萬': 10 ** 4,
                  u'亿': 10 ** 8, u'億': 10 ** 8, u'幺': 1,
                  u'０': 0, u'１': 1, u'２': 2, u'３': 3, u'４': 4,
                  u'５': 5, u'６': 6, u'７': 7, u'８': 8, u'９': 9, u'末': 7}
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
mid_day_time_list = ["上午","晌午","下午","中午","晚上","夜晚","夜里","早上","早晨","凌晨","傍晚","黄昏","深夜"]
year_time_dic = {
    "(本年)": 0,
    "(今年)": 0,
    "(去年)": 1,
    "(前年)": 2
}
year_time_list = ["去年","今年","前年"]
month_time_dic={
    "(当前月)":0,
    "(上上个月)":2
}
week_time_dic = {
    "上周":"上一周",
    "这周":"这一周",
    "本周":"这一周"
}
day_time_dic={
    "(今天|今日)":0,
    "(昨天|昨日)":1,
    "(前天|前日)":2
}
#劳动节|国庆节|元旦|妇女节|平安夜|圣诞节|万圣节|情人节|植树节|青年节|护士节|儿童节|建党节|建军节|双十一|双十二
holiday_dic={
    "五一":"5,1",
    "劳动节":"5,1",
    "十一":"10,1",
    "国庆节":"10,1",
    "元旦":"1,1",
    "妇女节":"3,8",
    "平安夜":"12,24",
    "圣诞节":"12,25",
    "万圣节":"11,1",
    "情人节":"2,14",
    "植树节":"3,12",
    "青年节":"5,4",
    "护士节":"5,12",
    "儿童节":"6,1",
    "建党节":"7,1",
    "建军节":"8,1",
    "双十一":"11,11",
    "双十二":"12,12"
}

def strftime(time, formart="%Y-%m-%d %H:%M:%S"):
    return time.astimezone(NYC).strftime(formart)

# 汉字转换成英文的数字
def convertChineseDigitsToArabic(chinese_digits):
    if isinstance(chinese_digits, str):
        chinese_digits = chinese_digits

    result = 0
    tmp = 0
    hnd_mln = 0
    for count in range(len(chinese_digits)):
        curr_char = chinese_digits[count]
        curr_digit = chs_arabic_map.get(curr_char, None)
        # meet 「亿」 or 「億」
        if curr_digit == 10 ** 8:
            result = result + tmp
            result = result * curr_digit
            # get result before 「亿」 and store it into hnd_mln
            # reset `result`
            hnd_mln = hnd_mln * 10 ** 8 + result
            result = 0
            tmp = 0
        # meet 「万」 or 「萬」
        elif curr_digit == 10 ** 4:
            result = result + tmp
            result = result * curr_digit
            tmp = 0
        # meet 「十」, 「百」, 「千」 or their traditional version
        elif curr_digit >= 10:
            tmp = 1 if tmp == 0 else tmp
            result = result + curr_digit * tmp
            tmp = 0
        # meet single digit
        elif curr_digit is not None:
            tmp = tmp * 10 + curr_digit
        else:
            return result
    result = result + tmp
    result = result + hnd_mln
    return result


# 是否是中文字符
def c_detect(texts):
    # chinese
    if re.search("[\u4e00-\u9FFF]", texts):
        return True
    return False

def convert_to_nmuber_int(strin):
    allc = all([c_detect(achar) for achar in strin])
    if allc :
        return convertChineseDigitsToArabic(strin)

    strin = "".join([str(convertChineseDigitsToArabic(char)) if c_detect(char) else str(char) for char in strin])
    return int(strin)

#偏僻说法的转换
def time_filter(word:str):
    word=word.replace("前月末","前月月末").replace("上月末","上个月月末")
    return word

class TimeStrConvert:

    def __init__(self):
        self.hour_base = 0
        self.time_base = 0
    #处理年相关的时间
    def pre_year_time_range(self,word,start:datetime,end:datetime):
        #数字形式替换
        word = word.replace("两","2")
        #第一种：(这|近|前|过去|去)？多少年
        first_regex = "(这|近|前|过去|上|曾经)(这)?[零一二三四五六七八九十百千两0-9]{1,4}年"
        m_1 = re.search(first_regex,word)
        if m_1:
            #找到数字
            m1 = re.search("[零一二三四五六七八九十百千0-9]{1,4}",word)
            if m1:
                value = m1.group()
                # value = value.replace("两","2")
                #判断是否是数字
                if str.isdigit(value):
                    start = start.replace(year=start.year-int(value),month=1,day=1,hour=0,minute=0,second=0)
                    end = datetime.now(tz=NYC)
                if value in "零一二三四五六七八九十百千":
                    start = start.replace(year=start.year-convertChineseDigitsToArabic(value),month=1,day=1,hour=0,minute=0,second=0)
                    end = datetime.now(tz=NYC)
            return start,end
        # 第二种情况：？年[内、中、前]
        seconds_regex = "[零一二三四五六七八九十百千0-9]{1,2}年[之以]?(前|内|中)"
        m_2 = re.search(seconds_regex,word)
        if m_2:
            #找到数字
            m2 = re.search("[零一二三四五六七八九十百千0-9]{1,2}",word)
            if m2:
                value = m2.group()
                #判断是否是汉字
                if value in "零一二三四五六七八九十百千":
                    value = convertChineseDigitsToArabic(value)
                #三年前；
                if word.endswith("前"):
                    start = start.replace(year=start.year - int(value), month=1, day=1, hour=0, minute=0, second=0)
                    end = end.replace(year=end.year - int(value), month=12, day=31, hour=23, minute=59, second=59)
                if word.endswith("内") or word.endswith("中"):
                    #三年内、中
                    start = start.replace(year=start.year - int(value), month=1, day=1, hour=0, minute=0, second=0)
                    end = datetime.now(tz=NYC)
            return start,end
        #第三种情况：2020年 20年 2020/ 20/等
        third_regex = "[零一二三四五六七八九十百千0-9]{1,4}[年\-/.](左右)?"
        m_3 = re.search(third_regex,word)
        if m_3:
            m2 = re.search("[零一二三四五六七八九十百千0-9]{1,4}",word)
            if m2:
                num_year = start.year
                value = m2.group()
                if not str.isdigit(value):
                    value = str(convertChineseDigitsToArabic(value))
                if str.isdigit(value):
                    #4位
                    if len(value)==4:
                        start = start.replace(year=int(value), month=1, day=1,hour=0, minute=0, second=0)
                        end = start.replace(year=int(value), month=12, day=31,hour=23, minute=59, second=59)
                    #2位
                    if len(value) ==2:
                        #获取当前年份的前两位
                        start = start.replace(year=int(str(start.year//100)+value), month=1, day=1,hour=0, minute=0, second=0)
                        end = start.replace(year=int(str(start.year//100)+value), month=12, day=31,hour=23, minute=59, second=59)

                if word.endswith("左右"):
                    start = start-relativedelta(years=1)
                    if (end+relativedelta(years=1))>end:
                        end=end
                    else:
                        end=end+relativedelta(years=1)
                # 和情况二存在冲突
                # elif word.endswith("前"):
                #     end=start-relativedelta(seconds=1)
                #     start=start-relativedelta(years=1)
            return start,end
        #今年、去年、前年
        for key in year_time_dic:
            m = re.match(key,word)
            if m:
                value = year_time_dic[key]
                start = start.replace(year=start.year-value,month=1,day=1,hour=0,minute=0,second=0)
                end = end.replace(year=end.year-value,month=12,day=31,hour=23,minute=59,second=59)
                return start,end
        return start,end

    #"(?P<half_year>(最)?(这|近|前|过去|去|曾经|今)?(这)?(上|下)?半年(之)?(前|内|中)?(年终|年末|年尾|年中|年初)?)?"
    def pre_half_year_time_range(self,word,start:datetime,end:datetime):

        if "下半" in word:
            start = start.replace(month=7,day=1,hour=0,minute=0,second=0)
            end = end.replace(month=12,day=31,hour=23,minute=59,second=59)
            return start,end
        elif "上半" in word:
            start = start.replace(month=1,day=1,hour=0,minute=0,second=0)
            end = end.replace(month=6,day=30,hour=23,minute=59,second=59)
            return start,end

        #  1月—4月 年中   5月-8月   年末 9月-12月
        if word.endswith("年终") or word.endswith("年尾") or word.endswith("年末"):
            start = start.replace(month=9,day=1,hour=0,minute=0,second=0)
            end = end.replace(month=12,day=31,hour=23,minute=59,second=59)
            return start,end
        if word.endswith("年初"):
            start = start.replace(month=1,day=1,hour=0,minute=0,second=0)
            end = end.replace(month=4,day=30,hour=23,minute=59,second=59)
            return start,end
        if word.endswith("年中"):
            start = start.replace(month=5,day=1,hour=0,minute=0,second=0)
            end = end.replace(month=8,day=31,hour=23,minute=59,second=59)
            return start,end

        # 这半年|近|前|过去|去|曾经
        start = start.replace(month=(start.month - 6)).replace(day=1, hour=0, minute=0, second=0)
        if word.endswith("前"):
            end = start - relativedelta(seconds=1)
            start = end - relativedelta(months=6) + relativedelta(seconds=1)
            # return start, end
        return start, end

    #(?P<month>(最)?(这|上|前|近|过去|去|曾经|本)?([零一二三四五六七八九十百千两0-9]{1,2})?(个)?[月\-/](份)?(之)?(前|内|左右)?)?
    def pre_month_time_range(self,word:str,start:datetime,end:datetime):
        #替换计量
        word = word.replace("两","2")
        #第一种：(这|近|前|过去|去)？多少月
        first_regex = "([这上本前](个)?)月([之以]?(前|内|左右|末|初|中))?"
        m_1 = re.search(first_regex,word)
        if m_1:
            if word.startswith("这") or word.startswith("本"):
                start=(start-relativedelta(days=(start.day-1))).replace(hour=0,minute=0,second=0)
            if word.startswith("上"):
                start=((start-relativedelta(days=(start.day-1))).replace(hour=0,minute=0,second=0))-relativedelta(months=1)
                end=start+relativedelta(months=1)-relativedelta(seconds=1)
            if word.startswith("前"):
                start=((start-relativedelta(days=(start.day-1))).replace(hour=0,minute=0,second=0))-relativedelta(months=2)
                end=start+relativedelta(months=1)-relativedelta(seconds=1)
            # return start, end
        # 第二种情况：？月[内、前、左右]
        seconds_regex = "((这|前|近|最近|最近这|过去|曾经)([一二三四五六七八九十两1-9]{1,2})(个)?)月([之以]?(前|内|左右))?"
        m_2 = re.search(seconds_regex,word)
        if m_2:
            #找到数字
            m2 = re.search("[一二三四五六七八九十1-9]{1,2}",word)
            if m2:
                value = m2.group()
                #判断是否是汉字
                if not value.isdigit():
                    value= convertChineseDigitsToArabic(value)
                start=start-relativedelta(months=int(value))
            # return start,end
        #第三种情况：1月，2月，10月等
        third_regex = "((0?[1-9]|1[0-2])|([一二三四五六七八九]|(十|十一|十二)))[月\-/](份)?([之以]?(前|内|左右|末|初|中))?"
        m_3 = re.search(third_regex,word)
        if m_3:
            m3 = re.search("[零一二三四五六七八九十0-9]{1,2}",word)
            if m3:
                value = m3.group()
                if not str.isdigit(value):
                    value = str(convertChineseDigitsToArabic(value))
                start = start.replace(month=int(value), day=1, hour=0, minute=0, second=0)
                end = start + relativedelta(months=1) - relativedelta(seconds=1)
                # if word.endswith("左右"):
                #     start = start-relativedelta(months=1)
                #     temp_end=end+relativedelta(months=1)
                #     if temp_end>datetime.now(tz=NYC):
                #         end=datetime.now(tz=NYC)
                #     else:
                #         end=temp_end
            # return start,end
        for key in month_time_dic.keys():
            m = re.match(key,word)
            if m:
                value = month_time_dic[key]
                start = start.replace(month=start.month-value,day=1,hour=0,minute=0,second=0)
                # calendar.monthrange(2016, 9) 计算月份多少天，返回元组（3,30）表示第一天为周三，一共30天
                end = end.replace(month=end.month-value,day=calendar.monthrange(end.year,end.month-value)[1],hour=23,minute=59,second=59)
                return start,end
        # (前 | 内 | 左右 | 末 | 初 | 中)
        if word.endswith("前"):
            end=start
            start=start-relativedelta(months=1)
        if word.endswith("左右"):
            end=start+relativedelta(months=1)
            start=start-relativedelta(months=1)
        #一月初，这月末
        if word.endswith("月末"):
            start = start.replace(day=21,hour=0,minute=0,second=0)
            end = start.replace(month=(start.month+1),day=1,hour=0,minute=0,second=0)-timedelta(seconds=1)
        if word.endswith("月中"):
            start = start.replace(day=11,hour=0,minute=0,second=0)
            end = end.replace(day=20,hour=23,minute=59,second=59)
        if word.endswith("月初"):
            start = start.replace(day=1,hour=0,minute=0,second=0)
            end = start.replace(day=10,hour=23,minute=59,second=59)
        return start,end

    #(?P<half_month>((最)?(这|近|前|过去|去|曾经|今)?(这)?(上|下)?半月(之)?(前|内|中)?)?(上旬|下旬|中旬)?(月初|月末|月中)?)?
    def pre_half_month_time_range(self,word,start:datetime,end:datetime):
        if "上半" in word:
            start = start.replace(day=1,hour=0,minute=0,second=0)
            end = end.replace(day=15,hour=23,minute=59,second=59)
            return start,end
        if "下半" in word:
            start = start.replace(day=16,hour=0,minute=0,second=0)
            end = end.replace(month=(end.month+1),day=1,hour=0,minute=0,second=0)-timedelta(seconds=1)
            return start,end
        # 上旬|下旬|中旬
        if word.endswith("上旬") or word.endswith("月初"):
            start = start.replace(day=1,hour=0,minute=0,second=0)
            end = end.replace(day=10,hour=23,minute=59,second=59)
            return start,end
        if word.endswith("中旬") or word.endswith("月中"):
            start = start.replace(day=11,hour=0,minute=0,second=0)
            end = end.replace(day=20,hour=23,minute=59,second=59)
            return start,end
        if word.endswith("下旬") or word.endswith("月末"):
            start = start.replace(day=21,hour=0,minute=0,second=0)
            end = end.replace(month=(end.month+1),day=1,hour=0,minute=0,second=0)-timedelta(seconds=1)
            return start,end

        # 这半月
        start = (start-relativedelta(days=15)).replace(hour=0,minute=0,second=0)
        if word.endswith("前"):
            end=start-relativedelta(seconds=1)
            start=end-relativedelta(days=15)
        return start, end

    # week_regex = "(?P<week>(最)?(上|前|这|过去|近)?([零一二三四五六七八九十百千两0-9]{1,2})?(个)?(周|星期)[一二三四五六七日天1-7末]?(之)?(前|内|中)?)?"
    def pre_week_time_range(self,word,start:datetime,end:datetime):
        #数字替换
        word=word.replace("两","2").replace("末","7").replace("天","7").replace("日","7")
        #第一种：(这|近|前|过去|去)？多少周
        first_regex = "(上|前|这|过去|近|曾经)?([零一二三四五六七八九十百千0-9]{1,2})(个)?(周|星期)[之以]?(前|内|中|左右)?"
        m_1 = re.search(first_regex,word)
        if m_1:
            #找到数字
            m1 = re.search("[零一二三四五六七八九十百千两0-9]{1,2}",word)
            if m1:
                value = m1.group()
                if value in "零一二三四五六七八九十百千":
                    value=convertChineseDigitsToArabic(value)
                if word.endswith("前"):
                    start = start - timedelta(days=(start.weekday()+(int(value)+1)*7))
                    start = start.replace(hour=0,minute=0,second=0)
                    end = start+relativedelta(days=8)-relativedelta(seconds=1)
                elif word.endswith("内") or word.endswith("中"):
                    start = start - timedelta(days=(start.weekday()+int(value)*7))
                    start = start.replace(hour=0,minute=0,second=0)
                    end = end
                elif word.endswith("左右"):
                    start = start - timedelta(days=(start.weekday()+(int(value)+1)*7))
                    start = start.replace(hour=0,minute=0,second=0)
                    end = start+relativedelta(days=15)-relativedelta(seconds=1)
                else:
                    #判断
                    start = start - timedelta(days=(start.weekday() + int(value) * 7))
                    start = start.replace(hour=0, minute=0, second=0)
                    end = end
            return start,end
        #第三种情况：2020年 20年 2020/ 20/等
        third_regex = "(上|前|这|过去|近|曾经)?(周|星期)[一二三四五六七1-7]"
        m_3 = re.search(third_regex,word)
        if m_3:
            m3 = re.search("[一二三四五六七日天1-7末]",word)
            if m3:
                value = m3.group()
                if value in "一二三四五六七":
                    value = str(convertChineseDigitsToArabic(value))

                if "上" in word or "前" in word:
                    #计算后面的数字到今天的天数
                    start = start - timedelta(start.weekday()+8-int(value))
                    start = start.replace(hour=0,minute=0,second=0)
                    end = start + timedelta(days=1) - timedelta(seconds=1)
                else:
                    #本周
                    start = start - timedelta(days=(start.weekday()-int(value)+1))
                    start = start.replace(hour=0,minute=0,second=0)
                    end = start + timedelta(days=1) - timedelta(seconds=1)
            return start,end
        #上周 这周
        if "上周" in word:
            start = start - timedelta(days=(start.weekday()+7))
            start = start.replace(hour=0, minute=0, second=0)
            end = start + timedelta(days=7)-timedelta(seconds=1)
        if "这周" in word or "本周" in word :
            start = (start - timedelta(days=start.weekday())).replace(hour=0,minute=0,second=0)
            end = datetime.now(tz=NYC)
        return start,end

    #处理天的相关；昨天、昨日、今天、今日、前天、前日等
    def pre_day_time_range(self,word,start: datetime,end:datetime):
        # 计量替换
        word=word.replace("两","2")
        first_regex = "(今|昨|前|过去|去|近|曾经)([零一二三四五六七八九十百千两半0-9]{1,2})[天日]"
        m_1 = re.search(first_regex, word)
        if m_1:
            # 找到数字
            m1 = re.search("[零一二三四五六七八九十百千两0-9]{1,2}", word)
            if m1:
                value = m1.group()
                # value = value.replace("两", "2")
                # 判断
                if value in "零一二三四五六七八九十百千":
                    value=convertChineseDigitsToArabic(value)
                start = start - relativedelta(days=int(value))
                start = start.replace(hour=0, minute=0, second=0)
                end = end
            return start, end
        seconds_regex = "([零一二三四五六七八九十百千两半0-9]{1,2})[天日][之以]?(前|内|左右)"
        m_2 = re.search(seconds_regex, word)
        if m_2:
            # 找到数字
            m2 = re.search("[零一二三四五六七八九十百千两0-9]{1,2}", word)
            if m2:
                value = m2.group()
                if value in "零一二三四五六七八九十百千":
                    value=convertChineseDigitsToArabic(value)
                if word.endswith("前"):
                    start=(start-relativedelta(days=(int(value)+3))).replace(hour=0, minute=0, second=0)
                    end = start+relativedelta(days=4)-relativedelta(seconds=1)
                elif word.endswith("内"):
                    start=(start-relativedelta(days=int(value))).replace(hour=0, minute=0, second=0)
                    end=end
                elif word.endswith("左右"):
                    start=(start-relativedelta(days=(int(value)+3))).replace(hour=0, minute=0, second=0)
                    if (start+relativedelta(days=6)-relativedelta(seconds=1)) > end:
                        end=end
                    else:
                        end=(start+relativedelta(days=6)-relativedelta(seconds=1))
            return start, end
        # 第三种情况：1号，2号，3号
        third_regex = "([零一二三四五六七八九十百千0-9]{1,2})(|日|号| )(左右)?"
        m_3 = re.search(third_regex, word)
        if m_3:
            m3 = re.search("([零一二三四五六七八九十百千0-9]{1,2})", word)
            if m3:
                value = m3.group()
                if not str.isdigit(value):
                   value = str(convertChineseDigitsToArabic(value))
                # if word.endswith("前"):
                #     start = start.replace(day=int(value), hour=0, minute=0, second=0)-relativedelta(days=3)
                #     end = end.replace(day=int(value), hour=0, minute=0, second=0)-relativedelta(seconds=1)
                if word.endswith("左右"):
                    start = start.replace(day=int(value), hour=0, minute=0, second=0)-relativedelta(days=3)
                    end_temp=end.replace(day=int(value), hour=0, minute=0, second=0)+relativedelta(days=3)
                    if end_temp>end:
                        end=end
                    else:
                        end=end_temp
                else:
                    start = start.replace(day=int(value), hour=0, minute=0, second=0)
                    end = start + timedelta(days=1) - timedelta(seconds=1)
            return start, end
        for key in day_time_dic.keys():
            m = re.match(key,word)
            if m:
                value = day_time_dic[key]
                start_time = datetime(tzinfo=NYC, year=start.year, month=start.month, day=start.day, hour=0, minute=0,
                                      second=0)
                start_time = start_time - relativedelta(days=value)
                end_time = start_time + relativedelta(days=1) - relativedelta(seconds=1)
                return start_time,end_time
        return start,end

    #处理午时的相关：中午、上午、凌晨、傍晚等
    def pre_mid_day_time_range(self,word,start:datetime,end:datetime):
        # if word not in time_interval_dic.keys():
        #     return start,end
        for key in mid_day_time_dic.keys():
            m = re.match(key,word)
            if m:
                value = mid_day_time_dic[key]
                self.hour_base = value[0]
                start = start.replace(hour=int(value[0]),minute=0,second=0)
                end = end.replace(hour=int(value[1]),minute=59,second=59)
                return start,end
        return start,end


    #(今|昨|前|过去|去|近)?([零一二三四五六七八九十百千两半0-9]{1,2})?(个)?(小)?[时点](辰)?(之)?(前|内|中)?
    def pre_hour_time_range(self,word,start:datetime,end:datetime):
        word=word.replace("两","2")
        first_regex = "(今|昨|前|过去|去|近|曾经)([零一二三四五六七八九十百千两半0-9]{1,2})(个)?(小)?[时点](辰)?"
        m_1 = re.search(first_regex, word)
        if m_1:
            # 找到数字
            m1 = re.search("[零一二三四五六七八九十百千半0-9]{1,2}", word)
            if m1:
                value = m1.group()
                if "半" in value:
                    start = (start - timedelta(minutes=30)).replace(second=0)
                    end=end
                    return start,end
                if not value.isdigit():
                    value=convertChineseDigitsToArabic(value)
                start=(start - timedelta(hours=int(value))).replace(minute=0,second=0)
                end = end
            return start, end
        seconds_regex = "([零一二三四五六七八九十百千两半0-9]{1,2})?(个)?(小)?(|时|点|:|：| )(辰)?[之以]?(前|内|中|左右|整|半)?"
        m_2 = re.search(seconds_regex, word)
        if m_2:
            # 找到数字
            m2 = re.search("[零一二三四五六七八九十百千半0-9]{1,2}", word)
            if m2:
                value = m2.group()
                if "半" in value:
                    end=start-relativedelta(seconds=1)
                    start = (start - timedelta(minutes=30)).replace(second=0)
                    # end=end
                else:
                    if not value.isdigit():
                        value=convertChineseDigitsToArabic(value)
                # 判断小时基数和hour_num大小关系
                if int(value) >= self.hour_base and int(value)<=23:
                    start = start.replace(hour=int(value), minute=0, second=0)
                    if int(value)==23:
                        end=(end+relativedelta(days=1)).replace(hour=0,minute=0,second=0)-relativedelta(seconds=1)
                    else:
                        end = end.replace(hour=(int(value)+1),minute=0, second=0)-relativedelta(seconds=1)
                else:
                    if int(value)+12 >= 24:
                        start = start.replace(hour=(int(value) + 12-24), minute=0, second=0)+relativedelta(days=1)
                        end = start+relativedelta(hours=1)-relativedelta(seconds=1)
                    else:
                        start = start.replace(hour=(int(value) + 12), minute=0, second=0)
                        end = start+relativedelta(hours=1)-relativedelta(seconds=1)
                if word.endswith("前"):
                    end=start-relativedelta(seconds=1)
                    start=start-relativedelta(hours=3)
                if word.endswith("左右"):
                    start=start-relativedelta(hours=3)
                    end=end+relativedelta(hours=2)
                if word.endswith("整"):
                    end=start
                if word.endswith("半"):
                    start=start.replace(minute=30)
            return start, end
        else:
            return start,end

    # (最)?(今|昨|前|过去|去|近)?([零一二三四五六七八九十百千两0-9]{1,2})?(个)?(分)(钟)?(之)?(前|内|中)?
    def pre_minutes_time_range(self, word, start: datetime, end: datetime):
        word=word.replace("两","2")
        first_regex = "(今|昨|前|过去|去|近|曾经)([零一二三四五六七八九十百千两0-9]{1,2})(个)?(分)(钟)?"
        m_1 = re.search(first_regex, word)
        if m_1:
            # 找到数字
            m1 = re.search("[零一二三四五六七八九十百千两0-9]{1,2}", word)
            if m1:
                value = m1.group()
                # 判断
                re_value = re.search("([零一二三四五六七八九]|[二三四五]?十[一二三四五六七八九])",value)
                if re_value:
                    value=convertChineseDigitsToArabic(value)
                start = start - timedelta(minutes=int(value))
                start = start.replace(second=0)
                end = end
            return start, end
        seconds_regex = "([零一二三四五六七八九十百千两0-9]{1,2})(个)?(|分|分钟|：|:)[之以]?(前|内|中|左右)?"
        m_2 = re.search(seconds_regex, word)
        if m_2:
            # 找到数字
            m2 = re.search("[零一二三四五六七八九十百千两0-9]{1,2}", word)
            if m2:
                # 判断
                value = m2.group()
                # 判断
                # re_value = re.search("([零一二三四五六七八九]|[二三四五]?十[一二三四五六七八九])",value)
                # if re_value:
                if not value.isdigit():
                    value=convertChineseDigitsToArabic(value)
                start = start.replace(minute=int(value),second=0)
                # start = start.replace(second=0)
                end = start.replace(second=59)
                if word.endswith("前"):
                    end=start-relativedelta(seconds=1)
                    start=start-relativedelta(minutes=3)
                    # end=end-relativedelta(minutes=3)
                if word.endswith("左右"):
                    start = start - relativedelta(minutes=3)
                    end = end + relativedelta(minutes=3)
            return start, end

    # (?P<seconds>(最)?(今|昨|前|过去|去|近)?([零一二三四五六七八九十百千两0-9]{1,2})?(个)?(秒)(钟)?(之)?(前|内|中)?)?
    def pre_seconds_time_range(self, word, start: datetime, end: datetime):
        first_regex = "(今|昨|前|过去|去|近|曾经)([零一二三四五六七八九十百千两0-9]{1,2})?(个)?(秒)(钟)?"
        seconds_regex = "([零一二三四五六七八九十百千两0-9]{1,2})?(个)?(秒)(钟)?[之以]?(前|内|中)"
        m = re.search(first_regex, word)
        m_2 = re.search(seconds_regex, word)
        if m or m_2:
            # 找到数字
            m2 = re.search("[零一二三四五六七八九十百千两0-9]{1,2}", word)
            if m2:
                value = m2.group()
                value = value.replace("两", "2")
                if not value.isdigit():
                    value=convertChineseDigitsToArabic(value)
                start = start - timedelta(seconds=int(value))
                end = end
            return start, end
        # 第三种情况：2020年 20年 2020/ 20/等
        third_regex = "([零一二三四五六七八九十百千两0-9]{1,2})?(秒|秒钟|)"
        m_3 = re.search(third_regex, word)
        if m_3:
            m2 = re.search("([零一二三四五六七八九十百千0-9]{1,2})", word)
            if m2:
                value = m2.group()
                value = value.replace("两","2")
                # 判断
                if not value.isdigit():
                    value=convertChineseDigitsToArabic(value)
                start = start.replace(second=int(value))
                end = start
            return start, end
        else:
            return start, end
    #"(?P<holiday>(劳动节|国庆节|元旦|妇女节|平安夜|圣诞节|万圣节|情人节|植树节|青年节|护士节|儿童节|建党节|建军节|双十一|双十二)?)?"
    def pre_holiday_range(self, word, start: datetime, end: datetime):
        time_value = holiday_dic[word]
        if time_value:
            time_list = time_value.split(",")
            month_number = time_list[0]
            day_number = time_list[1]
            start = start.replace(month=int(month_number),day=int(day_number),hour=0,minute=0,second=0)
            end = start+timedelta(days=1)-timedelta(seconds=1)
        return start,end

    #获取一个时间所不包含的时间单位(The unit of time)
    def pre_time_unit(self,word):
        logger.debug("pre_time_range TIME:\n" + word)
        dic = {}
        match=re.finditer(time_regex_str, word)
        for m in match:
            mdic = m.groupdict()
            for m2 in mdic:
                if mdic[m2]:
                    dic[m2] = mdic[m2]
        return dic

    #根据时间单位计算时间
    def pre_time_transformation(self,dic={}):
        try:
            start_time=datetime.now(tz=NYC)
            end_time=datetime.now(tz=NYC)
            #判断顺序不能变
            if "year" in dic.keys():
                start_time,end_time = self.pre_year_time_range(dic["year"],start_time,end_time)
            if "half_year" in dic.keys():
                start_time,end_time = self.pre_half_year_time_range(dic["half_year"],start_time,end_time)
            if "month" in dic.keys():
                 start_time,end_time = self.pre_month_time_range(dic["month"],start_time,end_time)
            if "half_month" in dic.keys():
                 start_time,end_time = self.pre_half_month_time_range(dic["half_month"],start_time,end_time)
            if "week" in dic.keys():
                 start_time,end_time = self.pre_week_time_range(dic["week"],start_time,end_time)
            if "day" in dic.keys() :
                start_time,end_time = self.pre_day_time_range(dic["day"], start_time,end_time)
            if "holiday" in dic.keys():
                start_time, end_time = self.pre_holiday_range(dic["holiday"],start_time,end_time)
            if "mid_day" in dic.keys():
                # start_time, now = self.pre_time_eml(dic["mid_day"], start_time, now)
                start_time,end_time =  self.pre_mid_day_time_range(dic["mid_day"],start_time,end_time)
            if "hour" in dic.keys():
                start_time,end_time = self.pre_hour_time_range(dic["hour"],start_time,end_time)
            if "minute" in dic.keys():
                start_time,end_time = self.pre_minutes_time_range(dic["minute"],start_time,end_time)
            if "seconds" in dic.keys():
                start_time,end_time = self.pre_seconds_time_range(dic["seconds"],start_time,end_time)
            if start_time:
                #解决夸天的时间段问题
                if self.time_base==0:
                    self.time_base=start_time
                else:
                    while end_time<self.time_base:
                        end_time=end_time+relativedelta(days=1)
                time_end = strftime(end_time,"%Y-%m-%d %H:%M:%S")
                time_start = strftime(start_time,"%Y-%m-%d %H:%M:%S")
                res_word = True, time_start + "," + time_end
                return res_word
        except Exception as e:
            logger.error("pre_time_range error")
            traceback.print_exc()

    # 前天，昨天，今天 ，上个月，去年
    def pre_time_range(self, word):
        # import pdb; pdb.set_trace()
        try:
            word=time_filter(word)
            time_list = re.split("[到至和~]", word)
            # str = ""
            if len(time_list) == 1:
                #首先获取dic
                dic=self.pre_time_unit(word)
                str = self.pre_time_transformation(dic)[1]
                self.time_base=0
                return str
            else:
                dic_1=self.pre_time_unit(time_list[0])
                dic_2=self.pre_time_unit(time_list[1])
                for key in dic_1.keys():
                    if key not in dic_2.keys():
                        dic_2[key]=dic_1[key]

                str_1 = self.pre_time_transformation(dic_1)
                str_2 = self.pre_time_transformation(dic_2)
                self.time_base=0
                str=str_1[1].split(",")[0]+","+str_2[1].split(",")[1]
                return str
        except Exception:
            logger.error("pre_time_range error," + word)
            traceback.print_exc()

if __name__ == "__main__":
    convert=TimeStrConvert()
    with open("/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/time_extract/time_extract_data/time_texts","r",encoding='utf-8') as f:
        lines=f.readlines()
    for line in lines:
        time_str = line.replace("\n","")
        if len(time_str)>0:
            if len(sys.argv) >1:
                time_str=sys.argv[1]
            # str = convert.pre_time_range(time_str)
            print(time_str,convert.pre_time_unit(time_str))

