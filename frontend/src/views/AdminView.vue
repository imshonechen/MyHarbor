<template>
  <main class="aurora-page">
    <section class="glass-shell spacer-stack">
      <header class="row-split">
        <div>
          <h1 class="hero-title">MyHarbor Admin</h1>
          <p class="hero-desc">Control panel with dark glass aesthetic and neon feedback.</p>
        </div>
        <a href="/" class="pill-btn secondary">Back Home</a>
      </header>

      <section v-if="!isLoggedIn" class="glass-section" style="max-width:420px; margin:0 auto;">
        <h2 style="margin:0 0 0.8rem; font-size:1.2rem;">Admin Login</h2>
        <form class="spacer-stack" @submit.prevent="onLogin">
          <input v-model.trim="loginForm.username" type="text" required placeholder="Username" class="pill-input" />
          <input v-model="loginForm.password" type="password" required placeholder="Password" class="pill-input" />
          <button type="submit" class="pill-btn">Login</button>
        </form>
        <p v-if="loginError" class="error-text" style="margin:0.6rem 0 0;">{{ loginError }}</p>
      </section>

      <section v-else class="space-y-6">
        <div class="row-split">
          <p class="text-muted small-text">Logged in as <strong>{{ adminUser }}</strong></p>
          <button type="button" class="pill-btn secondary" @click="onLogout">Logout</button>
        </div>

        <section class="glass-section spacer-stack">
          <div class="row-split">
            <h2 style="margin:0; font-size:1.16rem;">Visit Statistics</h2>
            <div class="action-row">
              <select v-model="rankingRange" class="pill-select" style="width:auto;">
                <option value="day">day</option>
                <option value="month">month</option>
                <option value="year">year</option>
                <option value="total">total</option>
              </select>
              <select v-model.number="trendDays" class="pill-select" style="width:auto;">
                <option :value="7">7d</option>
                <option :value="30">30d</option>
                <option :value="60">60d</option>
                <option :value="90">90d</option>
              </select>
              <input v-model.number="rankingLimit" type="number" min="1" max="100" class="pill-input" style="width:94px;" />
              <button type="button" class="pill-btn secondary" @click="loadStats">Refresh</button>
            </div>
          </div>

          <p v-if="statsError" class="error-text">{{ statsError }}</p>
          <p v-if="statsLoading" class="text-muted small-text">Loading stats...</p>

          <template v-else>
            <div class="surface-grid">
              <article class="metric-card"><div class="metric-label">Home Day</div><div class="metric-value">{{ overview.home.day }}</div></article>
              <article class="metric-card"><div class="metric-label">Home Month</div><div class="metric-value">{{ overview.home.month }}</div></article>
              <article class="metric-card"><div class="metric-label">Home Year</div><div class="metric-value">{{ overview.home.year }}</div></article>
              <article class="metric-card"><div class="metric-label">Home Total</div><div class="metric-value">{{ overview.home.total }}</div></article>
              <article class="metric-card"><div class="metric-label">Site Total</div><div class="metric-value">{{ overview.sites_total }}</div></article>
            </div>

            <div class="form-grid-two">
              <div class="glass-section">
                <h3 style="margin:0 0 0.5rem;">Top Sites</h3>
                <table class="table-glass">
                  <thead>
                    <tr>
                      <th>Site</th>
                      <th>Clicks</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="item in rankingItems" :key="item.site_id">
                      <td>{{ item.site_name }}</td>
                      <td>{{ item.click_count }}</td>
                    </tr>
                    <tr v-if="rankingItems.length === 0">
                      <td colspan="2" class="text-soft">No data</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="glass-section">
                <h3 style="margin:0 0 0.6rem;">Trend</h3>
                <div class="spacer-stack">
                  <article v-for="item in trendItems" :key="item.date" class="small-text">
                    <div class="row-split">
                      <span class="text-soft">{{ item.date }}</span>
                      <span class="text-soft">h{{ item.home_count }} / s{{ item.site_click_count }}</span>
                    </div>
                    <div class="trend-track" style="margin-top:0.26rem;">
                      <div class="trend-bar home" :style="{ width: `${Math.max(2, (item.home_count / trendMax) * 100)}%` }"></div>
                    </div>
                    <div class="trend-track" style="margin-top:0.25rem;">
                      <div class="trend-bar site" :style="{ width: `${Math.max(2, (item.site_click_count / trendMax) * 100)}%` }"></div>
                    </div>
                  </article>
                </div>
              </div>
            </div>
          </template>
        </section>

        <section class="glass-section spacer-stack">
          <div class="row-split">
            <h2 style="margin:0; font-size:1.16rem;">Uptime Legend</h2>
            <div class="action-row">
              <select v-model.number="selectedSiteId" class="pill-select" style="width:auto;">
                <option :value="0">Select site</option>
                <option v-for="site in sites" :key="site.id" :value="site.id">{{ site.name }}</option>
              </select>
              <select v-model.number="statusDays" class="pill-select" style="width:auto;">
                <option :value="7">7d</option>
                <option :value="14">14d</option>
                <option :value="30">30d</option>
              </select>
              <button type="button" class="pill-btn secondary" :disabled="!selectedSiteId" @click="loadStatusLogs">
                Refresh
              </button>
            </div>
          </div>

          <p class="text-muted small-text">
            {{ selectedSiteName ? `Current site: ${selectedSiteName}` : "Please select a site." }}
          </p>
          <p v-if="logsError" class="error-text">{{ logsError }}</p>
          <p v-if="logsLoading" class="text-muted small-text">Loading logs...</p>
          <template v-else-if="selectedSiteId">
            <div class="chip-row small-text text-muted">
              <span>online {{ statusLegendSummary.online }}</span>
              <span>offline {{ statusLegendSummary.offline }}</span>
              <span>no-data {{ statusLegendSummary.nodata }}</span>
            </div>
            <div class="legend-grid">
              <span
                v-for="item in statusLegend"
                :key="item.date"
                class="legend-cell"
                :class="statusToColorClass(item.status)"
                :title="legendTooltip(item)"
              ></span>
            </div>
          </template>
        </section>

        <section class="glass-section spacer-stack">
          <div class="row-split">
            <h2 style="margin:0; font-size:1.16rem;">{{ editingId ? "Edit Site" : "Add Site" }}</h2>
            <label class="chip-row small-text text-muted">
              <input v-model="siteForm.is_public" type="checkbox" />
              Public site
            </label>
          </div>
          <form class="form-grid-two" @submit.prevent="onSubmitSite">
            <input v-model.trim="siteForm.name" type="text" required placeholder="Site name" class="pill-input" />
            <input v-model.trim="siteForm.url" type="text" required placeholder="https://example.com" class="pill-input" />
            <input v-model.trim="siteForm.logo" type="text" placeholder="Logo URL" class="pill-input" />
            <input v-model.number="siteForm.sort_order" type="number" placeholder="Sort order" class="pill-input" />
            <input v-model.trim="siteForm.tags" type="text" placeholder="tags,comma,separated" class="pill-input full-span" />
            <textarea v-model.trim="siteForm.description" rows="2" placeholder="Description" class="pill-textarea full-span"></textarea>
            <div class="action-row full-span">
              <button type="submit" class="pill-btn">{{ editingId ? "Update" : "Create" }}</button>
              <button v-if="editingId" type="button" class="pill-btn secondary" @click="resetForm">Cancel</button>
            </div>
          </form>
          <p v-if="actionError" class="error-text">{{ actionError }}</p>
        </section>

        <section class="glass-section spacer-stack">
          <h2 style="margin:0; font-size:1.16rem;">System Settings</h2>
          <form class="form-grid-two" @submit.prevent="onSaveSettings">
            <input v-model.trim="settingsForm.site_title" type="text" placeholder="Site title" class="pill-input" />
            <input v-model.trim="settingsForm.icp_number" type="text" placeholder="ICP number" class="pill-input" />
            <textarea v-model.trim="settingsForm.site_description" rows="2" placeholder="Site description" class="pill-textarea full-span"></textarea>
            <input v-model.trim="settingsForm.copyright" type="text" placeholder="Copyright" class="pill-input full-span" />
            <input v-model.trim="settingsForm.admin_username" type="text" placeholder="Admin username" class="pill-input" />
            <input v-model.trim="settingsForm.admin_password" type="password" placeholder="New admin password" class="pill-input" />
            <input v-model.trim="settingsForm.admin_route_code" type="text" placeholder="Admin route code" class="pill-input" />
            <input v-model.number="settingsForm.check_interval" type="number" min="1" max="1440" placeholder="Check interval" class="pill-input" />
            <div class="full-span">
              <button type="submit" class="pill-btn">Save Settings</button>
            </div>
          </form>
          <p v-if="settingsMessage" class="ok-text">{{ settingsMessage }}</p>
          <p v-if="settingsError" class="error-text">{{ settingsError }}</p>
        </section>

        <section class="glass-section spacer-stack">
          <div class="row-split">
            <h2 style="margin:0; font-size:1.16rem;">Site List</h2>
            <div class="action-row">
              <input v-model.trim="query" type="text" placeholder="Search by name or URL" class="pill-input" style="min-width:230px;" />
              <button type="button" class="pill-btn secondary" :disabled="!sortDirty || !canDragSort" @click="onSaveSort">Save Order</button>
              <button type="button" class="pill-btn secondary" @click="loadSites">Refresh</button>
            </div>
          </div>
          <p class="small-text text-soft">Drag rows to reorder. Search must be empty while dragging.</p>
          <section v-if="loading" class="text-muted small-text">Loading...</section>
          <section v-else class="glass-section" style="overflow:auto;">
            <table class="table-glass" style="min-width:760px;">
              <thead>
                <tr>
                  <th>Sort</th>
                  <th>Name</th>
                  <th>URL</th>
                  <th>Status</th>
                  <th>Public</th>
                  <th>Tags</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="site in filteredSites"
                  :key="site.id"
                  :style="{ cursor: canDragSort ? 'move' : 'default' }"
                  :draggable="canDragSort"
                  @dragstart="onDragStart(site.id)"
                  @dragover.prevent
                  @drop.prevent="onDrop(site.id)"
                  @dragend="onDragEnd"
                >
                  <td>::</td>
                  <td>{{ site.name }}</td>
                  <td><a :href="site.url" target="_blank" rel="noreferrer" class="text-muted">{{ site.url }}</a></td>
                  <td>
                    <span class="status-pill" :class="site.status">
                      <span class="status-dot" :class="site.status"></span>{{ site.status }}
                    </span>
                  </td>
                  <td>
                    <button type="button" class="pill-btn secondary small-text" @click="onTogglePublic(site)">
                      {{ site.is_public ? "Public" : "Private" }}
                    </button>
                  </td>
                  <td>{{ site.tags }}</td>
                  <td>
                    <div class="action-row">
                      <button type="button" class="pill-btn secondary small-text" @click="startEdit(site)">Edit</button>
                      <button type="button" class="pill-btn danger small-text" @click="onDeleteSite(site)">Delete</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="filteredSites.length === 0">
                  <td colspan="7" class="text-soft">No sites</td>
                </tr>
              </tbody>
            </table>
          </section>
        </section>
      </section>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref, watch } from "vue"
