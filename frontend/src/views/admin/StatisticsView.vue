<template>
  <div class="statistics-view">
    <h1 class="page-title">{{ t('statistics.title') }}</h1>
    <p class="page-subtitle">{{ t('statistics.subtitle') }}</p>

    <!-- 控制栏 -->
    <div class="controls">
      <div class="control-group">
        <label>{{ t('statistics.controls.timeRange') }}</label>
        <select v-model="rankingRange" class="select-input">
          <option value="day">{{ t('statistics.ranges.day') }}</option>
          <option value="month">{{ t('statistics.ranges.month') }}</option>
          <option value="year">{{ t('statistics.ranges.year') }}</option>
          <option value="total">{{ t('statistics.ranges.total') }}</option>
        </select>
      </div>
      <div class="control-group">
        <label>{{ t('statistics.controls.trendDays') }}</label>
        <select v-model="trendDays" class="select-input">
          <option :value="7">{{ t('statistics.days.7') }}</option>
          <option :value="30">{{ t('statistics.days.30') }}</option>
          <option :value="60">{{ t('statistics.days.60') }}</option>
          <option :value="90">{{ t('statistics.days.90') }}</option>
        </select>
      </div>
      <div class="control-group">
        <label>{{ t('statistics.controls.topSites') }}</label>
        <input v-model.number="rankingLimit" type="number" min="5" max="100" class="number-input" />
      </div>
      <button @click="loadStats" class="refresh-btn" :disabled="loading">
        <span class="icon">↻</span>
        {{ t('statistics.controls.refresh') }}
      </button>
    </div>

    <!-- 统计卡片 -->
    <div v-if="loading" class="loading">{{ t('statistics.loading') }}</div>
    <div v-else-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="loadStats" class="retry-btn">{{ t('statistics.retry') }}</button>
    </div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('statistics.cards.homeToday') }}</div>
          <div class="stat-value">{{ overview.home?.day || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('statistics.cards.homeMonth') }}</div>
          <div class="stat-value">{{ overview.home?.month || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('statistics.cards.homeYear') }}</div>
          <div class="stat-value">{{ overview.home?.year || 0 }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('statistics.cards.homeTotal') }}</div>
          <div class="stat-value">{{ overview.home?.total || 0 }}</div>
        </div>
        <div class="stat-card highlight">
          <div class="stat-label">{{ t('statistics.cards.sitesTotal') }}</div>
          <div class="stat-value">{{ overview.sites_total || 0 }}</div>
        </div>
      </div>

      <!-- 排行榜和趋势图 -->
      <div class="data-section">
        <!-- 左侧：排行榜 -->
        <div class="ranking-panel">
          <h2 class="section-title">{{ t('statistics.ranking.title') }} ({{ t('statistics.ranges.' + rankingRange) }})</h2>
          <div v-if="rankingItems.length === 0" class="empty">{{ t('statistics.ranking.noData') }}</div>
          <div v-else class="ranking-list">
            <div v-for="(item, index) in rankingItems" :key="item.site_id" class="ranking-item">
              <div class="rank-number">{{ index + 1 }}</div>
              <div class="rank-info">
                <div class="rank-name">{{ item.site_name }}</div>
                <div class="rank-count">{{ item.click_count }} {{ t('statistics.ranking.clicks') }}</div>
              </div>
              <div class="rank-bar">
                <div
                  class="rank-bar-fill"
                  :style="{ width: getRankBarWidth(item.click_count) + '%' }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：趋势图 -->
        <div class="trend-panel">
          <h2 class="section-title">{{ t('statistics.trend.title') }} ({{ trendDays }} {{ t('statistics.days.' + trendDays) }})</h2>
          <div v-if="trendItems.length === 0" class="empty">{{ t('statistics.trend.noData') }}</div>
          <div v-else class="trend-chart">
            <div v-for="item in trendItems" :key="item.date" class="trend-bar">
              <div class="bar-container">
                <div
                  class="bar home"
                  :style="{ height: getTrendBarHeight(item.home_count) + '%' }"
                  :title="`${t('statistics.trend.homeVisits')}: ${item.home_count}`"
                ></div>
                <div
                  class="bar sites"
                  :style="{ height: getTrendBarHeight(item.site_click_count) + '%' }"
                  :title="`${t('statistics.trend.siteClicks')}: ${item.site_click_count}`"
                ></div>
              </div>
              <div class="bar-label">{{ formatDate(item.date) }}</div>
            </div>
          </div>
          <div class="legend">
            <div class="legend-item">
              <span class="legend-color home"></span>
              <span>{{ t('statistics.trend.homeVisits') }}</span>
            </div>
            <div class="legend-item">
              <span class="legend-color sites"></span>
              <span>{{ t('statistics.trend.siteClicks') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 点击统计表 -->
      <div class="table-panel">
        <div class="table-header">
          <h2 class="section-title" style="margin:0;">{{ t('statistics.table.title') }}</h2>
          <input
            v-model.trim="tableQuery"
            type="text"
            class="table-search"
            :placeholder="t('statistics.table.searchPlaceholder')"
          />
        </div>
        <div class="table-sortbar">
          <button type="button" class="sort-chip" :class="{ active: tableSortKey === null }" @click="resetTableSort">
            {{ t('statistics.table.columns.siteName') }}
          </button>
          <button
            type="button"
            class="sort-chip"
            :class="{ active: tableSortKey === 'clicks_today' }"
            @click="toggleTableSort('clicks_today')"
          >
            {{ t('statistics.table.columns.today') }}
            <span class="chip-indicator">{{ getTableSortIndicator('clicks_today') }}</span>
          </button>
          <button
            type="button"
            class="sort-chip"
            :class="{ active: tableSortKey === 'clicks_7d' }"
            @click="toggleTableSort('clicks_7d')"
          >
            {{ t('statistics.table.columns.days7') }}
            <span class="chip-indicator">{{ getTableSortIndicator('clicks_7d') }}</span>
          </button>
          <button
            type="button"
            class="sort-chip"
            :class="{ active: tableSortKey === 'clicks_30d' }"
            @click="toggleTableSort('clicks_30d')"
          >
            {{ t('statistics.table.columns.days30') }}
            <span class="chip-indicator">{{ getTableSortIndicator('clicks_30d') }}</span>
          </button>
          <button
            type="button"
            class="sort-chip"
            :class="{ active: tableSortKey === 'clicks_90d' }"
            @click="toggleTableSort('clicks_90d')"
          >
            {{ t('statistics.table.columns.days90') }}
            <span class="chip-indicator">{{ getTableSortIndicator('clicks_90d') }}</span>
          </button>
          <button
            type="button"
            class="sort-chip"
            :class="{ active: tableSortKey === 'clicks_365d' }"
            @click="toggleTableSort('clicks_365d')"
          >
            {{ t('statistics.table.columns.days365') }}
            <span class="chip-indicator">{{ getTableSortIndicator('clicks_365d') }}</span>
          </button>
          <button
            type="button"
            class="sort-chip"
            :class="{ active: tableSortKey === 'clicks_total' }"
            @click="toggleTableSort('clicks_total')"
          >
            {{ t('statistics.table.columns.total') }}
            <span class="chip-indicator">{{ getTableSortIndicator('clicks_total') }}</span>
          </button>
        </div>
        <div v-if="tableItems.length === 0" class="empty">{{ t('statistics.table.noData') }}</div>
        <div v-else class="table-wrapper">
          <table class="stats-table">
            <thead>
              <tr>
                <th>
                  <button type="button" class="sort-btn" @click="resetTableSort">
                    {{ t('statistics.table.columns.siteName') }}
                  </button>
                </th>
                <th>{{ t('statistics.table.columns.url') }}</th>
                <th class="num">
                  <button type="button" class="sort-btn num" @click="toggleTableSort('clicks_today')">
                    {{ t('statistics.table.columns.today') }}
                    <span class="sort-indicator">{{ getTableSortIndicator('clicks_today') }}</span>
                  </button>
                </th>
                <th class="num">
                  <button type="button" class="sort-btn num" @click="toggleTableSort('clicks_7d')">
                    {{ t('statistics.table.columns.days7') }}
                    <span class="sort-indicator">{{ getTableSortIndicator('clicks_7d') }}</span>
                  </button>
                </th>
                <th class="num">
                  <button type="button" class="sort-btn num" @click="toggleTableSort('clicks_30d')">
                    {{ t('statistics.table.columns.days30') }}
                    <span class="sort-indicator">{{ getTableSortIndicator('clicks_30d') }}</span>
                  </button>
                </th>
                <th class="num">
                  <button type="button" class="sort-btn num" @click="toggleTableSort('clicks_90d')">
                    {{ t('statistics.table.columns.days90') }}
                    <span class="sort-indicator">{{ getTableSortIndicator('clicks_90d') }}</span>
                  </button>
                </th>
                <th class="num">
                  <button type="button" class="sort-btn num" @click="toggleTableSort('clicks_365d')">
                    {{ t('statistics.table.columns.days365') }}
                    <span class="sort-indicator">{{ getTableSortIndicator('clicks_365d') }}</span>
                  </button>
                </th>
                <th class="num">
                  <button type="button" class="sort-btn num" @click="toggleTableSort('clicks_total')">
                    {{ t('statistics.table.columns.total') }}
                    <span class="sort-indicator">{{ getTableSortIndicator('clicks_total') }}</span>
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in tableDisplayRows"
                :key="row.site_id ?? 'home'"
                :class="{ home: row.site_id === null }"
              >
                <td class="name-cell" :data-label="t('statistics.table.columns.siteName')">
                  {{ row.site_id === null ? t('statistics.table.home') : row.site_name }}
                </td>
                <td class="url-cell" :data-label="t('statistics.table.columns.url')">
                  <a :href="row.site_url" target="_blank" rel="noreferrer" class="url-link">
                    {{ row.site_url }}
                  </a>
                </td>
                <td class="num" :data-label="t('statistics.table.columns.today')">{{ row.clicks_today }}</td>
                <td class="num" :data-label="t('statistics.table.columns.days7')">{{ row.clicks_7d }}</td>
                <td class="num" :data-label="t('statistics.table.columns.days30')">{{ row.clicks_30d }}</td>
                <td class="num" :data-label="t('statistics.table.columns.days90')">{{ row.clicks_90d }}</td>
                <td class="num" :data-label="t('statistics.table.columns.days365')">{{ row.clicks_365d }}</td>
                <td class="num" :data-label="t('statistics.table.columns.total')">{{ row.clicks_total }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { fetchStatsOverview, fetchSiteRanking, fetchStatsTable, fetchStatsTrend } from '../../api/stats.js'

const { t } = useI18n()

const overview = ref({ home: { day: 0, month: 0, year: 0, total: 0 }, sites_total: 0 })
const rankingItems = ref([])
const tableItems = ref([])
const trendItems = ref([])
const loading = ref(false)
const error = ref('')

const rankingRange = ref('day')
const rankingLimit = ref(20)
const trendDays = ref(30)

const tableQuery = ref('')
const tableSortKey = ref(null)
const tableSortDir = ref('desc')

const maxRankingCount = computed(() => {
  return Math.max(...rankingItems.value.map(item => item.click_count), 1)
})

const maxTrendValue = computed(() => {
  return Math.max(
    ...trendItems.value.map(item => Math.max(item.home_count, item.site_click_count)),
    1
  )
})

const loadStats = async () => {
  loading.value = true
  error.value = ''
  try {
    const [overviewData, rankingData, trendData, tableData] = await Promise.all([
      fetchStatsOverview(),
      fetchSiteRanking({ range: rankingRange.value, limit: rankingLimit.value }),
      fetchStatsTrend({ days: trendDays.value }),
      fetchStatsTable()
    ])

    overview.value = overviewData
    rankingItems.value = rankingData.items || []
    trendItems.value = trendData.items || []
    tableItems.value = tableData.items || []
  } catch (err) {
    console.error('Failed to load statistics:', err)
    error.value = err.message || 'Failed to load statistics. Please check console for details.'
  } finally {
    loading.value = false
  }
}

const resetTableSort = () => {
  tableSortKey.value = null
  tableSortDir.value = 'desc'
}

const toggleTableSort = (key) => {
  if (tableSortKey.value === key) {
    tableSortDir.value = tableSortDir.value === 'desc' ? 'asc' : 'desc'
    return
  }
  tableSortKey.value = key
  tableSortDir.value = 'desc'
}

const getTableSortIndicator = (key) => {
  if (tableSortKey.value !== key) return ''
  return tableSortDir.value === 'desc' ? '▼' : '▲'
}

const tableDisplayRows = computed(() => {
  const raw = Array.isArray(tableItems.value) ? tableItems.value : []
  const homeRow = raw.find(row => row.site_id === null) || null
  const siteRows = raw.filter(row => row.site_id !== null)

  const query = String(tableQuery.value || '').trim().toLowerCase()
  let filteredRows = siteRows
  if (query) {
    filteredRows = siteRows.filter((row) => {
      const name = String(row.site_name || '').toLowerCase()
      const url = String(row.site_url || '').toLowerCase()
      return name.includes(query) || url.includes(query)
    })
  }

  let sortedRows = filteredRows
  if (tableSortKey.value) {
    const key = tableSortKey.value
    const dir = tableSortDir.value
    const indexById = new Map(siteRows.map((row, idx) => [row.site_id, idx]))
    sortedRows = [...filteredRows].sort((a, b) => {
      const av = Number(a[key] || 0)
      const bv = Number(b[key] || 0)
      if (av === bv) {
        return (indexById.get(a.site_id) ?? 0) - (indexById.get(b.site_id) ?? 0)
      }
      return dir === 'desc' ? bv - av : av - bv
    })
  }

  const rows = []
  if (homeRow) rows.push(homeRow)
  rows.push(...sortedRows)
  return rows
})

const getRankBarWidth = (count) => {
  return (count / maxRankingCount.value) * 100
}

const getTrendBarHeight = (value) => {
  return (value / maxTrendValue.value) * 100
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// 监听参数变化自动刷新
watch([rankingRange, rankingLimit, trendDays], () => {
  loadStats()
})

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.statistics-view {
  max-width: 1600px;
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

.select-input,
.number-input {
  padding: 0.5rem 0.75rem;
  background: rgba(20, 121, 191, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  color: white;
  font-size: 0.875rem;
}

.number-input {
  width: 80px;
}

.refresh-btn {
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
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.25);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.stat-card:hover {
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.stat-card.highlight {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0.15) 100%);
  border-color: rgba(255, 255, 255, 0.4);
}

.stat-label {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
}

.data-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.ranking-panel,
.trend-panel,
.table-panel {
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
  padding: 1.5rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 1.5rem 0;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.rank-number {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 0.5rem;
  font-weight: 700;
  color: #ffffff;
  flex-shrink: 0;
}

.rank-info {
  flex: 1;
  min-width: 0;
}

.rank-name {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rank-count {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.5);
}

.rank-bar {
  flex: 1;
  height: 0.5rem;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 0.25rem;
  overflow: hidden;
}

.rank-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #ffffff 0%, rgba(255, 255, 255, 0.7) 100%);
  transition: width 0.5s ease;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 1rem 0;
  min-height: 250px;
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
  height: 200px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
}

.bar {
  flex: 1;
  border-radius: 0.25rem 0.25rem 0 0;
  transition: all 0.3s ease;
  min-height: 2px;
  cursor: pointer;
}

.bar.home {
  background: linear-gradient(180deg, #ffffff 0%, rgba(255, 255, 255, 0.7) 100%);
}

.bar.sites {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0.5) 100%);
}

.bar:hover {
  opacity: 0.8;
}

.bar-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.6);
}

.legend {
  display: flex;
  gap: 1.5rem;
  justify-content: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.legend-color {
  width: 1rem;
  height: 1rem;
  border-radius: 0.25rem;
}

.legend-color.home {
  background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
}

.legend-color.sites {
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%);
}

.table-panel {
  margin-top: 2rem;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.table-search {
  width: min(360px, 100%);
  padding: 0.55rem 0.75rem;
  background: rgba(20, 121, 191, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.75rem;
  color: white;
  font-size: 0.9rem;
}

.table-search::placeholder {
  color: rgba(255, 255, 255, 0.55);
}

.table-sortbar {
  display: none;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.sort-chip {
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.78);
  border-radius: 999px;
  padding: 0.45rem 0.7rem;
  font-size: 0.8rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.sort-chip.active {
  background: rgba(96, 165, 250, 0.25);
  border-color: rgba(96, 165, 250, 0.45);
  color: rgba(255, 255, 255, 0.92);
}

.chip-indicator {
  opacity: 0.8;
  min-width: 1rem;
  text-align: center;
}

.table-wrapper {
  width: 100%;
  overflow-x: auto;
}

.stats-table {
  width: 100%;
  min-width: 980px;
  border-collapse: collapse;
}

.stats-table th,
.stats-table td {
  padding: 0.75rem 0.875rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  vertical-align: middle;
}

.stats-table th {
  text-align: left;
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  white-space: nowrap;
}

.stats-table td {
  color: rgba(255, 255, 255, 0.78);
  font-size: 0.9rem;
}

.stats-table td.num,
.stats-table th.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.sort-btn {
  background: transparent;
  border: none;
  color: inherit;
  font: inherit;
  padding: 0;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.sort-btn.num {
  width: 100%;
  justify-content: flex-end;
}

.sort-indicator {
  opacity: 0.75;
  font-size: 0.75rem;
  min-width: 1rem;
  text-align: center;
}

.sort-btn:hover .sort-indicator {
  opacity: 1;
}

.stats-table tr.home td {
  background: rgba(255, 255, 255, 0.04);
}

.name-cell {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
}

.url-cell {
  min-width: 220px;
}

.url-link {
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  border-bottom: 1px dotted rgba(255, 255, 255, 0.35);
}

.url-link:hover {
  color: rgba(255, 255, 255, 0.9);
  border-bottom-color: rgba(255, 255, 255, 0.65);
}

.loading,
.empty {
  text-align: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.5);
}

.error-message {
  text-align: center;
  padding: 2rem;
  color: #f87171;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 1rem;
  margin-bottom: 2rem;
}

.error-message p {
  margin: 0 0 1rem 0;
  font-size: 1rem;
}

.retry-btn {
  padding: 0.5rem 1rem;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 0.5rem;
  color: #f87171;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.875rem;
}

.retry-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

@media (max-width: 1200px) {
  .data-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .statistics-view {
    max-width: 100%;
    overflow-x: hidden;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .page-subtitle {
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .stat-card {
    padding: 0.875rem;
  }

  .stat-label {
    font-size: 0.75rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .stat-value {
    font-size: 1.25rem;
  }

  .controls {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }

  .control-group {
    width: 100%;
  }

  .control-group label {
    font-size: 0.8rem;
  }

  .select-input,
  .number-input {
    width: 100%;
  }

  .refresh-btn {
    width: 100%;
    justify-content: center;
  }

  .section-title {
    font-size: 1rem;
    word-break: break-word;
  }

  .ranking-panel,
  .trend-panel,
  .table-panel {
    padding: 1rem;
    overflow-x: hidden;
  }

  .table-header {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }

  .table-sortbar {
    display: flex;
  }

  /* 移动端使用卡片布局替代表格 */
  .table-wrapper {
    overflow-x: visible;
  }

  .stats-table {
    display: block;
    min-width: 0;
  }

  .stats-table thead {
    display: none;
  }

  .stats-table tbody {
    display: block;
  }

  .stats-table tr {
    display: block;
    background: rgba(20, 121, 191, 0.3);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 1rem;
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .stats-table tr.home {
    border-color: rgba(96, 165, 250, 0.45);
  }

  .stats-table td {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.45rem 0;
    border: none;
    text-align: left;
  }

  .stats-table td::before {
    content: attr(data-label);
    color: rgba(255, 255, 255, 0.55);
    font-size: 0.8rem;
    flex: 0 0 auto;
  }

  .stats-table td.name-cell {
    display: block;
    padding: 0;
    margin-bottom: 0.5rem;
    font-size: 1.05rem;
  }

  .stats-table td.name-cell::before {
    content: none;
  }

  .stats-table td.url-cell {
    display: block;
    padding: 0;
    margin-bottom: 0.75rem;
  }

  .stats-table td.url-cell::before {
    content: none;
  }

  .stats-table td.url-cell a {
    word-break: break-all;
  }

  .stats-table td.num {
    font-variant-numeric: tabular-nums;
  }

  .ranking-item {
    gap: 0.5rem;
    flex-wrap: nowrap;
  }

  .rank-number {
    width: 1.5rem;
    height: 1.5rem;
    font-size: 0.75rem;
    flex-shrink: 0;
  }

  .rank-info {
    min-width: 0;
    flex: 1;
  }

  .rank-name {
    font-size: 0.85rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .rank-count {
    font-size: 0.75rem;
    white-space: nowrap;
  }

  .rank-bar {
    flex: 0 0 30%;
    min-width: 60px;
  }

  .trend-chart {
    gap: 0.2rem;
    padding: 0.5rem;
    min-height: 160px;
    overflow-x: auto;
    overflow-y: hidden;
  }

  .trend-bar {
    min-width: 30px;
  }

  .bar-container {
    height: 120px;
  }

  .bar-label {
    font-size: 0.65rem;
    white-space: nowrap;
  }

  .legend {
    flex-direction: row;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  .legend-item {
    font-size: 0.75rem;
  }
}
</style>
