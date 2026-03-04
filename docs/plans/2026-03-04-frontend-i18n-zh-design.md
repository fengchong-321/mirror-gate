# 前端界面中文化设计文档

> **创建日期**: 2026-03-04
> **当前版本**: v1.0
> **状态**: 已确认

---

## 一、目标

将前端所有界面的英文文本直接替换为中文，提升用户体验。

---

## 二、涉及文件

| 模块 | 文件 |
|------|------|
| Mock 管理 | `views/mock/index.vue`, `views/mock/SuiteEditor.vue`, `views/mock/CompareRecords.vue` |
| 用例管理 | `views/testcase/index.vue`, `views/testcase/CaseEditor.vue` |
| API 测试 | `views/api-test/index.vue` |
| UI 测试 | `views/ui-test/index.vue` |
| 登录页 | `views/Login.vue` |
| 主布局 | `App.vue` |

---

## 三、替换规则

### 3.1 表格列标题

| 英文 | 中文 |
|------|------|
| Name | 名称 |
| Description | 描述 |
| Enabled | 启用 |
| Compare | 对比 |
| Match Type | 匹配类型 |
| Created By | 创建人 |
| Created At | 创建时间 |
| Updated At | 更新时间 |
| Actions | 操作 |
| Status | 状态 |
| Path | 路径 |
| Method | 方法 |
| Field | 字段 |
| Operator | 操作符 |
| Value | 值 |
| Type | 类型 |

### 3.2 按钮文字

| 英文 | 中文 |
|------|------|
| Create Suite | 新建套件 |
| Edit | 编辑 |
| Copy | 复制 |
| Delete | 删除 |
| Cancel | 取消 |
| Save | 保存 |
| Submit | 提交 |
| Search | 搜索 |
| Reset | 重置 |
| Add Rule | 添加规则 |
| Add Response | 添加响应 |
| Add Whitelist | 添加白名单 |

### 3.3 表单标签

| 英文 | 中文 |
|------|------|
| Match Type | 匹配类型 |
| Match Any | 满足任一 |
| Match All | 满足全部 |
| Enable Compare | 开启对比 |
| Rules | 规则 |
| Responses | 响应 |
| Whitelists | 白名单 |
| Timeout(ms) | 超时(毫秒) |
| Empty Resp | 空响应 |
| Client ID | 客户端ID |
| User ID | 用户ID |

### 3.4 状态标签

| 英文 | 中文 |
|------|------|
| Yes | 是 |
| No | 否 |
| Valid | 有效 |
| Invalid | 无效 |
| Matched | 一致 |
| Mismatched | 有差异 |

### 3.5 弹窗标题

| 英文 | 中文 |
|------|------|
| Create Mock Suite | 新建 Mock 套件 |
| Edit Mock Suite | 编辑 Mock 套件 |
| Copy Mock Suite | 复制 Mock 套件 |
| Confirm Delete | 确认删除 |
| Compare Detail | 对比详情 |

---

## 四、实现方式

直接在 Vue 模板中替换英文字符串为中文，不使用国际化框架。

---

## 五、验收标准

1. 所有表格列标题为中文
2. 所有按钮文字为中文
3. 所有表单标签为中文
4. 所有弹窗标题为中文
5. 所有提示信息为中文
