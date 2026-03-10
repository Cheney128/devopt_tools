# Docker 构建失败问题排查报告

**日期**: 2026-03-10
**项目**: Switch Manage
**构建服务器**: root@10.21.65.20:22022
**项目目录**: /root/switch-manage-Build

---

## 问题概述

在 Switch Manage 项目的 Docker 镜像构建过程中，遇到了多个问题导致容器无法正常启动。本文档详细记录了问题现象、原因分析和解决方案。

---

## 问题 1: 前端构建权限错误

### 现象
```
#19 0.934 sh: vite: Permission denied
#19 ERROR: process "/bin/sh -c npm run build" did not complete successfully: exit code: 126
```

### 原因分析
Windows 上传的文件可能丢失执行权限，导致 `node_modules/.bin/` 目录下的可执行文件（如 `vite`）无法执行。

### 解决方案
在 `docker/Dockerfile.unified` 中添加权限修复命令：

```dockerfile
# 复制源代码并构建
COPY frontend/ ./

# 修复权限问题（Windows上传可能丢失执行权限）
RUN chmod -R +x node_modules/.bin/ 2>/dev/null || true

RUN npm run build
```

---

## 问题 2: pip 网络超时

### 现象
```
pip._vendor.urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='pypi.tuna.tsinghua.edu.cn', port=443): Read timed out.
```

### 原因分析
pip 默认超时时间较短，在大陆网络环境下下载大型包时容易超时。

### 解决方案
在 `docker/Dockerfile.unified` 中增加超时和重试参数：

```dockerfile
RUN pip install --no-cache-dir --timeout 600 --retries 5 -r requirements.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 问题 3: entrypoint.sh CRLF 行尾问题

### 现象
```
/usr/bin/env: 'bash\r': No such file or directory
```

### 原因分析
Windows 上编辑的 shell 脚本包含 CRLF (`\r\n`) 行尾，Linux 无法正确解析。

### 解决方案
1. **本地修复**（Windows PowerShell）:
```powershell
Get-ChildItem -Path "docker" -Filter "*.sh" | ForEach-Object { 
    $content = Get-Content $_.FullName -Raw
    $content = $content -replace "`r`n", "`n"
    Set-Content $_.FullName -Value $content -NoNewline
}
```

2. **服务器修复**:
```bash
sed -i 's/\r$//' docker/entrypoint.sh
```

---

## 问题 4: entrypoint.sh 文件被截断

### 现象
```
chown: cannot access '/var/log/superviso': No such file or directory
```

### 原因分析
服务器上的 `entrypoint.sh` 文件被截断，第 15 行 `/var/log/supervisor` 缺少了最后的 `r` 字符，变成了 `/var/log/superviso`。

这是一个非常隐蔽的问题，可能原因：
1. SCP 传输过程中文件被截断
2. 服务器磁盘空间不足
3. 文件系统问题

### 排查过程
```bash
# 检查服务器上的文件
head -20 /root/switch-manage-Build/docker/entrypoint.sh

# 发现第 15 行：
chown -R root:root /var/log/superviso  # 缺少 'r'
```

### 解决方案
重新上传完整的 `entrypoint.sh` 文件，并验证文件完整性：

```bash
# 上传后验证
wc -l /root/switch-manage-Build/docker/entrypoint.sh
# 应该显示 88 行左右

# 检查关键行
grep "chown" /root/switch-manage-Build/docker/entrypoint.sh
```

---

## 问题 5: sed 命令语法错误

### 现象
```
sed: -e expression #1, char 6: unknown option to `s'
```

### 原因分析
`entrypoint.sh` 中的 sed 命令使用了 `/` 作为分隔符，但正则表达式中也包含 `/`，导致语法错误：

```bash
# 错误写法
sed -E 's/:\/\/[^:]+:[^@]+@/:\/\/***:***@/'  # 转义混乱

# 正确写法 - 使用 | 作为分隔符
sed -E 's|://[^:]+:[^@]+@|://***:***@|'
```

### 解决方案
修改 `entrypoint.sh` 中的 sed 命令：

```bash
# 隐藏数据库密码
if [ -n "$DATABASE_URL" ]; then
    masked_url=$(echo "$DATABASE_URL" | sed -E 's|://[^:]+:[^@]+@|://***:***@|')
    echo "[Entrypoint] DATABASE_URL: $masked_url"
