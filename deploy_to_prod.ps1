$SSH_KEY = "D:\BaiduSyncdisk\5.code\tools\ssh_key\ssh_key"
$PROD_SERVER = "root@10.23.65.95"
$PROD_PORT = "22022"
$PROJECT_DIR = "/data/it-devops"

Write-Host "=== 拉取新镜像并部署到生产环境 ===" -ForegroundColor Cyan

$remoteCommands = @"
cd $PROJECT_DIR
echo "--- 拉取新镜像 ---"
docker compose -f docker-compose.prod.yml pull
echo "--- 重启服务 ---"
docker compose -f docker-compose.prod.yml up -d
echo "--- 等待容器启动 ---"
sleep 10
docker ps
"@

ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER $remoteCommands
