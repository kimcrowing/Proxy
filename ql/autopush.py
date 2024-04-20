# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Modify : 2024/2/8
'''
new Env('更新主页');
cron: 1-59/45 * * * *
'''
from git import Repo
import os
import datetime

# 获取当前的日期，并转换为字符串，格式为"yyyy-mm-dd"
date = datetime.datetime.now()
date_str = date.strftime("%Y-%m-%d-%H:%M:%S")
dirfile = os.path.abspath('/ql/data/repo/kimcrowing_kimcrowing.github.io') # code的文件位置，我默认将其存放在根目录下
repo = Repo(dirfile)

g = repo.git
g.push()
g.add("--all")
g.commit(m=date_str)

# 使用 while 循环来不断尝试 push，直到成功为止
while True:
    try:
        g.push()
        print("Successful push!")
        break
    except:
        print("Push failed, retrying...")
