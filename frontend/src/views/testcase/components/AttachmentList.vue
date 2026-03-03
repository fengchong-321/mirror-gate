<template>
  <div class="attachment-list">
    <!-- Upload Area -->
    <div class="upload-area">
      <el-upload
        ref="uploadRef"
        :action="uploadUrl"
        :headers="uploadHeaders"
        :data="{ case_id: caseId }"
        :multiple="true"
        :drag="true"
        :show-file-list="false"
        :before-upload="beforeUpload"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :on-progress="handleUploadProgress"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持常见文件格式，单文件最大 10MB
          </div>
        </template>
      </el-upload>
    </div>

    <!-- Upload Progress -->
    <div v-if="uploadingFiles.length > 0" class="upload-progress">
      <div v-for="file in uploadingFiles" :key="file.uid" class="progress-item">
        <div class="progress-info">
          <span class="file-name">{{ file.name }}</span>
          <span class="progress-text">{{ file.progress }}%</span>
        </div>
        <el-progress :percentage="file.progress" :status="file.status" />
      </div>
    </div>

    <!-- Attachment Table -->
    <div class="attachment-table">
      <el-table
        v-loading="loading"
        :data="attachments"
        border
        style="width: 100%"
      >
        <el-table-column prop="filename" label="文件名" min-width="200">
          <template #default="{ row }">
            <span
              :class="{ 'filename-link': isImage(row.filename) }"
              @click="isImage(row.filename) && handlePreview(row)"
            >
              <el-icon v-if="isImage(row.filename)" class="file-icon"><Picture /></el-icon>
              <el-icon v-else class="file-icon"><Document /></el-icon>
              {{ row.filename }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="file_type" label="类型" width="120">
          <template #default="{ row }">
            {{ row.file_type || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_by" label="上传者" width="120">
          <template #default="{ row }">
            {{ row.uploaded_by || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_at" label="上传时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.uploaded_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleDownload(row)">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button type="danger" size="small" link @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && attachments.length === 0" description="暂无附件" />
    </div>

    <!-- Image Preview Dialog -->
    <el-dialog
      v-model="previewVisible"
      title="图片预览"
      width="800px"
      destroy-on-close
    >
      <div class="preview-container">
        <img :src="previewUrl" :alt="previewFilename" class="preview-image" />
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="handleDownloadPreview">下载</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox, UploadFile, UploadInstance } from 'element-plus'
import { UploadFilled, Picture, Document, Download, Delete } from '@element-plus/icons-vue'
import {
  testcaseApi,
  type TestCaseAttachment
} from '@/api/testcase'

// Props
const props = defineProps<{
  caseId: number
}>()

// Refs
const uploadRef = ref<UploadInstance>()
const loading = ref(false)
const attachments = ref<TestCaseAttachment[]>([])

// Upload state
const uploadingFiles = ref<Array<{
  uid: number
  name: string
  progress: number
  status: '' | 'success' | 'exception' | 'warning'
}>>([])

// Preview state
const previewVisible = ref(false)
const previewUrl = ref('')
const previewFilename = ref('')
const previewAttachment = ref<TestCaseAttachment | null>(null)

// Upload configuration
const uploadUrl = computed(() => `/api/v1/testcase/cases/${props.caseId}/attachments/upload`)

const uploadHeaders = computed(() => {
  // Get token from localStorage or store
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
})

// Load attachments
const loadAttachments = async () => {
  if (!props.caseId) return

  loading.value = true
  try {
    const response = await testcaseApi.getAttachments(props.caseId)
    attachments.value = response.data
  } catch (error) {
    ElMessage.error('加载附件列表失败')
  } finally {
    loading.value = false
  }
}

// Before upload validation
const beforeUpload = (file: File) => {
  const maxSize = 10 * 1024 * 1024 // 10MB

  if (file.size > maxSize) {
    ElMessage.error(`文件 ${file.name} 超过 10MB 限制`)
    return false
  }

  // Add to uploading list
  uploadingFiles.value.push({
    uid: file.uid,
    name: file.name,
    progress: 0,
    status: ''
  })

  return true
}

// Handle upload progress
const handleUploadProgress = (event: { percent: number }, file: File) => {
  const uploadingFile = uploadingFiles.value.find(f => f.uid === file.uid)
  if (uploadingFile) {
    uploadingFile.progress = Math.round(event.percent)
  }
}

// Handle upload success
const handleUploadSuccess = (response: any, file: File) => {
  const uploadingFile = uploadingFiles.value.find(f => f.uid === file.uid)
  if (uploadingFile) {
    uploadingFile.progress = 100
    uploadingFile.status = 'success'
  }

  // Remove from uploading list after delay
  setTimeout(() => {
    uploadingFiles.value = uploadingFiles.value.filter(f => f.uid !== file.uid)
  }, 1000)

  ElMessage.success(`文件 ${file.name} 上传成功`)
  loadAttachments()
}

// Handle upload error
const handleUploadError = (error: Error, file: File) => {
  const uploadingFile = uploadingFiles.value.find(f => f.uid === file.uid)
  if (uploadingFile) {
    uploadingFile.status = 'exception'
  }

  // Remove from uploading list after delay
  setTimeout(() => {
    uploadingFiles.value = uploadingFiles.value.filter(f => f.uid !== file.uid)
  }, 2000)

  ElMessage.error(`文件 ${file.name} 上传失败`)
  console.error('Upload error:', error)
}

// Handle preview
const handlePreview = (attachment: TestCaseAttachment) => {
  previewUrl.value = testcaseApi.getAttachmentDownloadUrl(attachment.id)
  previewFilename.value = attachment.filename
  previewAttachment.value = attachment
  previewVisible.value = true
}

// Handle download
const handleDownload = (attachment: TestCaseAttachment) => {
  const url = testcaseApi.getAttachmentDownloadUrl(attachment.id)
  const link = document.createElement('a')
  link.href = url
  link.download = attachment.filename
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Handle download preview image
const handleDownloadPreview = () => {
  if (previewAttachment.value) {
    handleDownload(previewAttachment.value)
  }
}

// Handle delete
const handleDelete = async (attachment: TestCaseAttachment) => {
  try {
    await ElMessageBox.confirm(
      `确定删除文件 "${attachment.filename}" 吗？删除后无法恢复。`,
      '确认删除',
      { type: 'warning' }
    )

    await testcaseApi.deleteAttachment(attachment.id)
    ElMessage.success('删除成功')
    loadAttachments()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// Format file size
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

// Check if file is image
const isImage = (filename: string): boolean => {
  const ext = filename.toLowerCase().split('.').pop()
  return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext || '')
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

// Watch caseId changes
watch(() => props.caseId, (newId) => {
  if (newId) {
    loadAttachments()
  }
}, { immediate: true })

// Initialize
onMounted(() => {
  if (props.caseId) {
    loadAttachments()
  }
})
</script>

<style scoped>
.attachment-list {
  padding: 0 20px;
}

.upload-area {
  margin-bottom: 24px;
}

.upload-area :deep(.el-upload-dragger) {
  padding: 30px;
}

.upload-area :deep(.el-icon--upload) {
  font-size: 48px;
  color: var(--el-color-primary);
  margin-bottom: 16px;
}

.upload-area :deep(.el-upload__text) {
  color: var(--el-text-color-regular);
}

.upload-area :deep(.el-upload__text em) {
  color: var(--el-color-primary);
  font-style: normal;
}

.upload-area :deep(.el-upload__tip) {
  color: var(--el-text-color-secondary);
  margin-top: 8px;
}

.upload-progress {
  margin-bottom: 24px;
  padding: 16px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
}

.progress-item {
  margin-bottom: 12px;
}

.progress-item:last-child {
  margin-bottom: 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.file-name {
  font-size: 13px;
  color: var(--el-text-color-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 80%;
}

.progress-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.attachment-table {
  min-height: 200px;
}

.filename-link {
  color: var(--el-color-primary);
  cursor: pointer;
}

.filename-link:hover {
  text-decoration: underline;
}

.file-icon {
  margin-right: 6px;
  vertical-align: middle;
}

.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  max-height: 500px;
  overflow: auto;
}

.preview-image {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
}
</style>
