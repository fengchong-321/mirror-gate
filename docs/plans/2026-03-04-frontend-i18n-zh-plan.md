# 前端界面中文化实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将前端所有界面的英文文本替换为中文。

**Architecture:** 直接在 Vue 模板中替换英文字符串为中文，逐文件处理。

**Tech Stack:** Vue 3, TypeScript, Element Plus

---

## Task 1: Mock 管理列表页中文化

**Files:**
- Modify: `frontend/src/views/mock/index.vue`

**Step 1: 替换表格列标题**

将以下 label 替换为中文：

```vue
<!-- 第 22-50 行左右 -->
<el-table-column prop="id" label="ID" width="80" />
<el-table-column prop="name" label="名称" min-width="150" />
<el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
<el-table-column prop="is_enabled" label="启用" width="100">
  <template #default="{ row }">
    <el-tag :type="row.is_enabled ? 'success' : 'info'">
      {{ row.is_enabled ? '是' : '否' }}
    </el-tag>
  </template>
</el-table-column>
<el-table-column prop="enable_compare" label="对比" width="100">
  <template #default="{ row }">
    <el-tag :type="row.enable_compare ? 'warning' : 'info'" size="small">
      {{ row.enable_compare ? '是' : '否' }}
    </el-tag>
  </template>
</el-table-column>
<el-table-column prop="match_type" label="匹配类型" width="100">
  <template #default="{ row }">
    <el-tag size="small">{{ row.match_type === 'any' ? '任一' : '全部' }}</el-tag>
  </template>
</el-table-column>
<el-table-column prop="created_by" label="创建人" width="120" />
<el-table-column prop="created_at" label="创建时间" width="180">
<el-table-column label="操作" width="240" fixed="right">
```

**Step 2: 替换按钮和弹窗文字**

```vue
<!-- header 按钮 -->
<el-button type="primary" @click="handleCreate">新建套件</el-button>

<!-- 操作按钮 -->
<el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
<el-button type="success" size="small" @click="handleCopy(row)">复制</el-button>
<el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>

<!-- 复制弹窗 -->
<el-dialog v-model="copyDialogVisible" title="复制 Mock 套件" width="400px">
  <el-form-item label="新名称">
    <el-input v-model="copyForm.newName" placeholder="请输入新套件名称" />
  </el-form-item>
  <template #footer>
    <el-button @click="copyDialogVisible = false">取消</el-button>
    <el-button type="primary" @click="confirmCopy" :loading="copyLoading">确认</el-button>
  </template>
</el-dialog>
```

**Step 3: Commit**

```bash
git add frontend/src/views/mock/index.vue
git commit -m "i18n: localize mock list page to Chinese"
```

---

## Task 2: Mock 套件编辑器中文化

**Files:**
- Modify: `frontend/src/views/mock/SuiteEditor.vue`

**Step 1: 替换表单标签**

```vue
<el-form-item label="名称" prop="name">
  <el-input v-model="form.name" placeholder="请输入套件名称" />
</el-form-item>

<el-form-item label="匹配类型" prop="match_type">
  <el-select v-model="form.match_type" style="width: 100%">
    <el-option label="满足任一" value="any" />
    <el-option label="满足全部" value="all" />
  </el-select>
</el-form-item>

<el-form-item label="描述" prop="description">
  <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入描述" />
</el-form-item>

<el-form-item label="启用">
  <el-switch v-model="form.is_enabled" />
</el-form-item>

<el-form-item label="开启对比">
  <el-switch v-model="form.enable_compare" />
</el-form-item>
```

**Step 2: 替换 Tab 标签**

```vue
<el-tab-pane label="规则" name="rules">
<el-tab-pane label="响应" name="responses">
<el-tab-pane label="白名单" name="whitelists">
```

**Step 3: 替换规则表格**

```vue
<el-table :data="form.rules" border size="small">
  <el-table-column label="字段" min-width="150">
    <template #default="{ row }">
      <el-input v-model="row.field" placeholder="如: headers.x-user-id" />
    </template>
  </el-table-column>
  <el-table-column label="操作符" width="140">
    <template #default="{ row }">
      <el-select v-model="row.operator" style="width: 100%">
        <el-option label="等于" value="equals" />
        <el-option label="包含" value="contains" />
        <el-option label="不等于" value="not_equals" />
      </el-select>
    </template>
  </el-table-column>
  <el-table-column label="值" min-width="150">
    <template #default="{ row }">
      <el-input v-model="row.value" placeholder="匹配值" />
    </template>
  </el-table-column>
  <el-table-column label="操作" width="80">
</el-table>

<el-button type="primary" size="small" @click="addRule">添加规则</el-button>
```

**Step 4: 替换响应表格**

```vue
<el-table-column label="路径" min-width="150">
<el-table-column label="方法" width="120">
<el-table-column label="超时(ms)" width="120">
<el-table-column label="空响应" width="100">

<el-button type="primary" size="small" @click="addResponse">添加响应</el-button>

<!-- 预览标签 -->
<el-tag v-if="previewResult.valid" type="success" size="small">有效</el-tag>
<el-tag v-else type="danger" size="small">无效</el-tag>
```

**Step 5: 替换白名单表格**

```vue
<el-table-column label="类型" width="140">
  <template #default="{ row }">
    <el-select v-model="row.type" style="width: 100%">
      <el-option label="客户端ID" value="clientId" />
      <el-option label="用户ID" value="userId" />
      <el-option label="访客ID" value="vid" />
    </el-select>
  </template>
</el-table-column>
<el-table-column label="值" min-width="200">

<el-button type="primary" size="small" @click="addWhitelist">添加白名单</el-button>
```

