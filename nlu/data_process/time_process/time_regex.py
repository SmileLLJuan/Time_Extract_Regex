# -*- coding:utf-8 -*-
# @Time: 2020/12/21 16:17
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: time_regex.py
import re

year_regex = "(?P<year>([今本去前]年|(((20|19)\d{2})|((二零|一九)[零一二三四五六七八九]{2}))[年\-/.]|((最)?(这|近|前|过去|曾经)?(这)?([一二三四五六七八九十两1-9]{1,2}))年)[之以]?(前|内|中|左右)?)?"
half_year_regex = "(?P<half_year>(((((最)?(这|近|前|过去|曾经)(这)?)|(上|下))半年[之以]?(前|内|中)?)|(年终|年末|年尾|年中|年初)))?"
month_regex = "(?P<month>(((这|前|近|过去|去|曾经)?([一二三四五六七八九十两1-9]{1,2})(个)?)|([这上本前](个)?)|((0?[1-9]|1[0-2])|([一二三四五六七八九]|(十|十一|十二))))[月\-/](份)?[之以]?(前|内|左右|末|初|中)?)?"
half_month_regex="(?P<half_month>((((这|近|前|过去|曾经)(这)?)|(上|下)|)半(个)?月[之以]?(前|内|中)?|(上旬|下旬|中旬)|(月初|月末|月中)))?"
week_regex = "(?P<week>([上这本](周|星期)[一二三四五六七日天1-7末]?|((上|前|这|过去|近|去|曾经)?([零一二三四五六七八九十百千两0-9]{1,2}))(个)?(周|星期)|(周|星期)[一二三四五六七日天1-7末])[之以]?(前|内|中|左右)?)?"
day_regex = "(?P<day>(((前|过去|这|近|近这|最近|最近这|曾经)([零一二三四五六七八九十两半1-9]{1,2}))|[今昨前]|([012]?[0-9]|30|31)|([一二三四五六七八九]|(二)?十[一二三四五六七八九]?|(三十|三十一)))(天|日|号| )[之以]?(前|内|左右)?)?"
mid_day_regex = "(?P<mid_day>(上午|下午|晌午|中午|午时|早上|晚上|黄昏|深夜|凌晨|傍晚|夜晚|夜里|深夜)?)?"
hour_regex = "(?P<hour>(((上|前|过去|去|近|曾经)([零一二三四五六七八九十两半0-9]{1,2})(个)?(小)?)(时|时辰)|(([0-9]|1[0-9]|2[0-3])|([零一二三四五六七八九]|十[一二三四五六七八九]|二十[一二三]))(点|时|：|:| ))([之以]?(前|内|中|左右|整|半)?))?"
minute_regex = "(?P<minute>(((前|过去|近|曾经)?([零一二三四五六七八九十百千两0-9]{1,2}))|([0-9]|[1-5][0-9])|([零一二三四五六七八九]|[二三四五]?十[一二三四五六七八九]))(分|分钟|：|:| )[之以]?(前|内|中|左右)?)?"
seconds_regex = "(?P<seconds>(((前|过去|近|曾经)?([零一二三四五六七八九十百千两0-9]{1,2}))|([0-9]|[1-5][0-9])|([零一二三四五六七八九]|[二三四五]?十[一二三四五六七八九]))(秒|秒钟| |)[之以]?(前|内|中)?)?"
holiday_regex="(?P<holiday>(十一|五一|劳动节|国庆节|元旦|妇女节|平安夜|圣诞节|万圣节|情人节|植树节|青年节|护士节|儿童节|建党节|建军节|双十一|双十二)?)?"
time_regex_str =year_regex+half_year_regex+month_regex+half_month_regex+week_regex+day_regex+holiday_regex+mid_day_regex+hour_regex+minute_regex+seconds_regex

def get_time_regex_str():
    time_regex = "(" + time_regex_str + ")([至和到~]" + time_regex_str + ")?"
    re_com = re.compile("\?P<[a-z_]{1,10}>")
    time_regex = re_com.sub("", time_regex)
    return time_regex

#过滤匹配到的不是时间的字段
def filter(word:str):
    flag=True
    if word =="":
        flag=flag and False
    if len(word) <=1:
        flag=flag and False
    if word.isdigit():
        flag=flag and False
    if re.match("[零一二三四五六七八九十]{1,3}",word):
        flag=flag and False
    return flag

def recognition(word:str):
    res_time=[]
    # m_match=re.match(get_time_regex_str(),word)
    # print(m_match.groups())
    m_iter = re.finditer(get_time_regex_str(), word)
    # m_temp = None
    for m in m_iter:
        # if m and m.group() != '' and m.group() not in ["至","和","到","~"]:
        # if m:
        #     print(m.group())
        if m and filter(m.group()):
            res_time.append(m)
    return res_time
if __name__=="__main__":
    result=recognition("中秋节上午8点30")
    for m in result:
        if m:
            # 时间实体过滤
            print("值：" + m.group())
            print("start：" + str(m.span()[0]))
            print("end：" + str(m.span()[1]))

