<template>
  <div class="monitoring-view">
    <h1 class="page-title">{{ t('monitoring.title') }}</h1>
    <p class="page-subtitle">{{ t('monitoring.subtitle') }}</p>

    <!-- 控制栏 -->
    <div class="controls">
      <div class="control-group">
        <label>{{ t('monitoring.controls.days') }}</label>
        <select v-model="days" class="select-input" @change="loadAllSitesStatus">
          <option :value="1">{{ t('monitoring.days.1') }}</option>
          <option :value="7">{{ t('monitoring.days.7') }}</option>
          <option :value="14">{{ t('monitoring.days.14') }}</option>
          <option :value="30">{{ t('monitoring.days.30') }}</option>
        </select>
      </div>
      <button @click="checkAllSites" class="action-btn" :disabled="checkingAll">
        <span class="icon">🔄</span>
        {{ checkingAll ? t('monitoring.controls.checking') : t('monitoring.controls.checkAllSites') }}
      </button>
      <button @click="loadAllSitesStatus" class="action-btn">
        <span class="icon">↻</span>
        {{ t('monitoring.controls.refresh') }}
      </button>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading">{{ t('monitoring.loading') }}</div>

    <!-- 站点列表 -->
    <div v-else-if="sitesWithStatus.length === 0" class="empty-state">
      <div class="empty-icon">📊</div>
      <div class="empty-text">{{ t('monitoring.noSites') }}</div>
    </div>

    <!-- 站点状态列表 -->
    <div v-else class="sites-list">
      <div v-for="site in sitesWithStatus" :key="site.id" class="site-row">
        <!-- 站点信息 -->
        <div class="site-info">
          <div class="site-header">
            <h3 class="site-name">{{ site.name }}</h3>
            <div class="site-meta">
              <span :class="['status-indicator', site.currentStatus]"></span>
              <span class="status-text">{{ getStatusText(site.currentStatus) }}</span>
              <span v-if="site.uptime !== null" class="uptime-text">
                {{ site.uptime }}% {{ t('monitoring.stats.uptime') }}
              </span>
            </div>
          </div>
          <div class="site-url">{{ site.url }}</div>
        </div>

        <!-- 运行状态条 -->
        <div class="uptime-bar">
          <div class="bar-container">
            <div
              v-for="(block, index) in site.statusBlocks"
              :key="index"
              :class="['bar-block', block.status]"
              :style="{ width: block.width + '%' }"
              :title="getBlockTooltip(block)"
            ></div>
          </div>
          <div class="bar-labels">
            <span class="label-start">{{ site.startDate }}</span>
            <span class="label-end">{{ site.endDate }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  fetchAllSites,
  fetchSiteStatusLogs,
  checkAllSites as apiCheckAllSites
} from '../../api/sites.js'

const { t } = useI18n()

const sites = ref([])
const sitesStatusLogs = ref({}) // { siteId: [logs] }
const days = ref(1)
const loading = ref(false)
const checkingAll = ref(false)

// 计算每个站点的状态数据
const sitesWithStatus = computed(() => {
  return sites.value.map(site => {
    const logs = sitesStatusLogs.value[site.id] || []
    const statusBlocks = calculateStatusBlocks(logs, days.value)
    const uptime = calculateUptime(logs)
    const currentStatus = site.status || 'unknown'

    const today = new Date()
    const startDate = new Date(today)
    startDate.setDate(startDate.getDate() - days.value)

    return {
      ...site,
      statusBlocks,
      uptime,
      currentStatus,
      startDate: formatDate(startDate),
      endDate: formatDate(today)
    }
  })
})

// 计算状态块
const calculateStatusBlocks = (logs, daysCount) => {
  if (logs.length === 0) {
    return [{ status: 'nodata', width: 100, count: 0, date: null }]
  }

  const now = new Date()
  const blocks = []

  // 如果是1天，按小时分组（24小时）
  if (daysCount === 1) {
    for (let i = 23; i >= 0; i--) {
      const hourStart = new Date(now)
      hourStart.setHours(hourStart.getHours() - i, 0, 0, 0)
      const hourEnd = new Date(hourStart)
      hourEnd.setHours(hourEnd.getHours() + 1)

      // 查找该小时的日志
      const hourLogs = logs.filter(log => {
        const logTime = new Date(log.checked_at)
        return logTime >= hourStart && logTime < hourEnd
      })

      let status = 'nodata'
      if (hourLogs.length > 0) {
        const hasOffline = hourLogs.some(log => log.status === 'offline')
        status = hasOffline ? 'offline' : 'online'
      }

      const dateStr = `${hourStart.getMonth() + 1}/${hourStart.getDate()} ${hourStart.getHours()}:00`
      blocks.push({
        status,
        width: 100 / 24,
        count: hourLogs.length,
        date: dateStr
      })
    }
  } else {
    // 其他天数按天分组
    for (let i = daysCount - 1; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      const dateStr = date.toISOString().split('T')[0]

      // 查找该日期的日志
      const dayLogs = logs.filter(log => {
        const logDate = new Date(log.checked_at).toISOString().split('T')[0]
        return logDate === dateStr
      })

      let status = 'nodata'
      if (dayLogs.length > 0) {
        const hasOffline = dayLogs.some(log => log.status === 'offline')
        status = hasOffline ? 'offline' : 'online'
      }

      blocks.push({
        status,
        width: 100 / daysCount,
        count: dayLogs.length,
        date: dateStr
      })
    }
  }

  return blocks
}

