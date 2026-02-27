<template>
  <div class="admin-layout">
    <!-- 移动端顶部栏 -->
    <div class="mobile-topbar">
      <div class="mobile-user">
        <span class="icon">👤</span>
        <span class="username">{{ adminUser }}</span>
      </div>
      <div class="mobile-actions">
        <div class="mobile-lang-switcher">
          <button
            @click="switchLocale('zh-CN')"
            class="mobile-lang-btn"
            :class="{ active: locale === 'zh-CN' }"
          >
            中文
          </button>
          <button
            @click="switchLocale('en')"
            class="mobile-lang-btn"
            :class="{ active: locale === 'en' }"
          >
            EN
          </button>
        </div>
        <button @click="handleLogout" class="mobile-logout-btn">
          <span class="icon">🚪</span>
        </button>
      </div>
    </div>

    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1 class="logo">{{ t('login.title') }}</h1>
        <p class="subtitle">{{ t('layout.adminPanel') }}</p>
      </div>

      <nav class="nav-menu">
        <router-link to="/admin/dashboard" class="nav-item" active-class="active">
          <span class="icon">🏠</span>
          <span class="label">{{ t('layout.menu.dashboard') }}</span>
        </router-link>
        <router-link to="/admin/sites" class="nav-item" active-class="active">
          <span class="icon">🌐</span>
          <span class="label">{{ t('layout.menu.sites') }}</span>
        </router-link>
        <router-link to="/admin/statistics" class="nav-item" active-class="active">
          <span class="icon">📈</span>
          <span class="label">{{ t('layout.menu.statistics') }}</span>
        </router-link>
        <router-link to="/admin/monitoring" class="nav-item" active-class="active">
          <span class="icon">💚</span>
          <span class="label">{{ t('layout.menu.monitoring') }}</span>
        </router-link>
        <router-link to="/admin/settings" class="nav-item" active-class="active">
          <span class="icon">⚙️</span>
          <span class="label">{{ t('layout.menu.settings') }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <!-- 语言切换 -->
        <div class="lang-switcher">
          <button
            @click="switchLocale('zh-CN')"
            class="lang-btn"
            :class="{ active: locale === 'zh-CN' }"
          >
            中文
          </button>
          <button
            @click="switchLocale('en')"
            class="lang-btn"
            :class="{ active: locale === 'en' }"
          >
            EN
          </button>
        </div>

        <div class="user-info">
          <span class="icon">👤</span>
          <span class="username">{{ adminUser }}</span>
        </div>
        <button @click="handleLogout" class="logout-btn">
          <span class="icon">🚪</span>
          <span class="label">{{ t('common.logout') }}</span>
        </button>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="content-body">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { logoutAdmin, fetchCurrentAdmin } from '../api/auth.js'

const router = useRouter()
const { t, locale } = useI18n()
const adminUser = ref('')

onMounted(async () => {
  try {
    const user = await fetchCurrentAdmin()
    adminUser.value = user.username
  } catch (error) {
    console.error('Failed to fetch admin user:', error)
    router.push('/admin/login')
  }
})

const handleLogout = () => {
  logoutAdmin()
  router.push('/admin/login')
}

const switchLocale = (lang) => {
  locale.value = lang
  localStorage.setItem('locale', lang)
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
  background: linear-gradient(135deg, #00BFFF 0%, #B200FF 50%, #FF1493 100%);
}

/* 移动端顶部栏 - 默认隐藏 */
.mobile-topbar {
  display: none;
}

/* 侧边栏样式 */
.sidebar {
  width: 240px;
  background: rgba(20, 121, 191, 0.3);
  backdrop-filter: blur(12px);
  border-right: 1px solid rgba(255, 255, 255, 0.15);
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  left: 0;
  top: 0;
  z-index: 100;
}

.sidebar-header {
  padding: 2rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.logo {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #dbeafe 0%, #e9d5ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.subtitle {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 1);
  margin: 0.25rem 0 0 0;
}

.nav-menu {
  flex: 1;
  padding: 1rem 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1.5rem;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
  border-left-color: rgba(255, 255, 255, 0.3);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  border-left-color: #ffffff;
}

.nav-item .icon {
  font-size: 1.25rem;
  width: 1.5rem;
  text-align: center;
}

.nav-item .label {
  font-size: 0.9rem;
  font-weight: 500;
}

.sidebar-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.lang-switcher {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.lang-btn {
  flex: 1;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0.375rem;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.75rem;
  font-weight: 500;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.9);
}

.lang-btn.active {
  background: rgba(96, 165, 250, 0.3);
  border-color: rgba(96, 165, 250, 0.5);
  color: #ffffff;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.5rem;
  color: #f87171;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.875rem;
}

.logout-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
}

/* 主内容区样式 */
.main-content {
  flex: 1;
  margin-left: 240px;
  display: flex;
  flex-direction: column;
}

.content-body {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  /* 显示移动端顶部栏 */
  .mobile-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 50px;
    background: rgba(20, 121, 191, 0.95);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
    padding: 0 1rem;
    z-index: 1001;
  }

  .mobile-user {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.875rem;
  }

  .mobile-user .icon {
    font-size: 1.25rem;
  }

  .mobile-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .mobile-lang-switcher {
    display: flex;
    gap: 0.25rem;
  }

  .mobile-lang-btn {
    padding: 0.375rem 0.625rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 0.375rem;
    color: rgba(255, 255, 255, 0.7);
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 0.75rem;
    font-weight: 500;
  }

  .mobile-lang-btn.active {
    background: rgba(96, 165, 250, 0.3);
    border-color: rgba(96, 165, 250, 0.5);
    color: #ffffff;
  }

  .mobile-logout-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 2rem;
    height: 2rem;
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 0.375rem;
    color: #f87171;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 1rem;
  }

  .mobile-logout-btn:hover {
    background: rgba(239, 68, 68, 0.3);
  }

  .sidebar {
    width: 100%;
    height: auto;
    position: fixed;
    bottom: 0;
    top: auto;
    left: 0;
    right: 0;
    border-right: none;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
    flex-direction: row;
    z-index: 1000;
  }

  .sidebar-header {
    display: none;
  }

  .nav-menu {
    flex: 1;
    padding: 0;
    display: flex;
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
  }

  .nav-item {
    flex: 1;
    min-width: 60px;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 0.75rem 0.5rem;
    gap: 0.25rem;
    border-left: none;
    border-bottom: 3px solid transparent;
  }

  .nav-item:hover {
    border-left-color: transparent;
    border-bottom-color: rgba(255, 255, 255, 0.3);
  }

  .nav-item.active {
    border-left-color: transparent;
    border-bottom-color: #ffffff;
  }

  .nav-item .icon {
    font-size: 1.5rem;
    width: auto;
  }

  .nav-item .label {
    font-size: 0.7rem;
    text-align: center;
  }

  .sidebar-footer {
    display: none;
  }

  .main-content {
    margin-left: 0;
    margin-top: 50px;
    margin-bottom: 70px;
  }

  .content-body {
    padding: 1rem;
  }
}
</style>
