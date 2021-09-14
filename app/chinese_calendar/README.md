# 内容列表
<!-- TOC -->
# 参考地址：https://github.com/demeen68/chinese_permanent_calendar
- [简介](#简介)
- [使用说明](#使用说明)
- [示例](#示例)
- [属性说明](#属性说明)
- [其他说明](#其他说明)

<!-- /TOC -->


# 简介

Chinese permanent calendar

这是一个通过python查询中国万年历相关信息的的包，可以根据阳历日期或阴历日期查询，查询范围从1970-01-01到2099-12-31，返回结果包括：

- 公历信息：节日、星座
- 农历信息：宜、忌、冲、煞、神位、胎神、周易、五行、天干地支、彭祖百忌、董公择日法


# 使用说明
pypi地址：https://pypi.org/project/chinese-permanent-calendar

```bash
pip install chinese-permanent-calendar
```
# 示例

```py
import chinese_permanent_calendar as calendar
import datetime

# 根据阳历日期得到阴历日期的详情
date = datetime.date(2020, 1, 1)
luner_date = calendar.get_lunar_by_gregorian(date)
print("阳历：", luner_date.name, "阴历：", luner_date['LunarDate'])

# 根据阴历得到阳历日期及当天的详情
gregorian_date = calendar.get_gregorian_by_lunar(luner_date['LunarDate'])

# 得到所有节日包含国庆节的日期
date = calendar.get_days_by_festival(['国庆节'])

# 得到所有的日期数据
all_data = calendar.get_all_data(start=datetime.date(2020, 1, 1), end=datetime.date(2020, 2, 1))
```



# 属性说明

|属性|含义|
|-|-|
|GregorianDateTime|阳历日期|
|LunarDateTime|阴历日期|
|LJie|阴历节日|
|GJie|阳历节日|
|Yi|宜|
|Ji|忌|
|ShenWei|神位|
|Taishen|胎神|
|Chong|冲|
|SuiSha|岁煞|
|WuxingJiazi|五行甲子年|
|WuxingNaYear|五行纳音-年|
|WuxingNaMonth|五行纳音--月|
|WuxingNaDay|五行纳音-日|
|MoonName|月相|
|XingEast|东方星座-28星宿|
|XingWest|西方星座-12星座|
|PengZu|彭祖百忌|
|JianShen|十二建星|
|TianGanDiZhiYear|天干地支-年|
|TianGanDiZhiMonth|天干地支-月|
|TianGanDiZhiDay|天干地支-日|
|LMonthName|农历-月份别名|
|LYear|阴历-年|
|LMonth|阴历-月|
|LDay|阴历-日|
|SolarTermName|节气|
|GYear|阳历-年|
|GMonth|阳历-月|
|GDay|阳历-日|
|is_weekend|是否为周末|
|is_weekday|是否为工作日|



# 其他说明

1. 原始数据文件拿去:[cp_calendar.csv.gz](chinese_permanent_calendar/cp_calendar.csv.gz)
2. 有任何BUG、改进请提交issue或联系：<18813052953@163.com>
3. 本人学生一枚，闲人一个，希望与更多共同学习、共同进步的小伙伴们多多交流学习。
