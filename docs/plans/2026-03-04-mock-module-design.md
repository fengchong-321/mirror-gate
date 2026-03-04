# Mock 管理模块设计文档

> **创建日期**: 2026-03-04
> **当前版本**: v1.0
> **状态**: 已确认，待完善

---

## 版本记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-03-04 | 初始设计完成 |
| v1.1 | 2026-03-04 | 新增 Mock 预览和对比功能设计 |

---

## 一、模块概述

Mock 管理模块用于模拟 API 响应，支持测试环境下的接口 Mock，帮助前端开发和测试人员进行独立调试。

**核心能力**：
- 规则匹配：根据请求特征（header/query/body）匹配 Mock 套件
- 白名单控制：限制特定用户/客户端触发 Mock
- 响应定制：支持自定义响应内容、超时模拟、AB 测试
- 对比功能：对比 Mock 响应与真实响应的差异

---

## 二、数据模型

### 2.1 MockSuite（Mock 套件）

```python
class MockSuite:
    id: int                      # 主键
    name: str                    # 套件名称（唯一）
    description: str             # 描述
    is_enabled: bool             # 是否启用
    enable_compare: bool         # 是否开启对比
    match_type: MatchType        # 匹配类型：ANY | ALL
    created_by: str              # 创建人
    created_at: datetime         # 创建时间
    updated_by: str              # 更新人
    updated_at: datetime         # 更新时间

    # 关联
    rules: List[MockRule]        # 匹配规则
    responses: List[MockResponse] # 响应配置
    whitelists: List[MockWhitelist] # 白名单
```

### 2.2 MockRule（匹配规则）

```python
class MockRule:
    id: int                      # 主键
    suite_id: int                # 所属套件
    field: str                   # 匹配字段（支持嵌套：data.user.id）
    operator: RuleOperator       # 操作符：equals | contains | not_equals
    value: str                   # 匹配值
```

### 2.3 MockResponse（响应配置）

```python
class MockResponse:
    id: int                      # 主键
    suite_id: int                # 所属套件
    path: str                    # API 路径（支持通配符）
    method: str                  # HTTP 方法
    response_json: str           # 响应 JSON
    ab_test_config: str          # AB 测试配置
    timeout_ms: int              # 超时模拟（毫秒）
    empty_response: bool         # 是否返回空响应
```

### 2.4 MockWhitelist（白名单）

```python
class MockWhitelist:
    id: int                      # 主键
    suite_id: int                # 所属套件
    type: WhitelistType          # 类型：clientId | userId | vid
    value: str                   # 白名单值
```

### 2.5 枚举定义

```python
class MatchType(str, enum.Enum):
    ANY = "any"      # 满足任意一条规则即匹配
    ALL = "all"      # 满足所有规则才匹配

class RuleOperator(str, enum.Enum):
    EQUALS = "equals"           # 等于
    CONTAINS = "contains"       # 包含
    NOT_EQUALS = "not_equals"   # 不等于

class WhitelistType(str, enum.Enum):
    CLIENT_ID = "clientId"      # 客户端 ID
    USER_ID = "userId"          # 用户 ID
    VID = "vid"                 # 访客 ID
```

---

## 三、API 网关转发方案

### 3.1 架构设计

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Client    │────▶│   API Gateway   │────▶│ Mock Service │
└─────────────┘     └─────────────────┘     └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Real Backend │
                    └──────────────┘
```

### 3.2 转发流程

1. 客户端请求到达 API Gateway
2. Gateway 调用 Mock 服务检查是否命中 Mock 规则
3. 若命中：
   - 返回 Mock 响应
   - 若开启对比，同时请求真实后端并记录差异
4. 若未命中：转发到真实后端

### 3.3 实现方式

**方案 A：FastAPI 中间件（当前推荐）**

在现有 FastAPI 应用中添加中间件，拦截所有请求：

```python
@app.middleware("http")
async def mock_interceptor_middleware(request: Request, call_next):
    # 检查是否命中 Mock
    mock_response = mock_interceptor.get_mock_response(...)
    if mock_response:
        # 模拟超时
        if mock_response["delay_ms"] > 0:
            await asyncio.sleep(mock_response["delay_ms"] / 1000)
        return JSONResponse(
            content=json.loads(mock_response["body"]),
            status_code=mock_response["status_code"],
        )
    return await call_next(request)