import { fetchCurrentAdmin, loginAdmin, logoutAdmin } from "../api/auth"
import { fetchSystemConfig, updateSystemConfig } from "../api/config"
import { fetchSiteRanking, fetchStatsOverview, fetchStatsTrend } from "../api/stats"
import { createSite, deleteSite, fetchAllSites, fetchSiteStatusLogs, toggleSitePublic, updateSite, updateSiteSort } from "../api/sites"

const loginForm = ref({ username: "admin", password: "" })
const loginError = ref("")
const actionError = ref("")
const isLoggedIn = ref(false)
const adminUser = ref("")
const sites = ref([])
const loading = ref(false)
const query = ref("")
const editingId = ref(0)
const sortDirty = ref(false)
const draggingSiteId = ref(0)
const settingsError = ref("")
const settingsMessage = ref("")
const statsLoading = ref(false)
const statsError = ref("")
const logsLoading = ref(false)
const logsError = ref("")
const rankingRange = ref("day")
const rankingLimit = ref(10)
const trendDays = ref(30)
const selectedSiteId = ref(0)
const statusDays = ref(30)
const rankingItems = ref([])
const trendItems = ref([])
const statusLogs = ref([])
const overview = ref({ home: { day: 0, month: 0, year: 0, total: 0 }, sites_total: 0 })

