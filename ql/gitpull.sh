#!/bin/bash

'''
new Env('拉取远程更新');
cron: 12 1-23/5 * * *
'''
cd /ql/data/repo/kimcrowing_kimcrowing.github.io
git pull origin
