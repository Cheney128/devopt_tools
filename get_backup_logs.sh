#!/bin/bash
docker logs --tail 1000 switch_manage_unified 2>&1 | grep -A 10 -B 5 'ScheduledBackup\|BackupService\|Backup scheduler'
