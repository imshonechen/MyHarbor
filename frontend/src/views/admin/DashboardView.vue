<template>
  <div class="dashboard">
    <h1 class="page-title">{{ t('dashboard.title') }}</h1>
    <p class="page-subtitle">{{ t('dashboard.welcome') }}</p>

    <!-- 关键指标卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-label">{{ t('dashboard.stats.todayVisits') }}</div>
          <div class="stat-value">{{ overview.home?.day || 0 }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🌐</div>
        <div class="stat-content">
          <div class="stat-label">{{ t('dashboard.stats.totalSites') }}</div>
          <div class="stat-value">{{ sites.length }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-label">{{ t('dashboard.stats.onlineSites') }}</div>
          <div class="stat-value">{{ onlineSites }}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">❌</div>
        <div class="stat-content">
          <div class="stat-label">{{ t('dashboard.stats.offlineSites') }}</div>
          <div class="stat-value">{{ offlineSites }}</div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h2 class="section-title">{{ t('dashboard.quickActions.title') }}</h2>
      <div class="actions-grid">
        <button @click="goToSites" class="action-btn">
          <span class="icon">➕</span>
          <span class="label">{{ t('dashboard.quickActions.addSite') }}</span>
        </button>
        <button @click="checkAllSites" class="action-btn" :disabled="checking">
          <span class="icon">🔄</span>
          <span class="label">{{ checking ? t('dashboard.quickActions.checking') : t('dashboard.quickActions.checkAll') }}</span>
        </button>
        <button @click="goToStatistics" class="action-btn">
          <span class="icon">📈</span>
          <span class="label">{{ t('dashboard.quickActions.viewStats') }}</span>
        </button>
        <button @click="goToSettings" class="action-btn">
          <span class="icon">⚙️</span>
          <span class="label">{{ t('dashboard.quickActions.systemSettings') }}</span>
        </button>
      </div>
    </div>

    <!-- 最近更新的站点 -->
    <div class="recent-sites">
      <h2 class="section-title">{{ t('dashboard.recentSites.title') }}</h2>
      <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
      <div v-else-if="recentSites.length === 0" class="empty">{{ t('dashboard.recentSites.noSites') }}</div>
      <div v-else class="sites-list">
        <div v-for="site in recentSites" :key="site.id" class="site-item">
          <div class="site-info">
            <div class="site-name">{{ site.name }}</div>
            <div class="site-url">{{ site.url }}</div>
          </div>
          <div class="site-status">
            <span :class="['status-badge', site.status]">{{ getStatusText(site.status) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 7天访问趋势 -->
    <div class="trend-section">
      <h2 class="section-title">{{ t('dashboard.trend.title') }}</h2>
      <div v-if="statsLoading" class="loading">{{ t('common.loading') }}</div>
      <div v-else class="trend-chart">
        <div v-for="item in trendItems.slice(-7)" :key="item.date" class="trend-bar">
          <div class="bar-container">
            <div
              class="bar"
              :style="{ height: getTrendBarHeight(item.home_count + item.site_click_count) + '%' }"
            ></div>
          </div>
          <div class="bar-label">{{ formatDate(item.date) }}</div>
          <div class="bar-value">{{ item.home_count + item.site_click_count }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { fetchAllSites, checkAllSites as apiCheckAllSites } from '../../api/sites.js'
import { fetchStatsOverview, fetchStatsTrend } from '../../api/stats.js'

const router = useRouter()
const { t } = useI18n()

const sites = ref([])
const overview = ref({})
const trendItems = ref([])
const loading = ref(false)
const statsLoading = ref(false)
const checking = ref(false)

const onlineSites = computed(() => sites.value.filter(s => s.status === 'online').length)
const offlineSites = computed(() => sites.value.filter(s => s.status === 'offline').length)
const recentSites = computed(() => sites.value.slice(0, 5))

const getStatusText = (status) => {
  const statusMap = {
    'online': t('common.online'),
    'offline': t('common.offline'),
    'unknown': t('common.unknown')
  }
  return statusMap[status] || status
}

const loadData = async () => {
  loading.value = true
  statsLoading.value = true

  try {
    const [sitesData, overviewData, trendData] = await Promise.all([
      fetchAllSites(),
      fetchStatsOverview(),
      fetchStatsTrend({ days: 7 })
    ])

    sites.value = sitesData.items || []
    overview.value = overviewData
    trendItems.value = trendData.items || []
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    loading.value = false
    statsLoading.value = false
  }
}

const checkAllSites = async () => {
  checking.value = true
  try {
    await apiCheckAllSites()
    await loadData()
  } catch (error) {
    console.error('Failed to check sites:', error)
  } finally {
    checking.value = false
  }
}

const getTrendBarHeight = (value) => {
  const maxValue = Math.max(...trendItems.value.map(item => item.home_count + item.site_click_count), 1)
  return (value / maxValue) * 100
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const goToSites = () => router.push('/admin/sites')
const goToStatistics = () => router.push('/admin/statistics')
const goToSettings = () => router.push('/admin/settings')

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard {
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
}

.stat-card:hover {
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.stat-icon {
  font-size: 2.5rem;
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 0.75rem;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 1rem 0;
}

.quick-actions {
  margin-bottom: 2rem;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.75rem;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  font-weight: 500;
}

.action-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn .icon {
  font-size: 1.25rem;
}

.recent-sites {
  margin-bottom: 2rem;
}

.sites-list {
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
  overflow: hidden;
}

.site-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  transition: background 0.3s ease;
}

.site-item:last-child {
  border-bottom: none;
}

.site-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.site-info {
  flex: 1;
}

.site-name {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 0.25rem;
}

.site-url {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.online {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.status-badge.offline {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.status-badge.unknown {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
}

.trend-section {
  margin-bottom: 2rem;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  padding: 2rem;
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
  min-height: 200px;
}

.trend-bar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.bar-container {
  width: 100%;
  height: 120px;
  display: flex;
  align-items: flex-end;
}

.bar {
  width: 100%;
  background: linear-gradient(180deg, #ffffff 0%, rgba(255, 255, 255, 0.7) 100%);
  border-radius: 0.25rem 0.25rem 0 0;
  transition: all 0.3s ease;
  min-height: 4px;
}

.bar:hover {
  background: linear-gradient(180deg, #ffffff 0%, rgba(255, 255, 255, 0.9) 100%);
}

.bar-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.bar-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #ffffff;
}

.loading, .empty {
  text-align: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 1.5rem;
  }

  .page-subtitle {
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
  }

  .stat-card {
    padding: 1rem;
  }

  .stat-icon {
    font-size: 2rem;
    width: 2.5rem;
    height: 2.5rem;
  }

  .stat-label {
    font-size: 0.8rem;
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .section-title {
    font-size: 1.1rem;
  }

  .actions-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .action-btn {
    flex-direction: column;
    padding: 0.75rem 0.5rem;
    font-size: 0.8rem;
  }

  .action-btn .icon {
    font-size: 1.5rem;
  }

  .recent-sites {
    margin-bottom: 1.5rem;
  }

  .site-item {
    padding: 0.875rem 1rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .site-name {
    font-size: 0.9rem;
  }

  .site-url {
    font-size: 0.8rem;
    word-break: break-all;
  }

  .trend-chart {
    padding: 1rem;
    gap: 0.5rem;
    min-height: 150px;
  }

  .bar-container {
    height: 80px;
  }

  .bar-label {
    font-size: 0.7rem;
  }

  .bar-value {
    font-size: 0.8rem;
  }
}
</style>
