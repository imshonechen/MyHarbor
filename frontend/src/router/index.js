import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import { getAuthToken } from '../api/client.js'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/admin/dashboard'
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('../views/admin/DashboardView.vue')
        },
        {
          path: 'sites',
          name: 'sites',
          component: () => import('../views/admin/SitesView.vue')
        },
        {
          path: 'statistics',
          name: 'statistics',
          component: () => import('../views/admin/StatisticsView.vue')
        },
        {
          path: 'monitoring',
          name: 'monitoring',
          component: () => import('../views/admin/MonitoringView.vue')
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/admin/SettingsView.vue')
        }
      ]
    },
    {
      path: '/admin/login',
      name: 'login',
      component: () => import('../views/admin/LoginView.vue')
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = getAuthToken()

  if (to.meta.requiresAuth && !token) {
    // 需要认证但没有 token，跳转到登录页
    next('/admin/login')
  } else if (to.path === '/admin/login' && token) {
    // 已登录用户访问登录页，跳转到 dashboard
    next('/admin/dashboard')
  } else {
    next()
  }
})

export default router