const defaultSiteForm = () => ({
  name: "",
  url: "",
  logo: "",
  description: "",
  tags: "",
  is_public: true,
  sort_order: 9999
})

const siteForm = ref(defaultSiteForm())
const settingsForm = ref({
  site_title: "",
  site_description: "",
  copyright: "",
  icp_number: "",
  admin_username: "",
  admin_password: "",
  admin_route_code: "",
  check_interval: 5
})

const filteredSites = computed(() => {
  const q = query.value.toLowerCase()
  if (!q) return sites.value
  return sites.value.filter((site) => `${site.name} ${site.url}`.toLowerCase().includes(q))
})

const canDragSort = computed(() => !query.value)

const selectedSiteName = computed(() => {
  const selected = sites.value.find((site) => site.id === selectedSiteId.value)
  return selected ? selected.name : ""
})

const trendMax = computed(() => {
  if (!trendItems.value.length) return 1
  return Math.max(1, ...trendItems.value.map((item) => Math.max(Number(item.home_count || 0), Number(item.site_click_count || 0))))
})

const statusLegend = computed(() => {
  const dayCount = Number(statusDays.value || 30)
  const dateMap = new Map()
  for (const item of statusLogs.value) {
    const dateKey = String(item.checked_at || "").slice(0, 10)
    if (!dateKey) continue
    const current = dateMap.get(dateKey)
    if (!current || String(item.checked_at) > String(current.checked_at)) {
      dateMap.set(dateKey, item)
    }
  }

  const now = new Date()
  const anchor = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()))
  const result = []
  for (let offset = dayCount - 1; offset >= 0; offset -= 1) {
    const d = new Date(anchor)
    d.setUTCDate(anchor.getUTCDate() - offset)
    const key = d.toISOString().slice(0, 10)
    const item = dateMap.get(key)
    result.push({
      date: key,
      status: item?.status || "nodata",
      response_time: item?.response_time ?? null
    })
  }
  return result
})

