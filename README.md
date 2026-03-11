# MirrorGate

<div align="center">

**企业级全链路测试平台**

Mock 服务 | API 测试 | UI 自动化 | 测试报告

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4+-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 项目简介

MirrorGate 是一款面向测试团队的一站式测试平台，集成 Mock 服务管理、API 自动化测试、UI 自动化测试和测试报告生成能力。通过可视化界面和强大的执行引擎，帮助团队高效完成接口契约测试、前后端联调、回归测试等质量保障工作。

### 为什么选择 MirrorGate？

| 痛点 | MirrorGate 解决方案 |
|------|---------------------|
| 前后端开发进度不一致 | Mock 服务模拟接口响应，支持动态规则匹配 |
| 接口文档与实现不同步 | 实时对比 Mock 响应与真实接口，自动发现差异 |
| 测试用例维护成本高 | 可视化用例编辑，支持变量提取和断言链 |
| 测试报告分散难追溯 | 统一报告中心，支持 HTML/PDF/JSON 多格式导出 |

---

## 核心功能

### 1. Mock 服务管理

- **动态规则匹配**：支持 URL、Header、Body 多维度规则配置
- **响应模板引擎**：支持变量替换、条件逻辑、延迟模拟
- **实时对比**：自动对比 Mock 响应与真实接口，记录差异
- **请求日志追踪**：完整记录请求/响应，支持回放调试

### 2. API 自动化测试

- **用例编排**：支持测试套件和测试用例两级管理
- **变量系统**：环境变量、套件变量、用例变量三级作用域
- **断言引擎**：支持相等、包含、正则、JSONPath、状态码等多种断言
- **步骤编排**：支持前置步骤、后置步骤、条件执行
- **数据驱动**：支持 CSV/JSON 数据文件参数化

### 3. UI 自动化测试

- **Playwright 驱动**：基于 Playwright 实现跨浏览器自动化
- **步骤录制**：可视化录制操作步骤，自动生成测试脚本
- **元素定位**：支持 CSS、XPath、Text 等多种定位策略
- **产物管理**：自动截图、录屏、Trace 追踪

### 4. 测试报告

- **多格式导出**：HTML、PDF、JSON
- **趋势分析**：历史执行记录，通过率趋势
- **详细日志**：请求/响应、断言结果、错误堆栈

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  Vue 3 + Element Plus + Pinia + Vue Router                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│  FastAPI + SQLAlchemy + Pydantic + Alembic                  │
├─────────────────────────────────────────────────────────────┤
│  Services: Mock | API Test | UI Test | Report | Scheduler   │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │  MySQL   │   │  Redis   │   │Playwright│
        │  数据存储  │   │  缓存/队列 │   │ 浏览器驱动 │
        └──────────┘   └──────────┘   └──────────┘
```

---

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Node.js 18+ (开发环境)
- Python 3.11+ (开发环境)

### 5 分钟快速启动（推荐新手）

使用 Makefile 一键启动（macOS/Linux）：

```bash
# 1. 克隆项目
git clone https://github.com/fengchong-321/mirror-gate.git
cd mirror-gate

# 2. 一键启动（自动完成所有初始化）
make dev

# 3. 验证服务
make verify
```

### 使用 Docker Compose 部署（手动步骤）

```bash
# 1. 克隆项目
git clone https://github.com/fengchong-321/mirror-gate.git
cd mirror-gate

# 2. 配置环境变量
cp .env.example .env
# ⚠️ 重要：编辑 .env 修改 MYSQL_PASSWORD

# 3. 启动服务
docker-compose up -d

# 4. 等待数据库就绪（约 10 秒）
sleep 10

# 5. 初始化数据库
make init-db

# 6. 创建管理员账号
make create-admin

# 7. 加载演示数据（可选）
make seed-demo
```

> **提示**：首次启动后，系统会自动加载旅游电商演示数据。如需手动加载或清理，请参考下文"演示数据"章节。

服务启动后访问：
- 前端界面：http://localhost
- API 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

### ✅ 验证安装成功

运行以下检查确认服务正常：

```bash
make verify
```

或者手动检查：

| 检查项 | 命令 | 预期结果 |
|--------|------|----------|
| 后端健康 | `curl http://localhost:8000/health` | `{"status": "healthy"}` |
| 前端页面 | `curl http://localhost` | 返回 HTML |
| 数据库连接 | `docker-compose exec backend python -c "from app.database import SessionLocal; SessionLocal().close(); print('OK')"` | `OK` |
| API 文档 | 访问 http://localhost:8000/docs | 显示 Swagger UI |

