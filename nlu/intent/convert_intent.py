# -*- coding: utf-8 -*-
import json
import re
import os
from shutil import copyfile

def write_line(line, number, writer):
        writer.write(line + "" + "\t" + str(number) + "\n")


absFilePath = os.path.abspath(__file__)
cureent_dir, _ = os.path.split(absFilePath)


def convert_nlu_to_bert_text_classification(in_file:str):
    out_file_dir='/'.join(in_file.split('/')[:-1])
    if not os.path.exists(out_file_dir):
        os.makedirs(out_file_dir)
    
    fout_file_train = open(os.path.join(out_file_dir, "train.tsv"), 'w', encoding="utf-8")
    fout_file_train.write("sentence" + "\t" + "label" + "\n")
    fout_file_test = open(os.path.join(out_file_dir, "test.tsv"), 'w', encoding="utf-8")
    fout_file_test.write("sentence" + "\t" + "label" + "\n")
    
    fout_file_labels = open(os.path.join(out_file_dir, "labels.txt"), 'w', encoding="utf-8")
    # in_file = "face_body_vechletest.md"
    index = -1
    intentnum = -1
    class_map = {}
    labels = []
    with open(in_file, 'r', encoding='utf-8') as infile:
        class_str = ""
        for line in infile:
            if "## intent" not in line:
                line = line[2:]
                line = line.strip()  # .lower()
                if line:
                    line = line.replace(" ", ",")
                    index = index + 1
                    fout_file = fout_file_train if index % 20 != 0 else fout_file_test
                    line = re.sub(r'\[(.+?)\]\(.+?\)', r"\1", line)
                    line = line.lower()
                    write_line(line, class_str, fout_file)
     
            else:
                intentnum += 1
                class_str = line[line.index("intent:") + 7:].strip()
                class_map[intentnum] = class_str
                labels.append(class_str)
                fout_file_labels.write(class_str + "\n")
    fout_file_train.close()
    fout_file_test.close()
    fout_file_labels.close()
    
    copyfile(os.path.join(out_file_dir, "test.tsv"),os.path.join(out_file_dir, "dev.tsv"))
    
    with open(os.path.join(out_file_dir, 'class_map.txt'), 'w') as outfile:
        json.dump(labels, outfile)
