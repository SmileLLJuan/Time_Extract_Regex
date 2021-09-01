# -*- coding:utf-8 -*-
# @Time: 2021/5/13 14:55
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: ner_remove.py


# 移除一个实体包含另外一个实体的情况，以最长的实体为准
def _remove_include_entities(predict_entities):
    if predict_entities:
        for entity in predict_entities:
            if is_remove_entity(entity, predict_entities):
                predict_entities.remove(entity)
                _remove_include_entities(predict_entities)
        return predict_entities
    else:
        return []


def is_remove_entity(entity, all_entity):
    start = entity["start"]
    end = entity["end"]
    confidence = entity["confidence"]
    if confidence < 0.4:
        return True
    bool_flag = False
    for et in all_entity:
        et_start = et["start"]
        et_end = et["end"]
        et_confidence = et["confidence"]
        et_flag = (et_confidence - confidence) > 0.2
        confidence_flag = (confidence - et_confidence) > 0.2
        # 相同实体移除掉一个
        if et == entity:
            continue
        # 首先范围相同的实体，根据置信度判断
        if et_start == start and et_end == end or (entity["entity"] == et["entity"] and entity["value"] == et["value"]):
            # 保留置信度高的
            if et_confidence > confidence:
                bool_flag = bool_flag or True
            else:
                bool_flag = bool_flag or False
        # 存在重叠
        # if is_range_over(entity,et) or (et["entity"] == entity["entity"] and et != entity):
        if is_range_over(entity, et):
            # 如果存在置信度差值大于entity 0.2的实体，则移除
            if et_flag:
                bool_flag = bool_flag or True
            elif confidence_flag:
                bool_flag = bool_flag or False;
            else:
                # 置信度相差不大的时候
                # 存在一种情况无法判断：前4月份中的红色上衣抓拍 “前4月份” “4月份中”都识别为collectTime并且置信度都为1
                if (et_end - et_start) > (end - start):
                    bool_flag = bool_flag or True
                elif (et_end - et_start) == (end - start):
                    if et_confidence > confidence:
                        bool_flag = bool_flag or True
                    else:
                        bool_flag = bool_flag or False
                else:
                    bool_flag = bool_flag or False
    return bool_flag


'''判断两个实体start和end范围是否存在重叠'''


def is_range_over(entity, et_entity):
    start = entity["start"]
    end = entity["end"]
    et_start = et_entity["start"]
    et_end = et_entity["end"]
    range_a = range(start, end)
    range_b = range(et_start, et_end)
    range_inter = set(range_a) & set(range_b)
    return len(range_inter) > 0