### 首次登录后做什么？

1. **创建第一个 Mock 套件**：进入 Mock 管理 → 新建套件
2. **配置 Mock 规则**：添加 URL 匹配规则和响应
3. **启用 Mock 服务**：点击启用按钮
4. **测试 API**：使用 Postman 或 curl 验证 Mock 响应

---

### 本地开发环境

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 本地开发环境

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

---

## 项目结构

```
mirror-gate/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/v1/            # API 路由
│   │   │   ├── mock.py        # Mock 服务接口
│   │   │   ├── api_test.py    # API 测试接口
│   │   │   ├── ui_test.py     # UI 测试接口
│   │   │   └── ...
│   │   ├── models/            # 数据模型
│   │   ├── schemas/           # Pydantic 模式
│   │   ├── services/          # 业务逻辑
│   │   │   ├── mock_service.py
│   │   │   ├── api_test_executor.py
│   │   │   ├── playwright_executor.py
│   │   │   └── ...
│   │   └── utils/             # 工具函数
│   ├── alembic/               # 数据库迁移
│   └── requirements.txt
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   │   ├── mock/          # Mock 管理
│   │   │   ├── api-test/      # API 测试
│   │   │   ├── ui-test/       # UI 测试
│   │   │   └── ...
│   │   ├── api/               # API 客户端
│   │   ├── stores/            # Pinia 状态
│   │   └── router/            # 路由配置
│   └── package.json
│
├── docs/                       # 文档
│   └── plans/                  # 设计文档
│
└── docker-compose.yml          # 容器编排
```

---

## API 测试使用示例

### 创建测试套件

```bash
curl -X POST http://localhost:8000/api/v1/api-test/suites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "用户接口测试",
    "description": "用户模块 API 测试套件",
    "base_url": "https://api.example.com"
  }'
```

### 创建测试用例

```bash
curl -X POST http://localhost:8000/api/v1/api-test/suites/1/cases \
  -H "Content-Type: application/json" \
  -d '{
    "name": "获取用户列表",
    "method": "GET",
    "path": "/users",
    "steps": [
      {
        "name": "发送请求",
        "type": "request",
        "config": {
          "method": "GET",
          "path": "/users",
          "params": {"page": 1, "size": 10}
        }
      },
      {
        "name": "断言状态码",
        "type": "assertion",
        "config": {
          "type": "status",
          "expected": 200
        }
      },
      {
        "name": "断言响应结构",
        "type": "assertion",
        "config": {
          "type": "jsonpath",
          "path": "$.data.items",
          "expected": "exists"
        }
      }
    ]
  }'
```

### 执行测试

```bash
curl -X POST http://localhost:8000/api/v1/api-test/suites/1/execute
```

---

## Mock 服务使用示例

### 创建 Mock 规则

```bash
curl -X POST http://localhost:8000/api/v1/mock/suites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "用户服务 Mock",
    "path_prefix": "/api/users",
    "rules": [
      {
        "name": "获取用户列表",
        "method": "GET",
        "path": "/api/users",
        "response": {
          "status_code": 200,
          "body": {
            "code": 0,
            "data": {
              "items": [
                {"id": 1, "name": "张三"},
                {"id": 2, "name": "李四"}
              ],
              "total": 2
            }
          }
        }
      }
    ]
  }'
```

### 启用 Mock 服务

```bash
curl -X POST http://localhost:8000/api/v1/mock/suites/1/enable
```

---

## 配置说明

### ⚠️ 安全提示

**请勿将敏感信息提交到代码仓库！**

- 所有 API Key、密码、Token 等敏感信息请使用环境变量配置
- `.env` 文件已添加到 `.gitignore`，不会被提交
- 生产环境请修改所有默认密码

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你自己的配置
# NEVER commit .env file to git!
```

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MYSQL_HOST` | MySQL 主机 | localhost |
| `MYSQL_PORT` | MySQL 端口 | 3306 |
| `MYSQL_USER` | MySQL 用户 | root |
| `MYSQL_PASSWORD` | MySQL 密码 | - |
| `MYSQL_DATABASE` | 数据库名 | mirror_gate |
| `REDIS_HOST` | Redis 主机 | localhost |
| `REDIS_PORT` | Redis 端口 | 6379 |

---

## 测试

### 运行单元测试

```bash
cd backend
pytest tests/ -v --cov=app
```

### 运行 E2E 测试

