<template>
  <div class="drawer-overlay" @click="handleOverlayClick">
    <div class="drawer" @click.stop>
      <div class="drawer-header">
        <h2 class="drawer-title">{{ isEdit ? t('siteForm.titleEdit') : t('siteForm.titleAdd') }}</h2>
        <button @click="$emit('close')" class="close-btn">✕</button>
      </div>

      <form @submit.prevent="handleSubmit" class="drawer-body">
        <div class="form-group">
          <label for="name">{{ t('siteForm.fields.name') }}</label>
          <input
            id="name"
            v-model="form.name"
            type="text"
            class="form-input"
            :placeholder="t('siteForm.fields.namePlaceholder')"
            required
          />
        </div>

        <div class="form-group">
          <label for="url">{{ t('siteForm.fields.url') }}</label>
          <input
            id="url"
            v-model="form.url"
            type="text"
            class="form-input"
            :placeholder="t('siteForm.fields.urlPlaceholder')"
            required
          />
        </div>

        <div class="form-group">
          <label for="logo">{{ t('siteForm.fields.logo') }}</label>
          <div class="logo-row">
            <input
              id="logo"
              v-model="form.logo"
              type="text"
              class="form-input"
              :placeholder="t('siteForm.fields.logoPlaceholder')"
            />
            <button
              type="button"
              class="logo-fetch-btn"
              @click="handleFetchLogo"
              :disabled="fetchingLogo"
            >
              {{ fetchingLogo ? t('siteForm.logoFetch.loading') : t('siteForm.logoFetch.button') }}
            </button>
            <span v-if="logoFetchMessage" class="logo-fetch-message">{{ logoFetchMessage }}</span>
          </div>
        </div>

        <div class="form-group">
          <label for="sort_order">{{ t('siteForm.fields.sortOrder') }}</label>
          <input
            id="sort_order"
            v-model.number="form.sort_order"
            type="number"
            class="form-input"
            placeholder="10"
          />
          <small class="form-hint">{{ t('siteForm.fields.sortOrderHint') }}</small>
        </div>

        <div class="form-group">
          <label for="tags">{{ t('siteForm.fields.tags') }}</label>
          <input
            id="tags"
            v-model="form.tags"
            type="text"
            class="form-input"
            :placeholder="t('siteForm.fields.tagsPlaceholder')"
          />
          <small class="form-hint">{{ t('siteForm.fields.tagsHint') }}</small>
        </div>

        <div class="form-group">
          <label for="description">{{ t('siteForm.fields.description') }}</label>
          <textarea
            id="description"
            v-model="form.description"
            class="form-textarea"
            rows="3"
            :placeholder="t('siteForm.fields.descriptionPlaceholder')"
          ></textarea>
        </div>

        <div class="form-group checkbox-group">
          <label class="checkbox-label">
            <input
              v-model="form.is_public"
              type="checkbox"
              class="form-checkbox"
            />
            <span>{{ t('siteForm.fields.isPublic') }}</span>
          </label>
          <small class="form-hint">{{ t('siteForm.fields.isPublicHint') }}</small>
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>

        <div class="drawer-footer">
          <button type="button" @click="$emit('close')" class="cancel-btn">
            {{ t('siteForm.buttons.cancel') }}
          </button>
          <button type="submit" class="submit-btn" :disabled="saving">
            {{ saving ? t('siteForm.buttons.saving') : (isEdit ? t('siteForm.buttons.update') : t('siteForm.buttons.add')) }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { createSite, updateSite, fetchSiteLogo } from '../api/sites.js'

const { t } = useI18n()

const props = defineProps({
  site: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'saved'])

const isEdit = computed(() => !!props.site)

const form = ref({
  name: '',
  url: '',
  logo: '',
  sort_order: 9999,
  tags: '',
  description: '',
  is_public: true
})

const saving = ref(false)
const error = ref('')
const fetchingLogo = ref(false)
const logoFetchMessage = ref('')

onMounted(() => {
  if (props.site) {
    form.value = {
      name: props.site.name || '',
      url: props.site.url || '',
      logo: props.site.logo || '',
      sort_order: props.site.sort_order || 9999,
      tags: props.site.tags || '',
      description: props.site.description || '',
      is_public: props.site.is_public !== undefined ? props.site.is_public : true
    }
  }
})

const handleOverlayClick = () => {
  emit('close')
}

const handleFetchLogo = async () => {
  logoFetchMessage.value = ''

  let url = form.value.url.trim()
  if (!url) {
    logoFetchMessage.value = t('siteForm.logoFetch.noUrl')
    return
  }

  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url
  }

  fetchingLogo.value = true
  try {
    const response = await fetchSiteLogo(url)
    const logoUrl = response?.logo_url || response?.data?.logo_url
    if (logoUrl) {
      form.value.logo = logoUrl
      logoFetchMessage.value = ''
    } else {
      logoFetchMessage.value = t('siteForm.logoFetch.notFound')
    }
  } catch (err) {
    console.error('Failed to fetch logo:', err)
    logoFetchMessage.value = t('siteForm.logoFetch.failed')
  } finally {
    fetchingLogo.value = false
  }
}

