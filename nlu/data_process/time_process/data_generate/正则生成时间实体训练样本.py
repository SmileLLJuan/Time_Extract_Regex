#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/8/17 9:46
# @Author  : lilijuan
# @File    : 正则生成时间实体训练样本.py
import os,re
import rstr
import random

prefix=["这","最近","大概","曾经","过去","近","前"]
prefix_regex="(上|本|今|前|过去|这|近|近这|最近|最近这|曾经)?"
suffix=["之内","以内","前后","内","中","左右"]
suffix_regex="[之以]?(前|内|中|左右)?"   # 时间  [之以]?(前|内|中|左右|整|半)?
# year_rstr[0] 相对时间  year_rstr[1]绝对时间 year_rstr[2]时长
rstr_regex_with_chinese={"year_rstr":["(今|本|去|前|大前)年","((20|19)\d{2})|((二零|一九)[零一二三四五六七八九]{2})年","([一二三四五六七八九十两1-9]{1,2})年"],
            "half_year_rstr":["(上|下)半年|(年终|年末|年尾|年中|年初)"],
            "month_rstr": ["(本|这|前|上|上上|下|下下)(个)?月", "((0?[1-9]|1[0-2])|(零?[一二三四五六七八九]|十[一二]))月份?","([一二三四五六七八九十两1-9]{1,2})(个)?月"],
            "half_month_rstr":["(上|下)半(个)?月|(上旬|下旬|中旬)|(月初|月末|月中)"],
            "week_rstr":["(本|这|前|上|上上|下|下下)(个)?(周|星期)[一二三四五六七末1-7]","(周|星期)[一二三四五六七末1-7]","([一二三四五六七八九十两1-9]{1,2})(个)?(周|星期)"],
            "day_rstr":["((今|本|去|前|大前)天)","(([012]?[0-9]|30|31)|([一二三四五六七八九]|(二)?十[一二三四五六七八九]?|(三十|三十一)))[天号日]","([一二三四五六七八九十两1-9]{1,2})(天|日|day)"],
            "mid_day_rstr":["上午|下午|晌午|中午|午时|早上|晚上|黄昏|深夜|凌晨|傍晚|夜晚|夜里|深夜"],
            "holiday_rstr":["十一|五一|劳动节|国庆节|元旦|妇女节|平安夜|圣诞节|万圣节|情人节|植树节|青年节|护士节|儿童节|建党节|建军节|双十一|双十二"],
            "hour_rstr":["((0?[0-9]|1[0-9]|2[0-3])|([零一二三四五六七八九]|十[一二三四五六七八九]|二十[一二三]))(点|刻|时|hour|H|:|：)","([一二三四五六七八九十两1-9]{1,2})(个)?(时|小时|时辰|hour)",],
            "minute_rstr":["((0?[0-9]|[1-5][0-9])|([零一二三四五六七八九]|[一二三四五]十[一二三四五六七八九]|六十))(分|分钟|minute|：|:|)","([一二三四五六七八九十两1-9]{1,2})(分|分钟|minute)"],
            "seconds_rstr":["((0?[0-9]|[1-5][0-9])|([零一二三四五六七八九]|[一二三四五]十[一二三四五六七八九]|六十))(秒|秒钟|seconds|)","([一二三四五六七八九十两1-9]{1,2})(秒|秒钟|seconds)"]
}
rstr_regex={"year_rstr":["(今|本|去|前|大前)年","(20|19)\d{2}年","([1-9]{1,2})年"],
            "half_year_rstr":["(上|下)半年|(年终|年末|年尾|年中|年初)"],
            "month_rstr": ["(本|这|前|上|上上|下|下下)(个)?月", "(0?[1-9]|1[0-2])月份?","([1-9]{1,2})(个)?月"],
            "half_month_rstr":["(上|下)半(个)?月|(上旬|下旬|中旬)|(月初|月末|月中)"],
            "week_rstr":["(本|这|前|上|上上|下|下下)(个)?(周|星期)[1-7]","(周|星期)[1-7]","([1-9]{1,2})(个)?(周|星期)"],
            "day_rstr":["(今|本|昨|前|大前)儿?天","([012]?[0-9]|30|31)(号|日)?","([1-9]{1,2})(天|日|day)"],
            "mid_day_rstr":["上午|下午|晌午|中午|午时|早上|晚上|黄昏|深夜|凌晨|傍晚|夜晚|夜里|深夜"],
            "holiday_rstr":["十一|五一|劳动节|国庆节|元旦|妇女节|平安夜|圣诞节|万圣节|情人节|植树节|青年节|护士节|儿童节|建党节|建军节|双十一|双十二"],
            "hour_rstr":["(0?[0-9]|1[0-9]|2[0-3])(点|刻|时|hour|H|:|：)","([1-9]{1,2})(个)?(时|小时|时辰|hour)",],
            "minute_rstr":["(0?[0-9]|[1-5][0-9])(分|分钟|minute|：|:|)","([1-9]{1,2})(分|分钟|minute)"],
            "seconds_rstr":["(0?[0-9]|[1-5][0-9])(秒|秒钟|seconds|)","([1-9]{1,2})(秒|秒钟|seconds)"]
}
rstr_lamdba={}
def rstr_lamda_function(name):
    return lambda i: "[{}]({})".format(rstr.xeger(rstr_regex["{}_rstr".format(name)][i]),name)
