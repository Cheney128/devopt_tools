#!/bin/bash
docker exec switch_manage_unified ls -la /var/log/
docker exec switch_manage_unified ls -la /app/logs/ 2>/dev/null || echo "No /app/logs directory"
