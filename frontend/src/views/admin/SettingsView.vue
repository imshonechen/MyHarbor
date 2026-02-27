<template>
  <div class="settings-view">
    <h1 class="page-title">{{ t('settings.title') }}</h1>
    <p class="page-subtitle">{{ t('settings.subtitle') }}</p>

    <!-- Tab 导航 -->
    <div class="tabs">
      <button
        @click="activeTab = 'site'"
        :class="['tab-btn', { active: activeTab === 'site' }]"
      >
        <span class="icon">🌐</span>
        {{ t('settings.tabs.siteConfig') }}
      </button>
      <button
        @click="activeTab = 'admin'"
        :class="['tab-btn', { active: activeTab === 'admin' }]"
      >
        <span class="icon">👤</span>
        {{ t('settings.tabs.adminAccount') }}
      </button>
      <button
        @click="activeTab = 'monitoring'"
        :class="['tab-btn', { active: activeTab === 'monitoring' }]"
      >
        <span class="icon">⚙️</span>
        {{ t('settings.tabs.monitoring') }}
      </button>
      <button
        @click="activeTab = 'backup'"
        :class="['tab-btn', { active: activeTab === 'backup' }]"
      >
        <span class="icon">💾</span>
        {{ t('settings.tabs.backup') }}
      </button>
    </div>

    <!-- Tab 内容 -->
    <div class="tab-content">
      <!-- 站点配置 -->
      <div v-if="activeTab === 'site'" class="settings-panel">
        <h2 class="panel-title">{{ t('settings.tabs.siteConfig') }}</h2>
        <p class="panel-description">{{ t('settings.siteConfig.descriptionText') }}</p>

        <form @submit.prevent="saveSiteConfig" class="settings-form">
          <div class="form-group">
            <label for="site_title">{{ t('settings.siteConfig.title') }}</label>
            <input
              id="site_title"
              v-model="siteForm.site_title"
              type="text"
              class="form-input"
              placeholder="MyHarbor"
            />
          </div>

          <div class="form-group">
            <label for="site_description">{{ t('settings.siteConfig.description') }}</label>
            <textarea
              id="site_description"
              v-model="siteForm.site_description"
              class="form-textarea"
              rows="4"
              placeholder="Welcome to MyHarbor"
            ></textarea>
          </div>

          <div class="form-group">
            <label for="copyright">{{ t('settings.siteConfig.copyright') }}</label>
            <input
              id="copyright"
              v-model="siteForm.copyright"
              type="text"
              class="form-input"
              placeholder="© 2026 MyHarbor"
            />
          </div>

          <div class="form-group">
            <label for="icp_number">{{ t('settings.siteConfig.icpNumber') }}</label>
            <input
              id="icp_number"
              v-model="siteForm.icp_number"
              type="text"
              class="form-input"
              :placeholder="t('settings.siteConfig.icpPlaceholder')"
            />
          </div>

          <div v-if="siteError" class="error-message">{{ siteError }}</div>
          <div v-if="siteSuccess" class="success-message">{{ siteSuccess }}</div>

          <button type="submit" class="submit-btn" :disabled="siteSaving">
            {{ siteSaving ? t('common.saving') : t('settings.siteConfig.saveButton') }}
          </button>
        </form>
      </div>

      <!-- 管理员账号 -->
      <div v-if="activeTab === 'admin'" class="settings-panel">
        <h2 class="panel-title">{{ t('settings.tabs.adminAccount') }}</h2>
        <p class="panel-description">{{ t('settings.adminAccount.descriptionText') }}</p>

        <form @submit.prevent="saveAdminConfig" class="settings-form">
          <div class="form-group">
            <label for="admin_username">{{ t('settings.adminAccount.username') }}</label>
            <input
              id="admin_username"
              v-model="adminForm.admin_username"
              type="text"
              class="form-input"
              placeholder="admin"
            />
          </div>

          <div class="form-group">
            <label for="admin_password">{{ t('settings.adminAccount.newPassword') }}</label>
            <input
              id="admin_password"
              v-model="adminForm.admin_password"
              type="password"
              class="form-input"
              :placeholder="t('settings.adminAccount.passwordHint')"
            />
            <small class="form-hint">{{ t('settings.adminAccount.passwordNote') }}</small>
          </div>

          <div class="form-group">
            <label for="admin_route_code">{{ t('settings.adminAccount.routeCode') }}</label>
            <input
              id="admin_route_code"
              v-model="adminForm.admin_route_code"
              type="text"
              class="form-input"
              placeholder="a3x9k2b1"
              maxlength="32"
            />
            <small class="form-hint warning">
              {{ t('settings.adminAccount.routeCodeWarning') }}
            </small>
          </div>

          <div v-if="adminError" class="error-message">{{ adminError }}</div>
          <div v-if="adminSuccess" class="success-message">{{ adminSuccess }}</div>

          <button type="submit" class="submit-btn" :disabled="adminSaving">
            {{ adminSaving ? t('common.saving') : t('settings.adminAccount.saveButton') }}
          </button>
        </form>
      </div>

      <!-- 监控配置 -->
      <div v-if="activeTab === 'monitoring'" class="settings-panel">
        <h2 class="panel-title">{{ t('settings.tabs.monitoring') }}</h2>
        <p class="panel-description">{{ t('settings.monitoring.descriptionText') }}</p>

        <form @submit.prevent="saveMonitoringConfig" class="settings-form">
          <div class="form-group">
            <label for="check_interval">{{ t('settings.monitoring.checkInterval') }}</label>
            <input
              id="check_interval"
              v-model.number="monitoringForm.check_interval"
              type="number"
              min="1"
              max="1440"
              class="form-input"
              placeholder="5"
            />
            <small class="form-hint">
              {{ t('settings.monitoring.checkIntervalHint') }}
            </small>
          </div>

          <div v-if="monitoringError" class="error-message">{{ monitoringError }}</div>
          <div v-if="monitoringSuccess" class="success-message">{{ monitoringSuccess }}</div>

          <button type="submit" class="submit-btn" :disabled="monitoringSaving">
            {{ monitoringSaving ? t('common.saving') : t('settings.monitoring.saveButton') }}
          </button>
        </form>
      </div>

      <!-- 备份与恢复 -->
      <div v-if="activeTab === 'backup'" class="settings-panel">
        <h2 class="panel-title">{{ t('settings.tabs.backup') }}</h2>
        <p class="panel-description">{{ t('settings.backup.descriptionText') }}</p>

        <div class="settings-form">
          <!-- 导出备份 -->
          <div class="backup-section">
            <h3 class="section-title">{{ t('settings.backup.export.title') }}</h3>
            <p class="section-description">{{ t('settings.backup.export.description') }}</p>

            <div v-if="exportError" class="error-message">{{ exportError }}</div>
            <div v-if="exportSuccess" class="success-message">{{ exportSuccess }}</div>

            <button @click="handleExport" class="submit-btn" :disabled="exportLoading">
              {{ exportLoading ? t('settings.backup.export.exporting') : t('settings.backup.export.button') }}
            </button>
          </div>

          <!-- 导入备份 -->
          <div class="backup-section">
            <h3 class="section-title">{{ t('settings.backup.import.title') }}</h3>
            <p class="section-description">{{ t('settings.backup.import.description') }}</p>

            <div class="form-group">
              <label for="backup_file">{{ t('settings.backup.import.fileLabel') }}</label>
              <input
                id="backup_file"
                ref="fileInput"
                type="file"
                accept=".json"
                @change="handleFileSelect"
                class="form-input"
              />
            </div>

            <div class="form-group">
              <label for="import_strategy">{{ t('settings.backup.import.strategyLabel') }}</label>
              <select
                id="import_strategy"
                v-model="importStrategy"
                class="form-input"
              >
                <option value="skip">{{ t('settings.backup.import.strategySkip') }}</option>
                <option value="overwrite">{{ t('settings.backup.import.strategyOverwrite') }}</option>
              </select>
              <small class="form-hint">{{ t('settings.backup.import.strategyHint') }}</small>
            </div>

            <div v-if="importError" class="error-message">{{ importError }}</div>
            <div v-if="importSuccess" class="success-message">{{ importSuccess }}</div>

            <button @click="handleImport" class="submit-btn" :disabled="importLoading || !selectedFile">
              {{ importLoading ? t('settings.backup.import.importing') : t('settings.backup.import.button') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { fetchSystemConfig, updateSystemConfig } from '../../api/config.js'
import { exportBackup, importBackup } from '../../api/backup.js'

const router = useRouter()
const { t } = useI18n()

const activeTab = ref('site')

// 表单数据
const siteForm = ref({
  site_title: '',
  site_description: '',
  copyright: '',
  icp_number: ''
})

const adminForm = ref({
  admin_username: '',
  admin_password: '',
  admin_route_code: ''
})

const monitoringForm = ref({
  check_interval: 5
})

// 状态
const siteSaving = ref(false)
const adminSaving = ref(false)
const monitoringSaving = ref(false)

const siteError = ref('')
const adminError = ref('')
const monitoringError = ref('')

const siteSuccess = ref('')
const adminSuccess = ref('')
const monitoringSuccess = ref('')

// 备份状态
const exportLoading = ref(false)
const importLoading = ref(false)
const exportError = ref('')
const exportSuccess = ref('')
const importError = ref('')
const importSuccess = ref('')
const selectedFile = ref(null)
const fileInput = ref(null)
const importStrategy = ref('skip')

const loadSettings = async () => {
  try {
    const config = await fetchSystemConfig()

    siteForm.value = {
      site_title: config.site_title || '',
      site_description: config.site_description || '',
      copyright: config.copyright || '',
      icp_number: config.icp_number || ''
    }

    adminForm.value = {
      admin_username: config.admin_username || '',
      admin_password: '',
      admin_route_code: config.admin_route_code || ''
    }

    monitoringForm.value = {
      check_interval: config.check_interval || 5
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
  }
}

const saveSiteConfig = async () => {
  siteSaving.value = true
  siteError.value = ''
  siteSuccess.value = ''

  try {
    await updateSystemConfig(siteForm.value)
    siteSuccess.value = t('settings.messages.siteConfigSaved')
    setTimeout(() => {
      siteSuccess.value = ''
    }, 3000)
  } catch (error) {
    siteError.value = error.message || t('settings.messages.siteConfigError')
  } finally {
    siteSaving.value = false
  }
}

const saveAdminConfig = async () => {
  adminSaving.value = true
  adminError.value = ''
  adminSuccess.value = ''

  try {
    const payload = {
      admin_username: adminForm.value.admin_username,
      admin_route_code: adminForm.value.admin_route_code
    }

    // 只有填写了密码才发送
    if (adminForm.value.admin_password) {
      payload.admin_password = adminForm.value.admin_password
    }

    const result = await updateSystemConfig(payload)

    adminSuccess.value = t('settings.messages.adminSettingsSaved')

    // 如果路由码改变了，需要跳转到新路径
    if (result.new_route_code && result.new_route_code !== adminForm.value.admin_route_code) {
      adminSuccess.value += ' ' + t('settings.messages.redirecting')
      setTimeout(() => {
        window.location.href = `/admin/dashboard`
      }, 2000)
    } else {
      setTimeout(() => {
        adminSuccess.value = ''
      }, 3000)
    }

    // 清空密码字段
    adminForm.value.admin_password = ''
  } catch (error) {
    adminError.value = error.message || t('settings.messages.adminSettingsError')
  } finally {
    adminSaving.value = false
  }
}

const saveMonitoringConfig = async () => {
  monitoringSaving.value = true
  monitoringError.value = ''
  monitoringSuccess.value = ''

  try {
    await updateSystemConfig(monitoringForm.value)
    monitoringSuccess.value = t('settings.messages.monitoringSaved')
    setTimeout(() => {
      monitoringSuccess.value = ''
    }, 3000)
  } catch (error) {
    monitoringError.value = error.message || t('settings.messages.monitoringError')
  } finally {
    monitoringSaving.value = false
  }
}

const handleExport = async () => {
  exportLoading.value = true
  exportError.value = ''
  exportSuccess.value = ''

  try {
    const blob = await exportBackup()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `myharbor-backup-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    exportSuccess.value = t('settings.backup.export.success')
    setTimeout(() => {
      exportSuccess.value = ''
    }, 3000)
  } catch (error) {
    exportError.value = error.message || t('settings.backup.export.error')
  } finally {
    exportLoading.value = false
  }
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    importError.value = ''
    importSuccess.value = ''
  }
}

const handleImport = async () => {
  if (!selectedFile.value) {
    importError.value = t('settings.backup.import.noFileError')
    return
  }

  importLoading.value = true
  importError.value = ''
  importSuccess.value = ''

  try {
    await importBackup(selectedFile.value, importStrategy.value)
    importSuccess.value = t('settings.backup.import.success')

    // 清空文件选择
    selectedFile.value = null
    if (fileInput.value) {
      fileInput.value.value = ''
    }

    setTimeout(() => {
      importSuccess.value = ''
    }, 3000)
  } catch (error) {
    importError.value = error.message || t('settings.backup.import.error')
  } finally {
    importLoading.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-view {
  max-width: 900px;
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

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  font-weight: 500;
}

.tab-btn:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.1);
}

.tab-btn.active {
  color: #ffffff;
  border-bottom-color: #ffffff;
}

.tab-content {
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
  padding: 2rem;
}

.settings-panel {
  max-width: 600px;
}

.panel-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 0.5rem 0;
}

.panel-description {
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 2rem 0;
  font-size: 0.9rem;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.form-input,
.form-textarea {
  padding: 0.75rem;
  background: rgba(20, 121, 191, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  color: white;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #ffffff;
  background: rgba(20, 121, 191, 0.4);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.form-hint {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.form-hint.warning {
  color: #fbbf24;
}

.error-message {
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.5rem;
  color: #f87171;
  font-size: 0.875rem;
}

.success-message {
  padding: 0.75rem;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 0.5rem;
  color: #4ade80;
  font-size: 0.875rem;
}

.submit-btn {
  padding: 0.875rem 1.5rem;
  background: linear-gradient(135deg, #ffffff 0%, rgba(255, 255, 255, 0.8) 100%);
  border: none;
  border-radius: 0.75rem;
  color: #00BFFF;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(255, 255, 255, 0.3);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.backup-section {
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  margin-bottom: 1.5rem;
}

.backup-section:last-child {
  margin-bottom: 0;
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 0.5rem 0;
}

.section-description {
  color: rgba(255, 255, 255, 0.6);
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 1.5rem;
  }

  .page-subtitle {
    font-size: 0.875rem;
    margin-bottom: 1.5rem;
  }

  .tab-content {
    padding: 1.5rem;
  }

  .tabs {
    flex-direction: column;
    border-bottom: none;
    gap: 0;
  }

  .tab-btn {
    border-bottom: none;
    border-left: 2px solid transparent;
    justify-content: flex-start;
    padding: 0.875rem 1rem;
  }

  .tab-btn:hover {
    border-bottom-color: transparent;
    border-left-color: rgba(255, 255, 255, 0.3);
  }

  .tab-btn.active {
    border-left-color: #60a5fa;
    border-bottom-color: transparent;
  }

  .settings-panel {
    max-width: 100%;
  }

  .panel-title {
    font-size: 1.25rem;
  }

  .panel-description {
    font-size: 0.85rem;
  }

  .settings-form {
    gap: 1.25rem;
  }

  .form-group label {
    font-size: 0.8rem;
  }

  .form-input,
  .form-textarea {
    font-size: 0.875rem;
  }

  .form-hint {
    font-size: 0.75rem;
  }

  .submit-btn {
    font-size: 0.875rem;
  }

  .backup-section {
    padding: 1.25rem;
  }

  .section-title {
    font-size: 1rem;
  }

  .section-description {
    font-size: 0.8rem;
  }
}
</style>
