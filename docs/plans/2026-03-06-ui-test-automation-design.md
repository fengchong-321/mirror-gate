# UI 自动化测试模块设计文档

> **创建日期**: 2026-03-06
> **版本**: v1.0
> **状态**: 设计评审中

---

## 一、模块概述

UI 自动化测试模块用于自动化执行 UI 界面测试，支持 Web 和 App 两大平台。

### 1.1 核心能力

| 能力 | 描述 |
|------|------|
| 套件管理 | 组织和管理 UI 测试用例 |
| 用例编辑 | 支持 Gherkin 语法和步骤定义 |
| 测试执行 | Web(Playwright) / App(Airtest+Poco) |
| 步骤级结果 | 记录每个步骤的执行结果和截图 |
| 执行历史 | 查看历史执行记录和对比 |

### 1.2 技术选型

| 组件 | 技术 |
|------|------|
| 后端框架 | FastAPI + SQLAlchemy |
| Web 自动化 | Playwright |
| App 自动化 | Airtest + Poco |
| 前端框架 | Vue 3 + TypeScript + Element Plus |
| 用例格式 | Gherkin (Given/When/Then) |

---

## 二、现有设计分析

### 2.1 数据模型

当前已实现的模型位于 `app/models/ui_test.py`:

```
UiTestSuite ──< UiTestCase ──< UiTestExecution ──< UiTestStepResult
```

#### UiTestSuite（测试套件）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | str(100) | 套件名称 |
| description | text | 描述 |
| platform | enum | WEB / APP |
| config | text(JSON) | 平台配置 |
| created_by | str | 创建人 |
| created_at | datetime | 创建时间 |

**平台配置 (config)**:
```json
// Web 平台
{
  "base_url": "https://example.com",
  "browser": "chrome",
  "headless": false,
  "viewport": {"width": 1920, "height": 1080}
}

// App 平台
{
  "app_path": "/path/to/app.apk",
  "device_type": "android",
  "device_id": "device_serial"
}
```

#### UiTestCase（测试用例）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| suite_id | int | 套件 ID |
| name | str(200) | 用例名称 |
| description | text | 描述 |
| order | int | 执行顺序 |
| is_enabled | bool | 是否启用 |
| feature_content | text | Gherkin 特征文件内容 |
| steps | text(JSON) | 步骤定义 |

**步骤定义 (steps)**:
```json
[
  {
    "keyword": "Given",
    "text": "打开登录页面",
    "action": "open_url",
    "params": {"url": "/login"}
  },
  {
    "keyword": "When",
    "text": "输入用户名和密码",
    "action": "input",
    "params": {"selector": "#username", "value": "test"}
  },
  {
    "keyword": "Then",
    "text": "验证登录成功",
    "action": "assert",
    "params": {"selector": ".welcome", "expected": "visible"}
  }
]
```

#### UiTestExecution（执行记录）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| case_id | int | 用例 ID |
| batch_id | str | 批量执行 ID |
| status | enum | 执行状态 |
| duration_ms | int | 执行耗时 |
| error_message | text | 错误信息 |
| screenshot_paths | text(JSON) | 截图路径数组 |
| video_path | str | 录屏路径 |
| log_path | str | 日志路径 |
| executed_at | datetime | 执行时间 |

#### UiTestStepResult（步骤结果）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| execution_id | int | 执行 ID |
| step_order | int | 步骤顺序 |
| keyword | str | Given/When/Then/And |
| text | text | 步骤描述 |
| status | enum | 步骤状态 |
| error_message | text | 错误信息 |
| screenshot_path | str | 步骤截图 |
| duration_ms | int | 步骤耗时 |

### 2.2 API 端点

当前已实现的端点位于 `app/api/v1/ui_test.py`:

#### 套件管理
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/ui-tests/suites | 创建套件 |
| GET | /api/v1/ui-tests/suites | 套件列表 |
| GET | /api/v1/ui-tests/suites/{id} | 套件详情 |
| PUT | /api/v1/ui-tests/suites/{id} | 更新套件 |
| DELETE | /api/v1/ui-tests/suites/{id} | 删除套件 |

#### 用例管理
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/ui-tests/suites/{id}/cases | 创建用例 |
| GET | /api/v1/ui-tests/suites/{id}/cases | 用例列表 |
| GET | /api/v1/ui-tests/cases/{id} | 用例详情 |
| PUT | /api/v1/ui-tests/cases/{id} | 更新用例 |
| DELETE | /api/v1/ui-tests/cases/{id} | 删除用例 |

