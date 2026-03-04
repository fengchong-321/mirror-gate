# 用例管理模块增强实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完善用例管理模块，添加用例编辑/详情页面、附件上传、富文本编辑器和批量导入/导出功能。

**Architecture:** 前端使用 Vue 3 + Element Plus，富文本使用 Tiptap 编辑器，后端使用 FastAPI 处理文件上传和数据导入导出。

**Tech Stack:** Vue 3, Element Plus, Tiptap, FastAPI, SQLAlchemy, TypeScript

---

## Phase 1: 用例编辑页面

### Task 1: 创建用例编辑器组件

**Files:**
- Create: `frontend/src/views/testcase/CaseEditor.vue`
- Modify: `frontend/src/router/index.ts`

**功能需求：**

1. **基本信息区域**
   - 用例编号（自动生成，只读）
   - 标题（必填）
   - 用例类型（下拉选择）
   - 所属平台（下拉选择）
   - 优先级（P0-P4）
   - 状态（草稿/激活/废弃）
   - 维护人、开发负责人

2. **测试内容区域**
   - 页面地址（URL）
   - 前置条件（富文本）
   - 测试步骤（可编辑表格）
     - 步骤描述
     - 预期结果
     - 支持添加/删除/排序
   - 预期结果（富文本）
   - 备注（富文本）

3. **标签区域**
   - 标签选择/输入（支持多选和自定义）

4. **操作按钮**
   - 保存
   - 保存并返回
   - 取消
   - 复制（编辑模式下）

**Step 1: 创建编辑器组件骨架**

```vue
<!-- frontend/src/views/testcase/CaseEditor.vue -->
<template>
  <div class="case-editor">
    <el-page-header @back="handleBack">
      <template #content>
        <span class="page-title">{{ isEdit ? '编辑用例' : '新建用例' }}</span>
      </template>
    </el-page-header>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="case-form">
      <!-- 基本信息 -->
      <el-card header="基本信息" class="form-card">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="用例编号">
              <el-input v-model="form.code" disabled placeholder="自动生成" />
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="标题" prop="title">
              <el-input v-model="form.title" placeholder="请输入用例标题" maxlength="200" show-word-limit />
            </el-form-item>
          </el-col>
        </el-row>
        <!-- 更多字段... -->
      </el-card>

      <!-- 测试内容 -->
      <el-card header="测试内容" class="form-card">
        <!-- 页面地址、前置条件、测试步骤、预期结果、备注 -->
      </el-card>

      <!-- 标签 -->
      <el-card header="标签" class="form-card">
        <el-select v-model="form.tags" multiple filterable allow-create placeholder="选择或输入标签">
          <el-option v-for="tag in commonTags" :key="tag" :label="tag" :value="tag" />
        </el-select>
      </el-card>
    </el-form>

    <!-- 底部操作栏 -->
    <div class="footer-actions">
      <el-button @click="handleBack">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      <el-button type="success" @click="handleSaveAndBack" :loading="saving">保存并返回</el-button>
    </div>
  </div>
</template>
```

**Step 2: 添加路由**

```typescript
// frontend/src/router/index.ts
{
  path: '/testcase/create',
  name: 'TestCaseCreate',
  component: () => import('@/views/testcase/CaseEditor.vue'),
  meta: { requiresAuth: true }
},
{
  path: '/testcase/:id/edit',
  name: 'TestCaseEdit',
  component: () => import('@/views/testcase/CaseEditor.vue'),
  meta: { requiresAuth: true }
}
```

**Step 3: 提交**

```bash
git add frontend/src/views/testcase/CaseEditor.vue frontend/src/router/index.ts
git commit -m "feat(testcase): add case editor page"
```

---

### Task 2: 创建用例详情页面

**Files:**
- Create: `frontend/src/views/testcase/CaseDetail.vue`
- Modify: `frontend/src/router/index.ts`

**功能需求：**

1. **信息展示**
   - 基本信息卡片（只读展示）
   - 测试步骤表格（只读）
   - 标签展示

2. **Tab 切换**
   - 详情（默认）
   - 附件
   - 评论
   - 变更历史

3. **操作按钮**
   - 编辑
   - 复制
   - 删除

**Step 1: 创建详情页面**