```

**方案 B：独立网关服务**

使用 Kong/Nginx/Traefik 配置，调用 Mock 服务 API 判断是否拦截。

### 3.4 对比模式

当 `enable_compare=True` 时：

```
┌─────────┐     ┌─────────┐     ┌─────────────┐
│ Request │────▶│  Mock   │────▶│ Mock Response │
└─────────┘     └─────────┘     └─────────────┘
                     │
                     ▼ 异步请求
              ┌─────────────┐
              │ Real Backend │
              └─────────────┘
                     │
                     ▼
              ┌─────────────┐
              │   对比结果   │
              └─────────────┘
```

---

## 四、API 设计

### 4.1 套件管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/mock/suites | 获取套件列表 |
| GET | /api/v1/mock/suites/{id} | 获取套件详情 |
| POST | /api/v1/mock/suites | 创建套件 |
| PUT | /api/v1/mock/suites/{id} | 更新套件 |
| DELETE | /api/v1/mock/suites/{id} | 删除套件 |
| POST | /api/v1/mock/suites/{id}/copy | 复制套件 |

### 4.2 Mock 预览（待实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/mock/preview | 预览 Mock 响应 |

### 4.3 对比结果（待实现）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/mock/suites/{id}/compare-results | 获取对比结果 |
| POST | /api/v1/mock/compare | 手动对比 Mock 与真实响应 |

---

## 五、Mock 预览功能

### 5.1 功能概述

在编辑 Mock 响应时，实时预览格式化后的 JSON，帮助用户验证配置正确性。

### 5.2 设计决策

| 项目 | 决策 |
|------|------|
| 触发方式 | 实时预览（编辑 JSON 时自动更新） |
| 展示位置 | 右侧分栏（编辑器左，预览右） |
| 预览内容 | 格式化 JSON + 语法高亮 |

### 5.3 界面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  编辑 Mock 套件                                                      │
├───────────────────────────────────┬─────────────────────────────────┤
│  Responses Tab                    │  预览                           │
│  ┌─────────────────────────────┐  │  ┌─────────────────────────────┐│
│  │ {                           │  │  │ {                           ││
│  │   "code": 0,                │  │  │   "code": 0,        ✓       ││
│  │   "data": {                 │  │  │   "data": {                 ││
│  │     "name": "test"          │  │  │     "name": "test"          ││
│  │   }                         │  │  │   }                         ││
│  │ }                           │  │  │ }                           ││
│  └─────────────────────────────┘  │  └─────────────────────────────┘│
│                                   │  格式化 ✓ JSON 有效             │
└───────────────────────────────────┴─────────────────────────────────┘
```

### 5.4 技术实现

- 使用 `JSON.parse()` 验证 JSON 有效性
- 使用 `JSON.stringify(obj, null, 2)` 格式化
- 语法高亮可使用 `highlight.js` 或 `prism.js`
- 防抖处理（300ms）避免频繁更新

---

## 六、对比功能

### 6.1 功能概述

对比 Mock 响应与真实 API 响应的差异，帮助验证 Mock 数据的准确性。

### 6.2 设计决策

| 项目 | 决策 |
|------|------|
| 触发方式 | 实时对比 + 手动对比 |
| 展示位置 | 独立"对比记录"页面 |
| 差异展示 | 并排对比（左 Mock，右真实，差异高亮） |

### 6.3 对比记录列表页

