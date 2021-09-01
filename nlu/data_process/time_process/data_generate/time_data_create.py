'''
Created on 2020年7月22日
从数据库中读取，句式以及字典的值，
合成带标注的句子文件，保存为文件，还是数据库中呢。
@author: zhangjiwei
'''

import re
import random
import rstr
import os
import json
import pinyin

import logging
from enum import Enum

from importers.data_save_fetch import DictData
from nlu.data_process.regex.regex_factory import InnerRegexMatcher
from utils.error_code import DatabaseError

from utils.json_read import JsonRead
from utils.url import get_current_dir, get_nlu_data_dir

logger = logging.getLogger(__name__)
jr = JsonRead()


class Datatype(Enum):
    NEED_RECOGNIZE = 1
    JUST_VALUE = 2


class CreateData(object):
    def __init__(self, project="default"):
        self.project = project
        self.bot_id = project.split('.')[0]
        self.dictData = DictData(project=self.bot_id)
        self.regex_factory = InnerRegexMatcher()
        self.fieldValue_caches = {}
        self.default_pattern_field = r'[@#]\{(\S*?=\S*?)\}'
        self.pattern_field = r'@\{(\S*?)\}'
        self.pattern_val_field = r'@\[(\S*?)\]'
        # 正则槽位
        self.regex_pattern_field = r'#\{(\S*?)\}'
        self.regex_pattern_just_value = r'#\[(\S*?)\]'

    def create_data(self, sentence_url, line=1000):
        if not os.path.exists(sentence_url) and not os.path.isfile(sentence_url):
            raise FileNotFoundError

        # 对训练语料备份
        # nlu_data_dir = get_nlu_data_dir(self.project)
        nlu_data_dir="/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/time_extract/time_extract_data"
        if not os.path.exists(nlu_data_dir):
            os.makedirs(nlu_data_dir)
        save_nlu_file = os.path.join(nlu_data_dir, "nlu.md")
        if os.path.exists(save_nlu_file):
            save_nlu_file_bak = os.path.join(nlu_data_dir, "nlu_bak.md")
            os.rename(save_nlu_file, save_nlu_file_bak)

        # 读取句式文件
        intent_dic = jr.read_dict(sentence_url)
        # intent_dic={"hello":["@[搜]#{collectTime}@{humanTagType}",
        # "@[搜]#{collectTime}出现@[的]@{humanTagType}",]}
        # 每一个意图
        intents = intent_dic.keys()
        save_file_handle = open(save_nlu_file, 'w', encoding='utf8')
        for intent in intents:
            # 每个意图的，所有模板
            templates = intent_dic[intent]
            num_temp = len(templates)
            if num_temp > 0:
                # 写入意图名称
                save_file_handle.write("## intent:" + intent + "\n")
                # 每一个模板
                for template in templates:
                    print("template",template)
                    # 判断句式中是否存在槽位
                    if not re.search(self.default_pattern_field, template) and not re.search(self.regex_pattern_field,
                                                                                           template) and not re.search(
                            self.regex_pattern_just_value, template) and not re.search(self.pattern_field,
                                                                                      template) and not re.search(
                            self.pattern_val_field, template):
                        for _i in range(20):
                            template=del_(template)
                            print("- " + template + "\n")
                            save_file_handle.write("- " + template + "\n")
                    else:
                        for _i in range(line):
                            # @[搜]@{collectTime}@[一个]@{gender}
                            new_template = template
                            # 带默认值的实体字段
                            for match in re.finditer(self.default_pattern_field, new_template):
                                # collectTime
                                a_filed = match.groups()[0]
                                field_name = a_filed.split("=")[0]
                                field_val = a_filed.split("=")[1]
                                fieldVal = f'[{field_val}]({field_name})'
                                new_template = re.sub(self.default_pattern_field, fieldVal, new_template, 1)
                            # 正则表达式,需要标注
                            for match in re.finditer(self.regex_pattern_field, new_template):
                                filed_name = match.groups()[0]
                                fieldVal = self.regex_factory.generater(filed_name, True)
                                new_template = re.sub(self.regex_pattern_field, fieldVal, new_template, 1)

                            # 正则表达式,不需要标注
                            for match in re.finditer(self.regex_pattern_just_value, new_template):
                                filed_name = match.groups()[0]
                                fieldVal = self.regex_factory.generater(filed_name, False)
                                new_template = re.sub(self.regex_pattern_just_value, fieldVal, new_template, 1)

                            # 不带默认值实体字段，读取实体库
                            for match in re.finditer(self.pattern_field, new_template):
                                # collectTime
                                a_filed = match.groups()[0]
                                fieldVal = self.get_afiled_vaule(a_filed, Datatype.NEED_RECOGNIZE)
                                new_template = re.sub(self.pattern_field, fieldVal, new_template, 1)

                            # 不做标注的实体字段
                            for match in re.finditer(self.pattern_val_field, new_template):
                                a_filed = match.groups()[0]
                                fieldVal = self.get_afiled_vaule(a_filed, Datatype.JUST_VALUE)
                                new_template = re.sub(self.pattern_val_field, fieldVal, new_template, 1)

                            new_template=del_(new_template)
                            print("- " + new_template + "\n")
                            save_file_handle.write("- " + new_template + "\n")

        save_file_handle.close()
        return {"url": save_nlu_file}

    # data_type,1:{}需要训练识别,
    # data_type,2:[]不需要训练识别
    def get_afiled_vaule(self, a_field, data_type):
        # 处理字段+Spell特殊情况，使用字段，再转拼音
        fieldVal = ""
        if a_field.endswith("Spell") and len(a_field) > 5:
            a_new_field = a_field[:-5]
            fieldVal = self.get_val_from_dbtypeval(a_new_field)
            fieldVal = pinyin.get(fieldVal, format="strip", delimiter="")
        else:
            fieldVal = self.get_val_from_dbtypeval(a_field).strip()

        if data_type == Datatype.NEED_RECOGNIZE:
            fieldVal = f'[{fieldVal}]({a_field})'
        else:
            fieldVal = f'{fieldVal}'
        return fieldVal

    def get_val_from_dbtypeval(self, a_filed):
        # 随机一条记录
        if a_filed not in self.fieldValue_caches:
            self.fieldValue_caches[a_filed] = self.dictData.get_records_by_field_name(a_filed)
            # 按照来源分
            # field_name,field_value,field_code,field_type,field_source,enable_map,enable_match
            dict_map_by_source = {}
            for val_record in self.dictData.get_records_by_field_name(a_filed):
                # "default"
                field_source = val_record[4].strip()
                if field_source not in dict_map_by_source:
                    dict_map_by_source[field_source] = []
                dict_map_by_source[field_source].append(val_record)
            dict_by_source_list = [dict_map_by_source[akey] for akey in dict_map_by_source]
            self.fieldValue_caches[a_filed] = dict_by_source_list

        fvaca_len = len(self.fieldValue_caches[a_filed])
        if fvaca_len == 0:
            logger.warn(f"a_filed in db hase no field {a_filed}")
            # TODO 其实这里不应该raise，直接跳过就好了
            raise DatabaseError(f"a_filed in db hase no field {a_filed}")
        # 第一次随机
        source_list_index = int(fvaca_len * random.random())
        a_source_list = self.fieldValue_caches[a_filed][source_list_index]
        # 第二次随机
        source_list_len = len(a_source_list)
        index_val = int(source_list_len * random.random())
        val_record = a_source_list[index_val]
        # "(19|20)\\d{2}年"
        field_value = val_record[1]
        # "regex"
        field_type = val_record[3]

        fieldVal = ""
        # 需要 ["查找", "搜索", "检索", "查询", "找", "找一下",""]
        if field_type.lower() == "json_list":
            json_val = json.loads(field_value)
            logger.debug(f" for a  json_list a_filed： {json_val}")
            if len(json_val) > 0:
                fieldVal = json_val[int(len(json_val) * random.random())]
        # 正则表达式
        elif field_type.lower() == "regex":
            fieldVal = rstr.xeger(r'{}'.format(field_value))
        # 普通值
        elif field_type.lower() == "value":
            fieldVal = field_value
        else:
            fieldVal = field_value

        return fieldVal


