<template>
  <div class="history-page">
    <div class="header">
      <button class="btn-back" @click="goBack">←</button>
      <h2>历史会话</h2>
      <div></div>
    </div>

    <div class="filter-bar">
      <select v-model="selectedDeviceId" class="device-filter">
        <option value="">全部设备</option>
        <option v-for="device in devices" :key="device.deviceId" :value="device.deviceId">
          {{ device.model }} - {{ device.serialNo }}
        </option>
      </select>
    </div>

    <div class="session-list">
      <div
        v-for="session in filteredSessions"
        :key="session.sessionId"
        class="session-item"
        @click="viewSession(session.sessionId)"
      >
        <div class="session-header">
          <div class="session-info">
            <div class="device-model">{{ getDeviceModel(session.deviceId) }}</div>
            <div class="session-time">{{ formatTime(session.startTime) }}</div>
          </div>
          <div class="session-status">
            <span class="status-tag" :class="session.resolvedStatus">{{ session.resolvedStatus }}</span>
            <span v-if="session.escalatedToTicket" class="ticket-badge">工单</span>
          </div>
        </div>
        <div class="session-details">
          <div v-if="session.issueCategory" class="issue-category">
            {{ session.issueCategory }}
            <span v-if="session.alarmCode" class="alarm-code">{{ session.alarmCode }}</span>
          </div>
          <div v-if="session.summary" class="session-summary">{{ session.summary }}</div>
        </div>
      </div>

      <div v-if="filteredSessions.length === 0" class="empty-state">
        <p>暂无历史会话</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sessionRepo, deviceRepo } from '@/store/repositories'
import type { ChatSession, Device } from '@/models/types'

const route = useRoute()
const router = useRouter()

const sessions = ref<ChatSession[]>([])
const devices = ref<Device[]>([])
const selectedDeviceId = ref<string>('')

const filteredSessions = computed(() => {
  let result = sessions.value
  if (selectedDeviceId.value) {
    result = result.filter((s) => s.deviceId === selectedDeviceId.value)
  }
  return result.sort((a, b) => new Date(b.startTime).getTime() - new Date(a.startTime).getTime())
})

onMounted(() => {
  devices.value = deviceRepo.getAll()
  sessions.value = sessionRepo.getAll()
  const deviceId = route.query.deviceId as string
  if (deviceId) {
    selectedDeviceId.value = deviceId
  }
})

function getDeviceModel(deviceId: string): string {
  const device = deviceRepo.getById(deviceId)
  return device ? `${device.model} (${device.serialNo})` : '未知设备'
}

function formatTime(timeStr: string): string {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / 86400000)

  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  }
}

function viewSession(sessionId: string) {
  router.push(`/session/${sessionId}`)
}

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.history-page {
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

.filter-bar {
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
}

.device-filter {
  width: 100%;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
}

.session-list {
  padding: 16px;
}

.session-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.session-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.session-info {
  flex: 1;
}

.device-model {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.session-time {
  font-size: 12px;
  color: #999;
}

.session-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.未反馈 {
  background: #f0f0f0;
  color: #666;
}

.status-tag.已解决 {
  background: #d1e7dd;
  color: #0f5132;
}

.status-tag.未解决 {
  background: #f8d7da;
  color: #842029;
}

.ticket-badge {
  padding: 4px 8px;
  background: #cfe2ff;
  color: #084298;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.session-details {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.issue-category {
  font-size: 14px;
  color: #333;
  margin-bottom: 6px;
}

.alarm-code {
  display: inline-block;
  padding: 2px 8px;
  background: #fff3cd;
  color: #856404;
  border-radius: 4px;
  font-size: 12px;
  margin-left: 6px;
}

.session-summary {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}
</style>
