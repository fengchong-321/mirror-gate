# 用例管理模块修正实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.
>
> **重要**: 所有枚举值和字段定义必须严格按照 `docs/plans/2026-03-02-testcase-module-design.md`，不得自行定义！

**Goal:** 修正用例管理模块的枚举值和字段，使其与设计文档完全一致

**Architecture:** 后端 FastAPI + SQLAlchemy，前端 Vue 3 + Element Plus

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Vue 3, TypeScript, Element Plus

---

## 需要修正的内容

### 枚举值修正（严格按照设计文档第四章）

| 枚举 | 当前错误值 | 设计文档正确值 |
|------|-----------|---------------|
| CaseType | functional, api, ui, performance, security | 功能测试, 性能测试, 安全测试, 兼容性测试, 用户体验测试, 其他 |
| Platform | web, ios, android, mini_program | RN, 服务端, 小程序, Web, H5 |
| Priority | low, medium, high, critical | P0, P1, P2, P3, P4 |
| CaseStatus | draft, active, deprecated | 草稿, 评审中, 通过, 废弃 |

### 缺失字段（严格按照设计文档 5.2 TestCase）

| 字段 | 类型 | 说明 |
|------|------|------|
| is_core | bool | 核心用例 |
| owner | str | 维护人 |
| developer | str | 开发负责人 |
| page_url | str | 页面地址 |
| remark | text | 备注（富文本） |
| order | int | 排序序号 |

---

## Task 1: 修正后端数据模型

**Files:**
- Modify: `backend/app/models/testcase.py`

**Step 1: 修正 CaseType 枚举**

```python
class CaseType(str, enum.Enum):
    """用例类型 - 定义见设计文档 4.2"""
    FUNCTIONAL = "功能测试"
    PERFORMANCE = "性能测试"
    SECURITY = "安全测试"
    COMPATIBILITY = "兼容性测试"
    UX = "用户体验测试"
    OTHER = "其他"
```

**Step 2: 修正 Platform 枚举**

```python
class Platform(str, enum.Enum):
    """所属平台 - 定义见设计文档 4.2"""
    RN = "RN"           # Android + H5
    SERVER = "服务端"
    MINI_PROGRAM = "小程序"
    WEB = "Web"
    H5 = "H5"
```

**Step 3: 修正 Priority 枚举**

```python
class Priority(str, enum.Enum):
    """重要程度 - 定义见设计文档 4.2，P0最高，P4最低"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"
```

**Step 4: 修正 CaseStatus 枚举**

```python
class CaseStatus(str, enum.Enum):
    """用例状态 - 定义见设计文档 5.2"""
    DRAFT = "草稿"
    REVIEWING = "评审中"
    PASSED = "通过"
    DEPRECATED = "废弃"
```

**Step 5: 添加缺失字段到 TestCase 模型**

在 TestCase 类中添加：
```python
    order: int = Column(Integer, default=0)  # 排序序号
    is_core: bool = Column(Boolean, default=False)  # 核心用例
    owner: Optional[str] = Column(String(MAX_USER_LENGTH))  # 维护人
    developer: Optional[str] = Column(String(MAX_USER_LENGTH))  # 开发负责人
    page_url: Optional[str] = Column(String(500))  # 页面地址
    remark: Optional[str] = Column(Text)  # 备注（富文本）
```

**Step 6: 验证模型导入**

Run: `cd backend && python3 -c "from app.models.testcase import *; print('OK')"`
Expected: OK

---

## Task 2: 修正后端 Pydantic Schemas

**Files:**
- Modify: `backend/app/schemas/testcase.py`

**Step 1: 更新 TestCaseBase schema**

