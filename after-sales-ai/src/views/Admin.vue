<template>
  <div class="admin-page">
    <div class="header">
      <button class="btn-back" @click="goBack">←</button>
      <h2>管理页面</h2>
      <div></div>
    </div>

    <div class="content">
      <div class="stats-section">
        <div class="stat-card">
          <div class="stat-value">{{ stats.sessions }}</div>
          <div class="stat-label">会话数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.messages }}</div>
          <div class="stat-label">消息数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.tickets }}</div>
          <div class="stat-label">工单数</div>
        </div>
      </div>

      <div class="action-section">
        <JsonExportButton />
        <button class="btn-clear" @click="handleClearData">清空演示数据</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import JsonExportButton from '@/components/JsonExportButton.vue'
import { clearAllData, initIfNeeded } from '@/store/storage'
import { sessionRepo, messageRepo, ticketRepo } from '@/store/repositories'

const router = useRouter()

const stats = ref({
  sessions: 0,
  messages: 0,
  tickets: 0
})

onMounted(() => {
  updateStats()
})

function updateStats() {
  const allSessions = sessionRepo.getAll()
  let totalMessages = 0
  allSessions.forEach(session => {
    totalMessages += messageRepo.getBySessionId(session.sessionId).length
  })
  
  stats.value = {
    sessions: allSessions.length,
    messages: totalMessages,
    tickets: ticketRepo.getAll().length
  }
}

async function handleClearData() {
  if (confirm('确定要清空所有演示数据吗？此操作不可恢复！')) {
    await clearAllData()
    await initIfNeeded()
    updateStats()
    // 使用更友好的提示
    const message = '数据已清空，已重新初始化 mock 数据'
    showToast(message)
  }
}

function showToast(message: string) {
  const toast = document.createElement('div')
  toast.className = 'toast-message'
  toast.textContent = message
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.classList.add('show')
  }, 10)
  
  setTimeout(() => {
    toast.classList.remove('show')
    setTimeout(() => {
      document.body.removeChild(toast)
    }, 300)
  }, 2000)
}

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.btn-back {
  padding: 8px;
  background: none;
  border: none;
  font-size: 18px;
  color: #333;
  cursor: pointer;
}

.header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.content {
  padding: 16px;
}

.stats-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.stat-card {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #18a058;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.action-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-clear {
  padding: 14px;
  background: #ff4d4f;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-clear:hover {
  background: #ff7875;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.3);
}

.toast-message {
  position: fixed;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  z-index: 10000;
  opacity: 0;
  transition: all 0.3s;
  pointer-events: none;
}

.toast-message.show {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
</style>
