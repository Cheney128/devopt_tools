#!/bin/bash
echo "=== backend-error.log (last 500 lines) ==="
docker exec switch_manage_unified tail -500 /var/log/supervisor/backend-error.log
echo ""
echo "=== backend.log (last 500 lines) ==="
docker exec switch_manage_unified tail -500 /var/log/supervisor/backend.log
