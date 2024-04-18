#!/bin/bash

'''
new Env('拉取远程更新');
cron: 12 1-23/5 * * *
'''
local_path = "/ql/data/repo/kimcrowing.github.io"
cd $local_path
git pull origin
