# MirrorGate 项目结构设计

## 1. 项目概述

**名称**: MirrorGate - 全功能测试平台

**核心功能**:
- API Mock 服务
- 接口自动化测试
- UI 自动化测试（APP + Web）
- 请求日志追踪与历史比对

## 2. 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue 3 + Element Plus + TypeScript + Vite |
| 后端 | Python 3.11 + FastAPI + SQLAlchemy |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis |
| 部署 | Docker Compose |

## 3. 架构设计

采用**单体分层架构**：

```
┌─────────────────────────────────────────────────┐
│                  Vue 3 前端                      │
├─────────────────────────────────────────────────┤
│                FastAPI 后端                      │
│  ┌───────────┬───────────┬───────────────────┐  │
│  │ Mock服务  │ 接口自动化 │    UI自动化      │  │
│  └───────────┴───────────┴───────────────────┘  │
├─────────────────────────────────────────────────┤
│              MySQL + Redis                      │
└─────────────────────────────────────────────────┘
```

## 4. 项目目录结构

```
mirror-gate/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── config.py                 # 配置管理
│   │   ├── database.py               # 数据库连接
│   │   ├── api/                      # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mock.py           # Mock 服务 API
│   │   │   │   ├── api_test.py       # 接口自动化 API
│   │   │   │   ├── ui_test.py        # UI 自动化 API
│   │   │   │   └── history.py        # 历史比对 API
│   │   ├── models/                   # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── mock.py               # Mock 相关模型
│   │   │   ├── api_test.py           # 接口测试模型
│   │   │   ├── ui_test.py            # UI 测试模型
│   │   │   └── user.py               # 用户模型
│   │   ├── schemas/                  # Pydantic 模式
│   │   │   ├── __init__.py
│   │   │   ├── mock.py
│   │   │   ├── api_test.py
│   │   │   └── ui_test.py
│   │   ├── services/                 # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── mock_service.py       # Mock 核心逻辑
│   │   │   ├── api_test_service.py   # API 测试逻辑
│   │   │   ├── ui_test_service.py    # UI 测试逻辑
│   │   │   └── compare_service.py    # 历史比对逻辑
│   │   ├── core/                     # 核心功能
│   │   │   ├── __init__.py
│   │   │   ├── security.py           # 认证授权
│   │   │   └── exceptions.py         # 异常处理
│   │   └── utils/                    # 工具函数
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── alembic/                      # 数据库迁移
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/                        # 后端测试
│   ├── requirements.txt
│   ├── alembic.ini
│   └── Dockerfile
├── frontend/                         # 前端服务
│   ├── src/
│   │   ├── api/                      # API 调用
│   │   ├── views/                    # 页面组件
│   │   │   ├── mock/                 # Mock 管理页面
│   │   │   ├── api-test/             # 接口测试页面
│   │   │   └── ui-test/              # UI 测试页面
│   │   ├── components/               # 通用组件
│   │   ├── stores/                   # Pinia 状态管理
│   │   ├── router/                   # 路由配置
│   │   └── utils/                    # 工具函数
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
└── README.md
```

## 5. 模块设计

### 5.1 Mock 服务模块

**核心功能**:
- Mock 套件管理（名称、描述、开关、创建人/时间）
- 客户端白名单（clientId, userId, vid）
- 请求规则匹配（等于/包含/不等于，任一/全部满足）
- 响应配置（JSON响应、AB测试、模拟超时、空响应）

**数据模型**:
- MockSuite: Mock 套件
- MockRule: 匹配规则
- MockResponse: 响应配置
- MockWhitelist: 白名单

### 5.2 接口自动化模块

**核心功能**:
- 测试用例管理
- 测试执行引擎
- 历史比对（差异标红提示）
- 测试报告生成

**数据模型**:
- ApiTestCase: 测试用例
- ApiTestExecution: 执行记录
- ApiTestHistory: 历史结果

### 5.3 UI 自动化模块

**核心功能**:
- APP 端: Airtest + Poco 框架
- Web 端: Playwright 框架
- 关键字驱动: Behave (BDD)

**数据模型**:
- UiTestCase: UI 测试用例
- UiTestStep: 测试步骤
- UiTestExecution: 执行记录

## 6. API 设计规范

- RESTful 风格
- 版本控制: `/api/v1/`
- 统一响应格式:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {}
  }
  ```

## 7. 部署架构

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_DATABASE: mirror_gate

  redis:
    image: redis:7-alpine
```

## 8. 开发计划

1. **Phase 1**: 项目骨架搭建
2. **Phase 2**: Mock 服务开发
3. **Phase 3**: 接口自动化开发
4. **Phase 4**: UI 自动化开发
5. **Phase 5**: 集成测试与优化