fi
```

---

## 问题 6: 容器内缺少 entrypoint.sh 文件

### 现象
```bash
docker run --rm --entrypoint /bin/bash switch-manage:xxx -c "ls /entrypoint.sh"
# 输出: ls: cannot access /entrypoint.sh: No such file or directory
```

### 原因分析
Dockerfile 中的 `COPY docker/entrypoint.sh /entrypoint.sh` 命令执行时，源文件可能不存在或路径错误。

### 排查过程
```bash
# 检查服务器上的文件是否存在
ls -la /root/switch-manage-Build/docker/entrypoint.sh

# 检查 Dockerfile 内容
cat /root/switch-manage-Build/docker/Dockerfile.unified | grep entrypoint
```

### 解决方案
确保 `docker/entrypoint.sh` 文件存在且内容正确，然后重新构建镜像。

---

## 根本原因总结

### 1. 文件传输问题
- **SCP 传输不稳定**: Windows 到 Linux 的文件传输可能导致文件截断
- **建议**: 传输后验证文件 MD5 或 SHA 校验和

### 2. Windows/Linux 兼容性问题
- **行尾符差异**: Windows 使用 CRLF，Linux 使用 LF
- **建议**: 在 `.gitattributes` 中配置 `*.sh text eol=lf`

### 3. Docker 构建缓存问题
- **缓存导致问题**: Docker 使用缓存时，可能不会更新已修改的文件
- **建议**: 关键文件修改后使用 `--no-cache` 重新构建

---

## 最佳实践建议

### 1. 文件传输验证
```bash
# 传输后验证文件完整性
md5sum local_file
ssh server 'md5sum /remote/path/file'
```

### 2. Dockerfile 优化
```dockerfile
# 在 COPY 后立即验证
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && \
    test -f /entrypoint.sh && \
    head -1 /entrypoint.sh | grep -q "^#!/bin/bash"
```

### 3. 构建脚本标准化
创建 `build.sh` 脚本，标准化构建流程：

```bash
#!/bin/bash
# 构建前检查
echo "Checking files..."
test -f docker/entrypoint.sh || { echo "entrypoint.sh not found!"; exit 1; }
file docker/entrypoint.sh | grep -q "with CRLF" && { echo "CRLF detected!"; exit 1; }

# 构建
VERSION=$(date +%Y%m%d)
docker build --no-cache -f docker/Dockerfile.unified \
    --build-arg NPM_REGISTRY=https://registry.npmmirror.com \
    --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    -t switch-manage:$VERSION .

