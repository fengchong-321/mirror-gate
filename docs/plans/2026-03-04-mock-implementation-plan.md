# Mock 模块完善实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完善 Mock 管理模块，实现 API 网关中间件、Mock 预览和对比功能。

**Architecture:**
- 后端：FastAPI 中间件拦截请求，匹配 Mock 规则返回 Mock 响应
- 前端：编辑器分栏实时预览，独立对比记录页面

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, TypeScript, Element Plus

---

## Task 1: API 网关中间件

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/services/mock_interceptor.py`

**Step 1: 在 mock_interceptor.py 中添加异步方法**

在 `MockInterceptor` 类中添加异步方法支持：

```python
async def get_mock_response_async(
    self,
    method: str,
    path: str,
    headers: Dict[str, str],
    body: Optional[str],
    query_params: Dict[str, str],
    client_info: Dict[str, str],
) -> Optional[Dict[str, Any]]:
    """Async version of get_mock_response."""
    return self.get_mock_response(
        method, path, headers, body, query_params, client_info
    )
```

**Step 2: 在 main.py 中添加中间件**

```python
from fastapi import Request
from app.services.mock_interceptor import MockInterceptor
from app.database import SessionLocal
import asyncio

@app.middleware("http")
async def mock_interceptor_middleware(request: Request, call_next):
    # 只拦截 API 请求
    if not request.url.path.startswith("/api/"):
        return await call_next(request)

    # 排除 Mock 管理接口本身
    if request.url.path.startswith("/api/v1/mock/"):
        return await call_next(request)

    db = SessionLocal()
    try:
        interceptor = MockInterceptor(db)

        # 获取请求信息
        method = request.method
        path = request.url.path
        headers = dict(request.headers)
        query_params = dict(request.query_params)

        # 获取请求体（仅对有 body 的方法）
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            body = body.decode("utf-8") if body else None

        # 获取客户端信息
        client_info = {
            "clientId": request.headers.get("x-client-id", ""),
            "userId": request.headers.get("x-user-id", ""),
            "vid": request.headers.get("x-vid", ""),
        }

        # 检查是否命中 Mock
        mock_response = interceptor.get_mock_response(
            method, path, headers, body, query_params, client_info
        )

        if mock_response:
            # 模拟延迟
            if mock_response.get("delay_ms", 0) > 0:
                await asyncio.sleep(mock_response["delay_ms"] / 1000)

            from fastapi.responses import JSONResponse
            return JSONResponse(
                content=json.loads(mock_response["body"]) if mock_response["body"] else {},
                status_code=mock_response.get("status_code", 200),
                headers=mock_response.get("headers", {}),
            )
    finally:
        db.close()

    return await call_next(request)
```

**Step 3: 验证中间件工作**

启动后端服务，使用 curl 测试：

```bash
# 创建一个测试 Mock 套件
curl -X POST http://localhost:8000/api/v1/mock/suites \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "is_enabled": true, "match_type": "any", "rules": [], "responses": [{"path": "/api/test", "method": "GET", "response_json": "{\"code\": 0, \"msg\": \"mocked\"}"}], "whitelists": []}'

# 测试 Mock 是否生效
curl http://localhost:8000/api/test
# 期望返回: {"code": 0, "msg": "mocked"}
```

**Step 4: Commit**

```bash
git add backend/app/main.py backend/app/services/mock_interceptor.py
git commit -m "feat: add mock interceptor middleware for API gateway"
```

---

## Task 2: Mock 预览功能 - 后端

**Files:**
- Modify: `backend/app/api/v1/mock.py`

**Step 1: 添加预览 API**

```python
from pydantic import BaseModel
from typing import Optional

class MockPreviewRequest(BaseModel):
    response_json: Optional[str] = None

class MockPreviewResponse(BaseModel):
    valid: bool
    formatted: Optional[str] = None
    error: Optional[str] = None

