# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Modify : 2024/2/8
'''
new Env('上传公网IP');
cron: 0 6,10,12,15,17 * * *
'''
import sys
import os
import traceback
import requests
from loguru import logger

def post_msg(url: str, data: dict) -> bool:
    response = requests.post(url, data=data)
    code = response.status_code
    if code == 200:
        return True
    else:
        return False
        
def ServerChan_send(sendkey, title: str, desp: str = '') -> bool:
    url = 'https://sctapi.ftqq.com/{0}.send'.format(sendkey)
    data = {
        'title': title,  # 消息标题，必填。最大长度为 32
        'desp': desp  # 消息内容，选填。支持 Markdown语法 ，最大长度为 32KB ,消息卡片截取前 30 显示
    }

    return post_msg(url, data)

def PushPlus_send(token, title: str, desp: str = '', template: str = 'markdown') -> bool:
    url = 'http://www.pushplus.plus/send'
    data = {
        'token': token,  # 用户令牌
        'title': title,  # 消息标题
        'content': desp,  # 具体消息内容，根据不同template支持不同格式
        'template': template,  # 发送消息模板
    }

    return post_msg(url, data)
    
        
PUSH_KEY = ''
if os.getenv('PUSH_PLUS_TOKEN'):
    PUSH_PLUS_TOKEN = os.getenv('PUSH_PLUS_TOKEN')
if os.getenv('PUSH_KEY'):
    PUSH_KEY = os.getenv('PUSH_KEY')

url='http://jsonip.com'
# 获取IP地址
resp = requests.get(url)
info = resp.json()
public_ip = info.get('ip')
title = "IP为：" + public_ip
msg = "公网IP为：" + public_ip
print (msg)
if PUSH_PLUS_TOKEN:
	PushPlus_send(PUSH_PLUS_TOKEN, title, msg)
