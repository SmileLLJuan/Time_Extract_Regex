# -*- coding:utf-8 -*-
# @Time: 2020/12/18 16:41
# @Author: ShaozongLi
# @Email: lishaozong@hikvision.com.cn
# @File: generator_time.py
import random

import re
import rstr

from utils.url import get_time_file


class TimeGenderator():
    def __init__(self):
        self.time_list=self.read_time_sentence()
        self.connector=["至","到","和","~"]
    def read_time_sentence(self):
        time_list=[]
        '''
        读取文件加载到list，非"#"开头的
        :return:
        '''
        f=open(get_time_file())
        try:
            lines=f.readlines()
            for line in lines:
                if line and not line.startswith("#"):
                    time_list.append(line)
        finally:
            f.close()
        return time_list

    def get_field_value(self, fields_name:[]):
        '''
        :param fields_name:
        :return:
        '''
        pass

    def get_time_value(self,flag:True):
        '''
        从time_list中随机读取一行，进行时间生成
        :return:
        '''
        while True:
            if self.time_list:
                regex_line=self.time_list[random.randint(0,len(self.time_list)-1)]
                time_line=rstr.xeger(regex_line).replace("\r","").replace("\n","")
                if random.randint(0, 9) == 1:
                    regex_line_2=self.time_list[random.randint(0,len(self.time_list)-1)]
                    time_line_2=rstr.xeger(regex_line_2).replace("\r","").replace("\n","")
                    time_line=(time_line+self.connector[random.randint(0,3)]+time_line_2)
                if time_line:
                    break
        if flag:
            return "["+time_line+"](collectTime)"
        else:
            return time_line
if __name__=="__main__":
     genertor=TimeGenderator()
     for i in range(1,1000):
        print(genertor.get_time_value(flag=True))
        # print(random.randint(0,3))
     # print(rstr.xeger("((20|19)?\d{2})"))




