<template>
  <el-config-provider :locale="zhCn">
    <!-- Login page without layout -->
    <router-view v-if="!isAuthenticated || isLoginPage" />

    <!-- Main layout with sidebar -->
    <el-container v-else class="app-container">
      <el-aside width="200px" class="app-aside">
        <div class="logo">
          <h2>MirrorGate</h2>
        </div>
        <el-menu
          :default-active="currentRoute"
          router
          class="app-menu"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/mock">
            <el-icon><Document /></el-icon>
            <span>Mock管理</span>
          </el-menu-item>
          <el-menu-item index="/api-test">
            <el-icon><Connection /></el-icon>
            <span>接口测试</span>
          </el-menu-item>
          <el-menu-item index="/ui-test">
            <el-icon><Monitor /></el-icon>
            <span>UI测试</span>
          </el-menu-item>
          <el-menu-item index="/testcase">
            <el-icon><Tickets /></el-icon>
            <span>用例管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-container>
        <el-header class="app-header">
          <div class="header-content">
            <span class="page-title">{{ pageTitle }}</span>
            <div class="user-info">
              <el-dropdown trigger="click">
                <span class="user-dropdown">
                  <el-icon><User /></el-icon>
                  <span>{{ authStore.user?.username }}</span>
                  <el-tag size="small" :type="roleTagType">{{ roleLabel }}</el-tag>
                </span>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="handleChangePassword">
                      <el-icon><Key /></el-icon>
                      修改密码
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="handleLogout">
                      <el-icon><SwitchButton /></el-icon>
                      退出登录
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </el-header>
        <el-main class="app-main">
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <!-- Change Password Dialog -->
    <el-dialog v-model="showChangePassword" title="修改密码" width="400px">
      <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="REDACTED" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="REDACTED" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="REDACTED" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePassword = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="submitChangePassword">
          确定
        </el-button>
      </template>
    </el-dialog>
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { House, Document, Connection, Monitor, User, Key, SwitchButton, Tickets } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const isLoginPage = computed(() => route.name === 'Login')
const currentRoute = computed(() => route.path)

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    Dashboard: '仪表盘',
    Mock: 'Mock管理',
    ApiTest: '接口测试',
    UiTest: 'UI测试',
    TestCase: '用例管理',
    TestCaseCreate: '新建用例',
    TestCaseEdit: '编辑用例',
    TestCaseDetail: '用例详情'
  }
  return titles[route.name as string] || 'MirrorGate'
})

const roleLabel = computed(() => {
  const labels: Record<string, string> = {
    admin: '管理员',
    tester: '测试员',
    viewer: '访客'
  }
  return labels[authStore.user?.role || ''] || '用户'
})

const roleTagType = computed(() => {
  const types: Record<string, string> = {
    admin: 'danger',
    tester: 'success',
    viewer: 'info'
  }
  return types[authStore.user?.role || ''] || 'info'
})

// Change password
const showChangePassword = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const passwordRules: FormRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6个字符', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

function handleChangePassword() {
  passwordForm.old_password = ''
  passwordForm.new_password = ''
  passwordForm.confirm_password = ''
  showChangePassword.value = true
}

async function submitChangePassword() {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return

  passwordLoading.value = true
  try {
    await authApi.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success('密码修改成功，请重新登录')
    showChangePassword.value = false
    handleLogout()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    passwordLoading.value = false
  }
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await authStore.logout()
    router.push('/login')
  } catch {
    // Cancelled
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.app-container {
  height: 100%;
}

.app-aside {
  background-color: #304156;
  color: #fff;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
}

.logo h2 {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.app-menu {
  border-right: none;
  background-color: #304156;
}

.app-menu .el-menu-item {
  color: #bfcbd9;
}

.app-menu .el-menu-item:hover {
  background-color: #263445;
}

.app-menu .el-menu-item.is-active {
  color: #409eff;
  background-color: #263445;
}

.app-header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  padding: 0 20px;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
  color: #303133;
}

.user-info {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.app-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
