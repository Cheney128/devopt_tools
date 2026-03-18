
$SSH_KEY = "D:\BaiduSyncdisk\5.code\tools\ssh_key\ssh_key"
$SERVER = "root@10.21.65.20"
$PORT = 22022
$VERSION = "20260318-1315"

Write-Host "=== 推送镜像到私有仓库 ===" -ForegroundColor Cyan

$remoteCommands = @"
cd /root/switch-manage-Build
docker tag switch-manage:20260318 10.21.65.20:5000/switch-manage:$VERSION
docker push 10.21.65.20:5000/switch-manage:$VERSION
docker images | grep switch-manage
"@

ssh -i $SSH_KEY -p $PORT $SERVER $remoteCommands

