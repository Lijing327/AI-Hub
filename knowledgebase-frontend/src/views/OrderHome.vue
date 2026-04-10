<template>
  <div class="order-home">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>订单系统</span>
          <el-tag type="info">建设中</el-tag>
        </div>
      </template>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-statistic title="今日订单" :value="stats.todayOrders">
            <template #suffix>单</template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="待处理" :value="stats.pendingOrders">
            <template #suffix>单</template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="今日成交额" :value="stats.todayAmount" :precision="2">
            <template #prefix>¥</template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="本月订单" :value="stats.monthOrders">
            <template #suffix>单</template>
          </el-statistic>
        </el-col>
      </el-row>

      <el-divider />

      <el-empty description="订单系统功能开发中，敬请期待..." />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// 模拟数据
const stats = ref({
  todayOrders: 156,
  pendingOrders: 23,
  todayAmount: 45678.50,
  monthOrders: 3456
})
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stats-row {
  margin-bottom: 20px;
}

.stats-row :deep(.el-statistic) {
  text-align: center;
}

.stats-row :deep(.el-statistic__head) {
  font-size: 14px;
  color: #606266;
}

.stats-row :deep(.el-statistic__content) {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}
</style>