```vue
<!-- frontend/src/views/testcase/CaseDetail.vue -->
<template>
  <div class="case-detail">
    <el-page-header @back="handleBack">
      <template #content>
        <span class="page-title">{{ caseData?.title }}</span>
      </template>
      <template #extra>
        <el-button type="primary" @click="handleEdit">编辑</el-button>
        <el-button @click="handleCopy">复制</el-button>
        <el-button type="danger" @click="handleDelete">删除</el-button>
      </template>
    </el-page-header>

    <!-- 基本信息卡片 -->
    <el-card class="info-card">
      <el-descriptions :column="4" border>
        <el-descriptions-item label="用例编号">{{ caseData?.code }}</el-descriptions-item>
        <el-descriptions-item label="用例类型">{{ caseData?.case_type }}</el-descriptions-item>
        <!-- 更多字段... -->
      </el-descriptions>
    </el-card>

    <!-- Tab 区域 -->
    <el-tabs v-model="activeTab">
      <el-tab-pane label="详情" name="detail">
        <!-- 测试步骤、前置条件等 -->
      </el-tab-pane>
      <el-tab-pane label="附件" name="attachments">
        <!-- 附件列表 -->
      </el-tab-pane>
      <el-tab-pane label="评论" name="comments">
        <!-- 评论列表和添加 -->
      </el-tab-pane>
      <el-tab-pane label="变更历史" name="history">
        <!-- 变更历史时间线 -->
      </el-tab-pane>
    </el-tabs>
  </div>
</template>
```

**Step 2: 添加路由**

```typescript
{
  path: '/testcase/:id',
  name: 'TestCaseDetail',
  component: () => import('@/views/testcase/CaseDetail.vue'),
  meta: { requiresAuth: true }
}
```

**Step 3: 提交**

```bash
git add frontend/src/views/testcase/CaseDetail.vue frontend/src/router/index.ts
git commit -m "feat(testcase): add case detail page with tabs"
```

---

## Phase 2: 附件上传功能

### Task 3: 后端附件上传 API

**Files:**
- Modify: `backend/app/api/v1/testcase.py`

**功能需求：**

1. **上传附件**
   - POST `/testcase/cases/{case_id}/attachments`
   - 支持多文件上传
   - 文件大小限制（默认 10MB）
   - 文件类型限制（图片、文档等）

2. **下载附件**
   - GET `/testcase/attachments/{attachment_id}/download`

3. **删除附件**
   - DELETE `/testcase/attachments/{attachment_id}`

**Step 1: 添加上传目录配置**

```python
# backend/app/config.py 添加
UPLOAD_DIR: str = "uploads"
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"]
```

**Step 2: 添加附件 API**

```python
# backend/app/api/v1/testcase.py 添加
import os
import uuid
from fastapi import UploadFile, File
from pathlib import Path

@router.post("/cases/{case_id}/attachments", response_model=TestCaseAttachmentResponse)
async def upload_attachment(
    case_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传附件"""
    # 检查用例是否存在
    service = TestCaseService(db)
    case = service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    # 检查文件大小
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过限制")

    # 保存文件
    upload_dir = Path(settings.UPLOAD_DIR) / "testcase" / str(case_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_ext = os.path.splitext(file.filename)[1]
    new_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = upload_dir / new_filename

    with open(file_path, "wb") as f:
        f.write(content)

    # 创建数据库记录
    attachment = TestCaseAttachment(
        case_id=case_id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=file.content_type,
        uploaded_by="system"
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db)
):
    """下载附件"""
    attachment = db.query(TestCaseAttachment).filter(
        TestCaseAttachment.id == attachment_id
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")

    from fastapi.responses import FileResponse
    return FileResponse(
        path=attachment.file_path,
        filename=attachment.filename,
        media_type=attachment.file_type
    )


@router.delete("/attachments/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db)
):
    """删除附件"""
    attachment = db.query(TestCaseAttachment).filter(
        TestCaseAttachment.id == attachment_id
    ).first()
    if not attachment:
        raise HTTPException(status_code=404, detail="附件不存在")

    # 删除文件
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    db.delete(attachment)
    db.commit()
    return {"message": "删除成功"}
```

**Step 3: 提交**

```bash
git add backend/app/api/v1/testcase.py backend/app/config.py
git commit -m "feat(testcase): add attachment upload/download API"
```

---

### Task 4: 前端附件组件

**Files:**
- Create: `frontend/src/views/testcase/components/AttachmentList.vue`
- Modify: `frontend/src/api/testcase.ts`

**功能需求：**

1. **附件列表展示**
   - 文件名、大小、上传者、上传时间
   - 图片预览
   - 下载/删除操作

2. **上传功能**
   - 拖拽上传
   - 点击上传
   - 上传进度显示

**Step 1: 创建附件列表组件**

