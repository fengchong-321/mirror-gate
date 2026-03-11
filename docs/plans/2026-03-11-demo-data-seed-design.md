# 演示数据种子脚本设计文档

**日期**：2026-03-11
**状态**：已批准
**类型**：功能增强

---

## 1. 需求概述

为 MirrorGate 项目创建演示数据种子脚本，使新用户在首次启动后能够立即体验平台的完整功能，无需手动创建测试数据。

### 1.1 背景

当前项目已实现"开箱即用"的部署体验（通过 `make dev` 一键启动），但用户首次登录后面对的是空数据库，无法直观了解平台功能。

### 1.2 目标

- 提供有意义的演示数据，展示平台核心功能
- 数据量适中，不影响加载性能
- 幂等性设计，多次运行不会创建重复数据
- 集成到 `make dev` 流程，自动化加载

---

## 2. 演示数据设计

### 2.1 业务场景：旅游电商平台

选择旅游电商场景，因为：
- 业务流程清晰，易于理解
- 涵盖多种 API 类型（搜索、详情、下单、支付）
- 适合展示 Mock 服务和 API 测试能力

### 2.2 数据范围

| 模块 | 数据类型 | 数量 |
|------|---------|------|
| Mock 服务 | 套件 | 2 个 |
| API 测试 | 套件 + 用例 | 2 套件 + 4 用例 |
| 用例管理 | 分组 + 用例 | 4 分组 + 20 用例 |

**总计**：约 30 条核心数据

### 2.3 详细数据结构

#### 2.3.1 Mock 服务套件

**套件 1：机票服务 Mock**
```json
{
  "name": "机票服务 Mock",
  "description": "模拟航班搜索和预订 API",
  "path_prefix": "/api/flights",
  "rules": [
    {
      "name": "搜索航班",
      "method": "GET",
      "path": "/search",
      "response": {
        "status_code": 200,
        "body": {
          "code": 0,
          "data": {
            "flights": [
              {"flightNo": "CA1234", "from": "北京", "to": "上海", "price": 890},
              {"flightNo": "MU5678", "from": "北京", "to": "上海", "price": 950}
            ]
          }
        }
      }
    },
    {
      "name": "航班详情",
      "method": "GET",
      "path": "/{flightId}",
      "response": {
        "status_code": 200,
        "body": {
          "code": 0,
          "data": {"flightNo": "CA1234", "aircraft": "空客 A320", "seats": 164}
        }
      }
    }
  ]
}
```

**套件 2：酒店预订 Mock**
```json
{
  "name": "酒店预订 Mock",
  "description": "模拟酒店搜索和预订 API",
  "path_prefix": "/api/hotels",
  "rules": [
    {
      "name": "搜索酒店",
      "method": "GET",
      "path": "/search",
      "response": { "..." }
    },
    {
      "name": "房间详情",
      "method": "GET",
      "path": "/{hotelId}/rooms/{roomId}",
      "response": { "..." }
    }
  ]
}
```

#### 2.3.2 API 测试套件

**套件 1：机票 API 测试**
- 用例 1：搜索航班 - 验证状态码和返回结构
- 用例 2：获取航班详情 - 验证 JSONPath 断言

**套件 2：酒店 API 测试**
- 用例 1：搜索酒店 - 验证分页参数
- 用例 2：预订房间 - 验证创建订单响应

#### 2.3.3 用例管理分组

```
用例分组结构:
├── 机票模块 (分组)
│   ├── 搜索航班用例 1
│   ├── 搜索航班用例 2
│   ├── 搜索航班用例 3
│   ├── 搜索航班用例 4
│   ├── 搜索航班用例 5
│   ├── 预订流程用例 1
│   ├── 预订流程用例 2
│   └── 预订流程用例 3
├── 酒店模块 (分组)
│   ├── 搜索酒店用例 1-5
│   └── 订单管理用例 1-3
├── 用户模块 (分组)
│   ├── 登录测试用例 1-2
│   └── 注册测试用例 1-2
└── 支付模块 (分组)
    ├── 支付流程用例 1
    └── 退款流程用例 1
```

---

## 3. 技术设计

### 3.1 文件结构

```
backend/
├── scripts/
│   └── seed_demo_data.py      # 主脚本
├── data/
│   └── demo/
│       ├── mock_suites.json   # Mock 套件数据
│       ├── api_test_suites.json # API 测试数据
│       └── testcases.json     # 用例管理数据
└── ...
```

### 3.2 幂等性实现

使用"检查 - 跳过/更新"模式：

```python
def create_if_not_exists(model, unique_field, data):
    """如果不存在则创建，存在则跳过"""
    existing = db.query(model).filter(
        getattr(model, unique_field) == data[unique_field]
    ).first()

    if existing:
        print(f"⊘ 跳过：{model.__name__} '{data[unique_field]}' 已存在")
        return existing

    instance = model(**data)
    db.add(instance)
    db.commit()
    print(f"✓ 创建：{model.__name__} '{data[unique_field]}'")
    return instance
```

### 3.3 数据依赖关系

```
执行顺序:
1. Mock 套件 (无依赖)
2. API 测试套件 (无依赖)
3. API 测试用例 (依赖套件)
4. 用例分组 (无依赖)
5. 测试用例 (依赖分组)
```

### 3.4 错误处理

- 数据库连接失败：打印错误信息并退出
- 单个数据创建失败：记录错误，继续处理其他数据
- 数据验证失败：打印详细错误信息

---

## 4. 集成方案

### 4.1 Makefile 变更

新增命令：
```makefile
# 加载演示数据
seed-demo:
	@echo "📦 加载演示数据..."
	docker-compose exec -T backend python scripts/seed_demo_data.py
	@echo "✅ 演示数据加载完成"

# 清理演示数据
clean-demo:
	@echo "🧹 清理演示数据..."
	docker-compose exec -T backend python scripts/clean_demo_data.py
	@echo "✅ 演示数据清理完成"
```

修改 `make dev`：
```makefile
dev: check-docker
	# ... 现有步骤 ...
	@echo "Step 6: 加载演示数据..."
	$(MAKE) seed-demo
```

### 4.2 README 更新

在"快速开始"章节添加：

```markdown
### 演示数据

首次启动后，系统会自动加载旅游电商演示数据：
- Mock 服务套件：机票服务、酒店预订
- API 测试套件：机票 API 测试、酒店 API 测试
- 测试用例：20 条用例分布在 4 个模块

如需手动加载或清理：
```bash
# 重新加载演示数据
make seed-demo

# 清理演示数据
make clean-demo
```
```

---

## 5. 验收标准

- [ ] `make dev` 完成后自动加载演示数据
- [ ] 多次运行 `make dev` 不会创建重复数据
- [ ] 前端页面能看到演示数据
- [ ] 提供 `make clean-demo` 清理命令
- [ ] README 文档更新

---

## 6. 后续工作

1. 调用 `writing-plans` 技能创建详细实施计划
2. 创建种子脚本和数据文件
3. 更新 Makefile 和 README
4. 验证功能
