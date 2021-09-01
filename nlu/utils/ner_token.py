# -*- coding:utf-8 -*-
# @Time: 2021/6/16 16:12
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: ner_token.py

def _get_entity(tokens: list, start):
    word = tokens[0]['word']
    entity_name = tokens[0]['entity'][2:]
    score = tokens[0]['score']
    start_index = tokens[0]['index']
    token=tokens[0]
    next_index:int = token['index']
    for token in tokens[1:]:
        next_word: str = token['word']
        next_score: float = token['score']
        next_index: int = token['index']
        next_entity: str = token['entity']
        if next_entity.startswith('I-'):
            next_entity_name = token['entity'][2:]
            if next_entity_name == entity_name:
                word += next_word.replace('###', '')
                score += next_score
                continue
            else:
                break
        else:
            break
    score = score / (next_index - start_index) if token!= tokens[-1] else score / (next_index - start_index+1)
    return next_index, {"entity": entity_name, "value": word, "start": start, "confidence": score,
                        "end": (start + len(word))}


def get_entities_from_token(tokens: list):
    '''
    基于token的label list合成实体方法：
        已B-entity 开头，遇到'O' 或者 ’I-其他‘ 结束
    :param tokens:
    :return:
    '''
    tokens = tokens[1:-1]
    all_entities = []
    end = 0
    for i in range(0, len(tokens)):
        token = tokens[i]
        label: str = token['entity']
        if label.startswith('B-'):
            # 进入到另外一个方法，返回index：i和实体entity
            i, entity = _get_entity(tokens[i:], start=end)
            end = entity['end']
            all_entities.append(entity)
    return all_entities


if __name__ == '__main__':
    tokens = [
        {'word': '[CLS]', 'score': 0.998790442943573, 'entity': 'O', 'index': 0},
        {'word': '2021', 'score': 0.999862790107727, 'entity': 'B-collectTime', 'index': 1},
        {'word': '年', 'score': 0.9999338388442993, 'entity': 'I-collectTime', 'index': 2},
        {'word': '7', 'score': 0.9999339580535889, 'entity': 'I-collectTime', 'index': 3},
        {'word': '月', 'score': 0.9999332427978516, 'entity': 'I-collectTime', 'index': 4},
        {'word': '1', 'score': 0.9999317526817322, 'entity': 'I-collectTime', 'index': 5},
        {'word': '日', 'score': 0.9998916983604431, 'entity': 'I-collectTime', 'index': 6},
        {'word': '浙', 'score': 0.999714195728302, 'entity': 'B-address', 'index': 7},
        {'word': '江', 'score': 0.9999314546585083, 'entity': 'I-address', 'index': 8},
        {'word': '杭', 'score': 0.9999282360076904, 'entity': 'I-address', 'index': 9},
        {'word': '州', 'score': 0.9999381303787231, 'entity': 'I-address', 'index': 10},
        {'word': '滨', 'score': 0.9999385476112366, 'entity': 'I-address', 'index': 11},
        {'word': '江', 'score': 0.9999396800994873, 'entity': 'I-address', 'index': 12},
        {'word': '区', 'score': 0.9999390244483948, 'entity': 'I-address', 'index': 13},
        {'word': '江', 'score': 0.9999359250068665, 'entity': 'I-address', 'index': 14},
        {'word': '陵', 'score': 0.9999383091926575, 'entity': 'I-address', 'index': 15},
        {'word': '路', 'score': 0.9999366998672485, 'entity': 'I-address', 'index': 16},
        {'word': '穿', 'score': 0.9999743103981018, 'entity': 'O', 'index': 17},
        {'word': '白', 'score': 0.9996840953826904, 'entity': 'B-jacketColor', 'index': 18},
        {'word': '色', 'score': 0.9997743368148804, 'entity': 'I-jacketColor', 'index': 19},
        {'word': '短', 'score': 0.9997466802597046, 'entity': 'B-jacketType', 'index': 20},
        {'word': '袖', 'score': 0.9998107552528381, 'entity': 'I-jacketType', 'index': 21},
        {'word': '的', 'score': 0.9999678134918213, 'entity': 'O', 'index': 22},
        {'word': '中', 'score': 0.9994918704032898, 'entity': 'B-ageRange', 'index': 23},
        {'word': '年', 'score': 0.9997414350509644, 'entity': 'I-ageRange', 'index': 24},
        {'word': '男', 'score': 0.9998541474342346, 'entity': 'B-gender', 'index': 25},
        {'word': '子', 'score': 0.9999029636383057, 'entity': 'I-gender', 'index': 26},
        {'word': '[SEP]', 'score': 0.997530460357666, 'entity': 'I-gender', 'index': 27}
    ]
    print(get_entities_from_token(tokens))
