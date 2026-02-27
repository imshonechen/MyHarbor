import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import en from './en'

// 从 localStorage 获取保存的语言设置，默认为中文
const savedLocale = localStorage.getItem('locale') || 'zh-CN'

const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: savedLocale, // 默认语言
  fallbackLocale: 'zh-CN', // 回退语言
  messages: {
    'zh-CN': zhCN,
    'en': en
  }
})

export default i18n
