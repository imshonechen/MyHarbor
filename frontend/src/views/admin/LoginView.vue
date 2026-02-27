<template>
  <div class="login-view">
    <div class="login-container">
      <div class="login-header">
        <h1 class="logo">{{ t('login.title') }}</h1>
        <p class="subtitle">{{ t('login.subtitle') }}</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">{{ t('login.username') }}</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            class="form-input"
            :placeholder="t('login.usernamePlaceholder')"
            required
            autofocus
          />
        </div>

        <div class="form-group">
          <label for="password">{{ t('login.password') }}</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            class="form-input"
            :placeholder="t('login.passwordPlaceholder')"
            required
          />
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>

        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? t('login.loggingIn') : t('login.loginButton') }}
        </button>
      </form>

      <div class="login-footer">
        <button @click="goHome" class="home-link">
          {{ t('common.backToHome') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { loginAdmin } from '../../api/auth.js'

const router = useRouter()
const { t } = useI18n()

const form = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    await loginAdmin(form.value.username, form.value.password)
    router.push('/admin/dashboard')
  } catch (err) {
    console.error('Login failed:', err)
    if (err.message.includes('too many')) {
      error.value = t('login.errors.tooManyAttempts')
    } else if (err.message.includes('401') || err.message.includes('Invalid')) {
      error.value = t('login.errors.invalidCredentials')
    } else {
      error.value = err.message || t('login.errors.loginFailed')
    }
  } finally {
    loading.value = false
  }
}

const goHome = () => {
  router.push('/')
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #00BFFF 0%, #B200FF 50%, #FF1493 100%);
  padding: 2rem;
}

.login-container {
  width: 100%;
  max-width: 420px;
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1.5rem;
  padding: 3rem;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.logo {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 0.5rem 0;
}

.subtitle {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.login-form {
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

.form-input {
  padding: 0.875rem 1rem;
  background: rgba(20, 121, 191, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.75rem;
  color: white;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #ffffff;
  background: rgba(20, 121, 191, 0.4);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
}

.error-message {
  padding: 0.875rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.75rem;
  color: #f87171;
  font-size: 0.875rem;
  text-align: center;
}

.login-btn {
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #ffffff 0%, rgba(255, 255, 255, 0.8) 100%);
  border: none;
  border-radius: 0.75rem;
  color: #00BFFF;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 0.5rem;
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(255, 255, 255, 0.3);
}

.login-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.login-footer {
  margin-top: 2rem;
  text-align: center;
}

.home-link {
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 0.5rem;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.875rem;
}

.home-link:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 480px) {
  .login-container {
    padding: 2rem;
  }

  .logo {
    font-size: 2rem;
  }
}
</style>