for name in ["year","half_year","month","half_month","week","day","mid_day","holiday","hour","minute","seconds"]:
    rstr_lamdba["{}_lamdba".format(name)]=rstr_lamda_function(name)
rstr_lamdba['prefix_lamdba']=lambda :rstr.xeger("(前|过去|这|近|近这|最近|最近这|曾经|大概)?")
rstr_lamdba['suffix_lamdba']=lambda :rstr.xeger("[之以]?(前|内|中|左右)?")
added_rstr=["\[(20|19)\d{2}\]\(year\)[-./]\[(0?[1-9]|1[0-2])\]\(month\)[-./]\[([012]?[0-9]|30|31)\]\(day\)",
            "\[(0?[0-9]|1[0-9]|2[0-3])\]\(hour\)[:：]\[(0?[0-9]|[1-5][0-9])\]\(minute\)[:：]\[(0?[0-9]|[1-5][0-9])\]\(seconds\)"]
rstr_lamdba['added_lamdba']=lambda :rstr.xeger(added_rstr[random.randint(0,len(added_rstr)-1)])

def genetate_time(copy=100):
    time_regex_list=[
                    rstr_lamdba["year_lamdba"](random.randint(0,2)),
                    rstr_lamdba["half_year_lamdba"](random.randint(0,0)),
                    rstr_lamdba["month_lamdba"](random.randint(0,2)),
                    rstr_lamdba["half_month_lamdba"](random.randint(0,0)),
                    rstr_lamdba["week_lamdba"](random.randint(0,2)),
                    rstr_lamdba["day_lamdba"](random.randint(0,2)),
                    rstr_lamdba["mid_day_lamdba"](random.randint(0,0)),
                    rstr_lamdba["holiday_lamdba"](random.randint(0,0)),
                    rstr_lamdba["hour_lamdba"](random.randint(0,1)),
                    rstr_lamdba["minute_lamdba"](random.randint(0,1)),
                    rstr_lamdba["seconds_lamdba"](random.randint(0,1)),
                     rstr_lamdba["year_lamdba"](random.randint(0,1))+rstr_lamdba["month_lamdba"](1)+rstr_lamdba["day_lamdba"](1)+rstr_lamdba["hour_lamdba"](0)+rstr_lamdba["minute_lamdba"](0)+rstr_lamdba["seconds_lamdba"](0),
                     rstr_lamdba["year_lamdba"](random.randint(0,1))+rstr_lamdba["month_lamdba"](1)+rstr_lamdba["day_lamdba"](1)+rstr_lamdba["mid_day_lamdba"](0)+rstr_lamdba["hour_lamdba"](0)+rstr_lamdba["minute_lamdba"](0)+rstr_lamdba["seconds_lamdba"](0),
                     rstr_lamdba["year_lamdba"](random.randint(0, 1)) + rstr_lamdba["holiday_lamdba"](0) + rstr.xeger("(那天|这天|)") + rstr_lamdba["mid_day_lamdba"](0) + rstr_lamdba["hour_lamdba"](0) + rstr_lamdba["minute_lamdba"](0) + rstr_lamdba["seconds_lamdba"](0),
                     rstr_lamdba["year_lamdba"](random.randint(0, 1))+rstr_lamdba["month_lamdba"](1)+rstr_lamdba["half_month_lamdba"](0),
                     rstr_lamdba["year_lamdba"](random.randint(0, 1))+rstr_lamdba["month_lamdba"](1)+rstr_lamdba["day_lamdba"](1)+rstr_lamdba["hour_lamdba"](0)+rstr_lamdba["minute_lamdba"](0),
                     rstr_lamdba["mid_day_lamdba"](0)+rstr_lamdba["hour_lamdba"](0)+rstr_lamdba["minute_lamdba"](0),
                     rstr_lamdba["mid_day_lamdba"](0)+rstr_lamdba["hour_lamdba"](0)+rstr_lamdba["minute_lamdba"](0)+rstr_lamdba["seconds_lamdba"](0),
                     rstr_lamdba["week_lamdba"](0) + rstr_lamdba["hour_lamdba"](0),
                     rstr_lamdba["week_lamdba"](0)+rstr_lamdba["minute_lamdba"](0)+rstr_lamdba["hour_lamdba"](0),
                     rstr_lamdba['prefix_lamdba']()+rstr_lamdba["year_lamdba"](2)+rstr_lamdba["month_lamdba"](2)+rstr_lamdba["day_lamdba"](2)+rstr_lamdba["hour_lamdba"](1)+rstr_lamdba["minute_lamdba"](1)+rstr_lamdba["seconds_lamdba"](1)+rstr_lamdba['suffix_lamdba'](),
                     rstr_lamdba['prefix_lamdba']()+rstr_lamdba["year_lamdba"](2)+rstr_lamdba['suffix_lamdba'](),
                     rstr_lamdba['prefix_lamdba']()+rstr_lamdba["half_year_lamdba"](0)+rstr_lamdba['suffix_lamdba'](),
                     rstr_lamdba['prefix_lamdba']()+rstr_lamdba["month_lamdba"](2)+rstr_lamdba['suffix_lamdba'](),
                     rstr_lamdba['prefix_lamdba']()+rstr_lamdba["week_lamdba"](2)+rstr_lamdba['suffix_lamdba'](),
                     rstr_lamdba['prefix_lamdba']()+rstr_lamdba["day_lamdba"](2)+rstr_lamdba['suffix_lamdba'](),
                     rstr_lamdba['prefix_lamdba']()+rstr_lamdba["hour_lamdba"](1)+rstr_lamdba['suffix_lamdba'](),
                     rstr_lamdba['prefix_lamdba']()+rstr_lamdba["minute_lamdba"](1)+rstr_lamdba['suffix_lamdba'](),
                     rstr_lamdba['prefix_lamdba']()+rstr_lamdba["seconds_lamdba"](1)+rstr_lamdba['suffix_lamdba'](),
                     rstr_lamdba['added_lamdba'](),]
    return [time_regex_list[random.randint(0,len(time_regex_list)-1)] for i in range(copy)]

