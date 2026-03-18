$SSH_KEY = "D:\BaiduSyncdisk\5.code\tools\ssh_key\ssh_key"
$PROD_SERVER = "root@10.23.65.95"
$PROD_PORT = "22022"

Write-Host "=== 验证部署结果 ===" -ForegroundColor Cyan

Write-Host "`n--- 检查容器状态 ---" -ForegroundColor Yellow
ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER "docker ps"

Write-Host "`n--- 等待健康检查完成 (15秒) ---" -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "`n--- 再次检查容器状态 ---" -ForegroundColor Yellow
ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER "docker ps"

Write-Host "`n--- 执行健康检查 ---" -ForegroundColor Yellow
ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER "curl -s http://localhost/health"

Write-Host "`n--- 查看应用日志 ---" -ForegroundColor Yellow
ssh -i $SSH_KEY -p $PROD_PORT $PROD_SERVER "docker logs switch_manage_unified 2>&1 | tail -30"