const statusLegendSummary = computed(() =>
  statusLegend.value.reduce(
    (acc, item) => {
      if (item.status === "online") acc.online += 1
      else if (item.status === "offline") acc.offline += 1
      else acc.nodata += 1
      return acc
    },
    { online: 0, offline: 0, nodata: 0 }
  )
)

function normalizeTagInput(raw) {
  return raw.split(",").map((item) => item.trim()).filter(Boolean)
}

function resetForm() {
  editingId.value = 0
  siteForm.value = defaultSiteForm()
  actionError.value = ""
}

function statusToColorClass(status) {
  if (status === "online") return "legend-online"
  if (status === "offline") return "legend-offline"
  return "legend-nodata"
}

function legendTooltip(item) {
  if (item.status === "nodata") return `${item.date} | no data`
  return `${item.date} | ${item.status} | ${item.response_time === null ? "-" : `${item.response_time}ms`}`
}

async function loadSites() {
  try {
    loading.value = true
    actionError.value = ""
    const data = await fetchAllSites({ size: 100 })
    sites.value = data.items || []
    sortDirty.value = false

    if (!sites.value.length) {
      selectedSiteId.value = 0
      statusLogs.value = []
      return
    }

    const exists = sites.value.some((item) => item.id === selectedSiteId.value)
    if (!exists) {
      selectedSiteId.value = sites.value[0].id
    }
    await loadStatusLogs()
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to load sites"
    if (message.toLowerCase().includes("unauthorized") || message.includes("401")) onLogout()
    actionError.value = message
  } finally {
    loading.value = false
  }
}

