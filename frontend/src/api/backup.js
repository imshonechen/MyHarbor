import { getAuthToken } from './client.js'

/**
 * 导出备份数据
 */
export async function exportBackup() {
  const token = getAuthToken()
  if (!token) {
    throw new Error('Unauthorized')
  }

  const response = await fetch('/api/backup/export', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })

  if (!response.ok) {
    throw new Error('Failed to export backup')
  }

  // 返回 blob 供调用方处理
  return await response.blob()
}

/**
 * 导入备份数据
 * @param {File} file - JSON 备份文件
 * @param {string} strategy - 导入策略: 'skip' 或 'overwrite'
 */
export async function importBackup(file, strategy = 'skip') {
  const token = getAuthToken()
  if (!token) {
    throw new Error('Unauthorized')
  }

  const formData = new FormData()
  formData.append('file', file)
  formData.append('strategy', strategy)

  const response = await fetch('/api/backup/import', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || error.message || 'Failed to import backup')
  }

  const payload = await response.json()

  if (payload.code !== 0) {
    throw new Error(payload.message || 'Failed to import backup')
  }

  return payload.data
}
