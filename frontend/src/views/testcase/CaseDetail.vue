<template>
  <div class="case-detail" v-loading="loading">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <el-button link @click="handleBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <span class="title">{{ caseData?.title || '用例详情' }}</span>
      </div>
      <div class="header-right">
        <el-button @click="handleEdit">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button @click="handleCopy">
          <el-icon><CopyDocument /></el-icon>
          复制
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <!-- Basic Info Card -->
    <el-card class="info-card" shadow="never">
      <template #header>
        <span class="card-title">基本信息</span>
      </template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="用例编号">
          {{ caseData?.code || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="用例类型">
          <el-tag size="small" :type="getCaseTypeTag(caseData?.case_type)">
            {{ getCaseTypeText(caseData?.case_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="所属平台">
          <el-tag size="small" :type="getPlatformTag(caseData?.platform)">
            {{ getPlatformText(caseData?.platform) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="优先级">
          <el-tag size="small" :type="getPriorityTag(caseData?.priority)">
            {{ getPriorityText(caseData?.priority) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag size="small" :type="getStatusTag(caseData?.status)">
            {{ getStatusText(caseData?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="维护人">
          {{ caseData?.created_by || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建人">
          {{ caseData?.created_by || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(caseData?.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ formatDateTime(caseData?.updated_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- Tab Area -->
    <el-card class="tab-card" shadow="never">
      <el-tabs v-model="activeTab">
        <!-- Detail Tab -->
        <el-tab-pane label="详情" name="detail">
          <div class="detail-content">
            <div class="detail-section">
              <div class="section-label">页面地址</div>
              <div class="section-value">{{ caseData?.page_url || '-' }}</div>
            </div>
            <div class="detail-section">
              <div class="section-label">前置条件</div>
              <div class="section-value pre-wrap">{{ caseData?.preconditions || '-' }}</div>
            </div>
            <div class="detail-section">
              <div class="section-label">测试步骤</div>
              <el-table
                v-if="caseData?.steps && caseData.steps.length > 0"
                :data="caseData.steps"
                border
                style="width: 100%"
              >
                <el-table-column type="index" label="序号" width="60" />
                <el-table-column prop="step" label="步骤描述" min-width="300" />
                <el-table-column prop="expected" label="预期结果" min-width="300" />
              </el-table>
              <div v-else class="section-value">-</div>
            </div>
            <div class="detail-section">
              <div class="section-label">预期结果</div>
              <div class="section-value pre-wrap">{{ caseData?.expected_result || '-' }}</div>
            </div>
            <div class="detail-section">
              <div class="section-label">备注</div>
              <div class="section-value pre-wrap">{{ caseData?.remark || '-' }}</div>
            </div>
            <div class="detail-section">
              <div class="section-label">标签</div>
              <div class="section-value">
                <template v-if="caseData?.tags && caseData.tags.length > 0">
                  <el-tag
                    v-for="tag in caseData.tags"
                    :key="tag"
                    class="tag-item"
                  >
                    {{ tag }}
                  </el-tag>
                </template>
                <span v-else>-</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- Attachment Tab -->
        <el-tab-pane label="附件" name="attachment">
          <AttachmentList :case-id="caseId!" />
        </el-tab-pane>

        <!-- Comment Tab -->
        <el-tab-pane label="评论" name="comment">
          <div class="comment-content">
            <!-- Add Comment -->
            <div class="add-comment">
              <el-input
                v-model="newComment"
                type="textarea"
                :rows="3"
                placeholder="请输入评论内容..."
                maxlength="500"
                show-word-limit
              />
              <el-button
                type="primary"
                :loading="submittingComment"
                :disabled="!newComment.trim()"
                @click="handleAddComment"
              >
                发表评论
              </el-button>
            </div>

            <!-- Comment List -->
            <div class="comment-list">
              <template v-if="comments.length > 0">
                <div
                  v-for="comment in comments"
                  :key="comment.id"
                  class="comment-item"
                >
                  <div class="comment-avatar">
                    <el-avatar :size="36">{{ comment.created_by?.charAt(0)?.toUpperCase() }}</el-avatar>
                  </div>
                  <div class="comment-body">
                    <div class="comment-header">
                      <span class="comment-author">{{ comment.created_by }}</span>
                      <span class="comment-time">{{ formatDateTime(comment.created_at) }}</span>
                    </div>
                    <div class="comment-text pre-wrap">{{ comment.content }}</div>
                    <div class="comment-actions">
                      <el-button
                        type="primary"
                        size="small"
                        link
                        @click="handleReply(comment)"
                      >
                        回复
                      </el-button>
                      <el-button
                        type="danger"
                        size="small"
                        link
                        @click="handleDeleteComment(comment)"
                      >
                        删除
                      </el-button>
                    </div>

                    <!-- Reply Input -->
                    <div v-if="replyingTo === comment.id" class="reply-input">
                      <el-input
                        v-model="replyContent"
                        type="textarea"
                        :rows="2"
                        :placeholder="`回复 ${comment.created_by}...`"
                      />
                      <div class="reply-actions">
                        <el-button size="small" @click="cancelReply">取消</el-button>
                        <el-button
                          type="primary"
                          size="small"
                          :loading="submittingReply"
                          :disabled="!replyContent.trim()"
                          @click="handleAddReply(comment)"
                        >
                          回复
                        </el-button>
                      </div>
                    </div>

                    <!-- Nested Replies -->
                    <div v-if="comment.replies && comment.replies.length > 0" class="replies">
                      <div
                        v-for="reply in comment.replies"
                        :key="reply.id"
                        class="reply-item"
                      >
                        <div class="reply-avatar">
                          <el-avatar :size="28">{{ reply.created_by?.charAt(0)?.toUpperCase() }}</el-avatar>
                        </div>
                        <div class="reply-body">
                          <div class="reply-header">
                            <span class="reply-author">{{ reply.created_by }}</span>
                            <span class="reply-time">{{ formatDateTime(reply.created_at) }}</span>
                          </div>
                          <div class="reply-text pre-wrap">{{ reply.content }}</div>
                          <div class="reply-actions">
                            <el-button
                              type="danger"
                              size="small"
                              link
                              @click="handleDeleteComment(reply)"
                            >
                              删除
                            </el-button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
              <el-empty v-else description="暂无评论" />
            </div>
          </div>
        </el-tab-pane>

        <!-- History Tab -->
        <el-tab-pane label="变更历史" name="history">
          <div class="history-content">
            <template v-if="history.length > 0">
              <el-timeline>
                <el-timeline-item
                  v-for="item in history"
                  :key="item.id"
                  :timestamp="formatDateTime(item.changed_at)"
                  placement="top"
                >
                  <el-card class="history-card" shadow="never">
                    <div class="history-item">
                      <div class="history-field">
                        <span class="field-label">字段：</span>
                        <span class="field-name">{{ getFieldText(item.field_name) }}</span>
                      </div>
                      <div class="history-change">
                        <span class="old-value">{{ item.old_value || '(空)' }}</span>
                        <el-icon class="arrow"><Right /></el-icon>
                        <span class="new-value">{{ item.new_value || '(空)' }}</span>
                      </div>
                      <div class="history-user">
                        操作人：{{ item.changed_by }}
                      </div>
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </template>
            <el-empty v-else description="暂无变更历史" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Edit, CopyDocument, Delete, Right } from '@element-plus/icons-vue'
import {
  testcaseApi,
  type TestCaseDetail,
  type TestCaseComment,
  type TestCaseHistory
} from '@/api/testcase'
import AttachmentList from './components/AttachmentList.vue'

const route = useRoute()
const router = useRouter()

// Route params
const caseId = computed(() => {
  const id = route.params.id
  return id ? parseInt(id as string) : null
})

// State
const loading = ref(false)
const activeTab = ref('detail')
const caseData = ref<TestCaseDetail | null>(null)
const comments = ref<TestCaseComment[]>([])
const history = ref<TestCaseHistory[]>([])

// Comment state
const newComment = ref('')
const submittingComment = ref(false)
const replyingTo = ref<number | null>(null)
const replyContent = ref('')
const submittingReply = ref(false)

// Load case detail
const loadCaseDetail = async () => {
  if (!caseId.value) return

  loading.value = true
  try {
    const response = await testcaseApi.getCase(caseId.value)
    caseData.value = response.data
    comments.value = response.data.comments || []
    history.value = response.data.history || []
  } catch (error) {
    ElMessage.error('加载用例详情失败')
    router.push('/testcase')
  } finally {
    loading.value = false
  }
}

// Load comments
const loadComments = async () => {
  if (!caseId.value) return

  try {
    const response = await testcaseApi.getComments(caseId.value)
    comments.value = response.data
  } catch (error) {
    ElMessage.error('加载评论失败')
  }
}

// Handle back
const handleBack = () => {
  router.push('/testcase')
}

// Handle edit
const handleEdit = () => {
  router.push(`/testcase/${caseId.value}/edit`)
}

// Handle copy
const handleCopy = async () => {
  if (!caseData.value) return

  try {
    await ElMessageBox.confirm(
      `确定复制用例 "${caseData.value.title}" 吗？`,
      '确认复制',
      { type: 'info' }
    )
    await testcaseApi.copyCase(caseId.value!)
    ElMessage.success('复制成功')
    router.push('/testcase')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('复制失败')
    }
  }
}

// Handle delete
const handleDelete = async () => {
  if (!caseData.value) return

  try {
    await ElMessageBox.confirm(
      `确定删除用例 "${caseData.value.title}" 吗？删除后无法恢复。`,
      '确认删除',
      { type: 'warning' }
    )
    await testcaseApi.deleteCase(caseId.value!)
    ElMessage.success('删除成功')
    router.push('/testcase')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// Handle add comment
const handleAddComment = async () => {
  if (!caseId.value || !newComment.value.trim()) return

  submittingComment.value = true
  try {
    await testcaseApi.addComment(caseId.value, { content: newComment.value.trim() })
    ElMessage.success('评论成功')
    newComment.value = ''
    loadComments()
  } catch (error) {
    ElMessage.error('评论失败')
  } finally {
    submittingComment.value = false
  }
}

// Handle reply
const handleReply = (comment: TestCaseComment) => {
  replyingTo.value = comment.id
  replyContent.value = ''
}

// Cancel reply
const cancelReply = () => {
  replyingTo.value = null
  replyContent.value = ''
}

// Handle add reply
const handleAddReply = async (parentComment: TestCaseComment) => {
  if (!caseId.value || !replyContent.value.trim()) return

  submittingReply.value = true
  try {
    await testcaseApi.addComment(caseId.value, {
      content: replyContent.value.trim(),
      parent_id: parentComment.id
    })
    ElMessage.success('回复成功')
    replyContent.value = ''
    replyingTo.value = null
    loadComments()
  } catch (error) {
    ElMessage.error('回复失败')
  } finally {
    submittingReply.value = false
  }
}

// Handle delete comment
const handleDeleteComment = async (comment: TestCaseComment) => {
  try {
    await ElMessageBox.confirm(
      '确定删除该评论吗？',
      '确认删除',
      { type: 'warning' }
    )
    await testcaseApi.deleteComment(comment.id)
    ElMessage.success('删除成功')
    loadComments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// Format datetime
const formatDateTime = (datetime?: string) => {
  if (!datetime) return '-'
  const date = new Date(datetime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Tag helpers
const getCaseTypeTag = (type?: string) => {
  const types: Record<string, string> = {
    'functional': 'primary',
    'api': 'warning',
    'ui': 'success',
    'performance': 'danger',
    'security': 'danger'
  }
  return types[type || ''] || 'info'
}

const getCaseTypeText = (type?: string) => {
  const texts: Record<string, string> = {
    'functional': '功能测试',
    'api': 'API测试',
    'ui': 'UI测试',
    'performance': '性能测试',
    'security': '安全测试'
  }
  return texts[type || ''] || type || '-'
}

const getPlatformTag = (platform?: string) => {
  const types: Record<string, string> = {
    'web': 'primary',
    'ios': '',
    'android': 'success',
    'mini_program': 'warning'
  }
  return types[platform || ''] || 'info'
}

const getPlatformText = (platform?: string) => {
  const texts: Record<string, string> = {
    'web': 'Web',
    'ios': 'iOS',
    'android': 'Android',
    'mini_program': '小程序'
  }
  return texts[platform || ''] || platform || '-'
}

const getPriorityTag = (priority?: string) => {
  const types: Record<string, string> = {
    'critical': 'danger',
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return types[priority || ''] || 'info'
}

const getPriorityText = (priority?: string) => {
  const texts: Record<string, string> = {
    'critical': '严重',
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return texts[priority || ''] || priority || '-'
}

const getStatusTag = (status?: string) => {
  const types: Record<string, string> = {
    'draft': 'info',
    'active': 'success',
    'deprecated': 'warning'
  }
  return types[status || ''] || 'info'
}

const getStatusText = (status?: string) => {
  const texts: Record<string, string> = {
    'draft': '草稿',
    'active': '激活',
    'deprecated': '废弃'
  }
  return texts[status || ''] || status || '-'
}

const getFieldText = (fieldName: string) => {
  const texts: Record<string, string> = {
    'title': '标题',
    'case_type': '用例类型',
    'platform': '所属平台',
    'priority': '优先级',
    'status': '状态',
    'preconditions': '前置条件',
    'steps': '测试步骤',
    'expected_result': '预期结果',
    'tags': '标签',
    'page_url': '页面地址',
    'remark': '备注'
  }
  return texts[fieldName] || fieldName
}

// Initialize
onMounted(() => {
  if (!caseId.value) {
    ElMessage.warning('用例ID不存在')
    router.push('/testcase')
    return
  }
  loadCaseDetail()
})
</script>

<style scoped>
.case-detail {
  padding: 20px;
  min-height: calc(100vh - 100px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.info-card {
  margin-bottom: 20px;
}

.card-title {
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.tab-card {
  min-height: 400px;
}

.detail-content {
  padding: 0 20px;
}

.detail-section {
  margin-bottom: 24px;
}

.section-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}

.section-value {
  color: var(--el-text-color-primary);
  line-height: 1.6;
}

.pre-wrap {
  white-space: pre-wrap;
  word-break: break-word;
}

.tag-item {
  margin-right: 8px;
  margin-bottom: 8px;
}

.comment-content {
  padding: 0 20px;
}

.add-comment {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--el-border-color);
}

.add-comment .el-textarea {
  margin-bottom: 12px;
}

.comment-list {
  min-height: 200px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-body {
  flex: 1;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.comment-author {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.comment-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.comment-text {
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin-bottom: 8px;
}

.comment-actions {
  display: flex;
  gap: 16px;
}

.reply-input {
  margin-top: 12px;
  padding: 12px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.reply-input .el-textarea {
  margin-bottom: 8px;
}

.reply-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.replies {
  margin-top: 16px;
  padding-left: 20px;
  border-left: 2px solid var(--el-border-color-lighter);
}

.reply-item {
  display: flex;
  gap: 8px;
  padding: 12px 0;
}

.reply-body {
  flex: 1;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.reply-author {
  font-weight: 500;
  font-size: 13px;
  color: var(--el-text-color-primary);
}

.reply-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.reply-text {
  font-size: 13px;
  color: var(--el-text-color-regular);
  line-height: 1.5;
}

.reply-actions {
  margin-top: 4px;
}

.history-content {
  padding: 0 20px;
}

.history-card {
  margin-bottom: 0;
}

.history-item {
  padding: 8px 0;
}

.history-field {
  margin-bottom: 8px;
}

.field-label {
  color: var(--el-text-color-secondary);
}

.field-name {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.history-change {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.old-value {
  color: var(--el-color-danger);
  text-decoration: line-through;
}

.new-value {
  color: var(--el-color-success);
}

.arrow {
  color: var(--el-text-color-secondary);
}

.history-user {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

:deep(.el-timeline-item__timestamp) {
  color: var(--el-text-color-secondary);
}
</style>