```python
class TestCaseBase(BaseModel):
    """Base schema for TestCase - 定义见设计文档 4.1"""
    title: str = Field(..., min_length=1, max_length=200, description="用例标题")
    case_type: Optional[CaseType] = Field(None, description="用例类型")
    platform: Optional[Platform] = Field(None, description="所属平台")
    priority: Optional[Priority] = Field(None, description="重要程度")
    is_core: Optional[bool] = Field(False, description="核心用例")
    owner: Optional[str] = Field(None, max_length=50, description="维护人")
    developer: Optional[str] = Field(None, max_length=50, description="开发负责人")
    page_url: Optional[str] = Field(None, max_length=500, description="页面地址")
    preconditions: Optional[str] = Field(None, description="前置条件（富文本）")
    steps: Optional[Any] = Field(None, description="测试步骤（表格）")
    remark: Optional[str] = Field(None, description="备注（富文本）")
    tags: Optional[Any] = Field(None, description="标签数组")
```

**Step 2: 更新 TestCaseUpdate schema**

```python
class TestCaseUpdate(BaseModel):
    """Schema for updating an existing TestCase."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    group_id: Optional[int] = None
    case_type: Optional[CaseType] = None
    platform: Optional[Platform] = None
    priority: Optional[Priority] = None
    is_core: Optional[bool] = None
    owner: Optional[str] = Field(None, max_length=50)
    developer: Optional[str] = Field(None, max_length=50)
    page_url: Optional[str] = Field(None, max_length=500)
    preconditions: Optional[str] = None
    steps: Optional[Any] = None
    remark: Optional[str] = None
    tags: Optional[Any] = None
```

**Step 3: 更新 TestCaseResponse schema**

确保包含所有新字段：order, is_core, owner, developer, page_url, remark

**Step 4: 验证 schema 导入**

Run: `cd backend && python3 -c "from app.schemas.testcase import *; print('OK')"`
Expected: OK

---

## Task 3: 更新数据库表结构

**Files:**
- Run: Python script to add new columns

**Step 1: 添加新字段到数据库**

```python
# 在 backend 目录运行
python3 -c "
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # 添加缺失的字段
    columns = [
        ('order', 'INTEGER DEFAULT 0'),
        ('is_core', 'BOOLEAN DEFAULT FALSE'),
        ('owner', 'VARCHAR(50)'),
        ('developer', 'VARCHAR(50)'),
        ('page_url', 'VARCHAR(500)'),
        ('remark', 'TEXT'),
    ]
    for col_name, col_type in columns:
        try:
            conn.execute(text(f'ALTER TABLE testcases ADD COLUMN {col_name} {col_type}'))
            print(f'Added column: {col_name}')
        except Exception as e:
            if 'Duplicate column' in str(e) or 'already exists' in str(e).lower():
                print(f'Column already exists: {col_name}')
            else:
                print(f'Error adding {col_name}: {e}')
    conn.commit()
print('Done')
"
```

**Step 2: 验证表结构**

Run: `mysql -u root mirror_gate -e "DESCRIBE testcases;" 2>/dev/null | grep -E "order|is_core|owner|developer|page_url|remark"`

---

## Task 4: 修正前端枚举值

**Files:**
- Modify: `frontend/src/views/testcase/CaseEditor.vue`
- Modify: `frontend/src/views/testcase/index.vue`
- Modify: `frontend/src/api/testcase.ts`

**Step 1: 更新前端类型定义**

在 `frontend/src/api/testcase.ts` 中：

```typescript
// 用例类型 - 严格按照设计文档 4.2
export const CASE_TYPES = [
  { value: '功能测试', label: '功能测试' },
  { value: '性能测试', label: '性能测试' },
  { value: '安全测试', label: '安全测试' },
  { value: '兼容性测试', label: '兼容性测试' },
  { value: '用户体验测试', label: '用户体验测试' },
  { value: '其他', label: '其他' },
] as const

// 所属平台 - 严格按照设计文档 4.2
export const PLATFORMS = [
  { value: 'RN', label: 'RN (Android+H5)' },
  { value: '服务端', label: '服务端' },
  { value: '小程序', label: '小程序' },
  { value: 'Web', label: 'Web' },
  { value: 'H5', label: 'H5' },
] as const

// 重要程度 - 严格按照设计文档 4.2
export const PRIORITIES = [
  { value: 'P0', label: 'P0 (最高)' },
  { value: 'P1', label: 'P1' },
  { value: 'P2', label: 'P2' },
  { value: 'P3', label: 'P3' },
  { value: 'P4', label: 'P4 (最低)' },
] as const

// 用例状态 - 严格按照设计文档 5.2
export const CASE_STATUSES = [
  { value: '草稿', label: '草稿' },
  { value: '评审中', label: '评审中' },
  { value: '通过', label: '通过' },
  { value: '废弃', label: '废弃' },
] as const
```

