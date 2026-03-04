# 用例管理模块设计文档

> **创建日期**: 2026-03-02
> **当前版本**: v1.2
> **状态**: 已确认，待实现

---

## 版本记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v1.0 | 2026-03-02 | 初始设计完成 |
| v1.1 | 2026-03-03 | 用例ID改为7位纯数字；移除列表编号列；用例数量改为列表上方统计栏 |
| v1.2 | 2026-03-04 | 移除编辑页面状态字段（后端保留，前端不显示） |

---

## 一、模块概述

用例管理是MirrorGate平台的核心模块，用于管理所有测试用例。采用**用例集合（目录树）+ 用例详情**的两层结构。

---

## 二、用例集合（目录树）

### 2.1 结构设计

- **类型**: 多级目录树
- **用例挂载**: 用例挂载在目录节点下
- **排序**: 支持目录和用例的排序

### 2.2 左侧面板

| 组件 | 说明 |
|------|------|
| 搜索框 | 搜索目录名称 |
| 目录树 | 多级树形结构展示 |
| 节点操作 | 新增子目录、编辑、删除 |

### 2.3 右侧面板（选中目录后）

| 组件 | 说明 |
|------|------|
| 统计栏 | 显示"共 N 条用例" |
| 工具栏 | 全选框 + 新建用例 + 列设置 |
| 列设置 | 浮层可选展示列 + 重置按钮 |
| 用例列表 | 表格展示当前目录下的用例 |

---

## 三、用例列表

### 3.1 默认展示字段

| 序号 | 字段 | 说明 |
|------|------|------|
| 1 | 勾选框 | 批量操作 |
| 2 | 排序 | ≡ 图标，拖动排序 |
| 3 | 标题 | 用例标题 |
| 4 | 用例类型 | 功能测试等 |
| 5 | 所属平台 | Web/RN等 |
| 6 | 重要程度 | P0-P4 |
| 7 | 维护人 | 用户名 |
| 8 | 操作 | 编辑/复制/移动/删除 |

> **注意**: 用例编号仅在URL中体现（如 `/testcase/0000001/edit`），不在列表中显示。

### 3.2 列设置可选字段

- 开发负责人
- 核心用例
- 自动化标签
- 更新时间

### 3.3 操作说明

| 操作 | 说明 |
|------|------|
| 编辑 | 打开用例编辑页面 |
| 复制 | 复制到当前分组，自动重命名 |
| 移动 | 浮层选择目标分组 |
| 删除 | 二次确认后删除 |

---

## 四、单个用例字段

### 4.1 字段列表

**规则：仅标题必填，其他均为非必填**

| 序号 | 字段名 | 类型 | 必填 | 说明 |
|------|--------|------|------|------|
| 1 | 标题 | string | ✅ | 用例标题 |
| 2 | 用例编号 | string | 自动 | 7位纯数字，如 `0000001`（数据库自增ID补零） |
| 3 | 维护人 | string | ❌ | 用户选择 |
| 4 | 用例类型 | enum | ❌ | 功能测试/性能测试/安全测试/兼容性测试/用户体验测试/其他 |
| 5 | 所属平台 | enum | ❌ | RN(Android+H5)/服务端/小程序/Web/H5 |
| 6 | 开发负责人 | string | ❌ | 用户选择 |
| 7 | 重要程度 | enum | ❌ | P0/P1/P2/P3/P4（P4最低） |
| 8 | 核心用例 | boolean | ❌ | 是/否 |
| 9 | 页面地址 | string | ❌ | URL格式 |
| 10 | 前置条件 | 富文本 | ❌ | 富文本编辑器 |
| 11 | 步骤模式 | 表格 | ❌ | 两列：步骤描述 + 预期结果 |
| 12 | 备注 | 富文本 | ❌ | 富文本编辑器 |
| 13 | 标签 | array | ❌ | 自由输入 |
| 14 | 附件 | 关联表 | ❌ | 多文件，图片可预览 |
| 15 | 评论 | 关联表 | ❌ | 楼层式，支持回复 |
| 16 | 变更历史 | 关联表 | 自动 | 自动记录变更 |

### 4.2 字段详细说明

#### 用例类型（case_type）
```
- 功能测试
- 性能测试
- 安全测试
- 兼容性测试
- 用户体验测试
- 其他
```

#### 所属平台（platform）
```
- RN          # Android + H5
- 服务端
- 小程序
- Web
- H5
```

#### 重要程度（priority）
```
- P0   # 最高
- P1
- P2
- P3
- P4   # 最低
```

#### 标签（tags）
自由输入，常用标签示例：
```
- 冒烟
- 回归
- 上线前
- 接口自动化完成
- RN自动化完成
- Web自动化完成
```

#### 步骤模式（steps）
表格形式，两列：
```
| 步骤描述 | 预期结果 |
|----------|----------|
| 打开登录页面 | 页面正常显示 |
| 输入用户名密码 | 输入框显示内容 |
| 点击登录按钮 | 跳转到首页 |
```
- 支持添加步骤
- 支持删除步骤
- 支持拖动排序

---

## 五、数据模型

### 5.1 TestCaseGroup（用例分组）

```python
class TestCaseGroup:
    id: int
    name: str                    # 分组名称
    parent_id: int               # 父分组ID（null为根节点）
    order: int                   # 排序序号
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
```