@router.post(
    "/preview",
    response_model=MockPreviewResponse,
    summary="Preview mock response",
    description="Validate and format mock response JSON.",
)
def preview_response(request: MockPreviewRequest):
    """Validate and format JSON for preview."""
    import json

    if not request.response_json or not request.response_json.strip():
        return MockPreviewResponse(valid=True, formatted="{}")

    try:
        parsed = json.loads(request.response_json)
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
        return MockPreviewResponse(valid=True, formatted=formatted)
    except json.JSONDecodeError as e:
        return MockPreviewResponse(
            valid=False,
            error=f"JSON 解析错误: 行 {e.lineno}, 列 {e.colno} - {e.msg}"
        )
```

**Step 2: Commit**

```bash
git add backend/app/api/v1/mock.py
git commit -m "feat: add mock preview API endpoint"
```

---

## Task 3: Mock 预览功能 - 前端

**Files:**
- Modify: `frontend/src/api/mock.ts`
- Modify: `frontend/src/views/mock/SuiteEditor.vue`

**Step 1: 添加预览 API**

在 `frontend/src/api/mock.ts` 中添加：

```typescript
export interface MockPreviewRequest {
  response_json: string
}

export interface MockPreviewResponse {
  valid: boolean
  formatted: string | null
  error: string | null
}

export const mockApi = {
  // ... 现有方法

  previewResponse: (data: MockPreviewRequest) =>
    api.post<MockPreviewResponse>('/mock/preview', data),
}
```

**Step 2: 修改 SuiteEditor.vue 布局**

将 Responses Tab 改为左右分栏布局：

```vue
<!-- 在 Responses Tab 中替换现有内容 -->
<el-tab-pane label="Responses" name="responses">
  <div class="tab-header">
    <el-button type="primary" size="small" @click="addResponse">
      添加响应
    </el-button>
  </div>

  <!-- 响应列表 -->
  <el-table
    :data="form.responses"
    border
    size="small"
    highlight-current-row
    @current-change="(row) => { if (row) selectedResponseIndex = form.responses.indexOf(row) }"
  >
    <!-- 表格列保持不变 -->
  </el-table>

  <!-- 分栏区域：编辑器 + 预览 -->
  <div v-if="form.responses.length > 0 && form.responses[selectedResponseIndex]" class="response-editor">
    <div class="editor-panel">
      <div class="panel-header">Response JSON</div>
      <el-input
        v-model="form.responses[selectedResponseIndex].response_json"
        type="textarea"
        :rows="12"
        placeholder='{"code": 0, "data": {}}'
        @input="handlePreviewDebounced"
      />
    </div>
    <div class="preview-panel">
      <div class="panel-header">
        预览
        <el-tag v-if="previewResult.valid" type="success" size="small">有效</el-tag>
        <el-tag v-else type="danger" size="small">无效</el-tag>
      </div>
      <pre v-if="previewResult.valid" class="preview-content">{{ previewResult.formatted }}</pre>
      <div v-else class="preview-error">{{ previewResult.error }}</div>
    </div>
  </div>

  <!-- AB Test Config 保持不变 -->
</el-tab-pane>
```

**Step 3: 添加预览逻辑**

```typescript
import { debounce } from 'lodash-es'

// 预览状态
const previewResult = ref<{
  valid: boolean
  formatted: string | null
  error: string | null
}>({
  valid: true,
  formatted: '{}',
  error: null
})

// 防抖预览函数
const handlePreview = async () => {
  const currentResponse = form.value.responses?.[selectedResponseIndex.value]
  if (!currentResponse) return

  try {
    const response = await mockApi.previewResponse({
      response_json: currentResponse.response_json || ''
    })
    previewResult.value = response.data
  } catch {
    previewResult.value = {
      valid: false,
      formatted: null,
      error: '预览请求失败'
    }
  }
}

const handlePreviewDebounced = debounce(handlePreview, 300)

// 切换响应时更新预览
watch(selectedResponseIndex, () => {
  handlePreview()
})

// 打开编辑器时初始化预览
watch(() => props.visible, (newVal) => {
  if (newVal) {
    // ... 现有逻辑
    nextTick(() => {
      handlePreview()
    })
  }
})
```

**Step 4: 添加样式**

```css
.response-editor {
  display: flex;
  gap: 16px;
  margin-top: 16px;
}