def del_(template,del_other=True):
    #删除collectTime 的标签
    match = re.findall("\[\S*\](?=\(collectTime\))", template)
    if match:
        template = template.replace("{}(collectTime)".format(match[0]), match[0][1:-1])

    # 删除其他实体的标签
    other_ner = ['gender', 'tripWays', 'vehicleColor', 'nationality', 'houseNo', 'trousersColor', 'collectCode',
                 'cybercafeName', 'vehicleTagType', 'jacketColor', 'alarmMode', 'hairColor', 'deviceType', 'address',
                 'alarmType', 'isKeyPerson', 'violationBehavior', 'vehicleLogo', 'placeName', 'vehicleSeat',
                 'leaseStatus', 'ageRange', 'hasHat', 'CBD', 'hairStyle', 'uphone', 'jacketType', 'nativeCity',
                 'humanName', 'plateColor',  'action_menu', 'color', 'nation', 'hasBag', 'houseProperty',
                 'humanTagType', 'deviceName', 'hotelName', 'isRide', 'smile', 'glass', 'hasMask', 'CCD', 'vehicleType',
                 'hasThings', 'trousersType', 'communityName', 'arrivalPlace', 'placeType', 'humanNameSpell',
                 'departurePlace', 'serviceProvider', 'action']
    if del_other:
        for n in other_ner:
            pattern = "\[[^\]]*\](?=\({}\))".format(n)
            match = re.findall(pattern, template)
            if match:
                template = template.replace("{}".format(match[0]), match[0][1:-1]).replace("({})".format(n), "")
    # 包含有'birthday'类型的实体特殊  时间标注成 year month day 类型
    birthday_rstr_pattern = "(\[(19|20)\d{2}\]\(year\)\年\[(0?[1-9]|1[0-2])月\]\(month\)\[([012]?[0-9]|30|31)(日|号)\]\(day\))|" \
                            "\[(19|20)\d{2}\]\(year\)\/\[(0?[1-9]|1[0-2])\]\(month\)\/\[([012]?[0-9]|30|31)\]\(day\)" \
                            "|\[(19|20)\d{2}\]\(year\)-\[(0?[1-9]|1[0-2])\]\(month\)-\[([012]?[0-9]|30|31)\]\(day\)|" \
                            "\[(19|20)\d{2}\]\(year\)\.\[(0?[1-9]|1[0-2])\]\(month\)\.\[([012]?[0-9]|30|31)\]\(day\)"

    pattern = "\[[^\]]*\](?=\(birthday\))"
    match = re.findall(pattern, template)
    if match:
        template = template.replace("{}(birthday)".format(match[0]), rstr.xeger(birthday_rstr_pattern))

    return template
