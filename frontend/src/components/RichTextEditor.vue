<template>
  <div class="rich-text-editor" :class="{ 'is-disabled': disabled }">
    <div v-if="!disabled" class="toolbar">
      <el-button-group>
        <el-button
          size="small"
          :type="editor?.isActive('bold') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleBold().run()"
          title="加粗"
        >
          <el-icon><Bold /></el-icon>
        </el-button>
        <el-button
          size="small"
          :type="editor?.isActive('italic') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleItalic().run()"
          title="斜体"
        >
          <el-icon><Italic /></el-icon>
        </el-button>
        <el-button
          size="small"
          :type="editor?.isActive('underline') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleUnderline().run()"
          title="下划线"
        >
          <el-icon><UnderlineIcon /></el-icon>
        </el-button>
        <el-button
          size="small"
          :type="editor?.isActive('strike') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleStrike().run()"
          title="删除线"
        >
          <el-icon><Strikethrough /></el-icon>
        </el-button>
      </el-button-group>

      <el-divider direction="vertical" />

      <el-button-group>
        <el-button
          size="small"
          :type="editor?.isActive('heading', { level: 1 }) ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleHeading({ level: 1 }).run()"
          title="标题1"
        >
          H1
        </el-button>
        <el-button
          size="small"
          :type="editor?.isActive('heading', { level: 2 }) ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()"
          title="标题2"
        >
          H2
        </el-button>
        <el-button
          size="small"
          :type="editor?.isActive('heading', { level: 3 }) ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()"
          title="标题3"
        >
          H3
        </el-button>
      </el-button-group>

      <el-divider direction="vertical" />

      <el-button-group>
        <el-button
          size="small"
          :type="editor?.isActive('orderedList') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleOrderedList().run()"
          title="有序列表"
        >
          <el-icon><List /></el-icon>
        </el-button>
        <el-button
          size="small"
          :type="editor?.isActive('bulletList') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleBulletList().run()"
          title="无序列表"
        >
          <el-icon><Menu /></el-icon>
        </el-button>
        <el-button
          size="small"
          :type="editor?.isActive('codeBlock') ? 'primary' : 'default'"
          @click="editor?.chain().focus().toggleCodeBlock().run()"
          title="代码块"
        >
          <el-icon><Document /></el-icon>
        </el-button>
      </el-button-group>

      <el-divider direction="vertical" />

      <el-button-group>
        <el-button
          size="small"
          :type="editor?.isActive('link') ? 'primary' : 'default'"
          @click="setLink"
          title="链接"
        >
          <el-icon><LinkIcon /></el-icon>
        </el-button>
        <el-button
          size="small"
          @click="setImage"
          title="图片"
        >
          <el-icon><Picture /></el-icon>
        </el-button>
      </el-button-group>
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
import Underline from '@tiptap/extension-underline'
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  List,
  Menu,
  Document,
  Link as LinkIcon,
  Picture
} from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: string
  placeholder?: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const isDisabled = computed(() => props.disabled)

const editor = useEditor({
  content: props.modelValue,
  editable: !isDisabled.value,
  extensions: [
    StarterKit.configure({
      heading: {
        levels: [1, 2, 3]
      }
    }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: {
        target: '_blank',
        rel: 'noopener noreferrer'
      }
    }),
    Image.configure({
      inline: true,
      allowBase64: true
    }),
    Placeholder.configure({
      placeholder: props.placeholder || '请输入内容...'
    }),
    Underline
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  }
})

watch(
  () => props.modelValue,
  (newValue) => {
    if (editor.value && editor.value.getHTML() !== newValue) {
      editor.value.commands.setContent(newValue, false)
    }
  }
)

watch(
  () => props.disabled,
  (newDisabled) => {
    if (editor.value) {
      editor.value.setEditable(!newDisabled)
    }
  }
)

onBeforeUnmount(() => {
  editor.value?.destroy()
})