```
┌─────────────────────────────────────────────────────────────────────┐
│  对比记录                                      [套件▼] [时间范围▼]   │
├─────────────────────────────────────────────────────────────────────┤
│  时间       │ 套件名称 │ 路径         │ 差异数 │ 状态   │ 操作     │
├─────────────┼──────────┼──────────────┼────────┼────────┼──────────┤
│ 03-04 10:30 │ 登录Mock │ /api/login   │   3    │ 有差异 │ [查看]   │
│ 03-04 10:25 │ 用户Mock │ /api/user    │   0    │ 一致   │ [查看]   │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.4 对比详情（并排展示）

```
┌─────────────────────────────────────────────────────────────────────┐
│  对比详情 - /api/login                                               │
├─────────────────────────────┬───────────────────────────────────────┤
│  Mock 响应                   │  真实响应                              │
├─────────────────────────────┼───────────────────────────────────────┤
│  {                          │  {                                     │
│    "code": 0,               │    "code": 0,                          │
│ ┌─"data": {               ──┼──┐"data": {                           │
│ │    "name": "mock_name",  │  ││    "name": "real_name",   ← 差异   │
│ └─  "id": 123             ──┼──┘    "id": 123                        │
│    }                        │    }                                   │
│  }                          │  }                                     │
└─────────────────────────────┴───────────────────────────────────────┘
```

### 6.5 数据模型

```python
class MockCompareRecord:
    id: int                      # 主键
    suite_id: int                # 所属套件
    path: str                    # 请求路径
    method: str                  # HTTP 方法
    mock_response: str           # Mock 响应
    real_response: str           # 真实响应
    differences: json            # 差异列表
    is_match: bool               # 是否一致
    created_at: datetime         # 对比时间
```

### 6.6 API 设计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/mock/compare-records | 获取对比记录列表 |
| GET | /api/v1/mock/compare-records/{id} | 获取对比详情 |
| POST | /api/v1/mock/compare | 手动触发对比 |
| DELETE | /api/v1/mock/compare-records/{id} | 删除对比记录 |

---

## 七、界面布局

### 5.1 套件列表页

```
┌─────────────────────────────────────────────────────────────────────┐
│  Mock 管理                                        [新建套件]         │
├─────────────────────────────────────────────────────────────────────┤
│  ID │ 名称 │ 描述 │ 启用 │ 对比 │ 匹配类型 │ 创建人 │ 创建时间 │ 操作 │
├─────┼──────┼──────┼──────┼──────┼──────────┼────────┼──────────┼──────┤
│  1  │ 登录 │ ...  │  是  │  否  │   ANY    │  张三  │ 03-04   │ 编辑..│
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 套件编辑页

```
┌─────────────────────────────────────────────────────────────────────┐
│  编辑 Mock 套件                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  名称: [____________]    匹配类型: [ANY ▼]                          │
│  描述: [________________________________]                            │
│  启用: [开关]            开启对比: [开关]                            │
├─────────────────────────────────────────────────────────────────────┤
│  [规则] [响应] [白名单]                                              │
├─────────────────────────────────────────────────────────────────────┤
│  字段          │ 操作符     │ 值                                     │
│  header.x-uid  │ equals ▼  │ 12345                                  │
│  [添加规则]                                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                              [取消] [保存]           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 六、实现状态

### 6.1 已完成

- [x] 数据模型定义（models/mock.py）
- [x] Pydantic Schemas（schemas/mock.py）
- [x] 业务服务层（services/mock_service.py）
- [x] Mock 拦截器（services/mock_interceptor.py）
- [x] API 路由（api/v1/mock.py）
- [x] 前端列表页
- [x] 前端编辑器
- [x] 数据库迁移脚本

### 6.2 待完成

- [ ] API 网关中间件集成
- [ ] Mock 预览功能（右侧分栏实时预览）
- [ ] 对比功能
  - [ ] MockCompareRecord 数据模型
  - [ ] 对比记录 API
  - [ ] 对比记录列表页
  - [ ] 对比详情页（并排展示）
  - [ ] 手动对比功能
- [ ] Mock 日志记录
- [ ] 单元测试完善
- [ ] E2E 测试

---

## 七、实现优先级

### P0 - 核心功能
1. API 网关中间件集成
2. Mock 预览功能

### P1 - 重要功能
1. 对比功能 UI
2. Mock 日志记录

### P2 - 增强功能
1. 历史版本
2. 导入导出
3. 批量操作

---

## 八、技术栈

### 后端
- 框架: FastAPI
- ORM: SQLAlchemy
- 数据库: MySQL

### 前端
- 框架: Vue 3 + TypeScript
- UI库: Element Plus
- 状态管理: Pinia