```vue
<!-- frontend/src/views/testcase/components/AttachmentList.vue -->
<template>
  <div class="attachment-list">
    <el-upload
      ref="uploadRef"
      :action="uploadUrl"
      :headers="uploadHeaders"
      :on-success="handleUploadSuccess"
      :on-error="handleUploadError"
      :before-upload="beforeUpload"
      :show-file-list="false"
      drag
      multiple
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        拖拽文件到此处或 <em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 jpg/png/pdf/doc 等格式，单个文件不超过 10MB
        </div>
      </template>
    </el-upload>

    <el-table :data="attachments" v-loading="loading" class="attachment-table">
      <el-table-column prop="filename" label="文件名" min-width="200">
        <template #default="{ row }">
          <el-link @click="handlePreview(row)">{{ row.filename }}</el-link>
        </template>
      </el-table-column>
      <el-table-column prop="file_size" label="大小" width="100">
        <template #default="{ row }">
          {{ formatFileSize(row.file_size) }}
        </template>
      </el-table-column>
      <el-table-column prop="uploaded_by" label="上传者" width="100" />
      <el-table-column prop="uploaded_at" label="上传时间" width="180" />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button link @click="handleDownload(row)">下载</el-button>
          <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 图片预览 -->
    <el-dialog v-model="previewVisible" title="图片预览" width="60%">
      <img :src="previewUrl" style="width: 100%" />
    </el-dialog>
  </div>
</template>
```

**Step 2: 更新 API 客户端**

```typescript
// frontend/src/api/testcase.ts 添加
export const testcaseApi = {
  // ... 现有方法

  // 附件
  getAttachments: (caseId: number) =>
    api.get<TestCaseAttachment[]>(`/testcase/cases/${caseId}/attachments`),
  uploadAttachment: (caseId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<TestCaseAttachment>(`/testcase/cases/${caseId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  downloadAttachment: (attachmentId: number) =>
    `/api/v1/testcase/attachments/${attachmentId}/download`,
  deleteAttachment: (id: number) =>
    api.delete(`/testcase/attachments/${id}`),
}
```

**Step 3: 提交**

```bash
git add frontend/src/views/testcase/components/AttachmentList.vue frontend/src/api/testcase.ts
git commit -m "feat(testcase): add attachment upload component"
```

---

## Phase 3: 富文本编辑器

### Task 5: 集成 Tiptap 编辑器

**Files:**
- Create: `frontend/src/components/RichTextEditor.vue`
- Modify: `frontend/package.json`

**功能需求：**

1. **基础工具栏**
   - 加粗、斜体、下划线、删除线
   - 标题（H1-H3）
   - 有序/无序列表
   - 代码块
   - 链接
   - 图片

2. **支持 v-model 双向绑定**

**Step 1: 安装依赖**

```bash
cd frontend && npm install @tiptap/vue-3 @tiptap/starter-kit @tiptap/extension-link @tiptap/extension-image @tiptap/extension-placeholder
```

**Step 2: 创建富文本编辑器组件**

```vue
<!-- frontend/src/components/RichTextEditor.vue -->
<template>
  <div class="rich-text-editor" :class="{ 'is-disabled': disabled }">
    <div v-if="!disabled" class="toolbar">
      <el-button-group>
        <el-button size="small" @click="editor.chain().focus().toggleBold().run()" :type="editor.isActive('bold') ? 'primary' : ''">
          <strong>B</strong>
        </el-button>
        <el-button size="small" @click="editor.chain().focus().toggleItalic().run()" :type="editor.isActive('italic') ? 'primary' : ''">
          <em>I</em>
        </el-button>
        <el-button size="small" @click="editor.chain().focus().toggleUnderline().run()" :type="editor.isActive('underline') ? 'primary' : ''">
          <u>U</u>
        </el-button>
        <el-button size="small" @click="editor.chain().focus().toggleStrike().run()" :type="editor.isActive('strike') ? 'primary' : ''">
          <s>S</s>
        </el-button>
      </el-button-group>

      <el-button-group class="ml-2">
        <el-button size="small" @click="editor.chain().focus().toggleHeading({ level: 1 }).run()">H1</el-button>
        <el-button size="small" @click="editor.chain().focus().toggleHeading({ level: 2 }).run()">H2</el-button>
        <el-button size="small" @click="editor.chain().focus().toggleHeading({ level: 3 }).run()">H3</el-button>
      </el-button-group>

      <el-button-group class="ml-2">
        <el-button size="small" @click="editor.chain().focus().toggleBulletList().run()">
          <el-icon><List /></el-icon>
        </el-button>
        <el-button size="small" @click="editor.chain().focus().toggleOrderedList().run()">
          <el-icon><Document /></el-icon>
        </el-button>
        <el-button size="small" @click="editor.chain().focus().toggleCodeBlock().run()">
          <el-icon><DocumentCopy /></el-icon>
        </el-button>
      </el-button-group>

      <el-button size="small" class="ml-2" @click="insertLink">
        <el-icon><Link /></el-icon>
      </el-button>
      <el-button size="small" @click="insertImage">
        <el-icon><Picture /></el-icon>
      </el-button>
    </div>
    <editor-content :editor="editor" class="editor-content" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount, computed } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'