const setLink = async () => {
  if (!editor.value) return

  const previousUrl = editor.value.getAttributes('link').href || ''

  try {
    const { value } = await ElMessageBox.prompt('请输入链接地址', '插入链接', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: previousUrl,
      inputPattern: /^https?:\/\/.+/,
      inputErrorMessage: '请输入有效的URL地址（以http://或https://开头）'
    })

    if (value) {
      editor.value.chain().focus().extendMarkRange('link').setLink({ href: value }).run()
    }
  } catch {
    // User cancelled
  }
}

const setImage = async () => {
  if (!editor.value) return

  try {
    const { value } = await ElMessageBox.prompt('请输入图片地址', '插入图片', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^https?:\/\/.+/,
      inputErrorMessage: '请输入有效的URL地址（以http://或https://开头）'
    })

    if (value) {
      editor.value.chain().focus().setImage({ src: value }).run()
    }
  } catch {
    // User cancelled
  }
}
</script>

<style scoped>
.rich-text-editor {
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
  background-color: var(--el-bg-color);
  transition: border-color 0.2s;
}

.rich-text-editor:hover {
  border-color: var(--el-border-color-hover);
}

.rich-text-editor:focus-within {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 2px var(--el-color-primary-light-7);
}

.rich-text-editor.is-disabled {
  background-color: var(--el-disabled-bg-color);
  cursor: not-allowed;
}

.rich-text-editor.is-disabled .editor-content {
  color: var(--el-disabled-text-color);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px;
  border-bottom: 1px solid var(--el-border-color);
  background-color: var(--el-fill-color-light);
  border-radius: var(--el-border-radius-base) var(--el-border-radius-base) 0 0;
  flex-wrap: wrap;
}

.toolbar :deep(.el-button-group) {
  display: flex;
}

.toolbar :deep(.el-button) {
  padding: 5px 8px;
}

.toolbar :deep(.el-divider--vertical) {
  height: 20px;
  margin: 0 4px;
}

.editor-content {
  padding: 12px;
  min-height: 120px;
}

.editor-content :deep(.tiptap) {
  outline: none;
  min-height: 96px;
  line-height: 1.6;
}

.editor-content :deep(.tiptap p.is-editor-empty:first-child::before) {
  color: var(--el-text-color-placeholder);
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
}

.editor-content :deep(.tiptap h1) {
  font-size: 2em;
  font-weight: bold;
  margin: 0.5em 0;
}

.editor-content :deep(.tiptap h2) {
  font-size: 1.5em;
  font-weight: bold;
  margin: 0.5em 0;
}

.editor-content :deep(.tiptap h3) {
  font-size: 1.25em;
  font-weight: bold;
  margin: 0.5em 0;
}

.editor-content :deep(.tiptap ul),
.editor-content :deep(.tiptap ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.editor-content :deep(.tiptap ul) {
  list-style-type: disc;
}

.editor-content :deep(.tiptap ol) {
  list-style-type: decimal;
}

.editor-content :deep(.tiptap pre) {
  background-color: var(--el-fill-color-dark);
  border-radius: var(--el-border-radius-base);
  padding: 12px;
  font-family: monospace;
  overflow-x: auto;
}

.editor-content :deep(.tiptap code) {
  background-color: var(--el-fill-color-dark);
  padding: 2px 4px;
  border-radius: 4px;
  font-family: monospace;
}

.editor-content :deep(.tiptap a) {
  color: var(--el-color-primary);
  text-decoration: underline;
  cursor: pointer;
}

.editor-content :deep(.tiptap a:hover) {
  color: var(--el-color-primary-light-3);
}

.editor-content :deep(.tiptap img) {
  max-width: 100%;
  height: auto;
  border-radius: var(--el-border-radius-base);
  margin: 8px 0;
}

.editor-content :deep(.tiptap p) {
  margin: 0.5em 0;
}

.editor-content :deep(.tiptap strong) {
  font-weight: bold;
}

.editor-content :deep(.tiptap em) {
  font-style: italic;
}

.editor-content :deep(.tiptap u) {
  text-decoration: underline;
}

.editor-content :deep(.tiptap s) {
  text-decoration: line-through;
}
</style>
