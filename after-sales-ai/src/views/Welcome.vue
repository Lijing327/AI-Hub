<template>
  <div class="welcome-page">
    <div class="welcome-content">
      <!-- 主标题与插图区 -->
      <div class="hero">
        <div class="hero-icon" aria-hidden="true">
          <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="2" fill="none" opacity="0.9"/>
            <path d="M22 28h4v16h-4V28zm8 0h4v16h-4V28zm8 0h4v16h-4V28z" fill="currentColor" opacity="0.8"/>
            <path d="M20 24l12-8 12 8v4H20v-4z" stroke="currentColor" stroke-width="2" fill="none"/>
          </svg>
        </div>
        <h1 class="title">造型机售后智能客服</h1>
        <p class="subtitle">设备故障、报警码、操作问题，随时问我</p>
      </div>

      <!-- 简要说明 -->
      <ul class="features">
        <li><span class="dot"></span> 支持报警码与故障现象描述</li>
        <li><span class="dot"></span> 自动匹配知识库排查步骤与方案</li>
        <li><span class="dot"></span> 无法解决时可一键转工单</li>
      </ul>

      <!-- 主操作按钮 -->
      <div class="action">
        <button class="btn-start" @click="enterChat">
          <span class="btn-text">开始咨询</span>
          <span class="btn-arrow">→</span>
        </button>
        <p class="hint">无需登录，打开即可使用</p>
        <router-link to="/home" class="link-device">指定设备再咨询</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function enterChat() {
  router.push({ path: '/chat' })
}
</script>

<style scoped>
.welcome-page {
  min-height: 100vh;
  background: linear-gradient(160deg, #0f172a 0%, #1e293b 45%, #334155 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  padding-bottom: env(safe-area-inset-bottom);
}

.welcome-content {
  width: 100%;
  max-width: 400px;
  text-align: center;
}

.hero {
  margin-bottom: 32px;
}

.hero-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 20px;
  color: rgba(255, 255, 255, 0.95);
  animation: float 3s ease-in-out infinite;
}

.hero-icon svg {
  width: 100%;
  height: 100%;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}

.title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
  letter-spacing: 0.02em;
}

.subtitle {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0;
  line-height: 1.5;
}

.features {
  list-style: none;
  padding: 0;
  margin: 0 0 36px;
  text-align: left;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px 20px;
}

.features li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.88);
  padding: 6px 0;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #38bdf8;
  flex-shrink: 0;
}

.action {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.btn-start {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  max-width: 280px;
  padding: 16px 24px;
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
  color: #fff;
  border: none;
  border-radius: 14px;
  font-size: 17px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 14px rgba(14, 165, 233, 0.4);
}

.btn-start:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(14, 165, 233, 0.5);
}

.btn-start:active {
  transform: translateY(0);
}

.btn-arrow {
  font-size: 18px;
  transition: transform 0.2s;
}

.btn-start:hover .btn-arrow {
  transform: translateX(4px);
}

.hint {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.link-device {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  margin-top: 4px;
  display: inline-block;
  transition: color 0.2s;
}

.link-device:hover {
  color: rgba(255, 255, 255, 0.9);
}
</style>
