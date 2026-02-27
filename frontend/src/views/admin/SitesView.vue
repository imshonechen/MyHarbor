<template>
  <div class="sites-view">
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ t('sites.title') }}</h1>
        <p class="page-subtitle">{{ t('sites.subtitle') }}</p>
      </div>
      <button @click="openAddSite" class="primary-btn">
        <span class="icon">➕</span>
        {{ t('sites.addNew') }}
      </button>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="search-box">
        <span class="search-icon">🔍</span>
        <input
          v-model="query"
          type="text"
          :placeholder="t('sites.searchPlaceholder')"
          class="search-input"
        />
      </div>
      <div class="toolbar-actions">
        <button @click="handleCheckAll" class="secondary-btn" :disabled="checking">
          <span class="icon">🔄</span>
          {{ checking ? t('sites.checking') : t('sites.checkAll') }}
        </button>
        <button @click="loadSites" class="secondary-btn">
          <span class="icon">↻</span>
          {{ t('common.refresh') }}
        </button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="filters">
      <button
        @click="filterPublic = null"
        :class="['filter-btn', { active: filterPublic === null }]"
      >
        {{ t('sites.filters.all') }}
      </button>
      <button
        @click="filterPublic = true"
        :class="['filter-btn', { active: filterPublic === true }]"
      >
        {{ t('sites.filters.publicOnly') }}
      </button>
      <button
        @click="filterPublic = false"
        :class="['filter-btn', { active: filterPublic === false }]"
      >
        {{ t('sites.filters.hiddenOnly') }}
      </button>
    </div>

    <!-- 站点列表 -->
    <div v-if="loading" class="loading">{{ t('sites.loadingSites') }}</div>
    <div v-else-if="filteredSites.length === 0" class="empty">
      {{ t('sites.noSites') }}
    </div>
    <div v-else class="sites-table-container">
      <table class="sites-table">
        <thead>
          <tr>
            <th style="width: 60px">{{ t('sites.table.sort') }}</th>
            <th>{{ t('sites.table.name') }}</th>
            <th>{{ t('sites.table.url') }}</th>
            <th style="width: 100px">{{ t('sites.table.status') }}</th>
            <th style="width: 100px">{{ t('sites.table.public') }}</th>
            <th>{{ t('sites.table.tags') }}</th>
            <th style="width: 200px">{{ t('sites.table.actions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="site in filteredSites"
            :key="site.id"
            draggable="true"
            @dragstart="onDragStart($event, site)"
            @dragover.prevent
            @drop="onDrop($event, site)"
            class="site-row"
          >
            <td class="drag-handle">
              <span class="icon">⋮⋮</span>
              <span class="sort-order">{{ site.sort_order }}</span>
            </td>
            <td class="site-name">{{ site.name }}</td>
            <td class="site-url">
              <a :href="site.url" target="_blank" rel="noopener">{{ site.url }}</a>
            </td>
            <td>
              <span :class="['status-badge', site.status]">{{ getStatusText(site.status) }}</span>
            </td>
            <td>
              <button
                @click="togglePublic(site)"
                :class="['toggle-btn', { active: site.is_public }]"
              >
                {{ site.is_public ? '✓' : '✗' }}
              </button>
            </td>
            <td class="tags-cell">
              <span v-for="tag in site.tags_list" :key="tag" class="tag">{{ tag }}</span>
            </td>
            <td class="actions-cell">
              <button @click="editSite(site)" class="action-btn edit">{{ t('sites.actions.edit') }}</button>
              <button @click="checkSite(site)" class="action-btn check" :disabled="checkingSiteId === site.id">
                {{ checkingSiteId === site.id ? t('sites.checking') : t('sites.actions.check') }}
              </button>
              <button @click="deleteSite(site)" class="action-btn delete">{{ t('sites.actions.delete') }}</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="sortDirty" class="save-sort-bar">
        <span>{{ t('sites.orderChanged') }}</span>
        <button @click="saveSortOrder" class="primary-btn">{{ t('sites.saveOrder') }}</button>
      </div>
    </div>

    <!-- 站点表单抽屉 -->
    <SiteFormDrawer
      v-if="showDrawer"
      :site="editingSite"
      @close="closeDrawer"
      @saved="handleSiteSaved"
    />

    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-if="showDeleteDialog"
      :title="t('sites.deleteConfirm.title')"
      :message="t('sites.deleteConfirm.message', { name: deletingSite?.name })"
      @confirm="confirmDelete"
      @cancel="showDeleteDialog = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  fetchAllSites,
  toggleSitePublic,
  deleteSite as apiDeleteSite,
  updateSiteSort,
  checkSite as apiCheckSite,
  checkAllSites as apiCheckAllSites
} from '../../api/sites.js'
import SiteFormDrawer from '../../components/SiteFormDrawer.vue'
import ConfirmDialog from '../../components/ConfirmDialog.vue'

const { t } = useI18n()

const sites = ref([])
const loading = ref(false)
const checking = ref(false)
const checkingSiteId = ref(null)
const query = ref('')
const filterPublic = ref(null)
const sortDirty = ref(false)
const showDrawer = ref(false)
const editingSite = ref(null)
const showDeleteDialog = ref(false)
const deletingSite = ref(null)
const draggedSite = ref(null)

const filteredSites = computed(() => {
  let result = sites.value

  // 搜索过滤
  if (query.value) {
    const q = query.value.toLowerCase()
    result = result.filter(
      s => s.name.toLowerCase().includes(q) || s.url.toLowerCase().includes(q)
    )
  }

  // 公开状态过滤
  if (filterPublic.value !== null) {
    result = result.filter(s => s.is_public === filterPublic.value)
  }

  return result
})

const getStatusText = (status) => {
  const statusMap = {
    'online': t('common.online'),
    'offline': t('common.offline'),
    'unknown': t('common.unknown')
  }
  return statusMap[status] || status
}

const loadSites = async () => {
  loading.value = true
  try {
    const data = await fetchAllSites()
    sites.value = data.items || []
    sortDirty.value = false
  } catch (error) {
    console.error('Failed to load sites:', error)
  } finally {
    loading.value = false
  }
}

const openAddSite = () => {
  editingSite.value = null
  showDrawer.value = true
}

const editSite = (site) => {
  editingSite.value = site
  showDrawer.value = true
}

const closeDrawer = () => {
  showDrawer.value = false
  editingSite.value = null
}

const handleSiteSaved = () => {
  closeDrawer()
  loadSites()
}

const togglePublic = async (site) => {
  try {
    await toggleSitePublic(site.id)
    site.is_public = !site.is_public
  } catch (error) {
    console.error('Failed to toggle public status:', error)
  }
}

const deleteSite = (site) => {
  deletingSite.value = site
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  try {
    await apiDeleteSite(deletingSite.value.id)
    showDeleteDialog.value = false
    deletingSite.value = null
    await loadSites()
  } catch (error) {
    console.error('Failed to delete site:', error)
  }
}

const checkSite = async (site) => {
  checkingSiteId.value = site.id
  try {
    const result = await apiCheckSite(site.id)
    site.status = result.status
    site.last_check_time = result.checked_at
  } catch (error) {
    console.error('Failed to check site:', error)
  } finally {
    checkingSiteId.value = null
  }
}

const handleCheckAll = async () => {
  checking.value = true
  try {
    await apiCheckAllSites()
    await loadSites()
  } catch (error) {
    console.error('Failed to check all sites:', error)
  } finally {
    checking.value = false
  }
}

// 拖拽排序
const onDragStart = (event, site) => {
  draggedSite.value = site
  event.dataTransfer.effectAllowed = 'move'
}

const onDrop = (event, targetSite) => {
  if (!draggedSite.value || draggedSite.value.id === targetSite.id) return

  const draggedIndex = sites.value.findIndex(s => s.id === draggedSite.value.id)
  const targetIndex = sites.value.findIndex(s => s.id === targetSite.id)

  // 重新排列数组
  const newSites = [...sites.value]
  const [removed] = newSites.splice(draggedIndex, 1)
  newSites.splice(targetIndex, 0, removed)

  // 更新 sort_order
  newSites.forEach((site, index) => {
    site.sort_order = (index + 1) * 10
  })

  sites.value = newSites
  sortDirty.value = true
  draggedSite.value = null
}

const saveSortOrder = async () => {
  try {
    const items = sites.value.map(s => ({ id: s.id, sort_order: s.sort_order }))
    await updateSiteSort(items)
    sortDirty.value = false
  } catch (error) {
    console.error('Failed to save sort order:', error)
  }
}

onMounted(() => {
  loadSites()
})
</script>

<style scoped>
.sites-view {
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
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
  margin: 0;
}

.primary-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #ffffff 0%, rgba(255, 255, 255, 0.8) 100%);
  border: none;
  border-radius: 0.75rem;
  color: #00BFFF;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(255, 255, 255, 0.3);
}

.toolbar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.search-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 0.75rem;
}