async function loadSettings() {
  try {
    settingsError.value = ""
    const config = await fetchSystemConfig()
    settingsForm.value = {
      site_title: config.site_title || "",
      site_description: config.site_description || "",
      copyright: config.copyright || "",
      icp_number: config.icp_number || "",
      admin_username: config.admin_username || "",
      admin_password: "",
      admin_route_code: config.admin_route_code || "",
      check_interval: Number(config.check_interval || 5)
    }
  } catch (err) {
    settingsError.value = err instanceof Error ? err.message : "Failed to load settings"
  }
}

async function loadStats() {
  try {
    statsLoading.value = true
    statsError.value = ""
    const [overviewData, rankingData, trendData] = await Promise.all([
      fetchStatsOverview(),
      fetchSiteRanking({ range: rankingRange.value, limit: Number(rankingLimit.value || 10) }),
      fetchStatsTrend({ days: Number(trendDays.value || 30) })
    ])
    overview.value = overviewData
    rankingItems.value = rankingData.items || []
    trendItems.value = trendData.items || []
  } catch (err) {
    statsError.value = err instanceof Error ? err.message : "Failed to load stats"
  } finally {
    statsLoading.value = false
  }
}

async function loadStatusLogs() {
  if (!selectedSiteId.value) {
    statusLogs.value = []
    return
  }
  try {
    logsLoading.value = true
    logsError.value = ""
    const data = await fetchSiteStatusLogs(selectedSiteId.value, Number(statusDays.value || 30))
    statusLogs.value = data.items || []
  } catch (err) {
    logsError.value = err instanceof Error ? err.message : "Failed to load status logs"
  } finally {
    logsLoading.value = false
  }
}

function onDragStart(siteId) {
  if (!canDragSort.value) return
  draggingSiteId.value = siteId
}

function onDragEnd() {
  draggingSiteId.value = 0
}

function onDrop(targetSiteId) {
  if (!canDragSort.value) return
  const sourceSiteId = draggingSiteId.value
  if (!sourceSiteId || sourceSiteId === targetSiteId) return
  const sourceIndex = sites.value.findIndex((site) => site.id === sourceSiteId)
  const targetIndex = sites.value.findIndex((site) => site.id === targetSiteId)
  if (sourceIndex < 0 || targetIndex < 0) return
  const [moved] = sites.value.splice(sourceIndex, 1)
  sites.value.splice(targetIndex, 0, moved)
  draggingSiteId.value = 0
  sortDirty.value = true
}

async function onSaveSort() {
  try {
    actionError.value = ""
    const items = sites.value.map((site, index) => ({ id: site.id, sort_order: (index + 1) * 10 }))
    await updateSiteSort(items)
    await loadSites()
  } catch (err) {
    actionError.value = err instanceof Error ? err.message : "Save sort failed"
  }
}

async function onSaveSettings() {
  try {
    settingsError.value = ""
    settingsMessage.value = ""
    const payload = {
      site_title: settingsForm.value.site_title,
      site_description: settingsForm.value.site_description,
      copyright: settingsForm.value.copyright,
      icp_number: settingsForm.value.icp_number,
      admin_username: settingsForm.value.admin_username,
      admin_route_code: settingsForm.value.admin_route_code,
      check_interval: Number(settingsForm.value.check_interval || 5)
    }
    if (settingsForm.value.admin_password) payload.admin_password = settingsForm.value.admin_password
    const result = await updateSystemConfig(payload)
    settingsForm.value.admin_password = ""
    if (result.relogin_required) {
      onLogout()
      loginError.value = "Settings saved. Please login again with updated credentials."
      return
    }
    settingsMessage.value = result.new_route_code ? `Settings saved. New route code: ${result.new_route_code}` : "Settings saved."
    await loadSettings()
  } catch (err) {
    settingsError.value = err instanceof Error ? err.message : "Failed to save settings"
  }
}