#### 执行管理
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/ui-tests/cases/{id}/execute | 执行用例 |
| POST | /api/v1/ui-tests/suites/{id}/execute | 批量执行 |
| GET | /api/v1/ui-tests/cases/{id}/executions | 执行历史 |
| GET | /api/v1/ui-tests/executions/{id} | 执行详情 |

### 2.3 服务层

当前服务层位于 `app/services/ui_test_service.py`:

```python
class UiTestService:
    # 套件操作
    create_suite()
    get_suite()
    get_suites()
    update_suite()
    delete_suite()

    # 用例操作
    create_case()
    get_case()
    get_cases_by_suite()
    update_case()
    delete_case()

    # 执行操作
    execute_case()         # 支持 Web/App 平台
    _execute_step_mock()   # 模拟执行
    batch_execute()
    get_executions()
```

### 2.4 执行引擎

服务层中的 `execute_case` 方法支持:

1. **Web 平台**: 使用 Playwright 进行浏览器自动化
2. **App 平台**: 使用 Airtest + Poco 进行移动应用自动化

当前实现为 **Mock 模式**, 需要实现真实的执行引擎。

---

## 三、设计补充建议

### 3.1 缺失功能

| 功能 | 优先级 | 说明 |
|------|--------|------|
| UI 执行引擎 | P0 | 真实的 Playwright/Airtest 执行器 |
| 步骤库管理 | P1 | 可复用的步骤定义库 |
| 页面对象模型 | P1 | Page Object 模式支持 |
| 执行报告 | P1 | HTML 报告生成 |
| 用例导入导出 | P2 | Gherkin 文件导入导出 |
| 录屏功能 | P2 | 执行过程录制 |
| 元素定位器管理 | P2 | 统一的元素定位配置 |

### 3.2 数据模型扩展建议

#### 新增：UiTestStepLibrary（步骤库）
```python
class UiTestStepLibrary:
    id: int                    # 主键
    name: str                  # 步骤名称
    category: str              # 分类：导航/表单/断言等
    keyword: str               # Given/When/Then
    text: str                  # 自然语言描述
    action: str                # 动作类型
    params_schema: str         # JSON Schema 定义参数
    implementation: str        # 实现代码/函数名
    platform: str              # web/app/both
    is_enabled: bool           # 是否启用
    created_at: datetime
```

#### 新增：UiTestPage（页面对象）
```python
class UiTestPage:
    id: int                    # 主键
    suite_id: int              # 所属套件
    name: str                  # 页面名称
    url_pattern: str           # URL 模式
    elements: str              # JSON: 元素定义
    platform: str              # web/app
```

#### 新增：UiTestReport（测试报告）
```python
class UiTestReport:
    id: int                    # 主键
    batch_id: str              # 批量执行 ID
    suite_id: int              # 套件 ID
    name: str                  # 报告名称
    total_cases: int           # 总用例数
    passed: int                # 通过数
    failed: int                # 失败数
    error: int                 # 错误数
    duration_ms: int           # 总耗时
    html_path: str             # HTML 报告路径
    status: str                # 状态
    created_at: datetime
```

### 3.3 UI 执行引擎设计

#### 架构设计
```
┌─────────────────────────────────────────────────────────────┐
│                    UI Test Executor                          │
├─────────────────────────────────────────────────────────────┤
│  Step Parser    │  Step Registry    │  Result Collector    │
├─────────────────┼───────────────────┼──────────────────────┤
│  Web Executor   │  App Executor     │  Screenshot Service  │
│  (Playwright)   │  (Airtest/Poco)   │  Video Recorder      │
└─────────────────┴───────────────────┴──────────────────────┘
```

#### 步骤注册表
```python
STEP_REGISTRY = {
    "open_url": {
        "web": playwright_executor.open_url,
        "app": airtest_executor.open_app,
    },
    "click": {
        "web": playwright_executor.click,
        "app": poco_executor.click,
    },
    "input": {
        "web": playwright_executor.fill,
        "app": airtest_executor.text,
    },
    "assert": {
        "web": playwright_executor.assert_element,
        "app": poco_executor.assert_exists,
    },
    "screenshot": {
        "web": playwright_executor.screenshot,
        "app": airtest_executor.snapshot,
    },
}
```