// 计算在线率
const calculateUptime = (logs) => {
  if (logs.length === 0) return null

  const onlineCount = logs.filter(log => log.status === 'online').length
  const totalCount = logs.length

  return ((onlineCount / totalCount) * 100).toFixed(1)
}

const getStatusText = (status) => {
  const statusMap = {
    'online': t('monitoring.stats.online'),
    'offline': t('monitoring.stats.offline'),
    'unknown': t('monitoring.stats.unknown'),
    'nodata': t('monitoring.stats.noData')
  }
  return statusMap[status] || status
}

const getBlockTooltip = (block) => {
  const parts = [
    `${t('monitoring.tooltip.date')}: ${block.date || t('monitoring.stats.noData')}`,
    `${t('monitoring.tooltip.status')}: ${getStatusText(block.status)}`,
    `${t('monitoring.tooltip.checks')}: ${block.count}`
  ]
  return parts.join('\n')
}

const formatDate = (date) => {
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}/${day}`
}

const loadSites = async () => {
  try {
    const data = await fetchAllSites()
    sites.value = data.items || []
  } catch (error) {
    console.error('Failed to load sites:', error)
  }
}

const loadAllSitesStatus = async () => {
  loading.value = true
  try {
    await loadSites()

    // 并发加载所有站点的状态日志
    const promises = sites.value.map(async (site) => {
      try {
        const data = await fetchSiteStatusLogs(site.id, { days: days.value })
        return { siteId: site.id, logs: data.items || [] }
      } catch (error) {
        console.error(`Failed to load status logs for site ${site.id}:`, error)
        return { siteId: site.id, logs: [] }
      }
    })

    const results = await Promise.all(promises)

    // 构建状态日志映射
    const logsMap = {}
    results.forEach(result => {
      logsMap[result.siteId] = result.logs
    })
    sitesStatusLogs.value = logsMap
  } catch (error) {
    console.error('Failed to load sites status:', error)
  } finally {
    loading.value = false
  }
}

const checkAllSites = async () => {
  checkingAll.value = true
  try {
    await apiCheckAllSites()
    await loadAllSitesStatus()
  } catch (error) {
    console.error('Failed to check all sites:', error)
  } finally {
    checkingAll.value = false
  }
}

onMounted(() => {
  loadAllSitesStatus()
})
</script>

<style scoped>
.monitoring-view {
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #dbeafe 0%, #e9d5ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 0.5rem 0;
}

.page-subtitle {
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 2rem 0;
}

.controls {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-group label {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.select-input {
  padding: 0.5rem 0.75rem;
  background: rgba(20, 121, 191, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  color: white;
  font-size: 0.875rem;
  min-width: 150px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.875rem;
}

.action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.25);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading,
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-text {
  font-size: 1.125rem;
  color: rgba(255, 255, 255, 0.6);
}

.loading {
  color: rgba(255, 255, 255, 0.5);
}

/* 站点列表 */
.sites-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.site-row {
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.site-row:hover {
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.site-info {
  margin-bottom: 1rem;
}

.site-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.site-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.site-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.status-indicator {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  display: inline-block;
}

.status-indicator.online {
  background: #4ade80;
  box-shadow: 0 0 8px rgba(74, 222, 128, 0.6);
}

.status-indicator.offline {
  background: #f87171;
  box-shadow: 0 0 8px rgba(248, 113, 113, 0.6);
}

.status-indicator.unknown,
.status-indicator.nodata {
  background: #9ca3af;
}

.status-text {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.uptime-text {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.site-url {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
  font-family: monospace;
}

/* 运行状态条 */
.uptime-bar {
  width: 100%;
}

.bar-container {
  display: flex;
  height: 2.5rem;
  border-radius: 0.5rem;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.2);
}

.bar-block {
  transition: all 0.3s ease;
  cursor: pointer;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
}

.bar-block:last-child {
  border-right: none;
}

.bar-block:hover {
  opacity: 0.8;
  transform: scaleY(1.1);
}

.bar-block.online {
  background: rgba(34, 197, 94, 0.6);
}

.bar-block.offline {
  background: rgba(239, 68, 68, 0.6);
}

.bar-block.nodata {
  background: rgba(156, 163, 175, 0.3);
}

.bar-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 768px) {
  .page-title {
    font-size: 1.5rem;
  }

  .page-subtitle {
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }

  .controls {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }

  .control-group {
    width: 100%;
  }

  .select-input {
    width: 100%;
  }

  .action-btn {
    width: 100%;
    justify-content: center;
  }

  .site-row {
    padding: 1rem;
  }

  .site-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .site-name {
    font-size: 1.1rem;
  }

  .site-meta {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .site-url {
    font-size: 0.8rem;
    word-break: break-all;
  }

  .bar-container {
    height: 2rem;
  }

  .bar-labels {
    font-size: 0.7rem;
  }
}
</style>
