# 用例管理 UI 修复实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 修复用例管理的UI问题，包括去重分组、调整用例数量显示位置、修改用例ID格式

**Architecture:** 后端修改ID生成逻辑和路由，前端调整列表显示和URL格式

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, TypeScript, Element Plus

---

## 变更摘要

| 变更项 | 当前 | 调整后 |
|--------|------|--------|
| 用例ID格式 | TC-20260303-001 | 0000001（7位纯数字） |
| 用例数量显示 | 文件夹后显示 (6) | 列表上方显示"共 6 条用例" |
| 编号列 | 表格有"编号"列 | 移除该列 |
| 用例详情URL | /testcase/1/edit | /testcase/0000001/edit |
| 重复分组 | 3组重复 | 清理为1组 |

---

## Task 1: 清理重复分组数据

**Files:**
- N/A（数据库操作）

**Step 1: 删除空分组**

```sql
-- 删除空的重复分组（id=1-12）
DELETE FROM testcase_groups WHERE id IN (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12);
```

**Step 2: 验证数据**

```sql
SELECT * FROM testcase_groups ORDER BY id;
SELECT COUNT(*) FROM testcases;
```

---

## Task 2: 修改后端用例ID生成逻辑

**Files:**
- Modify: `backend/app/services/testcase_service.py:188-216`

**Step 1: 修改 _generate_case_code 方法**

```python
def _generate_case_code(self) -> str:
    """Generate a unique test case code.

    Format: 7-digit zero-padded number (e.g., 0000001)

    Returns:
        A unique test case code string.
    """
    # Get the highest ID from existing cases
    latest_case = (
        self.db.query(TestCase)
        .order_by(TestCase.id.desc())
        .first()
    )

    if latest_case:
        next_id = latest_case.id + 1
    else:
        next_id = 1

    return f"{next_id:07d}"
```

**Step 2: 更新现有用例的code字段**

```sql
UPDATE testcases SET code = LPAD(id, 7, '0');
```

---

## Task 3: 修改后端路由支持7位数字ID

**Files:**
- Modify: `backend/app/api/v1/testcase.py`

**Step 1: 添加ID转换逻辑**

在路由处理函数中，将7位字符串ID转换为整数：

```python
@router.get("/cases/{case_id}", response_model=TestCaseDetailResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    # 支持纯数字ID（去除前导零）
    try:
        numeric_id = int(case_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid case ID format")

    service = TestCaseService(db)
    case = service.get_case(numeric_id)
    # ...
```

**Step 2: 更新所有相关路由**

- GET /cases/{case_id}
- PUT /cases/{case_id}
- DELETE /cases/{case_id}
- POST /cases/{case_id}/copy
- PUT /cases/{case_id}/move

---

## Task 4: 修改前端用例数量显示位置

**Files:**
- Modify: `frontend/src/views/testcase/index.vue`

**Step 1: 移除树节点上的数量徽章**

删除模板中的 `<el-badge>` 组件：

```vue
<!-- 修改前 -->
<span class="node-label">
  <el-icon><Folder /></el-icon>
  <span>{{ data.label }}</span>
  <el-badge :value="data.case_count" :max="99" class="case-count" />
</span>

<!-- 修改后 -->
<span class="node-label">
  <el-icon><Folder /></el-icon>
  <span>{{ data.label }}</span>
</span>
```

**Step 2: 在用例列表上方添加统计栏**

```vue
<!-- 在工具栏上方添加 -->
<div v-if="selectedGroupId" class="case-stats">
  <span>共 {{ totalCases }} 条用例</span>
</div>
```

**Step 3: 添加样式**

```css
.case-stats {
  padding: 8px 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
```

---

## Task 5: 移除前端用例编号列

**Files:**
- Modify: `frontend/src/views/testcase/index.vue`

**Step 1: 从列配置中移除code列**

```typescript
// 修改前
const allColumns = [
  { prop: 'code', label: '编号', width: 140 },
  { prop: 'title', label: '标题', minWidth: 200 },
  // ...
]

// 修改后
const allColumns = [
  { prop: 'title', label: '标题', minWidth: 200 },
  // ...
]
```

**Step 2: 从默认显示列中移除**

```typescript
// 修改前
const visibleColumns = ref(['code', 'title', 'case_type', 'platform', 'priority', 'owner'])

// 修改后
const visibleColumns = ref(['title', 'case_type', 'platform', 'priority', 'owner'])
```

---

## Task 6: 修改前端URL格式

**Files:**
- Modify: `frontend/src/views/testcase/index.vue`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/views/testcase/CaseEditor.vue`
- Modify: `frontend/src/views/testcase/CaseDetail.vue`

**Step 1: 修改编辑按钮跳转**

```typescript
// index.vue
const handleEditCase = (row: TestCase) => {
  // 使用7位格式化ID
  const formattedId = String(row.id).padStart(7, '0')
  router.push(`/testcase/${formattedId}/edit`)
}
```

**Step 2: 修改路由参数获取**

```typescript
// CaseEditor.vue / CaseDetail.vue
const caseId = computed(() => {
  const id = route.params.id
  if (id) {
    // 去除前导零，转为数字
    return parseInt(id as string, 10)
  }
  return null
})
```

**Step 3: 更新API调用**

确保API调用使用数字ID：

```typescript
// testcase.ts API文件
getCase: (id: number) => http.get(`/testcase/cases/${id}`),
```

---

## Task 7: 更新测试数据脚本

**Files:**
- Modify: `backend/scripts/create_testcase_testdata.py`

**Step 1: 移除旧的code生成依赖**

确保脚本不依赖旧的code格式，让后端自动生成新的7位格式。

---

## Task 8: 端到端验证

**Step 1: 验证分组无重复**

```bash
curl -s http://localhost:8000/api/v1/testcase/groups/tree | python3 -c "
import sys, json
data = json.load(sys.stdin)
names = []
def collect_names(nodes):
    for n in nodes:
        names.append(n['label'])
        collect_names(n.get('children', []))
collect_names(data)
print('Group names:', names)
print('Duplicates:', [n for n in names if names.count(n) > 1])
"
```

**Step 2: 验证用例ID格式**

```bash
curl -s "http://localhost:8000/api/v1/testcase/cases?group_id=16&skip=0&limit=3" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data['items'][:3]:
    print(f\"ID: {item['id']}, Code: {item['code']}\")
"
```

**Step 3: 验证前端显示**

- 启动前端
- 确认分组树无数量徽章
- 确认列表上方有"共 N 条用例"
- 确认列表无"编号"列
- 确认编辑按钮跳转URL为7位格式

---

## 执行顺序

1. Task 1 - 清理重复分组数据
2. Task 2 - 修改后端用例ID生成逻辑
3. Task 3 - 修改后端路由支持7位数字ID
4. Task 4 - 修改前端用例数量显示位置
5. Task 5 - 移除前端用例编号列
6. Task 6 - 修改前端URL格式
7. Task 7 - 更新测试数据脚本
8. Task 8 - 端到端验证
