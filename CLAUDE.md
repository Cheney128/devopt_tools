# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**交换机批量管理与巡检系统** — A full-stack network device management system for enterprise NetDevOps. Manages, inspects, and backs up network switch configurations via SSH.

- **Backend**: Python 3.9+ / FastAPI (async, ASGI via uvicorn)
- **Frontend**: Vue 3 / Element Plus SPA (built with Vite)
- **Database**: MySQL 5.7+ / MariaDB 11 (SQLAlchemy ORM, no Alembic)
- **Deployment**: Single Docker container (Nginx + uvicorn via Supervisor)

---

## Commands

### Backend (local dev)

```bash
# Install dependencies (use Tsinghua mirror)
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Initialize DB tables
python scripts/init_db.py

# Seed admin user and roles
python scripts/init_auth_data.py

# Run backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend (local dev)

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
npm run dev       # Dev server at http://localhost:5173 (proxies /api → localhost:8000)
npm run build     # Production build to frontend/dist/
```

### Testing

```bash
# Run all backend tests
python -m pytest -v

# Run a single test file
python -m pytest tests/unit/test_backup_scheduler.py -v

# Frontend tests (single run)
cd frontend && npm run test:run
```

### Docker (production)

```bash
docker-compose up -d          # Unified container on port 80
docker-compose logs -f app    # Watch logs
docker-compose down
```

---

## Architecture

### Backend Layers

```
app/
├── api/endpoints/    # 11 FastAPI routers (one per domain)
├── services/         # Business logic (SSH, scheduling, Git, Excel)
├── models/           # SQLAlchemy ORM models
├── schemas/          # Pydantic v2 request/response models
├── core/security.py  # JWT, password hashing, captcha
├── config.py         # Settings read from env vars / .env
└── main.py           # App factory, middleware, startup events
```

**Key service files:**
- `app/services/netmiko_service.py` — Core SSH operations using Netmiko (Huawei/Cisco/H3C). Largest file (~47KB).
- `app/services/backup_scheduler.py` — APScheduler cron-based backup scheduling (hourly/daily/monthly).
- `app/services/backup_executor.py` — Executes backup jobs, writes results to DB + Git.
- `app/services/latency_scheduler.py` + `latency_service.py` — Background ICMP latency checks every N minutes.
- `app/services/git_service.py` — GitPython integration for config versioning.
- `app/services/ssh_connection_pool.py` — SSH session pooling.

**API endpoints (`app/api/endpoints/`):**
`auth`, `users`, `devices`, `ports`, `vlans`, `inspections`, `configurations`, `device_collection`, `git_configs`, `command_templates`, `command_history`

### Frontend

```
frontend/src/
├── api/          # Axios client with JWT interceptors
├── views/        # 11 page-level components
├── stores/       # Pinia (authStore, deviceStore, deviceCollectionStore)
├── router/       # Vue Router with auth guard
└── components/   # Shared UI components
```

### Database (no Alembic)

Migrations are manual scripts in `scripts/`. On Docker startup, `scripts/auto_migrate.py` is called by `docker/entrypoint.sh` to detect and apply schema changes.

- **New columns/tables**: Add a script in `scripts/`, then register it in `auto_migrate.py`.
- **Rollback**: `python scripts/db_rollback.py`

---

## Key Configuration

Environment variables (see `.env.example`):

| Variable | Description |
|---|---|
| `DATABASE_URL` | `mysql+pymysql://user:pass@host:3306/switch_manage` |
| `SECRET_KEY` | JWT signing key (must set in production) |
| `LATENCY_CHECK_ENABLED` | Enable background ping checks (`True`/`False`) |
| `LATENCY_CHECK_INTERVAL` | Ping interval in minutes (default `5`) |
| `DEPLOY_MODE` | Set to `unified` in Docker to suppress `.env` file loading |

Swagger UI (interactive API docs): `http://localhost:8000/docs`

---

## Development Workflow

**设计阶段：**
1. 首先将用户的需求进行解析，生成对应的功能描述
2. 根据功能描述，将代码结构和关系进行设计
3. 将涉及内容进行复核，确保涉及所有功能模块和代码文件
4. 将复核过的内容生成本次的开发文档

**开发阶段：**
1. 开发之前先将项目本次状态备份（git commit），添加项目描述和必要的注释
2. 按照设计文档进行编码，使用模块化设计，避免代码重复
3. 测试文件放在项目根目录下的 `tests/` 中，命名使用 `test_` 前缀。每个测试代码开头包含详细描述。禁止未经同意使用启动文件进行整体测试。
4. 进行代码优化，提高性能和用户体验

**整理阶段：**
1. 将变更提交到代码库（git commit/merge）
2. 更新 `README.md` 及相关设计文档
3. 将 task 规划和执行过程以 `.md` 格式记录，存放在项目目录 `/tasks` 下，文件名为：`需求名称_taskname`

**其他注意事项：**
- python、npm 等依赖安装使用国内镜像站（清华、中科大）