**Step 2: 更新 CaseEditor.vue 使用新枚举**

- 替换所有 case_type 选项
- 替换所有 platform 选项
- 替换所有 priority 选项
- 添加新字段：is_core, owner, developer, page_url, remark

**Step 3: 更新用例列表显示**

在 `index.vue` 中更新表格列定义，使用新的枚举值

---

## Task 5: 修复前端编辑按钮问题

**Files:**
- Modify: `frontend/src/views/testcase/index.vue`

**Step 1: 检查编辑按钮点击事件**

确保编辑按钮的点击事件正确绑定：
```vue
<el-button link type="primary" @click="handleEdit(row)">
  编辑
</el-button>
```

**Step 2: 检查 handleEdit 函数**

```typescript
function handleEdit(row: TestCase) {
  router.push({ name: 'TestCaseEdit', params: { id: row.id } })
}
```

**Step 3: 验证路由配置**

确保 `/testcase/:id/edit` 路由正确指向 CaseEditor.vue

---

## Task 6: 清空旧数据并添加新测试数据

**Files:**
- Modify: `backend/scripts/create_testcase_testdata.py`

**Step 1: 清空旧数据**

```sql
DELETE FROM testcase_history;
DELETE FROM testcase_comments;
DELETE FROM testcase_attachments;
DELETE FROM testcases;
DELETE FROM testcase_groups;
```

**Step 2: 更新测试数据脚本使用新枚举值**

```python
test_cases = [
    {
        "group_id": login_group.id,
        "title": "用户使用手机号和密码登录",
        "case_type": "功能测试",  # 使用中文值
        "platform": "Web",        # 使用设计文档定义的值
        "priority": "P0",         # 使用 P0-P4
        "status": "草稿",
        "is_core": True,
        "owner": "admin",
        # ... 其他字段
    },
    # ... 更多用例
]
```

**Step 3: 运行测试数据脚本**

Run: `cd backend && python3 scripts/create_testcase_testdata.py`

---

## Task 7: 端到端验证

**Step 1: 验证后端 API**

```bash
# 测试分组树
curl -s http://localhost:8000/api/v1/testcase/groups/tree | python3 -m json.tool

# 测试用例列表
curl -s "http://localhost:8000/api/v1/testcase/cases?group_id=1" | python3 -m json.tool

# 测试用例详情
curl -s http://localhost:8000/api/v1/testcase/cases/1 | python3 -m json.tool
```

**Step 2: 验证前端功能**

1. 刷新页面 http://localhost:5173/testcase
2. 点击分组树节点，查看用例列表
3. 点击"新建用例"按钮，验证表单字段和枚举选项
4. 点击用例的"编辑"按钮，验证能跳转到编辑页面
5. 点击用例标题，验证能查看用例详情

**Step 3: 验证枚举值显示正确**

- 用例类型显示：功能测试、性能测试等中文
- 所属平台显示：RN、服务端、小程序、Web、H5
- 重要程度显示：P0、P1、P2、P3、P4

---

## 验收标准

- [ ] 后端枚举值与设计文档完全一致
- [ ] 数据库包含所有设计文档定义的字段
- [ ] 前端枚举选项与设计文档完全一致
- [ ] 编辑按钮点击能正常跳转
- [ ] 至少 10 条测试用例数据
- [ ] 用例列表显示正常
- [ ] 新建/编辑用例功能正常