```bash
cd frontend
npm run test:e2e
```

---

## 演示数据

首次启动后，系统会自动加载旅游电商演示数据：

### 包含内容

| 模块 | 演示数据 |
|------|---------|
| Mock 服务 | 机票服务 Mock、酒店预订 Mock |
| API 测试 | 机票 API 测试套件、酒店 API 测试套件 |
| 用例管理 | 机票模块、酒店模块、用户模块、支付模块（共 25 用例） |

### 管理演示数据

```bash
# 手动加载演示数据
make seed-demo

# 清理演示数据
make clean-demo
```

---

## 故障排查

### 常见问题 FAQ

#### 1. 服务启动失败："Connection refused"

**原因**：MySQL 容器尚未启动完成

**解决方案**：
```bash
# 查看容器状态
docker-compose ps

# 等待 MySQL 就绪（看到 "healthy" 状态）
docker-compose logs mysql | grep "ready for connections"

# 重启服务
docker-compose down && docker-compose up -d
```

#### 2. 数据库迁移失败："Table doesn't exist"

**原因**：数据库未初始化

**解决方案**：
```bash
# 重新运行迁移
make init-db
# 或者手动执行
docker-compose exec backend alembic upgrade head
```

#### 3. 前端无法连接后端

**原因**：代理配置问题或后端未启动

**解决方案**：
```bash
# 检查后端日志
docker-compose logs backend

# 验证后端可访问
curl http://localhost:8000/health

# 重启前端容器
docker-compose restart frontend
```

#### 4. 管理员账号无法登录

**原因**：初始管理员账号未创建

**解决方案**：
```bash
# 创建管理员账号
make create-admin
# 默认账号：admin / admin123

# 或者手动执行
docker-compose exec backend python create_admin.py
```

#### 5. Redis 连接失败

**原因**：Redis 容器未启动

**解决方案**：
```bash
# 检查 Redis 状态
docker-compose ps redis

# 重启 Redis
docker-compose restart redis

# 验证连接
docker-compose exec redis redis-cli ping
# 应返回：PONG
```

#### 6. 端口被占用："Address already in use"

**原因**：80 或 8000 端口已被其他服务占用

**解决方案**：
```bash
# 查找占用端口的进程
lsof -i :80
lsof -i :8000

# 停止占用进程或修改 docker-compose.yml 端口映射
```

#### 7. Docker 内存不足

**症状**：容器反复重启，OOMKilled 错误

**解决方案**：
```bash
# 增加 Docker Desktop 内存限制（macOS/Windows）
# Docker Desktop → Preferences → Resources → Memory → 调整为 4GB+

# 或者清理未使用的容器
docker system prune -a
```

### 日志查看命令

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql

# 查看最近 100 行
docker-compose logs --tail=100 backend
```

### 重置环境

如果问题无法解决，可以完全重置：

```bash
# 1. 停止并删除所有容器和数据卷
docker-compose down -v

# 2. 清理
docker system prune -a

# 3. 重新启动
docker-compose up -d

# 4. 重新初始化
make init-db
make create-admin
```

---

## 脚本和工具

### Makefile 命令

| 命令 | 说明 |
|------|------|
| `make dev` | 一键启动开发环境（包含所有初始化） |
| `make init-db` | 初始化数据库表结构 |
| `make create-admin` | 创建管理员账号（admin/admin123） |
| `make seed-demo` | 加载旅游电商演示数据 |
| `make clean-demo` | 清理演示数据 |
| `make verify` | 验证所有服务健康状态 |
| `make logs` | 查看所有服务日志 |
| `make clean` | 清理所有容器和数据卷 |
| `make test` | 运行所有测试 |

### Scripts 目录

位于项目根目录的 `scripts/`：

- `seed_mock_data.py` - 填充 Mock 测试数据
- `backup_db.sh` - 数据库备份脚本
- `reset_env.sh` - 重置开发环境

---

## 路线图

- [ ] 测试调度器（定时任务、CI 集成）
- [ ] 测试报告邮件通知
- [ ] 测试数据工厂（ Faker 集成）
- [ ] 性能测试模块（ k6 集成）
- [ ] 多环境管理
- [ ] 测试用例版本控制
- [ ] 团队协作与权限管理

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '功能: 添加某某功能'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 许可证

本项目基于 [MIT](LICENSE) 许可证开源。

---

## 联系方式

如有问题或建议，欢迎提交 [Issue](https://github.com/fengchong-321/mirror-gate/issues)。
