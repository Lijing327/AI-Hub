<template>
  <div class="json-export">
    <button class="btn-export" @click="handleExport">导出 JSON</button>
    <button class="btn-copy" @click="handleCopy" v-if="exported">复制</button>
    <textarea
      v-if="exported"
      v-model="jsonText"
      class="json-textarea"
      readonly
      rows="10"
    ></textarea>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { exportAllAsJson } from '@/store/storage'

const exported = ref(false)
const jsonText = ref('')

function handleExport() {
  jsonText.value = exportAllAsJson()
  exported.value = true
}

function handleCopy() {
  navigator.clipboard.writeText(jsonText.value).then(() => {
    showToast('已复制到剪贴板')
  }).catch(() => {
    showToast('复制失败，请手动复制')
  })
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
</script>

<style scoped>
.json-export {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-export,
.btn-copy {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-export {
  background: #18a058;
  color: #fff;
}

.btn-export:hover {
  background: #159050;
}

.btn-copy {
  background: #667eea;
  color: #fff;
}

.btn-copy:hover {
  background: #5568d3;
}

.json-textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  resize: vertical;
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
