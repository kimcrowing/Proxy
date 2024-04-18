#!/bin/bash

# 先注册azure应用,确保应用有以下权限:
# files:	Files.Read.All、Files.ReadWrite.All、Sites.Read.All、Sites.ReadWrite.All
# user:	User.Read.All、User.ReadWrite.All、Directory.Read.All、Directory.ReadWrite.All
# mail:  Mail.Read、Mail.ReadWrite、MailboxSettings.Read、MailboxSettings.ReadWrite
# 注册后一定要再点代表xxx授予管理员同意,否则outlook api无法调用
# 请填写好下面配置CLIENT_ID、CLIENT_SECRET、REFRESH_TOKEN
#获取微软Office 365应用APPID、secret、access_token、refresh_token等：https://gitee.com/kimcrowing/www/raw/master/Office%20365.jpeg
#青龙环境变量添加CLIENT_ID，CLIENT_SECRET，REFRESH_TOKEN
# 配置开始
'''
new Env('拉取远程更新');
cron: 12 1-23/5 * * *
'''
local_path = "/ql/data/repo/kimcrowing.github.io"
cd local_path
git pull origin
