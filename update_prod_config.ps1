$SSH_KEY = "D:\BaiduSyncdisk\5.code\tools\ssh_key\ssh_key"
$PROD_SERVER = "root@10.23.65.95"
$PROD_PORT = "22022"
$PROJECT_DIR = "/data/it-devops"
$OLD_VERSION = "20260311-05"
$NEW_VERSION = "20260318"

Write-Host "=== 更新生产环境 docker-compose.prod.yml ===" -ForegroundColor Cyan

$remoteCommands = @"
cd $PROJECT_DIR
sed -i 's/switch-manage:$OLD_VERSION/switch-manage:$NEW_VERSION/' docker-compose.prod.yml
cat docker-compose.prod.yml | grep image
"@

ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER $remoteCommands
