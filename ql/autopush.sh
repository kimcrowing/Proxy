#!/bin/bash
'''
new Env('更新主页');
cron: 1-59/45 * * * *
'''

# 获取 PAT (PAT 是一个访问仓库的授权码)
PAT=$pat

# 定义仓库地址和本地路径
REPO_URL="https://$PAT@github.com/kimcrowing/kimcrowing.github.io.git"  # 仓库地址，包含 PAT 用于授权
LOCAL_PATH="/ql/data/repo/kimcrowing_kimcrowing.github.io"  # 本地仓库目录
JSON_PATH="$LOCAL_PATH/Data"  # JSON 数据文件所在目录
TAB_PATH="$LOCAL_PATH/Tab"    # Tab 标签文件所在目录（似乎没有用到）

# 创建本地路径 (如果不存在)
if [ ! -d "$LOCAL_PATH" ]; then
  mkdir "$LOCAL_PATH"  # 创建本地目录，用于存放仓库克隆下来的内容
fi

# 获取当前时间
CURRENT_TIME=$(date +"%Y-%m-%d %H:%M:%S")  # 获取当前时间，格式为 "2024-04-20 19:26:43"

# 更新 index.html 文件
INDEX_PATH="$LOCAL_PATH/index.html"
sed -i "s~\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b~$CURRENT_TIME~g" "$INDEX_PATH"  # 用当前时间替换 IP 地址匹配模式

# 输出修改后的 index 内容
MODIFIED_INDEX_CONTENT=$(cat "$INDEX_PATH")
echo "修改后的 index 内容 (完整):"
echo "$MODIFIED_INDEX_CONTENT"

# 更新 gfw.pac 文件
GFW_PAC_PATH="$JSON_PATH/gfw.pac"
sed -i "s~\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b~$CURRENT_TIME~g" "$GFW_PAC_PATH"  # 用当前时间替换 IP 地址匹配模式

# 输出修改后的 gfw 内容
MODIFIED_GFW_CONTENT=$(cat "$GFW_PAC_PATH")
echo "修改后的 gfw 内容 (完整):"
echo "$MODIFIED_GFW_CONTENT"

# 更新仓库
git clone "$REPO_URL" "$LOCAL_PATH"  # 克隆仓库到本地目录
cd "$LOCAL_PATH"
git pull origin master  # 拉取远程仓库的最新代码

# 提交并推送改动，并实现重试机制
MAX_RETRY_COUNT=5  # 设置最大重试次数
RETRY_COUNT=0  # 初始化重试计数器

while [ $RETRY_COUNT -lt $MAX_RETRY_COUNT ]; do
  git add .
  git commit -m "更新 IP 地址和内容至 $CURRENT_TIME"
  git push origin master

  if [ $? -eq 0 ]; then
    echo "推送成功！"
    break
  else
    echo "推送失败！重试 $((RETRY_COUNT + 1))/$MAX_RETRY_COUNT..."
    sleep 10  # 重试之间延迟 10 秒
    RETRY_COUNT=$((RETRY_COUNT + 1))
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRY_COUNT ]; then
  echo "经过 $MAX_RETRY_COUNT 次重试后仍推送失败。请检查网络连接并手动重试。"
fi

