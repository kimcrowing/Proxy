# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Modify : 2024/3/10
'''
new Env('更新io');
cron: 0/35 * * * *
'''
# 导入必要的模块
import os
import git
import re
import json
import requests
import datetime
from urllib import parse


Pat = os.getenv('pat')
# 定义github仓库的url和本地路径
repo_url = "https://"+Pat+"@github.com/kimcrowing/kimcrowing.github.io.git"
local_path = "/ql/data/repo/kimcrowing.github.io"
json_path="/ql/data/repo/kimcrowing.github.io/Data"
tab_path="/ql/data/repo/kimcrowing.github.io/Tab"
# 登录并获取网盘中的目录
url = 'http://192.168.3.110:5244'
headers = {
    'UserAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
    'Authorization': ''
}

# 使用getToken函数，传入用户名和密码，获取token
username = 'admin'
password = 'qinjing16'

# 如果本地路径不存在，就创建一个
if not os.path.exists(local_path):
    os.mkdir(local_path)

# 使用git模块克隆或拉取仓库到本地
repo = git.Repo.init(local_path)
'''
if not repo.remotes:
    origin = repo.create_remote("origin", repo_url)
else:
    origin = repo.remotes.origin

origin = repo.remotes.origin
origin.fetch("master")
repo.git.rebase(origin.refs[0].remote_head)

# 找到index.html文件的路径
index_path = os.path.join(local_path, "index.html")
# 找到pac文件的路径
proxy_path = os.path.join(json_path, "proxy.pac")
gfw_path = os.path.join(json_path, "gfw.pac")
# 使用requests模块访问一个可以返回你的公网地址的网站，例如https://api.ipify.org/
ip_address = requests.get("https://api.ipify.org/").text

# 检查返回的内容是否为 IP 地址，如果不是，则重试直到获取到 IP 地址为止
while not re.match(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ip_address):
    print("Not an IP address, retrying...")
    ip_address = requests.get("https://api.ipify.org/").text

print(ip_address)

# 打开index.html文件，并读取内容
with open(index_path, "r", encoding="utf-8") as f:
    content = f.read()

# 使用正则表达式修改内容，匹配任意的IP地址，并将其替换为当前本机的公网地址
content = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ip_address, content)
print(content)

# 保存修改后的内容到index.html文件
with open(index_path, "w", encoding="utf-8") as f:
    f.write(content)
'''

# 找到index.html文件的路径
hom_path = os.path.join(local_path, "index.html")
# 找到pac文件的路径
proxy_path = os.path.join(json_path, "proxy.pac")
gfw_path = os.path.join(json_path, "gfw.pac")
# 使用requests模块访问一个可以返回你的公网地址的网站，例如https://api.ipify.org/
ip_address = requests.get("https://api.ipify.org/").text

# 检查返回的内容是否为 IP 地址，如果不是，则重试直到获取到 IP 地址为止
while not re.match(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ip_address):
    print("Not an IP address, retrying...")
    ip_address = requests.get("https://api.ipify.org/").text

print(ip_address)

# 打开index.html文件，并读取内容
with open(hom_path, "r", encoding="utf-8") as f:
    content = f.read()

# 使用正则表达式修改内容，匹配任意的IP地址，并将其替换为当前本机的公网地址
content = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ip_address, content)
print(content)

# 保存修改后的内容到index.html文件
with open(hom_path, "w", encoding="utf-8") as f:
    f.write(content)


# 打开gfw文件，并读取内容
with open(gfw_path, "r", encoding="utf-8") as f:
    conte = f.read()

# 使用正则表达式修改内容，匹配任意的IP地址，并将其替换为当前本机的公网地址
conte = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ip_address, conte)
print(conte)

# 保存修改后的内容到gfw文件
with open(gfw_path, "w", encoding="utf-8") as f:
    f.write(conte)


# 打开pac文件，并读取内容
with open(proxy_path, "r", encoding="utf-8") as f:
    conten = f.read()

# 使用正则表达式修改内容，匹配任意的IP地址，并将其替换为当前本机的公网地址
conten = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", ip_address, conten)
print(conten)

# 保存修改后的内容到index.html文件
with open(proxy_path, "w", encoding="utf-8") as f:
    f.write(conten)

'''
#获取alist文件目录
# 通过用户名、密码获取 token
def getToken(username, password):
    data = {
        'username': username,
        'password': password
    }
    try:
        return json.loads(requests.post(f'{url}/auth/login', data=json.dumps(data), headers={'Content-Type': 'application/json'}).text)
    except Exception as e:
        return {'code': -1, 'message': e}
# 遍历目录及子目录并获取所有文件的文件名、地址
def get_files(path):
    files = []
    data = {
        'password': password,
        'path': path,
    }
    list_url = url + '/api/fs/list'
    response = requests.post(list_url, json=data, headers=headers)
    data = json.loads(response.text)
    for item in data['data']['content']:
        if item['is_dir'] == True:
            files.extend(get_files(path + '/' + item['name']))
            #print(files)
        elif re.search(r'\.(mp4|mkv|flv)$', item['name']) or re.search(r'nfo', item['name']):
            files.append({'name': item['name'], 'path': path + '/' + item['name']})
            #print(files)
    return files

token = getToken(username, password)
if token['code'] == 0:
    headers['Authorization'] = token['data']
else:
    print(token['message'])

path = '/ATV'
files = get_files(path)

url_path = os.path.join(json_path, "url.json")
with open(url_path, 'w') as f:
    json.dump(files, f)
print(files)


#获取视频播放地址
def getDownloadInfo(path):
    data = {
        'path': path
    }
    try:
        response = requests.post(
            f'{url}/api/fs/get', data=data, headers=headers).json()
        if response['code'] == 200:
            # 使用正则表达式判断文件名是否包含-poster或者文件后缀是否为.mp4或.mkv或.flv，并且文件类型为file
            pattern = r'-poster|\.mp4|\.mkv|\.flv'
            if (re.search(pattern, response['data']['name']) and response['data']):
                return response['data']
            else:
                return {}
        else:
            return {'code': -1, 'message': response['message']}
    except Exception as e:
        return {'code': -1, 'message': e}


# 读取url.json文件中的视频文件路径
with open(url_path, 'r') as f:
    files = json.load(f)

# 筛选出所有视频文件的path
video_files = [file for file in files if re.search(r'\.(mp4|mkv|flv)$', file['name'])]

data = []
# 遍历所有视频文件
for file in video_files:
    # 获取视频文件的路径
    path = file['path']
    # 使用getDownloadInfo函数，传入文件路径，获取下载信息
    download_info = getDownloadInfo(path)
    print(download_info)
    # 判断是否获取成功，如果成功，打印下载地址和访问密钥
    if isinstance(download_info, dict) and 'raw_url' in download_info and 'thumb' in download_info:
        print(f'下载地址：{download_info["raw_url"]}')
        #print(f'海报：{download_info["thumb"]}')
        # 遍历related列表中的每个字典
        for file in download_info["related"]:
            # 如果name中含有-poster
            if "-poster" in file["name"]:
                # 打印thumb值
                print(f'海报：{file["thumb"]}')
                data.append({
                    'name': download_info['name'],
                    'raw_url': download_info['raw_url'],
                    'thumb': file['thumb']
                })

# 将数据保存至data.json文件中
data_path=os.path.join(json_path, "data.json")
with open(data_path, 'w') as f:
    json.dump(data, f)
    print("获取视频地址成功")

'''