.search-icon {
  font-size: 1.25rem;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: white;
  font-size: 0.9rem;
}

.toolbar-actions {
  display: flex;
  gap: 0.5rem;
}

.secondary-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.75rem;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.secondary-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
}

.secondary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.filters {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.filter-btn {
  padding: 0.5rem 1rem;
  background: rgba(20, 121, 191, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 0.5rem;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.875rem;
}

.filter-btn:hover {
  border-color: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.9);
}

.filter-btn.active {
  background: rgba(255, 255, 255, 0.25);
  border-color: #ffffff;
  color: #ffffff;
}

.sites-table-container {
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
  overflow: hidden;
}

.sites-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.sites-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  font-size: 0.875rem;
}

.sites-table td {
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.875rem;
}

.site-row {
  cursor: move;
  transition: background 0.3s ease;
}

.site-row:hover {
  background: rgba(255, 255, 255, 0.1);
}

.drag-handle {
  color: rgba(255, 255, 255, 0.4);
}

.drag-handle .icon {
  margin-right: 0.5rem;
}

.site-name {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.site-url a {
  color: #ffffff;
  text-decoration: none;
}

.site-url a:hover {
  text-decoration: underline;
}

.status-badge {
  display: inline-block;
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

.toggle-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-btn.active {
  background: rgba(34, 197, 94, 0.3);
  border-color: #4ade80;
  color: #4ade80;
}

.tags-cell {
  max-width: 200px;
}

.tags-cell .tag {
  display: inline-block;
  margin-right: 0.25rem;
  margin-bottom: 0.25rem;
}

.tag {
  padding: 0.25rem 0.5rem;
  background: rgba(167, 139, 250, 0.2);
  border-radius: 0.25rem;
  font-size: 0.75rem;
  color: #a78bfa;
}

.actions-cell {
  white-space: nowrap;
}

.actions-cell .action-btn {
  display: inline-block;
  margin-right: 0.5rem;
}

.actions-cell .action-btn:last-child {
  margin-right: 0;
}

.action-btn {
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  border: 1px solid;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.75rem;
  font-weight: 500;
}

.action-btn.edit {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  color: #ffffff;
}

.action-btn.edit:hover {
  background: rgba(255, 255, 255, 0.25);
}

.action-btn.check {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.action-btn.check:hover {
  background: rgba(34, 197, 94, 0.2);
}

.action-btn.delete {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.action-btn.delete:hover {
  background: rgba(239, 68, 68, 0.2);
}

.save-sort-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: rgba(255, 255, 255, 0.15);
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

.loading, .empty {
  text-align: center;
  padding: 3rem;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
}

@media (max-width: 1200px) {
  .sites-table {
    font-size: 0.8rem;
  }

  .actions-cell {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .page-title {
    font-size: 1.5rem;
  }

  .page-subtitle {
    font-size: 0.875rem;
  }

  .primary-btn {
    width: 100%;
    justify-content: center;
  }

  .toolbar {
    flex-direction: column;
    gap: 0.75rem;
  }

  .toolbar-actions {
    width: 100%;
    flex-direction: column;
  }

  .secondary-btn {
    width: 100%;
    justify-content: center;
  }

  .filters {
    flex-wrap: wrap;
  }

  .filter-btn {
    flex: 1;
    min-width: 100px;
  }

  /* 移动端使用卡片布局替代表格 */
  .sites-table-container {
    background: transparent;
    border: none;
  }

  .sites-table {
    display: block;
  }

  .sites-table thead {
    display: none;
  }

  .sites-table tbody {
    display: block;
  }

  .site-row {
    display: block;
    background: rgba(20, 121, 191, 0.3);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 1rem;
    padding: 1rem;
    margin-bottom: 1rem;
    cursor: default;
  }

  .sites-table td {
    display: block;
    padding: 0.5rem 0;
    border: none;
    text-align: left;
  }

  .drag-handle {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 0.75rem;
    margin-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .drag-handle .icon {
    margin-right: 0.5rem;
  }

  .site-name {
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
  }

  .site-url {
    margin-bottom: 0.75rem;
  }

  .site-url a {
    word-break: break-all;
  }

  .sites-table td:nth-child(4),
  .sites-table td:nth-child(5) {
    display: inline-block;
    width: auto;
    margin-right: 1rem;
  }

  .sites-table td:nth-child(4)::before {
    content: '状态: ';
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.8rem;
  }

  .sites-table td:nth-child(5)::before {
    content: '公开: ';
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.8rem;
  }

  .tags-cell {
    max-width: 100%;
    margin: 0.5rem 0;
  }

  .actions-cell {
    display: flex;
    flex-direction: row;
    gap: 0.5rem;
    padding-top: 0.75rem;
    margin-top: 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .actions-cell .action-btn {
    flex: 1;
    margin: 0;
    text-align: center;
  }

  .save-sort-bar {
    flex-direction: column;
    gap: 0.75rem;
    text-align: center;
  }

  .save-sort-bar .primary-btn {
    width: 100%;
  }
}
</style>