**Step 6: 替换底部按钮**

```vue
<el-button @click="handleClose">取消</el-button>
<el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
```

**Step 7: Commit**

```bash
git add frontend/src/views/mock/SuiteEditor.vue
git commit -m "i18n: localize mock suite editor to Chinese"
```

---

## Task 3: 对比记录页面中文化

**Files:**
- Modify: `frontend/src/views/mock/CompareRecords.vue`

**Step 1: 替换筛选器和表格**

```vue
<!-- 筛选器 -->
<el-select v-model="filterSuiteId" placeholder="全部套件" clearable>
<el-select v-model="filterMatch" placeholder="全部状态" clearable>
  <el-option label="一致" :value="true" />
  <el-option label="有差异" :value="false" />
</el-select>

<!-- 表格列 -->
<el-table-column prop="id" label="ID" width="80" />
<el-table-column prop="suite_id" label="套件ID" width="100" />
<el-table-column prop="path" label="路径" min-width="200" />
<el-table-column prop="method" label="方法" width="100" />
<el-table-column prop="is_match" label="状态" width="120">
  <template #default="{ row }">
    <el-tag :type="row.is_match ? 'success' : 'danger'">
      {{ row.is_match ? '一致' : `差异(${row.differences?.length || 0})` }}
    </el-tag>
  </template>
</el-table-column>
<el-table-column prop="created_at" label="对比时间" width="180">
<el-table-column label="操作" width="150" fixed="right">
  <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
  <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
</el-table-column>
```

**Step 2: 替换详情弹窗**

```vue
<el-dialog v-model="detailVisible" title="对比详情" width="90%" top="5vh">
  <div class="detail-header">
    <span>路径: {{ currentRecord.path }}</span>
    <span>方法: {{ currentRecord.method }}</span>
    <el-tag :type="currentRecord.is_match ? 'success' : 'danger'">
      {{ currentRecord.is_match ? '一致' : '有差异' }}
    </el-tag>
  </div>
  <div class="compare-panels">
    <div class="panel">
      <div class="panel-title">Mock 响应</div>
      <pre class="panel-content">{{ formatJson(currentRecord.mock_response) }}</pre>
    </div>
    <div class="panel">
      <div class="panel-title">真实响应</div>
      <pre class="panel-content">{{ formatJson(currentRecord.real_response) }}</pre>
    </div>
  </div>
  <div class="differences">
    <div class="diff-title">差异列表</div>
    <el-table :data="currentRecord.differences" border size="small">
      <el-table-column prop="path" label="路径" width="200" />
      <el-table-column prop="type" label="类型" width="120" />
      <el-table-column label="Mock 值" min-width="150">
        <template #default="{ row }">
          {{ row.expected ?? row.value ?? '-' }}
        </template>
      </el-table-column>
      <el-table-column label="真实值" min-width="150">
        <template #default="{ row }">
          {{ row.actual ?? '-' }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</el-dialog>
```

**Step 3: Commit**

```bash
git add frontend/src/views/mock/CompareRecords.vue
git commit -m "i18n: localize compare records page to Chinese"
```

---

## Task 4: 用例管理页面中文化

**Files:**
- Modify: `frontend/src/views/testcase/index.vue`
- Modify: `frontend/src/views/testcase/CaseEditor.vue`

**Step 1: 检查现有中文，补充缺失**

用例管理页面可能已有部分中文，检查并补充：

```bash
# 检查英文文本
grep -n 'label="[A-Z]' frontend/src/views/testcase/*.vue
```

**Step 2: 替换发现的英文**

按 Task 1-3 的模式替换。

**Step 3: Commit**

```bash
git add frontend/src/views/testcase/
git commit -m "i18n: localize testcase pages to Chinese"
```

---

## Task 5: 其他页面中文化

**Files:**
- Modify: `frontend/src/views/api-test/index.vue`
- Modify: `frontend/src/views/ui-test/index.vue`
- Modify: `frontend/src/views/Login.vue`

**Step 1: 检查并替换英文**

```bash
# 检查英文文本
grep -n 'label="[A-Z]' frontend/src/views/api-test/*.vue
grep -n 'label="[A-Z]' frontend/src/views/ui-test/*.vue
grep -n '>[A-Z][a-z]*<' frontend/src/views/Login.vue
```

**Step 2: Commit**

```bash
git add frontend/src/views/
git commit -m "i18n: localize remaining pages to Chinese"
```

---

## Task 6: 侧边栏菜单中文化

**Files:**
- Modify: `frontend/src/App.vue`

**Step 1: 检查菜单项**

侧边栏菜单应该已经是中文（仪表盘、用例管理等），确认无需修改。

**Step 2: Commit（如有修改）**

```bash
git add frontend/src/App.vue
git commit -m "i18n: localize sidebar menu to Chinese"
```

---

## 最终验证

**Step 1: 启动前端**

```bash
cd frontend && npm run dev
```

**Step 2: 检查各页面**

- [ ] Mock 套件列表页
- [ ] Mock 套件编辑器
- [ ] 对比记录页面
- [ ] 用例管理页面
- [ ] API 测试页面
- [ ] UI 测试页面
- [ ] 登录页面

**Step 3: 最终 Commit**

```bash
git add -A
git commit -m "i18n: complete frontend Chinese localization"
```
