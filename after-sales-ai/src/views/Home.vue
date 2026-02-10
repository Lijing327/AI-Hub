<template>
  <div class="home-page">
    <div class="header">
      <h1>造型机技术资源库</h1>
      <p class="subtitle">选择设备开始咨询</p>
    </div>

    <div class="content">
      <!-- 客户选择（可选） -->
      <div class="section" v-if="customers.length > 0">
        <div class="section-title">选择客户（可选）</div>
        <div class="customer-list">
          <div
            v-for="customer in customers"
            :key="customer.customerId"
            class="customer-item"
            :class="{ active: selectedCustomerId === customer.customerId }"
            @click="selectCustomer(customer.customerId)"
          >
            <div class="customer-name">{{ customer.name }}</div>
            <div class="customer-contact">{{ customer.contactName }} · {{ customer.phone }}</div>
          </div>
        </div>
      </div>

      <!-- 设备选择 -->
      <div class="section">
        <div class="section-title">选择设备</div>
        <div v-if="loading" class="loading-state">正在加载设备数据...</div>
        <div v-else-if="availableDevices.length === 0" class="empty-state">
          <p>暂无可用设备</p>
          <button class="btn-refresh" @click="refreshData">刷新</button>
        </div>
        <DevicePicker
          v-else
          :devices="availableDevices"
          :selected-device-id="selectedDeviceId ?? undefined"
          @select="selectDevice"
        />
      </div>

      <!-- 进入客服按钮 -->
      <div class="action-section">
        <button
          class="btn-enter"
          :disabled="!selectedDeviceId"
          @click="enterChat"
        >
          进入客服
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DevicePicker from '@/components/DevicePicker.vue'
import { customerRepo, deviceRepo } from '@/store/repositories'
import { initIfNeeded } from '@/store/storage'
import type { Customer, Device } from '@/models/types'

const router = useRouter()

const customers = ref<Customer[]>([])
const devices = ref<Device[]>([])
const selectedCustomerId = ref<string | null>(null)
const selectedDeviceId = ref<string | null>(null)
const loading = ref(true)

const availableDevices = computed(() => {
  if (selectedCustomerId.value) {
    return devices.value.filter((d) => d.customerId === selectedCustomerId.value)
  }
  return devices.value
})

// 加载数据
function loadData() {
  customers.value = customerRepo.getAll()
  devices.value = deviceRepo.getAll()
  loading.value = false
}

// 刷新数据
async function refreshData() {
  loading.value = true
  await initIfNeeded()
  loadData()
}

onMounted(async () => {
  // 确保数据已初始化
  await initIfNeeded()
  // 加载数据
  loadData()
})

function selectCustomer(customerId: string) {
  selectedCustomerId.value = selectedCustomerId.value === customerId ? null : customerId
  selectedDeviceId.value = null // 切换客户时清空设备选择
}

function selectDevice(device: Device) {
  selectedDeviceId.value = device.deviceId
}

function enterChat() {
  if (!selectedDeviceId.value) return

  const device = deviceRepo.getById(selectedDeviceId.value)
  if (!device) return

  router.push({
    path: '/chat',
    query: {
      deviceId: selectedDeviceId.value,
      customerId: device.customerId
    }
  })
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.header {
  text-align: center;
  color: #fff;
  margin-bottom: 30px;
  padding-top: 40px;
}

.header h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
}

.subtitle {
  font-size: 14px;
  opacity: 0.9;
}

.content {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 12px;
}

.customer-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.customer-item {
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.customer-item:hover {
  background: #e9ecef;
}

.customer-item.active {
  background: #e8f5e9;
  border-color: #18a058;
}

.customer-name {
  font-size: 15px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.customer-contact {
  font-size: 13px;
  color: #666;
}

.action-section {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.btn-enter {
  width: 100%;
  padding: 16px;
  background: #18a058;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-enter:hover:not(:disabled) {
  background: #159050;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(24, 160, 88, 0.3);
}

.btn-enter:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.loading-state {
  padding: 40px 20px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.empty-state p {
  color: #999;
  font-size: 14px;
  margin-bottom: 16px;
}

.btn-refresh {
  padding: 8px 16px;
  background: #18a058;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-refresh:hover {
  background: #159050;
}
</style>