def add_samples():
    # 加入正则没有生成的样本类型到训练数据中，nlu.md+add_time_regex.md-->added_nlu.md
    nlu_sample_file = "/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/time_extract/time_extract_data/nlu.md"
    with open(nlu_sample_file, 'r', encoding='utf-8') as f:
        nlu_md = f.readlines()
    print(len(nlu_md), nlu_md[:10])
    with open("/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/time_extract/time_extract_data/add_time_regex.md",
              'r', encoding='utf-8') as f:
        add_time_regex = f.readlines()
    print(len(add_time_regex), add_time_regex[:10])

    intent_dict = {}
    intent = "MULTI_INTENT"
    for line in nlu_md + add_time_regex:
        line = line.replace("\n", "")
        if len(line) > 0:
            if "## intent:" in line:
                intent = line.replace("## intent:", "").replace("\n", "")
                if intent in intent_dict:
                    continue
                else:
                    intent_dict[intent] = []
            else:
                intent_dict[intent].append(line)
    print(intent_dict.keys())
    print([(k, len(v)) for k, v in intent_dict.items()])

    with open("/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/time_extract/time_extract_data/added_nlu.md", 'w', encoding='utf-8') as f:
        for k, v in intent_dict.items():
            f.write("## intent:" + k + "\n")
            for v_i in v:
                f.write(v_i + "\n")
def main():
    cdata = CreateData()
    cdata.create_data(sentence_url="/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/data/yundao_data/intent_multi_0722.json",
        line=20)
    add_samples()


def test():
    cdata = CreateData()
    cdata.create_data(sentence_url="/mnt/disk1/lilijuan/HK/HKcode/USTA-nlp/release_2.1.0/llj_test/data/yundao_data/test.json",
        line=10)

if __name__ == '__main__':
    main()



