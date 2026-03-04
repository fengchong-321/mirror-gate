import http from './http'

export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
  role: 'admin' | 'tester' | 'viewer'
  is_active: boolean
  created_at: string
  updated_at: string
  last_login_at: string | null
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface UserListResponse {
  total: number
  items: User[]
}

export const authApi = {
  // Login
  login(data: LoginRequest) {
    return http.post<LoginResponse>('/auth/login', data)
  },

  // Register
  register(data: RegisterRequest) {
    return http.post<User>('/auth/register', data)
  },

  // Logout
  logout() {
    return http.post('/auth/logout')
  },

  // Refresh token
  refreshToken(refreshToken: string) {
    return http.post('/auth/refresh', { refresh_token: refreshToken })
  },

  // Get current user
  getCurrentUser() {
    return http.get<User>('/auth/me')
  },

  // Change password
  changePassword(data: { old_password: string; new_password: string }) {
    return http.post('/auth/change-password', data)
  },

  // Admin: List users
  getUsers(params?: { skip?: number; limit?: number; search?: string }) {
    return http.get<UserListResponse>('/auth/users', { params })
  },

  // Admin: Get user by ID
  getUser(id: number) {
    return http.get<User>(`/auth/users/${id}`)
  },

  // Admin: Update user
  updateUser(id: number, data: Partial<User> & { password?: string }) {
    return http.put<User>(`/auth/users/${id}`, data)
  },

  // Admin: Delete user
  deleteUser(id: number) {
    return http.delete(`/auth/users/${id}`)
  }
}
