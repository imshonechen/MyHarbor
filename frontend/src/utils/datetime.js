/**
 * 格式化日期时间为本地时区显示
 * @param {string|Date} dateInput - ISO 8601 格式的日期字符串或 Date 对象
 * @returns {string} 格式化后的日期时间字符串，格式：YYYY-MM-DD HH:mm:ss
 */
export function formatDateTime(dateInput) {
  if (!dateInput) return 'N/A'

  const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput

  // 检查日期是否有效
  if (isNaN(date.getTime())) return 'Invalid Date'

  // 使用 toLocaleString 自动转换为本地时区
  const formatted = date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })

  // 将格式从 "YYYY/MM/DD HH:mm:ss" 转换为 "YYYY-MM-DD HH:mm:ss"
  return formatted.replace(/\//g, '-')
}

/**
 * 格式化日期为 YYYY-MM-DD 格式
 * @param {string|Date} dateInput - ISO 8601 格式的日期字符串或 Date 对象
 * @returns {string} 格式化后的日期字符串
 */
export function formatDate(dateInput) {
  if (!dateInput) return 'N/A'

  const date = typeof dateInput === 'string' ? new Date(dateInput) : dateInput

  if (isNaN(date.getTime())) return 'Invalid Date'

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}