### 5.2 TestCase（用例）

```python
class TestCase:
    id: int
    group_id: int               # 所属分组ID
    code: str                    # 用例编号（7位纯数字，如0000001）
    title: str                   # 用例标题（必填）
    order: int                   # 排序序号

    # 分类属性（非必填）
    case_type: str               # 用例类型
    platform: str                # 所属平台
    priority: str                # 重要程度
    is_core: bool                # 核心用例

    # 人员信息
    owner: str                   # 维护人
    developer: str               # 开发负责人

    # 测试内容
    page_url: str                # 页面地址
    preconditions: text          # 前置条件（富文本）
    steps: json                  # 测试步骤（表格）
    remark: text                 # 备注（富文本）
    tags: json                   # 标签数组

    # 状态（后端保留，前端不显示）
    status: str                  # 草稿/评审中/通过/废弃

    # 时间戳
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
```

### 5.3 TestCaseAttachment（附件）

```python
class TestCaseAttachment:
    id: int
    case_id: int                 # 关联用例ID
    filename: str                # 文件名
    file_path: str               # 存储路径
    file_size: int               # 文件大小
    file_type: str               # 文件类型
    uploaded_at: datetime
    uploaded_by: str
```

### 5.4 TestCaseComment（评论）

```python
class TestCaseComment:
    id: int
    case_id: int                 # 关联用例ID
    parent_id: int               # 父评论ID（支持盖楼）
    content: text                # 评论内容
    created_at: datetime
    created_by: str
```

### 5.5 TestCaseHistory（变更历史）

```python
class TestCaseHistory:
    id: int
    case_id: int                 # 关联用例ID
    field_name: str              # 修改字段
    old_value: text              # 旧值
    new_value: text              # 新值
    changed_at: datetime
    changed_by: str
```

---

## 六、界面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  用例管理                                                            │
├────────────────┬────────────────────────────────────────────────────┤
│   目录树         │              用例列表                              │
│  [搜索框]       │  ☑ 全选  [新建用例] [列设置▼]                       │
│  ┌──────────┐  │  ┌────────────────────────────────────────────────┐│
│  │ 📁 用户模块▼│  │  │☐│≡│编号   │标题    │类型│平台│优先级│维护人│操作 ││
│  │  📁 登录   │  │  ├─┼─┼───────┼────────┼────┼────┼──────┼──────┼─────┤│
│  │  📁 注册   │  │  │☐│≡│TC-001 │用户登录│功能│Web │P1   │张三  │编辑..││
│  │ 📁 订单模块 │  │  │☐│≡│TC-002 │用户注册│功能│RN │P2   │李四  │编辑..││
│  │  📁 支付   │  │  └────────────────────────────────────────────────┘│
│  └──────────┘  │                                                  │
│  [+新增][编辑] │                                                  │
└────────────────┴────────────────────────────────────────────────────┘
```

---

## 七、API设计

### 7.1 用例分组

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/testcase/groups | 获取目录树 |
| POST | /api/v1/testcase/groups | 创建分组 |
| PUT | /api/v1/testcase/groups/{id} | 更新分组 |
| DELETE | /api/v1/testcase/groups/{id} | 删除分组 |
| PUT | /api/v1/testcase/groups/{id}/move | 移动分组 |

### 7.2 用例

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/testcase/cases | 获取用例列表（按分组） |
| GET | /api/v1/testcase/cases/{id} | 获取用例详情 |
| POST | /api/v1/testcase/cases | 创建用例 |
| PUT | /api/v1/testcase/cases/{id} | 更新用例 |
| DELETE | /api/v1/testcase/cases/{id} | 删除用例 |
| POST | /api/v1/testcase/cases/{id}/copy | 复制用例 |
| PUT | /api/v1/testcase/cases/{id}/move | 移动用例 |
| PUT | /api/v1/testcase/cases/reorder | 批量排序 |

### 7.3 附件

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/testcase/cases/{id}/attachments | 上传附件 |
| GET | /api/v1/testcase/cases/{id}/attachments | 获取附件列表 |
| DELETE | /api/v1/testcase/attachments/{id} | 删除附件 |

### 7.4 评论

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/testcase/cases/{id}/comments | 获取评论列表 |
| POST | /api/v1/testcase/cases/{id}/comments | 添加评论 |
| DELETE | /api/v1/testcase/comments/{id} | 删除评论 |

### 7.5 变更历史

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/testcase/cases/{id}/history | 获取变更历史 |

---

## 八、实现优先级

1. **P0 - 核心功能**
   - 用例分组CRUD
   - 用例CRUD（基础字段）
   - 用例列表展示

2. **P1 - 重要功能**
   - 步骤模式（表格）
   - 标签系统
   - 附件上传

3. **P2 - 增强功能**
   - 评论系统
   - 变更历史
   - 富文本编辑器

---

## 九、技术实现

### 9.1 后端

- 框架: FastAPI
- ORM: SQLAlchemy
- 数据库: MySQL

### 9.2 前端

- 框架: Vue 3 + TypeScript
- UI库: Element Plus
- 状态管理: Pinia
- 树组件: el-tree
- 富文本: 可选 wangEditor 或 Tiptap
