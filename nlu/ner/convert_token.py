# -*- coding: utf-8 -*-
import os
import re
from shutil import copyfile

from transformers import BertTokenizer

def pre_part(part, tokenizer,writer):
    for atoken in tokenizer.tokenize(part.lower()):
        atoken = atoken[2:] if atoken.startswith("##") else atoken
        writer.write(atoken + " O\n")


def pre_part_BIO(part, tokenizer,writer, field, lable_set):
    index = 0
    for atoken in tokenizer.tokenize(part.lower()):
        atoken = atoken[2:] if atoken.startswith("##") else atoken
        BI = "B-" + field if index == 0 else "I-" + field
        lable_set.add(BI)
        writer.write(atoken + " " + BI + "\n")
        index = index + 1


def convert_nlu_biou(in_file, out_file_train,out_file_dev, lable_set,model_name_or_path):
    # in_file = "face_body_vechletest.md"
    tokenizer = BertTokenizer.from_pretrained(model_name_or_path)
    fout_file_train = open(out_file_train, 'w', encoding="utf-8")
    fout_file_test = open(out_file_dev, 'w', encoding="utf-8")
    index = -1
    with open(in_file, 'r', encoding='utf-8') as infile:
        for line in infile:
            if "## intent" not in line:
                line = line[2:]
                # 是否需要小写，bert模型只支持小写
                line = line.strip()  # .lower()
                if line:
                    # 插入了许多空格，替换成,是否合适
                    line = line.replace(" ", ",")
                    index = index + 1
                    # 20:1的训练、测试集合拆分
                    fout_file = fout_file_train if index % 20 != 0 else fout_file_test
                    rasa_lable = '\[(?P<entity_name>.+?)\]\((?P<entity_field>.+?)(:(?P<entity_val>.+?))?\)'
                    match_list = re.finditer(rasa_lable, line)
                    start = 0
                    for  match in match_list:
                        if start < match.span()[0]:
                            _part = pre_part(line[start:match.span()[0]],tokenizer, fout_file)
                        pre_part_BIO(match.groupdict()['entity_name'],tokenizer, fout_file, match.groupdict()['entity_field'], lable_set)
                        start = match.span()[1]
                        # mdic = match.groupdict()
                    if start < len(line):
                        pre_part(line[start:len(line)],tokenizer, fout_file)
    
                    fout_file.write("\n")
    
    fout_file_train.close()
    fout_file_test.close()

    
# python3 preprocess_new.py nlu3.test 64  nlu3.result.test
# python3 preprocess_new.py nlu3.train 64  nlu3.result.train
# 将iou中字符转成 bert分词格式
def convert_token_to_bert(dataset_nlu_file, max_len, out_file,model_name_or_path):
    subword_len_counter = 0
    
    tokenizer = BertTokenizer.from_pretrained(model_name_or_path)
    print("tokenizer.num_special_tokens_to_add():", tokenizer.num_special_tokens_to_add())
    max_len -= tokenizer.num_special_tokens_to_add()
    fout_file = open(out_file, 'w', encoding="utf-8")
    with open(dataset_nlu_file, "rt", encoding="utf-8") as f_p:
        for line in f_p:
            line = line.rstrip()
    
            if not line:
                # print("not nothing")
                fout_file.write(line + "\n")
                subword_len_counter = 0
                continue
    
            token = line.split()[0]
    
            current_subwords_len = len(tokenizer.tokenize(token))
    
            # Token contains strange control characters like \x96 or \x95
            # Just filter out the complete line
            if current_subwords_len == 0:
                print("strange:token")
                continue
    
            if (subword_len_counter + current_subwords_len) > max_len:
                # print("")
                fout_file.write("\n")
                # print("line,too long")
                subword_len_counter = current_subwords_len
                continue
    
            subword_len_counter += current_subwords_len
            fout_file.write(line + "\n")
    fout_file.close()


# nlu_md_file:nlu3_hangzhou.md ,max_len:64
# 输出四个有用的文件"train.txt","dev.txt","test.txt","labels.txt"
def convert_nlu_to_bert_token_classification(nlu_md_file:str,model_name_or_path,max_len=64):

    data_dir='/'.join(nlu_md_file.split('/')[:-1])
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    # 中间数据
    out_file_train = os.path.join(data_dir, "nlu.train")
    out_file_dev = os.path.join(data_dir, "nlu.dev")
    lable_set = set()
    lable_set.add("O")
    convert_nlu_biou(nlu_md_file, out_file_train, out_file_dev, lable_set,model_name_or_path)
    with open(os.path.join(data_dir, "labels.txt"), "w", encoding="utf-8") as lablef:
        for alabe in lable_set:
            lablef.write(alabe + "\n")
    
    # 将iou中字符转成 bert分词格式
    convert_token_to_bert(out_file_train, max_len, os.path.join(data_dir, "train.txt"),model_name_or_path)
    convert_token_to_bert(out_file_dev, max_len, os.path.join(data_dir, "dev.txt"),model_name_or_path)
    copyfile(os.path.join(data_dir, "dev.txt"), os.path.join(data_dir, "test.txt"))
