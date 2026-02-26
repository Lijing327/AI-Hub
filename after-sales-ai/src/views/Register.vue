<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <h1>注册</h1>
        <p>创建您的账号，开始使用 AI 客服</p>
      </div>

      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="account">手机号/邮箱/用户名</label>
          <input
            id="account"
            v-model="form.account"
            type="text"
            placeholder="请输入手机号、邮箱或用户名"
            @input="checkAccountAvailability"
            :class="{ 'error': errors.account }"
          />
          <span v-if="errors.account" class="error-message">{{ errors.account }}</span>
          <span v-if="!errors.account && form.account && !accountAvailable" class="checking-message">
            <span class="spinner">●</span> 检查中...
          </span>
          <span v-if="!errors.account && form.account && accountAvailable" class="success-message">
            账号可用
          </span>
        </div>

        <div v-if="isPhoneAccount" class="form-group">
          <label for="deviceMN">机器号</label>
          <input
            id="deviceMN"
            v-model="form.deviceMN"
            type="text"
            placeholder="请输入设备机器号（如 354220030025）"
            :class="{ 'error': errors.deviceMN }"
          />
          <span v-if="errors.deviceMN" class="error-message">{{ errors.deviceMN }}</span>
          <span v-else class="form-hint">机器号需在设备管理表中存在方可注册</span>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="请输入密码（至少 6 位）"
            :class="{ 'error': errors.password }"
          />
          <span v-if="errors.password" class="error-message">{{ errors.password }}</span>
        </div>

        <div class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            :class="{ 'error': errors.confirmPassword }"
          />
          <span v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</span>
        </div>

        <div v-if="errorMessage" class="form-error">
          {{ errorMessage }}
        </div>

        <button type="submit" class="btn-register" :disabled="isLoading || !canSubmit">
          {{ isLoading ? '注册中...' : '注册' }}
        </button>

        <div class="form-footer">
          <router-link to="/login" class="link-login">
            已有账号？立即登录
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '@/api/auth'

const router = useRouter()

const form = reactive({
  account: '',
  deviceMN: '',
  password: '',
  confirmPassword: ''
})

const errors = reactive({
  account: '',
  deviceMN: '',
  password: '',
  confirmPassword: ''
})

// 是否为手机号（手机号注册需填写机器号）
const isPhoneAccount = computed(() => /^1[3-9]\d{9}$/.test(form.account))

const errorMessage = ref('')
const isLoading = ref(false)
const accountAvailable = ref(true)
let accountCheckingTimer: ReturnType<typeof setTimeout> | null = null

// 计算是否可以提交（手机号时需填写机器号）
const canSubmit = computed(() => {
  const base = form.account && form.password && form.confirmPassword &&
    !errors.account && !errors.password && !errors.confirmPassword && accountAvailable.value
  if (isPhoneAccount.value) {
    return base && form.deviceMN && !errors.deviceMN
  }
  return base
})

// 验证账号（手机号/邮箱/用户名）
function validateAccount() {
  if (!form.account) {
    errors.account = '请输入手机号/邮箱/用户名'
    return false
  }

  // 手机号验证（纯数字）
  if (/^\d+$/.test(form.account)) {
    if (!/^1[3-9]\d{9}$/.test(form.account)) {
      errors.account = '请输入正确的手机号'
      return false
    }
    return true
  }

  // 邮箱验证（包含@）
  if (form.account.includes('@')) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(form.account)) {
      errors.account = '请输入正确的邮箱'
      return false
    }
    return true
  }

  // 用户名验证（允许 admin 等）
  if (form.account.length < 2) {
    errors.account = '用户名长度至少 2 位'
    return false
  }

  return true
}

// 验证表单
function validateForm() {
  let isValid = true

  // 清空错误
  errors.account = ''
  errors.deviceMN = ''
  errors.password = ''
  errors.confirmPassword = ''
  errorMessage.value = ''

  // 验证账号
  if (!validateAccount()) {
    isValid = false
  }

  // 手机号注册时验证机器号
  if (isPhoneAccount.value && !form.deviceMN?.trim()) {
    errors.deviceMN = '手机号注册需填写机器号'
    isValid = false
  } else if (isPhoneAccount.value && form.deviceMN?.trim().length < 6) {
    errors.deviceMN = '请输入正确的机器号'
    isValid = false
  }

  // 验证密码
  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  } else if (form.password.length < 6) {
    errors.password = '密码长度不能少于 6 位'
    isValid = false
  }

  // 验证确认密码
  if (!form.confirmPassword) {
    errors.confirmPassword = '请确认密码'
    isValid = false
  } else if (form.confirmPassword !== form.password) {
    errors.confirmPassword = '两次输入的密码不一致'
    isValid = false
  }

  return isValid
}

// 检查账号是否可用（防抖处理）
function checkAccountAvailability() {
  accountAvailable.value = true
  errors.account = ''

  if (accountCheckingTimer) {
    clearTimeout(accountCheckingTimer)
  }

  if (form.account) {
    accountCheckingTimer = setTimeout(async () => {
      try {
        // 这里可以调用接口检查账号是否已被注册
        // 目前先设置为可用
        accountAvailable.value = true
      } catch (error) {
        errors.account = '检查账号失败'
      }
    }, 500)
  }
}

// 处理注册
async function handleRegister() {
  if (!validateForm()) return

  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await authService.register({
      account: form.account,
      password: form.password,
      deviceMN: isPhoneAccount.value ? form.deviceMN?.trim() : undefined
    })

    // 保存 token 和用户信息
    localStorage.setItem('token', response.token)
    localStorage.setItem('user', JSON.stringify(response.user))

    // 注册成功后直接跳转到聊天页
    router.push('/chat')
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '注册失败，请稍后重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-container {
  background: white;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.register-header h1 {
  font-size: 28px;
  color: #333;
  margin-bottom: 8px;
}

.register-header p {
  font-size: 16px;
  color: #666;
}

.register-form {
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

.checking-message {
  font-size: 12px;
  color: #666;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.success-message {
  font-size: 12px;
  color: #48bb78;
}

.form-hint {
  font-size: 12px;
  color: #718096;
}

.form-error {
  padding: 12px;
  background: #fee;
  border-radius: 8px;
  color: #c53030;
  font-size: 14px;
  text-align: center;
}

.btn-register {
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

.btn-register:hover:not(:disabled) {
  background: #5a67d8;
}

.btn-register:disabled {
  background: #a0aec0;
  cursor: not-allowed;
}

.form-footer {
  text-align: center;
  margin-top: 16px;
}

.link-login {
  color: #667eea;
  text-decoration: none;
  font-size: 14px;
}

.link-login:hover {
  text-decoration: underline;
}
</style>
