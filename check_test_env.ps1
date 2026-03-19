$SSH_KEY = "D:\BaiduSyncdisk\5.code\tools\ssh_key\ssh_key"
$SERVER = "root@10.21.65.20"
$PORT = 22022

Write-Host "=== 检查测试环境端口使用情况 ===" -ForegroundColor Cyan

$remoteCommands = @'
echo "--- 检查现有容器 ---"
docker ps -a

echo ""
echo "--- 检查端口占用 ---"
netstat -tlnp 2&gt;/dev/null || ss -tlnp

echo ""
echo "--- 检查本地 Docker 镜像 ---"
docker images | grep switch-manage
'@

ssh -i $SSH_KEY -p $PORT $SERVER $remoteCommands
