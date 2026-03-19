$SSH_KEY = "D:\BaiduSyncdisk\5.code\tools\ssh_key\ssh_key"
$PROD_SERVER = "root@10.23.65.95"
$PROD_PORT = "22022"
$PROJECT_DIR = "/data/it-devops"
$VERSION = "20260318-1647"

Write-Host "=== 部署到生产环境 ===" -ForegroundColor Cyan
Write-Host "版本: $VERSION" -ForegroundColor Green

# 1. 读取当前配置
Write-Host "--- 读取当前 docker-compose.prod.yml ---" -ForegroundColor Yellow
ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER "cat $PROJECT_DIR/docker-compose.prod.yml"

Write-Host ""
Write-Host "--- 更新配置文件 ---" -ForegroundColor Yellow

# 创建远程更新脚本
$remoteUpdateScript = @"
#!/bin/bash
cd $PROJECT_DIR

VERSION="$VERSION"
IMAGE="10.21.65.20:5000/switch-manage:\$VERSION"

echo "当前镜像版本:"
grep "image:" docker-compose.prod.yml

echo "更新为: \$IMAGE"
sed -i "s|image: 10.21.65.20:5000/switch-manage:.*|image: \$IMAGE|" docker-compose.prod.yml

echo "更新后的配置:"
grep "image:" docker-compose.prod.yml
"@

# 执行更新
$tempUpdateScript = "d:\temp\update_prod_config.sh"
$remoteUpdateScript | Out-File -FilePath $tempUpdateScript -Encoding utf8 -NoNewline

scp -i $SSH_KEY -P $PROD_PORT $tempUpdateScript ${PROD_SERVER}:/root/update_prod_config.sh

ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER 'sed -i "s/\r$//" /root/update_prod_config.sh && chmod +x /root/update_prod_config.sh && /root/update_prod_config.sh'

Remove-Item $tempUpdateScript -Force

Write-Host ""
Write-Host "--- 拉取新镜像并重启服务 ---" -ForegroundColor Yellow

# 拉取镜像并重启
ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER @"
cd $PROJECT_DIR
echo "--- 拉取新镜像 ---"
docker compose -f docker-compose.prod.yml pull
echo "--- 重启服务 ---"
docker compose -f docker-compose.prod.yml up -d
echo "--- 等待容器启动 ---"
sleep 20
echo "--- 检查容器状态 ---"
docker ps
echo ""
echo "--- 健康检查 ---"
curl -s http://localhost/health
echo ""
echo "--- 应用日志 ---"
docker logs switch_manage_unified --tail 50
"@
