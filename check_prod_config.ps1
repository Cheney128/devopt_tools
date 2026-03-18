$SSH_KEY = "D:\BaiduSyncdisk\5.code\tools\ssh_key\ssh_key"
$PROD_SERVER = "root@10.23.65.95"
$PROD_PORT = "22022"
$PROJECT_DIR = "/data/it-devops"

Write-Host "=== 查看生产环境 docker-compose 配置 ===" -ForegroundColor Cyan
ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER "cat $PROJECT_DIR/docker-compose.prod.yml"

Write-Host "`n=== 查看当前运行的容器 ===" -ForegroundColor Cyan
ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER "docker ps"
