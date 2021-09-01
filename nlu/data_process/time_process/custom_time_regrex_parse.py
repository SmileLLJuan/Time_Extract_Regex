from datetime import datetime
import logging
import re
from dateutil.relativedelta import relativedelta

from dateutil import tz

# from nlu.data_process.time_process.convert_time_str import TimeStrConvert
from nlu.data_process.time_process.text_convert_time import TimeStrConvert
from utils.nlu_config import NluConfig

NYC = tz.gettz('Asia/Shanghai')


def strftime(time, formart="%Y-%m-%d %H:%M:%S"):
    return time.astimezone(NYC).strftime(formart)


logger = logging.getLogger(__name__)


class CustomTimeParse:

    def __init__(self, project='default'):
        self.nlu_config = NluConfig(project)
        self.time_convert = self.nlu_config.get_value("time.convert", 1)
        self.convert=TimeStrConvert(project="project_time",use_ner=False)
    @staticmethod
    def my_len(adic):
        count = 0
        for akey in adic:
            if adic[akey]:
                count += 1
        return count

    def process_agerange_years(self, aentity):
        # xx岁 agerange中的12岁
        # agerange_years = r'(?P<years>\d{1,3})(?P<plus>[多几])?岁?'
        agerange_years = r'(?P<years>(\d{1,2}[几多后]?)|([一二三四五六七八九十]十?[几多一二三四五六七八九十]?))'
        zh_age = r'(?P<years>(\d{1,2}[几多后]?)|([一二三四五六七八九十]十?[几多一二三四五六七八九十]?))'
        brith_str = aentity["value"]
        # 2008 返回2008-01-01，2008-12-31
        # 解决：30到40岁 的问题
        start_time = None
        end_time = None
        zh2num = {
            '一': 1,
            '二': 2,
            '三': 3,
            '四': 4,
            '五': 5,
            '六': 6,
            '七': 7,
            '八': 8,
            '九': 9,
            '十': 1
        }

        for m in re.finditer(agerange_years, aentity["value"]):
            mdic = m.groupdict()
            original_year = mdic['years']
            span_max = 0
            span_min = 0
            is_multi_years = False
            is_age = True  # False：表示是年份：80年，90年，True：表示是年龄
            if re.match(zh_age, original_year):
                if original_year.__contains__('几') or \
                        original_year.__contains__('多'):
                    is_multi_years = True
                    is_age = True
                if original_year.__contains__('后'):
                    is_multi_years = True
                    is_age = False
                if not is_age:  # 是年份：80后
                    m_num = re.search(r"\d{1,2}", original_year).group(0)
                    is_2000_later = re.search('[0-1][0-9]', original_year)
                    if is_2000_later:  # 00后:2000-2009；05后:2005-2009; 10后：2010-2019
                        start_year_int = 2000 + int(m_num)
                    else:  # 80后：1980-1989；85后：1985-1989
                        start_year_int = 1900 + int(m_num)
                    end_year_int = start_year_int // 10 * 10 + 9
                    temp_start = datetime(tzinfo=NYC, year=start_year_int,
                                          month=1, day=1, hour=0, minute=0, second=0)
                    temp_end = datetime(tzinfo=NYC, year=end_year_int,
                                        month=12, day=31, hour=23, minute=59, second=59)
                else:  # 是年龄: 80岁
                    if is_multi_years:
                        # 十几岁；三十几岁
                        m_num = re.search(r"\d{1,2}", original_year)
                        if m_num:
                            span_min = int(m_num.group(0))
                            span_max = span_min + 9
                        else:
                            span_min = zh2num[original_year[0]] * 10
                            span_max = span_min + 9
                    else:
                        if str.isdigit(original_year):
                            span_max = int(original_year)
                        else:
                            # 三十五岁, 四十岁
                            if len(original_year) > 2:
                                span_max = zh2num[original_year[0]] * 10 + zh2num[original_year[2]]
                            else:
                                span_max = zh2num[original_year[0]] * 10
                        span_min = span_max
                    now = datetime.now(tz=NYC)
                    original_time_start = now - relativedelta(years=int(span_max))
                    original_time_end = now - relativedelta(years=int(span_min))
                    temp_start = datetime(tzinfo=NYC, year=original_time_start.year, month=1, day=1, hour=0, minute=0,
                                          second=0)
                    temp_end = datetime(tzinfo=NYC, year=original_time_end.year, month=12, day=31, hour=23, minute=59,
                                        second=59)
                # 只有start_time没有被赋值过 or 比当下的temp_start要大，才修改；end_time同理
                # 三十几到四十几
                if not start_time or start_time > temp_start:
                    start_time = temp_start
                if not end_time or end_time < temp_end:
                    end_time = temp_end
        if start_time:
            start_time = strftime(start_time, "%Y-%m-%d")
            end_time = strftime(end_time, "%Y-%m-%d")
            brith_str = start_time + "," + end_time
            aentity["entity"] = "birthday"
        aentity["value"] = brith_str

    def process_birthday(self, aentity):
        birthday_regrex = r'(?P<year>\d{4})(年|-)?((?P<month>\d{1,2})(月|-)?)?((?P<day>\d{1,2})(日|号)?)?'
        birth_str = aentity["value"]
        start_time = None
        for m in re.finditer(birthday_regrex, aentity["value"]):
            mdic = m.groupdict()
            if "year" in mdic and mdic["year"]:
                # 2008 返回2008-01-01，2008-12-31
                birth_str = mdic["year"]
                start_time = datetime(tzinfo=NYC, year=int(mdic['year']), month=1, day=1, hour=0, minute=0, second=0)
                end_time = datetime(tzinfo=NYC, year=int(mdic['year']), month=12, day=31, hour=23, minute=59, second=59)

            if "month" in mdic and mdic["month"]:
                # 2008年3月 返回2008-03-01，2008-03-31
                birth_str += "-" + ("0" + mdic["month"] if len(mdic["month"]) == 1 else mdic["month"])
                start_time = datetime(tzinfo=NYC, year=int(mdic['year']), month=int(mdic['month']), day=1, hour=0,
                                      minute=0, second=0)
                end_time = start_time + relativedelta(months=1) - relativedelta(seconds=1)
            if "day" in mdic and mdic["day"]:
                # 2008年3月5日 返回2008-03-05，2008-03-06
                birth_str += "-" + ("0" + mdic["day"] if len(mdic["day"]) == 1 else mdic["day"])
                start_time = datetime(tzinfo=NYC, year=int(mdic['year']), month=int(mdic['month']),
                                      day=int(mdic['day']), hour=0, minute=0, second=0)
                end_time = start_time
        if start_time:
            start_time = strftime(start_time, "%Y-%m-%d")
            end_time = strftime(end_time, "%Y-%m-%d")
            birth_str = start_time + "," + end_time
        aentity["value"] = birth_str

    # token_start兼容对一个collectTime token的分析，而不是一个text
    def process_time(self, text, all_extracted, token_start=0):
        str = self.convert.pre_time_range(text)
        if str:
            entity = {"entity": "collectTime",
                      "value": str,
                      "start": token_start,
                      "confidence": 1.0,
                      "end": token_start + len(text)}
            all_extracted.append(entity)

    def special_field_process(self, all_extracted):
        # TODO:这里有几个字段特殊处理
        all_extracted_result = []
        for aentity in all_extracted:
            if aentity["entity"] == "birthday":
                self.process_birthday(aentity)
                all_extracted_result.append(aentity)
            elif aentity["entity"] == "ageRange":
                self.process_agerange_years(aentity)
                all_extracted_result.append(aentity)
            elif aentity["entity"] == "collectTime" and self.time_convert == '1':
                logger.debug("collectTime {}".format(aentity))
                self.process_time(aentity["value"], all_extracted_result, token_start=aentity["start"])
            else:
                all_extracted_result.append(aentity)

        return all_extracted_result


import time
if __name__ == '__main__':
    ctp = CustomTimeParse()
    # szde = SpacyZhEntityExtractor()
    texts = ["查询本个月30号凌晨13时零分31秒钟以内仪丰快捷宾馆分局辅助接警","昨天上午2点", "近一周", "从2020年4月6日到2020年4月8日", "上周星期二下午2点", "2020年7月5日", "从上周三到上周5下午3点", "上周 江陵路"]
    # with open("/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/time_extract/time_extract_data/time_texts", "r", encoding='utf-8') as f:
    #     texts = f.readlines()
    for text in texts:
        all_extracted = []
        t0=time.time()
        ctp.process_time(text, all_extracted)
        print(text,all_extracted,"耗时:{}".format(time.time()-t0))
