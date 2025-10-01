#!/bin/sh

'''
new Env('更新主页');
cron: 18 1-23/2 * * *
'''
user="kimcrowing"
Pat="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"
# 定义仓库URL和本地路径
repo_url="https://$user:$Pat@github.com/kimcrowing/kimcrowing.github.io.git"
local_path="$(pwd)"
#"~/storage/downloads/TV/kimcrowing.github.io"

# 检查目录是否存在
if [ ! -d "$local_path" ]; then
  # 目录不存在，创建目录并克隆仓库
  mkdir -p "$local_path"
  git clone "$repo_url" "$local_path"
else
  # 目录存在，进入目录并更新仓库
  (cd "$local_path" && git pull)
fi

# 获取公网IP地址
while true; do
  ip_address=$(curl -s https://api-ipv4.ip.sb/ip -A Mozilla)
  if [[ $ip_address =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "有效的IP地址: $ip_address"
    break
  else
    echo "获取的IP地址无效: $ip_address，正在重试..."
    sleep 1
  fi
done

# 在index.html和gfw.pac文件中查找所有IP地址
ip_regex="([0-9]{1,3}\.){3}[0-9]{1,3}"

# 打印index.html和gfw.pac文件中匹配的IP地址
for file in "$local_path/index.html" "$local_path/Data/gfw.pac"; do
  echo "在 $file 中匹配的IP地址:"
  sed -i -E "s/$ip_regex/$ip_address/g" "$file"
  if [ $? -ne 0 ]; then
    echo "替换 $file 中的IP地址失败"
    exit 1
  fi
done

# 显示替换后的index.html内容echo "替换后的index.html内容:"cat "$local_path/index.html"

# 将更改添加到暂存区
cd "$local_path"
git add .

# 检查是否有文件更改
# 获取文件的最后修改时间
last_modified_time=$(stat -c %y "$local_path/index.html" | cut -d'.' -f1)



# 定义一个带有重试的推送更改函数
push_changes() {
  local max_retries=3
  local delay_between_retries=5 # 秒
  local attempt=1

  while [ $attempt -le $max_retries ]; do
    echo "尝试第 $attempt 次推送更改..."
    git push
    if [ $? -eq 0 ]; then
      echo "推送成功。"
      return 0
    else
      echo "推送失败。$delay_between_retries 秒后重试..."
      sleep $delay_between_retries
      attempt=$((attempt+1))
    fi
  done

  echo "尝试了 $max_retries 次推送后失败。"
  return 1
}
# 使用文件的最后修改时间作为提交消息
git commit -m "$last_modified_time"

# 调用函数推送更改
push_changes
