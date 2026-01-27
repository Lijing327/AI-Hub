<template>
  <div class="tickets-page">
    <div class="header">
      <button class="btn-back" @click="goBack">←</button>
      <h2>工单列表</h2>
      <div></div>
    </div>

    <div class="filter-bar">
      <select v-model="selectedDeviceId" class="device-filter">
        <option value="">全部设备</option>
        <option v-for="device in devices" :key="device.deviceId" :value="device.deviceId">
          {{ device.model }} - {{ device.serialNo }}
        </option>
      </select>
      <select v-model="selectedStatus" class="status-filter">
        <option value="">全部状态</option>
        <option value="待处理">待处理</option>
        <option value="处理中">处理中</option>
        <option value="已解决">已解决</option>
        <option value="已关闭">已关闭</option>
      </select>
    </div>

    <div class="ticket-list">
      <div
        v-for="ticket in filteredTickets"
        :key="ticket.ticketId"
        class="ticket-item"
        @click="viewTicket(ticket.ticketId)"
      >
        <div class="ticket-header">
          <div class="ticket-title">{{ ticket.title }}</div>
          <TicketStatusTag :status="ticket.status" />
        </div>
        <div class="ticket-info">
          <div class="info-row">
            <span class="label">设备：</span>
            <span class="value">{{ getDeviceModel(ticket.deviceId) }}</span>
          </div>
          <div class="info-row">
            <span class="label">优先级：</span>
            <span class="value priority" :class="ticket.priority">{{ ticket.priority }}</span>
          </div>
          <div class="info-row">
            <span class="label">创建时间：</span>
            <span class="value">{{ formatTime(ticket.createdAt) }}</span>
          </div>
        </div>
      </div>

      <div v-if="filteredTickets.length === 0" class="empty-state">
        <p>暂无工单</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TicketStatusTag from '@/components/TicketStatusTag.vue'
import { ticketRepo, deviceRepo } from '@/store/repositories'
import type { Ticket, Device } from '@/models/types'

const route = useRoute()
const router = useRouter()

const tickets = ref<Ticket[]>([])
const devices = ref<Device[]>([])
const selectedDeviceId = ref<string>('')
const selectedStatus = ref<string>('')

const filteredTickets = computed(() => {
  let result = tickets.value
  if (selectedDeviceId.value) {
    result = result.filter((t) => t.deviceId === selectedDeviceId.value)
  }
  if (selectedStatus.value) {
    result = result.filter((t) => t.status === selectedStatus.value)
  }
  return result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
})

onMounted(() => {
  devices.value = deviceRepo.getAll()
  tickets.value = ticketRepo.getAll()
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
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
  }
}

function viewTicket(ticketId: string) {
  router.push(`/ticket/${ticketId}`)
}

function goBack() {
  router.push('/')
}
</script>

<style scoped>
.tickets-page {
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
  display: flex;
  gap: 12px;
}

.device-filter,
.status-filter {
  flex: 1;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  background: #fff;
}

.ticket-list {
  padding: 16px;
}

.ticket-item {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.ticket-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.ticket-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.ticket-title {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.ticket-info {
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.info-row {
  font-size: 13px;
  margin-bottom: 6px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.label {
  color: #666;
}

.value {
  color: #333;
}

.value.priority {
  font-weight: 500;
}

.value.priority.低 {
  color: #52c41a;
}

.value.priority.中 {
  color: #faad14;
}

.value.priority.高 {
  color: #ff7875;
}

.value.priority.紧急 {
  color: #ff4d4f;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
}
</style>