### 3.4 前端界面设计

#### 套件列表页
```
┌─────────────────────────────────────────────────────────────────┐
│  UI 测试管理                               [新建套件]            │
├─────────────────────────────────────────────────────────────────┤
│  平台筛选：[全部▼]  状态：[全部▼]  搜索：[________] [搜索]     │
├─────┬────────┬─────────┬────────┬────────┬──────────┬──────────┤
│ ID  │ 名称   │ 平台    │ 用例数 │ 状态   │ 最后执行 │ 操作     │
├─────┼────────┼─────────┼────────┼────────┼──────────┼──────────┤
│  1  │ 登录流程│  Web    │   12   │  通过  │ 10 分钟前│ [执行]...│
└─────────────────────────────────────────────────────────────────┘
```

#### 用例编辑器
```
┌─────────────────────────────────────────────────────────────────┐
│  编辑用例：用户登录流程                          [保存] [执行]   │
├─────────────────────────────────────────────────────────────────┤
│  [Gherkin] [步骤列表] [页面对象]                                 │
├───────────────────────────────────┬─────────────────────────────┤
│  Feature: 用户登录                 │  步骤预览                    │
│                                   │                              │
│  Scenario: 成功登录                │  Given 打开登录页面          │
│    Given 打开登录页面              │  When 输入用户名 "test"      │
│    When 输入用户名和密码           │  When 输入密码 "123456"      │
│    Then 验证登录成功               │  Then 验证登录成功          │
│                                   │                              │
│  [添加步骤]                        │                              │
└───────────────────────────────────┴─────────────────────────────┘
```

#### 执行详情页
```
┌─────────────────────────────────────────────────────────────────┐
│  执行详情 - 用户登录流程 #001                                    │
├─────────────────────────────────────────────────────────────────┤
│  状态：✓ 通过    耗时：3.2s    执行时间：2026-03-06 10:30:00    │
├─────────────────────────────────────────────────────────────────┤
│  步骤结果                                                       │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ ✓ Given 打开登录页面                            500ms      ││
│  │ ✓ When 输入用户名 "test"                        300ms      ││
│  │ ✓ When 输入密码 "****"                          300ms      ││
│  │ ✓ Then 验证登录成功                             200ms      ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                  │
│  截图  [缩略图 1] [缩略图 2] [缩略图 3] [查看全部]               │
│  录屏  [播放视频]                                                 │
│  日志  [下载日志]                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、实现优先级

### P0 - 核心功能（必需）
1. **UI 执行引擎**
   - Playwright Web 执行器
   - 步骤解析和注册表
   - 截图和错误处理

2. **基础前端界面**
   - 套件列表和编辑
   - 用例编辑器（步骤配置）
   - 执行结果查看

### P1 - 重要功能
1. **步骤库管理**
   - 可复用步骤定义
   - 步骤分类和搜索

2. **页面对象模型**
   - 页面元素管理
   - 元素定位器配置

3. **执行报告**
   - HTML 报告生成
   - 报告邮件发送

### P2 - 增强功能
1. **用例导入导出**
   - Gherkin .feature 文件导入
   - 导出为标准格式

2. **录屏功能**
   - Web 执行过程录制
   - 视频格式转换

3. **CI/CD 集成**
   - GitHub Actions 集成
   - Jenkins 插件

---

## 五、技术实现细节

### 5.1 Playwright Web 执行器

```python
from playwright.async_api import async_playwright

class PlaywrightExecutor:
    def __init__(self, config: dict):
        self.base_url = config.get("base_url", "")
        self.browser_type = config.get("browser", "chromium")
        self.headless = config.get("headless", True)

    async def execute(self, steps: list) -> ExecutionResult:
        async with async_playwright() as p:
            browser = await getattr(p, self.browser_type).launch(
                headless=self.headless
            )
            page = await browser.new_page()

            results = []
            for step in steps:
                result = await self._execute_step(page, step)
                results.append(result)
                if not result.success:
                    break

            await browser.close()
            return ExecutionResult(steps=results)
```

### 5.2 Airtest App 执行器

```python
from airtest.core.api import connect_device, touch, text, assert_exists
from poco.drivers.android.uiautomation import AndroidUiautomationPoco

