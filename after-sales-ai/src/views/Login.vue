<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <h1>登录</h1>
        <p>请输入您的手机号和密码</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="phone">手机号</label>
          <input
            id="phone"
            v-model="form.phone"
            type="tel"
            placeholder="请输入手机号"
            maxlength="11"
            :class="{ 'error': errors.phone }"
          />
          <span v-if="errors.phone" class="error-message">{{ errors.phone }}</span>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :class="{ 'error': errors.password }"
          />
          <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
        </div>

        <div v-if="errorMessage" class="form-error">
          {{ errorMessage }}
        </div>

        <button type="submit" class="btn-login" :disabled="isLoading">
          {{ isLoading ? '登录中...' : '登录' }}
        </button>

        <div class="form-footer">
          <router-link to="/register" class="link-register">
            还没有账号？立即注册
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authService } from '@/api/auth'

const router = useRouter()
const route = useRoute()

const form = reactive({
  phone: '',
  password: ''
})

const errors = reactive({
  phone: '',
  password: ''
})

const errorMessage = ref('')
const isLoading = ref(false)

// 验证表单
function validateForm() {
  let isValid = true

  // 清空错误
  errors.phone = ''
  errors.password = ''
  errorMessage.value = ''

  // 验证手机号
  if (!form.phone) {
    errors.phone = '请输入手机号'
    isValid = false
  } else if (!/^1[3-9]\d{9}$/.test(form.phone)) {
    errors.phone = '请输入正确的手机号'
    isValid = false
  }

  // 验证密码
  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  } else if (form.password.length < 6) {
    errors.password = '密码长度不能少于6位'
    isValid = false
  }

  return isValid
}

// 处理登录
async function handleLogin() {
  if (!validateForm()) return

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await authService.login({
      phone: form.phone,
      password: form.password
    })

    // 保存token和用户信息
    localStorage.setItem('token', response.token)
    localStorage.setItem('user', JSON.stringify(response.user))

    // 获取重定向地址，如果没有则默认跳转到聊天页
    const redirect = route.query.redirect as string || '/chat'
    router.push(redirect)
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '登录失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  background: white;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 28px;
  color: #333;
  margin-bottom: 8px;
}

.login-header p {
  font-size: 16px;
  color: #666;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.form-group input {
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.form-group input.error {
  border-color: #f56565;
}

.error-message {
  font-size: 12px;
  color: #f56565;
}

.form-error {
  padding: 12px;
  background: #fee;
  border-radius: 8px;
  color: #c53030;
  font-size: 14px;
  text-align: center;
}

.btn-login {
  padding: 14px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-login:hover:not(:disabled) {
  background: #5a67d8;
}

.btn-login:disabled {
  background: #a0aec0;
  cursor: not-allowed;
}

.form-footer {
  text-align: center;
  margin-top: 16px;
}

.link-register {
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
}

.link-register:hover {
  text-decoration: underline;
}
</style>