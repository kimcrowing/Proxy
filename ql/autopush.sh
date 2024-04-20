#!/bin/bash
'''
new Env('更新主页');
cron: 12 1-23/2 * * *
'''
# 获取 PAT
PAT=$pat

# 定义仓库地址和本地路径
REPO_URL="https://$PAT@github.com/kimcrowing/kimcrowing.github.io.git"
LOCAL_PATH="/ql/data/repo/kimcrowing_kimcrowing.github.io"
JSON_PATH="$LOCAL_PATH/Data"
TAB_PATH="$LOCAL_PATH/Tab"

# 创建本地路径 (如果不存在)
if [ ! -d "$LOCAL_PATH" ]; then
  mkdir "$LOCAL_PATH"
fi

# 获取当前时间
CURRENT_TIME=$(date +"%Y-%m-%d %H:%M:%S")

# 检查未提交的更改
UNCOMMITTED_CHANGES=$(git status -s)
if [ ! -z "$UNCOMMITTED_CHANGES" ]; then
  echo "本地仓库中发现未提交的更改："
  echo "$UNCOMMITTED_CHANGES"
  echo "正在丢弃这些更改..."
  git checkout -- .git/HEAD@{1}  # 丢弃未提交的更改
fi

# 更新 index.html 文件
INDEX_PATH="$LOCAL_PATH/index.html"
sed -i "s~\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b~$CURRENT_TIME~g" "$INDEX_PATH"

# 输出修改后的 index 内容
MODIFIED_INDEX_CONTENT=$(cat "$INDEX_PATH")
echo "修改后的 index 内容 (完整):"
echo "$MODIFIED_INDEX_CONTENT"

# 更新 gfw.pac 文件
GFW_PAC_PATH="$JSON_PATH/gfw.pac"
sed -i "s~\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b~$CURRENT_TIME~g" "$GFW_PAC_PATH"

# 输出修改后的 gfw 内容
MODIFIED_GFW_CONTENT=$(cat "$GFW_PAC_PATH")
echo "修改后的 gfw 内容 (完整):"
echo "$MODIFIED_GFW_CONTENT"

# 更新仓库
git clone "$REPO_URL" "$LOCAL_PATH"  # 克隆仓库到本地目录
cd "$LOCAL_PATH"
git pull origin master  # 从远程仓库拉取最新更改

# 提交并推送更改，并实现重试机制
MAX_RETRY_COUNT=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRY_COUNT ]; do
  git add .
  git commit -m "更新 IP 地址和内容至 $CURRENT_TIME"
  git push origin master

  if [ $? -eq 0 ]; then
    echo "推送成功！"
    break
  else
    echo "推送失败！重试 $((RETRY_COUNT + 1))/$MAX_RETRY_COUNT..."
    sleep 10
    RETRY_COUNT=$((RETRY_COUNT + 1))
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRY_COUNT ]; then
  echo "经过 $MAX_RETRY_COUNT 次重试后仍推送失败。请检查网络连接并手动重试。"
fi
