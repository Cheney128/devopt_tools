#!/bin/bash
cd /data/it-devops

VERSION="20260318-1647"
IMAGE="10.21.65.20:5000/switch-manage:$VERSION"

echo "=== 部署到生产环境 ==="
echo "版本: $VERSION"
echo ""

echo "--- 当前镜像版本 ---"
grep "image:" docker-compose.prod.yml

echo ""
echo "--- 更新配置文件 ---"
sed -i "s|image: 10.21.65.20:5000/switch-manage:.*|image: $IMAGE|" docker-compose.prod.yml

echo "更新后的配置:"
grep "image:" docker-compose.prod.yml

echo ""
echo "--- 拉取新镜像 ---"
docker compose -f docker-compose.prod.yml pull

echo ""
echo "--- 重启服务 ---"
docker compose -f docker-compose.prod.yml up -d

echo ""
echo "--- 等待容器启动 (20秒) ---"
sleep 20

echo ""
echo "--- 检查容器状态 ---"
docker ps

echo ""
echo "--- 健康检查 ---"
curl -s http://localhost/health

echo ""
echo "--- 应用日志 ---"
docker logs switch_manage_unified --tail 80