# 验证
docker run --rm switch-manage:$VERSION echo "Build successful!"
```

---

## 成功构建的最终镜像

| 镜像版本 | 状态 | 备注 |
|---------|------|------|
| switch-manage:20260310 | 失败 | 前端权限问题 |
| switch-manage:20260310-02 | 失败 | pip 超时 |
| switch-manage:20260310-03 | 失败 | entrypoint.sh 截断 |
| switch-manage:20260310-04 | 失败 | sed 语法错误 |
| switch-manage:20260310-05 | 失败 | entrypoint.sh 截断 |
| switch-manage:20260310-06 | 失败 | entrypoint.sh 截断 |
| switch-manage:20260310-07 | 失败 | 容器内无 entrypoint.sh |
| switch-manage:20260310-08 | 失败 | sed 语法错误 |

---

## 待解决问题

1. **entrypoint.sh 文件截断问题**需要进一步排查根本原因
2. **容器内 entrypoint.sh 文件缺失**需要检查 Dockerfile COPY 命令执行情况
3. **sed 命令语法**需要使用正确的分隔符

---

## 深入分析：SCP 传输后文件失败的根本原因

### 问题现象回顾

在本次调试过程中，多次出现以下问题：
1. `entrypoint.sh` 文件内容被截断（`/var/log/supervisor` 变成 `/var/log/superviso`）
2. 容器内 `entrypoint.sh` 文件不存在
3. 多次重新上传后问题依然存在

### 本地文件验证

经过十六进制分析，本地文件是**完全正确**的：

```
本地文件 MD5: A80BEBF6708D09E674F6E5FDEC47A5F7
行尾格式: LF (0x0A) - 正确
第15行内容: chown -R root:root /var/log/supervisor - 完整
```

十六进制关键片段：
```
00000150   2F 6C 6F 67 2F 73 75 70 65 72 76 69 73 6F 72 0A  /log/supervisor.
```
可以看到 `supervisor` 的 `r` (0x72) 是存在的。

### 可能的根本原因分析

#### 原因 1: 百度同步盘文件锁定问题 ⚠️ **高度可疑**

**现象**：项目位于 `BaiduSyncdisk` 目录下，百度同步盘可能在文件传输过程中对文件进行了锁定或部分读取。

**原理**：
- 百度同步盘会实时监控文件变化
- 当 SCP 读取文件进行传输时，同步盘可能同时也在读取/同步该文件
- 这可能导致文件读取不完整或读取到中间状态

**验证方法**：
```powershell
# 检查文件是否被锁定
Get-Process | Where-Object {$_.Modules.FileName -like "*entrypoint.sh*"}
```

#### 原因 2: SCP 传输中断

**现象**：网络不稳定导致传输中断，但 SCP 没有报错。

**原理**：
- SCP 在某些情况下可能不会正确报告传输错误
- 特别是当服务器端文件已存在时，可能会出现覆盖不完整的情况

**验证方法**：
```bash
# 使用 -v 参数查看详细传输日志
scp -v -P 22022 docker/entrypoint.sh root@10.21.65.20:/root/switch-manage-Build/docker/
```

#### 原因 3: 服务器端磁盘或文件系统问题

**现象**：服务器磁盘空间不足或文件系统错误。

**验证方法**：
```bash
# 检查磁盘空间
df -h

# 检查文件系统
dmesg | grep -i error
```

#### 原因 4: Docker 构建上下文问题

**现象**：文件上传正确，但 Docker 构建时使用了错误的文件。

**原理**：
- Docker 构建上下文可能缓存了旧文件
- `.dockerignore` 可能排除了某些文件

**验证方法**：
```bash
# 检查 .dockerignore
cat .dockerignore

# 使用 --no-cache 构建
docker build --no-cache -f docker/Dockerfile.unified -t switch-manage:test .
```

### 解决方案建议

#### 方案 1: 避免在同步盘目录下操作（推荐）

```powershell
# 将项目复制到非同步目录
Copy-Item -Recurse "D:\BaiduSyncdisk\5.code\netdevops\switch_manage" "D:\Projects\switch_manage"
# 在非同步目录下进行 Docker 构建操作
```

#### 方案 2: 使用 rsync 替代 scp

```powershell
# rsync 有更好的错误检测和恢复机制
rsync -avz --checksum -e "ssh -p 22022" docker/ root@10.21.65.20:/root/switch-manage-Build/docker/
```

#### 方案 3: 传输后验证文件完整性

```bash
# 上传后立即验证 MD5
LOCAL_MD5=$(Get-FileHash -Path "docker/entrypoint.sh" -Algorithm MD5).Hash
REMOTE_MD5=$(ssh -p 22022 root@10.21.65.20 "md5sum /root/switch-manage-Build/docker/entrypoint.sh | awk '{print `$1}'")

if [ "$LOCAL_MD5" != "$REMOTE_MD5" ]; then
    echo "ERROR: 文件传输不完整!"
    exit 1
fi
```

#### 方案 4: 在服务器上直接创建文件

```bash
# 通过 SSH 直接在服务器上创建文件，避免传输问题
ssh -p 22022 root@10.21.65.20 "cat > /root/switch-manage-Build/docker/entrypoint.sh << 'EOF'
#!/bin/bash
set -e
# ... 完整的 entrypoint.sh 内容 ...
EOF
chmod +x /root/switch-manage-Build/docker/entrypoint.sh"
```

### 结论

**最可能的原因是百度同步盘与 SCP 传输的冲突**。建议：

1. 将项目移出同步盘目录后再进行 Docker 构建操作
2. 或者在传输前暂停百度同步盘
3. 传输后务必验证文件 MD5 校验和

---

## 相关文件

- `docker/Dockerfile.unified` - Docker 构建文件
- `docker/entrypoint.sh` - 容器入口脚本
- `docs/docker-build-skill.md` - Docker 构建技能文档
