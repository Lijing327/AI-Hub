<template>
  <div class="device-picker">
    <div class="device-list">
      <div
        v-for="device in devices"
        :key="device.deviceId"
        class="device-item"
        :class="{ active: selectedDeviceId === device.deviceId }"
        @click="handleSelect(device)"
      >
        <div class="device-info">
          <div class="device-model">{{ device.model }}</div>
          <div class="device-serial">SN: {{ device.serialNo }}</div>
          <div class="device-controller">控制器: {{ device.controllerType }}</div>
        </div>
        <div class="device-status" :class="device.status">{{ device.status }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import type { Device } from '@/models/types'

interface Props {
  devices: Device[]
  selectedDeviceId?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  select: [device: Device]
}>()

function handleSelect(device: Device) {
  emit('select', device)
}
</script>

<style scoped>
.device-picker {
  padding: 16px;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.device-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.device-item.active {
  border: 2px solid #18a058;
  background: #f0f9ff;
}

.device-info {
  flex: 1;
}

.device-model {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.device-serial {
  font-size: 14px;
  color: #666;
  margin-bottom: 2px;
}

.device-controller {
  font-size: 12px;
  color: #999;
}

.device-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.device-status.正常 {
  background: #e8f5e9;
  color: #2e7d32;
}

.device-status.故障 {
  background: #ffebee;
  color: #c62828;
}

.device-status.维护中 {
  background: #fff3e0;
  color: #ef6c00;
}
</style>