.editor-panel,
.preview-panel {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.panel-header {
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-panel .el-textarea {
  border: none;
}

.editor-panel .el-textarea :deep(.el-textarea__inner) {
  border: none;
  border-radius: 0;
}

.preview-content {
  padding: 12px;
  margin: 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.5;
  background: #fafafa;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 300px;
  overflow: auto;
}

.preview-error {
  padding: 12px;
  color: #f56c6c;
  font-size: 13px;
}
```

**Step 5: 安装 lodash-es（如果未安装）**

```bash
cd frontend && npm install lodash-es && npm install -D @types/lodash-es
```

**Step 6: Commit**

```bash
git add frontend/src/api/mock.ts frontend/src/views/mock/SuiteEditor.vue frontend/package.json
git commit -m "feat: add mock preview with split-panel layout"
```

---

## Task 4: 对比功能 - 数据模型

**Files:**
- Create: `backend/app/models/mock_compare.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/002_mock_compare_record.py`

**Step 1: 创建数据模型**

```python
# backend/app/models/mock_compare.py
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class MockCompareRecord(Base):
    """对比记录 - 记录 Mock 响应与真实响应的对比结果。"""
    __tablename__ = "mock_compare_records"

    id: int = Column(Integer, primary_key=True, index=True)
    suite_id: int = Column(Integer, ForeignKey("mock_suites.id"), nullable=False, index=True)
    path: str = Column(String(255), nullable=False)
    method: str = Column(String(10), nullable=False)
    mock_response: str = Column(Text)
    real_response: str = Column(Text)
    differences: dict = Column(JSON, default=list)
    is_match: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    suite = relationship("MockSuite", backref="compare_records")
```

**Step 2: 在 __init__.py 中导出**

```python
from app.models.mock_compare import MockCompareRecord
```

**Step 3: 创建迁移脚本**

```python
# backend/alembic/versions/002_mock_compare_record.py
def upgrade():
    op.create_table(
        'mock_compare_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('suite_id', sa.Integer(), nullable=False),
        sa.Column('path', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('mock_response', sa.Text(), nullable=True),
        sa.Column('real_response', sa.Text(), nullable=True),
        sa.Column('differences', sa.JSON(), nullable=True),
        sa.Column('is_match', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['suite_id'], ['mock_suites.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mock_compare_records_id'), 'mock_compare_records', ['id'], unique=False)
    op.create_index(op.f('ix_mock_compare_records_suite_id'), 'mock_compare_records', ['suite_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_mock_compare_records_suite_id'), table_name='mock_compare_records')
    op.drop_index(op.f('ix_mock_compare_records_id'), table_name='mock_compare_records')
    op.drop_table('mock_compare_records')
```

**Step 4: 运行迁移**

```bash
cd backend && alembic upgrade head
```

**Step 5: Commit**

```bash
git add backend/app/models/mock_compare.py backend/app/models/__init__.py backend/alembic/versions/002_mock_compare_record.py
git commit -m "feat: add MockCompareRecord model for compare feature"
```

---

## Task 5: 对比功能 - 后端 API

**Files:**
- Create: `backend/app/schemas/mock_compare.py`
- Modify: `backend/app/services/mock_interceptor.py`
- Create: `backend/app/api/v1/mock_compare.py`
- Modify: `backend/app/main.py` (注册路由)

**Step 1: 创建 Pydantic Schema**

```python
# backend/app/schemas/mock_compare.py
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel


class CompareRequest(BaseModel):
    """手动对比请求"""
    mock_response: str
    real_api_url: str
    real_api_method: str = "GET"
    real_api_headers: Optional[dict] = None
    real_api_body: Optional[str] = None


class CompareResult(BaseModel):
    """对比结果"""
    is_match: bool
    differences: List[dict]


class MockCompareRecordResponse(BaseModel):
    """对比记录响应"""
    id: int
    suite_id: int
    path: str
    method: str
    mock_response: Optional[str]
    real_response: Optional[str]
    differences: List[Any]
    is_match: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MockCompareRecordListResponse(BaseModel):
    """对比记录列表响应"""
    total: int
    items: List[MockCompareRecordResponse]
```

**Step 2: 在 mock_interceptor.py 中添加对比记录保存逻辑**

```python
from app.models.mock_compare import MockCompareRecord

def save_compare_record(
    self,
    suite_id: int,
    path: str,
    method: str,
    mock_response: str,
    real_response: str,
) -> MockCompareRecord:
    """保存对比记录。"""
    from app.services.mock_interceptor import MockCompareTool

    # 执行对比
    result = MockCompareTool.compare_responses(mock_response, real_response)

    record = MockCompareRecord(
        suite_id=suite_id,
        path=path,
        method=method,
        mock_response=mock_response,
        real_response=real_response,
        differences=result["differences"],
        is_match=result["match"],
    )
    self.db.add(record)
    self.db.commit()
    self.db.refresh(record)
    return record
```

**Step 3: 创建对比 API**

```python
# backend/app/api/v1/mock_compare.py
from typing import Optional
import httpx

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.mock_compare import MockCompareRecord
from app.models.mock import MockSuite
from app.services.mock_interceptor import MockCompareTool
from app.schemas.mock_compare import (
    CompareRequest,
    CompareResult,
    MockCompareRecordResponse,
    MockCompareRecordListResponse,
)


router = APIRouter(prefix="/mock/compare", tags=["mock-compare"])


@router.get("/records", response_model=MockCompareRecordListResponse)
def list_compare_records(
    suite_id: Optional[int] = Query(None, description="Filter by suite ID"),
    is_match: Optional[bool] = Query(None, description="Filter by match status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """获取对比记录列表。"""
    query = db.query(MockCompareRecord)

    if suite_id is not None:
        query = query.filter(MockCompareRecord.suite_id == suite_id)
    if is_match is not None:
        query = query.filter(MockCompareRecord.is_match == is_match)

    total = query.count()
    items = query.order_by(MockCompareRecord.created_at.desc()).offset(skip).limit(limit).all()

    return MockCompareRecordListResponse(
        total=total,
        items=[MockCompareRecordResponse.model_validate(item) for item in items],
    )


@router.get("/records/{record_id}", response_model=MockCompareRecordResponse)
def get_compare_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """获取对比记录详情。"""
    record = db.query(MockCompareRecord).filter(MockCompareRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Compare record {record_id} not found")
    return MockCompareRecordResponse.model_validate(record)


@router.post("/manual", response_model=MockCompareRecordResponse)
async def manual_compare(
    request: CompareRequest,
    suite_id: Optional[int] = Query(None, description="Associated suite ID"),
    db: Session = Depends(get_db),
):
    """手动触发对比。"""
    # 请求真实 API
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.real_api_method,
                url=request.real_api_url,
                headers=request.real_api_headers or {},
                content=request.real_api_body,
            )
            real_response = response.text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch real API: {str(e)}")

    # 执行对比
    result = MockCompareTool.compare_responses(request.mock_response, real_response)

    # 保存记录
    record = MockCompareRecord(
        suite_id=suite_id or 0,
        path=request.real_api_url,
        method=request.real_api_method,
        mock_response=request.mock_response,
        real_response=real_response,
        differences=result["differences"],
        is_match=result["match"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return MockCompareRecordResponse.model_validate(record)


@router.delete("/records/{record_id}", status_code=204)
def delete_compare_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """删除对比记录。"""
    record = db.query(MockCompareRecord).filter(MockCompareRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Compare record {record_id} not found")
    db.delete(record)
    db.commit()
    return None
```

**Step 4: 注册路由**

在 `main.py` 中添加：

```python
from app.api.v1 import mock_compare

app.include_router(mock_compare.router, prefix="/api/v1")
```

**Step 5: Commit**

```bash
git add backend/app/schemas/mock_compare.py backend/app/services/mock_interceptor.py backend/app/api/v1/mock_compare.py backend/app/main.py
git commit -m "feat: add compare records API and manual compare endpoint"
```

---

## Task 6: 对比功能 - 前端列表页

**Files:**
- Modify: `frontend/src/api/mock.ts`
- Create: `frontend/src/views/mock/CompareRecords.vue`
- Modify: `frontend/src/router/index.ts`

**Step 1: 添加前端 API**

```typescript
// 在 frontend/src/api/mock.ts 中添加

export interface MockCompareRecord {
  id: number
  suite_id: number
  path: string
  method: string
  mock_response: string | null
  real_response: string | null
  differences: any[]
  is_match: boolean
  created_at: string
}

export interface MockCompareRecordListResponse {
  total: number
  items: MockCompareRecord[]
}

export interface CompareRequest {
  mock_response: string
  real_api_url: string
  real_api_method?: string
  real_api_headers?: Record<string, string>
  real_api_body?: string
}

export const mockApi = {
  // ... 现有方法

  // 对比记录
  getCompareRecords: (params: { suite_id?: number; is_match?: boolean; skip?: number; limit?: number }) =>
    api.get<MockCompareRecordListResponse>('/mock/compare/records', { params }),

  getCompareRecord: (id: number) =>
    api.get<MockCompareRecord>(`/mock/compare/records/${id}`),

  manualCompare: (data: CompareRequest, suiteId?: number) =>
    api.post<MockCompareRecord>('/mock/compare/manual', data, {
      params: suiteId ? { suite_id: suiteId } : {}
    }),

  deleteCompareRecord: (id: number) =>
    api.delete(`/mock/compare/records/${id}`),
}
```

**Step 2: 创建对比记录列表页**

```vue
<!-- frontend/src/views/mock/CompareRecords.vue -->
<template>
  <div class="compare-records-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>对比记录</span>
          <div class="header-actions">
            <el-select v-model="filterSuiteId" placeholder="全部套件" clearable style="width: 200px" @change="fetchData">
              <el-option v-for="suite in suites" :key="suite.id" :label="suite.name" :value="suite.id" />
            </el-select>
            <el-select v-model="filterMatch" placeholder="全部状态" clearable style="width: 120px" @change="fetchData">
              <el-option label="一致" :value="true" />
              <el-option label="有差异" :value="false" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="path" label="路径" min-width="200" show-overflow-tooltip />
        <el-table-column prop="method" label="方法" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_match ? 'success' : 'danger'">
              {{ row.is_match ? '一致' : `差异(${row.differences?.length || 0})` }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="对比时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchData"
          @current-change="fetchData"
        />
      </div>
    </el-card>

    <!-- 对比详情弹窗 -->
    <el-dialog v-model="detailVisible" title="对比详情" width="90%" top="5vh">
      <div v-if="currentRecord" class="compare-detail">
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
        <div v-if="!currentRecord.is_match && currentRecord.differences?.length" class="differences">
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
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { mockApi, type MockCompareRecord, type MockSuite } from '@/api/mock'

const tableData = ref<MockCompareRecord[]>([])
const suites = ref<MockSuite[]>([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const filterSuiteId = ref<number | undefined>()
const filterMatch = ref<boolean | undefined>()

const detailVisible = ref(false)
const currentRecord = ref<MockCompareRecord | null>(null)

const fetchData = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const response = await mockApi.getCompareRecords({
      suite_id: filterSuiteId.value,
      is_match: filterMatch.value,
      skip,
      limit: pageSize.value,
    })
    tableData.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取对比记录失败')
  } finally {
    loading.value = false
  }
}

const fetchSuites = async () => {
  try {
    const response = await mockApi.getSuites(0, 1000)
    suites.value = response.data.items
  } catch (error) {
    console.error('Failed to fetch suites:', error)
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString()
}

const formatJson = (jsonStr: string | null) => {
  if (!jsonStr) return ''
  try {
    return JSON.stringify(JSON.parse(jsonStr), null, 2)
  } catch {
    return jsonStr
  }
}

const handleView = (row: MockCompareRecord) => {
  currentRecord.value = row
  detailVisible.value = true
}

const handleDelete = async (row: MockCompareRecord) => {
  try {
    await ElMessageBox.confirm('确定删除该对比记录？', '确认', { type: 'warning' })
    await mockApi.deleteCompareRecord(row.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchSuites()
  fetchData()
})
</script>

<style scoped>
.compare-records-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.compare-detail {
  padding: 16px 0;
}

.detail-header {
  display: flex;
  gap: 24px;
  align-items: center;
  margin-bottom: 16px;
}

.compare-panels {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.panel {
  flex: 1;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.panel-title {
  padding: 8px 12px;
  background: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  font-weight: 500;
}

.panel-content {
  padding: 12px;
  margin: 0;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.5;
  background: #fafafa;
  max-height: 400px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.differences {
  margin-top: 16px;
}

.diff-title {
  font-weight: 500;
  margin-bottom: 12px;
}
</style>
```

**Step 3: 添加路由**

```typescript
// 在 frontend/src/router/index.ts 中添加
{
  path: '/mock/compare',
  name: 'MockCompare',
  component: () => import('@/views/mock/CompareRecords.vue'),
  meta: { title: '对比记录' }
}
```

**Step 4: Commit**

```bash
git add frontend/src/api/mock.ts frontend/src/views/mock/CompareRecords.vue frontend/src/router/index.ts
git commit -m "feat: add compare records list page"
```

---

## Task 7: 实时对比集成

**Files:**
- Modify: `backend/app/main.py` (中间件)

**Step 1: 在中间件中添加对比逻辑**

修改 `main.py` 中的中间件，当 `enable_compare=True` 时，异步请求真实 API 并保存对比记录：

```python
import asyncio
import httpx
from app.models.mock import MockSuite

@app.middleware("http")
async def mock_interceptor_middleware(request: Request, call_next):
    # ... 现有代码 ...

    if mock_response:
        # 获取套件信息检查是否需要对比
        suite = db.query(MockSuite).filter(
            MockSuite.is_enabled == True
        ).first()  # 简化：实际应根据匹配的规则找到对应套件

        if suite and suite.enable_compare:
            # 异步请求真实 API
            asyncio.create_task(
                compare_and_save(
                    suite.id,
                    request.method,
                    str(request.url.path),
                    mock_response.get("body", "{}"),
                    str(request.url),
                    request.method,
                    dict(request.headers),
                    body,
                )
            )

        # ... 返回 Mock 响应 ...
```

**Step 2: 添加异步对比函数**

```python
async def compare_and_save(
    suite_id: int,
    method: str,
    path: str,
    mock_response: str,
    real_url: str,
    real_method: str,
    headers: dict,
    body: str,
):
    """异步请求真实 API 并保存对比记录。"""
    db = SessionLocal()
    try:
        # 请求真实 API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=real_method,
                url=real_url,
                headers=headers,
                content=body,
            )
            real_response = response.text

        # 保存对比记录
        from app.services.mock_interceptor import MockCompareTool
        result = MockCompareTool.compare_responses(mock_response, real_response)

        record = MockCompareRecord(
            suite_id=suite_id,
            path=path,
            method=method,
            mock_response=mock_response,
            real_response=real_response,
            differences=result["differences"],
            is_match=result["match"],
        )
        db.add(record)
        db.commit()
    except Exception as e:
        print(f"Compare error: {e}")
    finally:
        db.close()
```

**Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: integrate real-time compare in mock middleware"
```

---

## Task 8: Mock 管理页面入口

**Files:**
- Modify: `frontend/src/views/mock/index.vue`

**Step 1: 添加对比记录入口**

在 Mock 套件列表页添加"对比记录"按钮：

```vue
<template #header>
  <div class="card-header">
    <span>Mock 套件</span>
    <div class="header-actions">
      <el-button @click="goToCompare">对比记录</el-button>
      <el-button type="primary" @click="handleCreate">新建套件</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const goToCompare = () => {
  router.push('/mock/compare')
}
</script>

<style scoped>
.header-actions {
  display: flex;
  gap: 12px;
}
</style>
```

**Step 2: Commit**

```bash
git add frontend/src/views/mock/index.vue
git commit -m "feat: add compare records entry in mock suite page"
```

---

## 最终验证

**Step 1: 启动后端**

```bash
cd backend && uvicorn app.main:app --reload
```

**Step 2: 启动前端**

```bash
cd frontend && npm run dev
```

**Step 3: 功能验证清单**

- [ ] Mock 中间件生效（创建 Mock 后请求返回 Mock 响应）
- [ ] 编辑器实时预览（修改 JSON 右侧自动更新）
- [ ] 对比记录列表页可访问
- [ ] 手动对比功能正常
- [ ] 实时对比记录保存正常（enable_compare=True 时）

**Step 4: 最终 Commit**

```bash
git add -A
git commit -m "feat: complete mock module with preview and compare features"
```
