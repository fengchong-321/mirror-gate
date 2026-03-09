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

### 使用 Docker Compose 部署

```bash
# 克隆项目
git clone https://github.com/fengchong-321/mirror-gate.git
cd mirror-gate

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 MYSQL_PASSWORD 等敏感配置

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

服务启动后访问：
- 前端界面：http://localhost
- API 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

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
