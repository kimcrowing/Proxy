#!/bin/bash
'''
new Env('更新主页');
cron: 18 1-23/3 * * *
'''

# 获取 PAT (PAT 是一个访问仓库的授权码)
PAT=$pat

# 定义仓库地址和本地路径
REPO_URL="https://$PAT@github.com/kimcrowing/kimcrowing.github.io.git" # 仓库地址，包含 PAT 用于授权
LOCAL_PATH="/ql/data/repo/kimcrowing_kimcrowing.github.io" # 本地仓库目录
JSON_PATH="$LOCAL_PATH/Data" # JSON 数据文件所在目录
TAB_PATH="$LOCAL_PATH/Tab"  # Tab 标签文件所在目录（似乎没有用到）

# 创建本地路径 (如果不存在)
if [ ! -d "$LOCAL_PATH" ]; then
 mkdir "<span class="math-inline">LOCAL\_PATH" \# 创建本地目录，用于存放仓库克隆下来的内容
fi
\# 获取公网 IP 地址
IP\_ADDRESS\=</span>(curl -s https://api.ipify.org/)
while ! [[ <span class="math-inline">IP\_ADDRESS \=\~ ^\[0\-9\]\{1,3\}\\\.\[0\-9\]\{1,3\}\\\.\[0\-9\]\{1,3\}\\\.\[0\-9\]\{1,3\}</span> ]]; do
 echo "无效的 IP 地址，重试..."
 IP_ADDRESS=<span class="math-inline">\(curl \-s https\://api\.ipify\.org/\)
done
\# 检查未提交的更改
UNCOMMITTED\_CHANGES\=</span>(git status -s)
if [ ! -z "$UNCOMMITTED_CHANGES" ]; then
  echo "本地仓库中发现未提交的更改："
  echo "$UNCOMMITTED_CHANGES"
  echo "正在丢弃这些更改..."
  git checkout -- .git/HEAD@{1}  # 丢弃未提交的更改
fi

# 更新 index.html 文件
INDEX_PATH="$LOCAL_PATH/index.html"
sed -i "s~\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b~$IP_ADDRESS~g" "<span class="math-inline">INDEX\_PATH"
\# 输出修改后的 index 内容
MODIFIED\_INDEX\_CONTENT\=</span>(cat "$INDEX_PATH")
echo "修改后的 index 内容 (完整):"
echo "$MODIFIED_INDEX_CONTENT"

# 更新 gfw.pac 文件
GFW_PAC_PATH="$JSON_PATH/gfw.pac"
sed -i "s~\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b~$IP_ADDRESS~g" "<span class="math-inline">GFW\_PAC\_PATH"
\# 输出修改后的 gfw 内容
MODIFIED\_GFW\_CONTENT\=</span>(cat "$GFW_PAC_PATH")
echo "修改后的 gfw 内容 (完整):"
\# echo "$MODIFIED_GFW_CONTENT"

# 更新仓库
git clone "$REPO_URL" "$LOCAL_PATH" # 克隆仓库到本地目录
cd "$LOCAL_PATH"

# 使用重试机制更新仓库
MAX_RETRY_COUNT=5  # 最大重试次数
RETRY_COUNT=0      # 重试计数器

# 拉取远程仓库更新，并实现重试机制
while [ $RETRY_COUNT -lt $MAX_RETRY_COUNT ]; do
  git pull origin master

  if [ $? -eq 0 ]; then
    echo "拉取成功！"
    break
  else
    echo "拉取失败！尝试第 $((RETRY_COUNT + 1))/<span class="math-inline">MAX\_RETRY\_COUNT 次重试\.\.\."
sleep 10
RETRY\_COUNT\=</span>((RETRY_COUNT + 1))
  fi
done

if [ $RETRY_COUNT -eq $MAX_RETRY_COUNT ]; then
  echo "拉取失败，重试 $MAX_RETRY_COUNT 次后仍无法拉取。请检查网络连接并手动重试。"
fi

# 提交并推送更改，并实现重试机制
RETRY_COUNT=0  # 重试计数器重置

while [ $RETRY_COUNT -lt $MAX_RETRY_COUNT ]; do
  git add .
  git commit -m "更新 IP 地址和内容"
  git push origin master

  if [ $? -eq 0 ]; then
    echo "推送成功！"
    break
  else
    echo "推送失败！尝试第 $((RETRY_COUNT + 1))/<span class="math-inline">MAX\_RETRY\_COUNT 次重试\.\.\."
sleep 10
RETRY\_COUNT\=</span>((RETRY_COUNT + 1))
  fi
done

if 
