<template>
  <div class="register-page">
    <div class="register-container">
      <div class="register-header">
        <h1>注册</h1>
        <p>创建您的账号，开始使用AI客服</p>
      </div>

      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group">
          <label for="phone">手机号</label>
          <input
            id="phone"
            v-model="form.phone"
            type="tel"
            placeholder="请输入手机号"
            maxlength="11"
            @input="checkPhoneAvailability"
            :class="{ 'error': errors.phone }"
          />
          <span v-if="errors.phone" class="error-message">{{ errors.phone }}</span>
          <span v-if="!errors.phone && form.phone && !phoneAvailable" class="checking-message">
            <span class="spinner">●</span> 检查中...
          </span>
          <span v-if="!errors.phone && form.phone && phoneAvailable" class="success-message">
            手机号可用
          </span>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            placeholder="请输入密码（至少6位）"
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
  phone: '',
  password: '',
  confirmPassword: ''
})

const errors = reactive({
  phone: '',
  password: '',
  confirmPassword: ''
})

const errorMessage = ref('')
const isLoading = ref(false)
const phoneAvailable = ref(true)
let phoneCheckingTimer: NodeJS.Timeout | null = null

// 计算是否可以提交
const canSubmit = computed(() => {
  return form.phone &&
         form.password &&
         form.confirmPassword &&
         !errors.phone &&
         !errors.password &&
         !errors.confirmPassword &&
         phoneAvailable.value
})

// 验证表单
function validateForm() {
  let isValid = true

  // 清空错误
  errors.phone = ''
  errors.password = ''
  errors.confirmPassword = ''
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

// 检查手机号是否可用（防抖处理）
function checkPhoneAvailability() {
  phoneAvailable.value = true
  errors.phone = ''

  if (phoneCheckingTimer) {
    clearTimeout(phoneCheckingTimer)
  }

  if (form.phone && /^1[3-9]\d{9}$/.test(form.phone)) {
    phoneCheckingTimer = setTimeout(async () => {
      try {
        // 这里可以调用接口检查手机号是否已被注册
        // 目前先设置为可用
        phoneAvailable.value = true
      } catch (error) {
        errors.phone = '检查手机号失败'
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
      phone: form.phone,
      password: form.password
    })

    // 保存token和用户信息
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