class AirtestExecutor:
    def __init__(self, config: dict):
        self.device_id = config.get("device_id")
        self.app_package = config.get("app_package")
        connect_device(f"Android:///{self.device_id}")
        self.poco = AndroidUiautomationPoco()

    def execute(self, steps: list) -> ExecutionResult:
        results = []
        for step in steps:
            result = self._execute_step(step)
            results.append(result)
            if not result.success:
                break
        return ExecutionResult(steps=results)
```

### 5.3 步骤注册表

```python
class StepRegistry:
    _registry: Dict[str, Dict[str, Callable]] = {}

    @classmethod
    def register(cls, action: str, platform: str, func: Callable):
        if action not in cls._registry:
            cls._registry[action] = {}
        cls._registry[action][platform] = func

    @classmethod
    def get(cls, action: str, platform: str) -> Optional[Callable]:
        return cls._registry.get(action, {}).get(platform)

# 注册 Web 步骤
StepRegistry.register("open_url", "web", PlaywrightExecutor.open_url)
StepRegistry.register("click", "web", PlaywrightExecutor.click)
StepRegistry.register("input", "web", PlaywrightExecutor.fill)
StepRegistry.register("assert", "web", PlaywrightExecutor.assert_element)

# 注册 App 步骤
StepRegistry.register("open_app", "app", AirtestExecutor.open_app)
StepRegistry.register("click", "app", AirtestExecutor.touch)
StepRegistry.register("input", "app", AirtestExecutor.text)
StepRegistry.register("assert", "app", AirtestExecutor.assert_exists)
```

---

## 六、待完成任务清单

### 后端
- [ ] 实现 `app/services/ui_executor.py` - UI 执行引擎
- [ ] 实现 `app/services/playwright_executor.py` - Web 执行器
- [ ] 实现 `app/services/airtest_executor.py` - App 执行器
- [ ] 添加步骤注册表 `app/services/step_registry.py`
- [ ] 添加报告模型 `app/models/ui_test_report.py`
- [ ] 添加报告服务 `app/services/ui_report_service.py`
- [ ] 添加步骤库模型和服务
- [ ] 添加页面对象模型和服务
- [ ] 添加截图和视频管理服务
- [ ] 完善 API 端点（报告、步骤库等）

### 前端
- [ ] 创建视图 `frontend/src/views/ui-test/index.vue` - 套件列表
- [ ] 创建视图 `frontend/src/views/ui-test/SuiteEditor.vue` - 套件编辑
- [ ] 创建视图 `frontend/src/views/ui-test/CaseEditor.vue` - 用例编辑
- [ ] 创建视图 `frontend/src/views/ui-test/ExecutionDetail.vue` - 执行详情
- [ ] 创建视图 `frontend/src/views/ui-test/ReportList.vue` - 报告列表
- [ ] 创建 API `frontend/src/api/ui-test.ts`
- [ ] 添加步骤库管理界面
- [ ] 添加页面对象管理界面

### 测试
- [ ] 后端单元测试
- [ ] 执行引擎集成测试
- [ ] 前端组件测试
- [ ] E2E 测试

---

## 七、与 API 测试模块对比

| 特性 | API 测试 | UI 测试 |
|------|----------|----------|
| 执行速度 | 快 (ms 级) | 慢 (s 级) |
| 稳定性 | 高 | 中（受 UI 变化影响） |
| 维护成本 | 低 | 高 |
| 测试层级 | 接口层 | 界面层 |
| 执行引擎 | httpx | Playwright/Airtest |
| 用例格式 | JSON | Gherkin |
| 截图 | 不需要 | 必需 |
| 录屏 | 不需要 | 可选 |

---

## 八、验收标准

### Phase 1: 核心功能
- [ ] 可以创建和编辑 UI 测试套件
- [ ] 可以创建和编辑 UI 测试用例（步骤配置）
- [ ] Web 测试用例可以实际执行
- [ ] 执行结果包含步骤级详情
- [ ] 失败步骤有截图记录

### Phase 2: 增强功能
- [ ] 步骤库可以创建和复用
- [ ] 页面对象可以管理元素定位器
- [ ] HTML 报告可以生成和查看
- [ ] 支持批量执行和统计

### Phase 3: 完善功能
- [ ] App 测试可以实际执行
- [ ] 支持录屏功能
- [ ] 支持 Gherkin 文件导入导出
- [ ] CI/CD 集成完成

---

**文档版本**: v1.0
**最后更新**: 2026-03-06
**审核状态**: 待确认
