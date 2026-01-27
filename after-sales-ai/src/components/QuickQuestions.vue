<template>
  <div class="quick-questions">
    <div class="questions-scroll">
      <button
        v-for="(question, index) in questions"
        :key="index"
        class="question-chip"
        @click="handleClick(question.text)"
      >
        {{ question.text }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'
import type { DemoQuestion } from '@/models/types'

interface Props {
  questions: DemoQuestion[]
}

defineProps<Props>()

const emit = defineEmits<{
  select: [question: string]
}>()

function handleClick(question: string) {
  emit('select', question)
}
</script>

<style scoped>
.quick-questions {
  padding: 12px 16px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
}

.questions-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.questions-scroll::-webkit-scrollbar {
  display: none;
}

.question-chip {
  flex-shrink: 0;
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.question-chip:hover {
  background: #18a058;
  color: #fff;
  border-color: #18a058;
}

.question-chip:active {
  transform: scale(0.95);
}
</style>
