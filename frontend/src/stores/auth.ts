import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type User, type LoginRequest, type RegisterRequest } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(credentials: LoginRequest) {
    const response = await authApi.login(credentials)
    const data = response.data

    token.value = data.access_token
    refreshToken.value = data.refresh_token
    user.value = data.user

    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))

    return data
  }

  async function register(userData: RegisterRequest) {
    const response = await authApi.register(userData)
    return response.data
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch (e) {
      // Ignore logout errors
    }

    token.value = null
    refreshToken.value = null
    user.value = null

    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  async function fetchCurrentUser() {
    if (!token.value) return null

    try {
      const response = await authApi.getCurrentUser()
      user.value = response.data
      return response.data
    } catch (e) {
      logout()
      return null
    }
  }

  function initFromStorage() {
    const storedUser = localStorage.getItem('user')
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
      } catch (e) {
        // Invalid JSON, clear storage
        logout()
      }
    }
  }

  // Initialize from storage
  initFromStorage()

  return {
    user,
    token,
    refreshToken,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    fetchCurrentUser
  }
})