const handleSubmit = async () => {
  saving.value = true
  error.value = ''

  try {
    // 自动补全 URL 协议
    let url = form.value.url.trim()
    if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url
    }

    // 处理标签
    const tags = form.value.tags
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0)

    const payload = {
      name: form.value.name.trim(),
      url: url,
      logo: form.value.logo.trim() || null,
      sort_order: form.value.sort_order,
      tags: tags,
      description: form.value.description.trim() || null,
      is_public: form.value.is_public
    }

    if (isEdit.value) {
      await updateSite(props.site.id, payload)
    } else {
      await createSite(payload)
    }

    emit('saved')
  } catch (err) {
    console.error('Failed to save site:', err)
    error.value = err.message || 'Failed to save site'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(20, 121, 191, 0.4);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.drawer {
  width: 100%;
  max-width: 500px;
  background: rgba(20, 121, 191, 0.95);
  backdrop-filter: blur(12px);
  border-left: 1px solid rgba(255, 255, 255, 0.15);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.drawer-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.close-btn {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1.25rem;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  color: rgba(255, 255, 255, 1);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
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

.logo-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.logo-row .form-input {
  flex: 1 1 240px;
  min-width: 0;
}

.logo-fetch-btn {
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
}

.logo-fetch-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.25);
}

.logo-fetch-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.logo-fetch-message {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.75);
  white-space: nowrap;
}

.checkbox-group {
  gap: 0.75rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: normal;
}

.form-checkbox {
  width: 1.25rem;
  height: 1.25rem;
  cursor: pointer;
}

.error-message {
  padding: 0.75rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.5rem;
  color: #f87171;
  font-size: 0.875rem;
}

.drawer-footer {
  display: flex;
  gap: 1rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(20, 121, 191, 0.3);
}

.cancel-btn,
.submit-btn {
  flex: 1;
  padding: 0.875rem 1.5rem;
  border-radius: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #ffffff;
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.submit-btn {
  background: linear-gradient(135deg, #ffffff 0%, rgba(255, 255, 255, 0.8) 100%);
  border: none;
  color: #00BFFF;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(255, 255, 255, 0.3);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .drawer {
    max-width: 100%;
  }

  .drawer-header {
    padding: 1rem 1.5rem;
  }

  .drawer-title {
    font-size: 1.25rem;
  }

  .drawer-body {
    padding: 1.5rem;
    gap: 1.25rem;
  }

  .drawer-footer {
    padding: 1rem 1.5rem;
    flex-direction: column;
  }

  .cancel-btn,
  .submit-btn {
    width: 100%;
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
}
</style>
