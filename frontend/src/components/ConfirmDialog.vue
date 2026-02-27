<template>
  <div class="dialog-overlay" @click="$emit('cancel')">
    <div class="dialog" @click.stop>
      <div class="dialog-header">
        <h3 class="dialog-title">{{ title }}</h3>
      </div>
      <div class="dialog-body">
        <p class="dialog-message">{{ message }}</p>
      </div>
      <div class="dialog-footer">
        <button @click="$emit('cancel')" class="cancel-btn">
          {{ t('common.cancel') }}
        </button>
        <button @click="$emit('confirm')" class="confirm-btn">
          {{ t('common.confirm') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps({
  title: {
    type: String,
    default: ''
  },
  message: {
    type: String,
    required: true
  }
})

defineEmits(['confirm', 'cancel'])
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.dialog {
  width: 90%;
  max-width: 450px;
  background: rgba(20, 121, 191, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1rem;
  overflow: hidden;
  animation: scaleIn 0.2s ease;
}

@keyframes scaleIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.dialog-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.dialog-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.dialog-body {
  padding: 1.5rem;
}

.dialog-message {
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}

.dialog-footer {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(20, 121, 191, 0.3);
}

.cancel-btn,
.confirm-btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
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

.confirm-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border: none;
  color: white;
}

.confirm-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(239, 68, 68, 0.3);
}
</style>
