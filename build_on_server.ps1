$SSH_KEY = "D:\BaiduSyncdisk\5.code\tools\ssh_key\ssh_key"
$SERVER = "root@10.21.65.20"
$PORT = 22022

Write-Host "=== 连接到远程服务器并执行构建 ===" -ForegroundColor Cyan

# 创建在远程服务器上执行的命令
$remoteCommands = @'
cd /root/switch-manage-Build || exit 1

echo "--- 检查目录 ---"
pwd
ls -la

echo "--- 拉取最新代码 ---"
export GIT_SSH_COMMAND='ssh -i ~/.ssh/git_ssh'
git fetch --all
git checkout fix/backup-schedule-phase1
git pull

echo "--- 修复 CRLF ---"
sed -i 's/\r$//' docker/entrypoint.sh
file docker/entrypoint.sh

echo "--- 检查现有镜像 ---"
docker images | grep switch-manage

echo "--- 执行 Docker 构建 ---"
VERSION=$(date +%Y%m%d)
# 检查版本是否已存在
COUNT=$(docker images | grep switch-manage | grep $VERSION | wc -l)
if [ $COUNT -gt 0 ]; then
    # 递增版本号
    VERSION="${VERSION}-02"
fi
echo "使用版本号: $VERSION"

docker build \
  -f docker/Dockerfile.unified \
  --build-arg NPM_REGISTRY=https://registry.npmmirror.com \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
  -t switch-manage:$VERSION .

echo "--- 验证构建结果 ---"
docker images | grep switch-manage
'@

# 执行远程命令
ssh -i $SSH_KEY -p $PORT $SERVER $remoteCommands
