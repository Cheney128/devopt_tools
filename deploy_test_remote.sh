#!/bin/bash
cd /root/switch-manage-Build

VERSION="20260318-1647"
TEST_PORT=8080
DB_HOST=10.21.65.20
DB_PORT=3307
DB_USER=root
DB_PASS="1qaz%40WSX"
DB_NAME=switch_manage

echo "--- 停止旧的测试容器 ---"
docker stop switch-manage-test 2>/dev/null || true
docker rm switch-manage-test 2>/dev/null || true

echo "--- 启动测试容器 ---"
docker run -d \
  --name switch-manage-test \
  -p ${TEST_PORT}:80 \
  -e DATABASE_URL="mysql+pymysql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_NAME}" \
  -e APP_NAME="Switch Manage System (Test)" \
  -e APP_VERSION="1.0.0" \
  -e DEBUG=True \
  -e DEPLOY_MODE=unified \
  --restart unless-stopped \
  --memory=1g \
  --cpus=1.0 \
  switch-manage:$VERSION

echo "--- 等待容器启动 ---"
sleep 20

echo "--- 检查容器状态 ---"
docker ps | grep switch-manage-test

echo ""
echo "--- 检查容器日志 ---"
docker logs switch-manage-test --tail 100

echo ""
echo "测试环境部署完成！"
echo "访问地址: http://10.21.65.20:${TEST_PORT}"