const props = defineProps<{
  modelValue: string
  placeholder?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const editor = useEditor({
  content: props.modelValue,
  editable: !props.disabled,
  extensions: [
    StarterKit,
    Link.configure({ openOnClick: false }),
    Image,
    Placeholder.configure({ placeholder: props.placeholder || '请输入内容...' }),
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
})

watch(() => props.modelValue, (value) => {
  if (editor.value && editor.value.getHTML() !== value) {
    editor.value.commands.setContent(value, false)
  }
})

watch(() => props.disabled, (disabled) => {
  if (editor.value) {
    editor.value.setEditable(!disabled)
  }
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})

const insertLink = () => {
  const url = prompt('请输入链接地址')
  if (url) {
    editor.value?.chain().focus().setLink({ href: url }).run()
  }
}

const insertImage = () => {
  const url = prompt('请输入图片地址')
  if (url) {
    editor.value?.chain().focus().setImage({ src: url }).run()
  }
}
</script>

<style scoped>
.rich-text-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.toolbar {
  padding: 8px;
  border-bottom: 1px solid #dcdfe6;
  background: #f5f7fa;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.editor-content {
  min-height: 150px;
  padding: 12px;
}

.editor-content :deep(.ProseMirror) {
  outline: none;
}

.editor-content :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  color: #adb5bd;
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

.is-disabled {
  background: #f5f7fa;
}

.ml-2 {
  margin-left: 8px;
}
</style>
```

**Step 3: 提交**

```bash
git add frontend/src/components/RichTextEditor.vue frontend/package.json frontend/package-lock.json
git commit -m "feat: add rich text editor component with Tiptap"
```

---

### Task 6: 在用例编辑器中集成富文本

**Files:**
- Modify: `frontend/src/views/testcase/CaseEditor.vue`

**Step 1: 替换文本域为富文本编辑器**

```vue
<!-- 在 CaseEditor.vue 中 -->
<script setup lang="ts">
import RichTextEditor from '@/components/RichTextEditor.vue'
</script>

<template>
  <!-- 前置条件 -->
  <el-form-item label="前置条件">
    <RichTextEditor v-model="form.preconditions" placeholder="请输入前置条件" />
  </el-form-item>

  <!-- 预期结果 -->
  <el-form-item label="预期结果">
    <RichTextEditor v-model="form.expected_result" placeholder="请输入预期结果" />
  </el-form-item>

  <!-- 备注 -->
  <el-form-item label="备注">
    <RichTextEditor v-model="form.remark" placeholder="请输入备注" />
  </el-form-item>
</template>
```

**Step 2: 提交**

```bash
git add frontend/src/views/testcase/CaseEditor.vue
git commit -m "feat(testcase): integrate rich text editor in case editor"
```

---

## Phase 4: 批量导入/导出

### Task 7: 后端导入导出 API

**Files:**
- Modify: `backend/app/api/v1/testcase.py`
- Modify: `backend/app/services/testcase_service.py`

**功能需求：**

1. **导出用例**
   - GET `/testcase/groups/{group_id}/export`
   - 支持导出为 JSON 或 Excel 格式
   - 包含所有用例字段

2. **导入用例**
   - POST `/testcase/groups/{group_id}/import`
   - 支持 JSON 或 Excel 文件
   - 返回导入结果（成功/失败数量）

**Step 1: 添加导入导出服务方法**

```python
# backend/app/services/testcase_service.py 添加
import json
from io import BytesIO
from typing import List, Dict, Any

def export_cases(self, group_id: int, format: str = "json") -> Any:
    """导出用例"""
    cases = self.get_cases_by_group(group_id, 0, 10000)

    if format == "json":
        return [self._case_to_dict(c) for c in cases]
    elif format == "excel":
        return self._export_to_excel(cases)

def _case_to_dict(self, case: TestCase) -> Dict:
    """将用例转换为字典"""
    return {
        "code": case.code,
        "title": case.title,
        "case_type": case.case_type.value if case.case_type else None,
        "platform": case.platform.value if case.platform else None,
        "priority": case.priority.value if case.priority else None,
        "status": case.status.value if case.status else None,
        "preconditions": case.preconditions,
        "steps": case.steps,
        "expected_result": case.expected_result,
        "tags": case.tags,
        "owner": case.owner,
        "developer": case.developer,
        "page_url": case.page_url,
    }

def import_cases(self, group_id: int, data: List[Dict], created_by: str) -> Dict:
    """导入用例"""
    success = 0
    failed = 0
    errors = []

    for i, item in enumerate(data):
        try:
            case_data = TestCaseCreate(
                group_id=group_id,
                title=item.get("title", f"导入用例 {i+1}"),
                case_type=item.get("case_type"),
                platform=item.get("platform"),
                priority=item.get("priority"),
                preconditions=item.get("preconditions"),
                steps=item.get("steps"),
                expected_result=item.get("expected_result"),
                tags=item.get("tags"),
                owner=item.get("owner"),
                developer=item.get("developer"),
                page_url=item.get("page_url"),
            )
            self.create_case(case_data, created_by)
            success += 1
        except Exception as e:
            failed += 1
            errors.append(f"第 {i+1} 行: {str(e)}")

    return {"success": success, "failed": failed, "errors": errors}
```

**Step 2: 添加 API 端点**

```python
# backend/app/api/v1/testcase.py 添加
from fastapi.responses import StreamingResponse

@router.get("/groups/{group_id}/export")
def export_cases(
    group_id: int,
    format: str = Query("json", description="导出格式: json 或 excel"),
    db: Session = Depends(get_db)
):
    """导出用例"""
    service = TestCaseService(db)
    data = service.export_cases(group_id, format)

    if format == "json":
        import json
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=testcases_{group_id}.json"}
        )
    elif format == "excel":
        # Excel 导出逻辑
        pass


@router.post("/groups/{group_id}/import")
async def import_cases(
    group_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """导入用例"""
    service = TestCaseService(db)

    content = await file.read()

    if file.filename.endswith('.json'):
        data = json.loads(content)
    elif file.filename.endswith(('.xlsx', '.xls')):
        # Excel 解析逻辑
        data = []
    else:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    result = service.import_cases(group_id, data, created_by="system")
    return result
```

**Step 3: 提交**

```bash
git add backend/app/api/v1/testcase.py backend/app/services/testcase_service.py
git commit -m "feat(testcase): add import/export API"
```

---

### Task 8: 前端导入导出功能

**Files:**
- Modify: `frontend/src/views/testcase/index.vue`
- Modify: `frontend/src/api/testcase.ts`

**功能需求：**

1. **导出按钮**
   - 选择导出格式（JSON/Excel）
   - 下载文件

2. **导入按钮**
   - 上传文件
   - 显示导入结果

**Step 1: 更新主页面**

```vue
<!-- frontend/src/views/testcase/index.vue 工具栏添加 -->
<el-dropdown @command="handleExport">
  <el-button>
    导出 <el-icon><ArrowDown /></el-icon>
  </el-button>
  <template #dropdown>
    <el-dropdown-menu>
      <el-dropdown-item command="json">导出为 JSON</el-dropdown-item>
      <el-dropdown-item command="excel">导出为 Excel</el-dropdown-item>
    </el-dropdown-menu>
  </template>
</el-dropdown>

<el-upload
  :show-file-list="false"
  :before-upload="handleImport"
  accept=".json,.xlsx,.xls"
  style="display: inline-block; margin-left: 8px;"
>
  <el-button>导入</el-button>
</el-upload>
```

**Step 2: 更新 API 客户端**

```typescript
// frontend/src/api/testcase.ts 添加
export const testcaseApi = {
  // ... 现有方法

  exportCases: (groupId: number, format: 'json' | 'excel' = 'json') =>
    api.get(`/testcase/groups/${groupId}/export`, {
      params: { format },
      responseType: 'blob'
    }),

  importCases: (groupId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/testcase/groups/${groupId}/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
}
```

**Step 3: 提交**

```bash
git add frontend/src/views/testcase/index.vue frontend/src/api/testcase.ts
git commit -m "feat(testcase): add import/export UI"
```

---

## 总结

本实施计划覆盖用例管理模块的增强功能：

**Phase 1: 用例编辑页面**
- Task 1: 创建用例编辑器组件
- Task 2: 创建用例详情页面

**Phase 2: 附件上传功能**
- Task 3: 后端附件上传 API
- Task 4: 前端附件组件

**Phase 3: 富文本编辑器**
- Task 5: 集成 Tiptap 编辑器
- Task 6: 在用例编辑器中集成富文本

**Phase 4: 批量导入/导出**
- Task 7: 后端导入导出 API
- Task 8: 前端导入导出功能
