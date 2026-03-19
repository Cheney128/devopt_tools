$SSH_KEY = "D:\BaiduSyncdisk\5.code\tools\ssh_key\ssh_key"
$PROD_SERVER = "root@10.23.65.95"
$PROD_PORT = "22022"
$PROJECT_DIR = "/data/it-devops"

Write-Host "=== 检查生产环境状态 ===" -ForegroundColor Cyan

$remoteCommands = @'
cd /data/it-devops
echo "--- 当前 docker-compose.prod.yml ---"
cat docker-compose.prod.yml
echo ""
echo "--- 当前运行的容器 ---"
docker ps
echo ""
echo "--- 健康检查 ---"
curl -s http://localhost/health
'@

ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER $remoteCommands
