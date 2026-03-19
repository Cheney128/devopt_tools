#!/bin/bash
docker exec switch_manage_unified ls -la /var/log/supervisor/
echo "=== backend stderr log ==="
docker exec switch_manage_unified tail -500 /var/log/supervisor/backend-stderr---supervisor*.log 2>/dev/null || echo "No backend stderr log"
echo ""
echo "=== backend stdout log ==="
docker exec switch_manage_unified tail -500 /var/log/supervisor/backend-stdout---supervisor*.log 2>/dev/null || echo "No backend stdout log"