def main():
    with open("../time_extract_data/time.md",'w',encoding='utf-8') as f:
        f.write("## intent:" + "time" + "\n")
        for i in range(300):
            for line in genetate_time(100):
                f.write("- " + line + "\n")
    with open("../time_extract_data/nlu.md",'r',encoding='utf-8') as f:
        other_lines=f.readlines()
    print(len(other_lines),other_lines[:10])

    with open("../time_extract_data/time.md",'a',encoding='utf-8') as f:
        f.write("## intent:" + "other" + "\n")
        for line in other_lines:
            line=line[2:-1]
            match=re.findall("(intent|\)\[|\{[a-zA-Z]*\})",line)
            if match:
                continue
            else:
                f.write("- " + line + "\n")
    show_md()
def show_md():
    with open("../time_extract_data/time.md",'r',encoding='utf-8') as f:
        lines=f.readlines()
    print(len(lines))
    print(lines[:10])
    print(lines[-10:])
# def add_time_samples():
#     with open("../time_extract_data/time.md",'a',encoding='utf-8') as f:
#         f.write("- " + "[上月](month)[月初](half_month)" + "\n")
#         f.write("- " + "[2012年](year)[上月](month)[月初](half_month)" + "\n")
if __name__ == '__main__':
    # print([rstr_lamdba["day_lamdba"](0) for i in range(10)])
    main()
    pass

