<template>
  <div class="mall-home">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>商城系统</span>
          <el-tag type="info">建设中</el-tag>
        </div>
      </template>

      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-statistic title="商品总数" :value="stats.totalProducts">
            <template #suffix>件</template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="在售商品" :value="stats.activeProducts">
            <template #suffix>件</template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="商品分类" :value="stats.categories">
            <template #suffix>个</template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="今日浏览" :value="stats.todayViews">
            <template #suffix>次</template>
          </el-statistic>
        </el-col>
      </el-row>

      <el-divider />

      <el-empty description="商城系统功能开发中，敬请期待..." />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// 模拟数据
const stats = ref({
  totalProducts: 128,
  activeProducts: 96,
  categories: 12,
  todayViews: 3456
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