async function onLogin() {
  try {
    loginError.value = ""
    await loginAdmin(loginForm.value.username, loginForm.value.password)
    const me = await fetchCurrentAdmin()
    adminUser.value = me.username
    isLoggedIn.value = true
    await loadSettings()
    await loadSites()
    await loadStats()
  } catch (err) {
    loginError.value = err instanceof Error ? err.message : "Login failed"
  }
}

function onLogout() {
  logoutAdmin()
  isLoggedIn.value = false
  adminUser.value = ""
  sites.value = []
  rankingItems.value = []
  trendItems.value = []
  statusLogs.value = []
  selectedSiteId.value = 0
  loginForm.value.password = ""
  settingsMessage.value = ""
  settingsError.value = ""
  statsError.value = ""
  logsError.value = ""
  resetForm()
}

function startEdit(site) {
  editingId.value = site.id
  siteForm.value = {
    name: site.name || "",
    url: site.url || "",
    logo: site.logo || "",
    description: site.description || "",
    tags: site.tags || "",
    is_public: !!site.is_public,
    sort_order: site.sort_order ?? 9999
  }
}

async function onSubmitSite() {
  try {
    actionError.value = ""

    // 验证必填字段
    if (!siteForm.value.name || !siteForm.value.name.trim()) {
      actionError.value = "站点名称不能为空"
      return
    }

    if (!siteForm.value.url || !siteForm.value.url.trim()) {
      actionError.value = "站点地址不能为空"
      return
    }

    // 自动补全 URL 协议
    let url = siteForm.value.url.trim()
    if (url && !url.match(/^https?:\/\//i)) {
      url = 'https://' + url
    }

    const payload = {
      name: siteForm.value.name.trim(),
      url: url,
      logo: siteForm.value.logo || null,
      description: siteForm.value.description || null,
      tags: normalizeTagInput(siteForm.value.tags),
      is_public: !!siteForm.value.is_public,
      sort_order: Number(siteForm.value.sort_order || 9999)
    }
    if (editingId.value) await updateSite(editingId.value, payload)
    else await createSite(payload)
    resetForm()
    await loadSites()
    await loadStats()
  } catch (err) {
    // 解析后端返回的详细错误信息
    if (err instanceof Error) {
      let errorMsg = err.message

      // 尝试解析 FastAPI 的验证错误格式
      try {
        const match = errorMsg.match(/Value error, (.+)/)
        if (match) {
          errorMsg = match[1]
        }
      } catch (e) {
        // 忽略解析错误
      }

      actionError.value = errorMsg
    } else {
      actionError.value = "保存失败"
    }
  }
}

async function onTogglePublic(site) {
  try {
    actionError.value = ""
    await toggleSitePublic(site.id)
    await loadSites()
  } catch (err) {
    actionError.value = err instanceof Error ? err.message : "Toggle failed"
  }
}

async function onDeleteSite(site) {
  if (!window.confirm(`Delete site "${site.name}"?`)) return
  try {
    actionError.value = ""
    await deleteSite(site.id)
    if (editingId.value === site.id) resetForm()
    await loadSites()
    await loadStats()
  } catch (err) {
    actionError.value = err instanceof Error ? err.message : "Delete failed"
  }
}

async function initAdminState() {
  try {
    const me = await fetchCurrentAdmin()
    adminUser.value = me.username
    isLoggedIn.value = true
    await loadSettings()
    await loadSites()
    await loadStats()
  } catch {
    onLogout()
  }
}

watch([rankingRange, rankingLimit, trendDays], () => {
  if (isLoggedIn.value) loadStats()
})

watch([selectedSiteId, statusDays], () => {
  if (isLoggedIn.value) loadStatusLogs()
})

onMounted(() => {
  initAdminState()
})
</script>
