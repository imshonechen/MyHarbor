export default {
  common: {
    confirm: '确认',
    cancel: '取消',
    save: '保存',
    saving: '保存中...',
    delete: '删除',
    edit: '编辑',
    add: '添加',
    search: '搜索',
    loading: '加载中...',
    refresh: '刷新',
    back: '返回',
    backToHome: '← 返回首页',
    logout: '退出登录',
    all: '全部',
    yes: '是',
    no: '否',
    online: '在线',
    offline: '离线',
    unknown: '未知'
  },

  home: {
    searchPlaceholder: '输入名称或描述以搜索...',
    allTags: '所有标签',
    noDescription: '暂无描述'
  },

  login: {
    title: 'MyHarbor',
    subtitle: '管理后台',
    username: '用户名',
    usernamePlaceholder: '请输入用户名',
    password: '密码',
    passwordPlaceholder: '请输入密码',
    loginButton: '登录',
    loggingIn: '登录中...',
    errors: {
      tooManyAttempts: '登录尝试次数过多，请稍后再试',
      invalidCredentials: '用户名或密码错误',
      loginFailed: '登录失败，请重试'
    }
  },

  layout: {
    adminPanel: '管理后台',
    menu: {
      dashboard: '仪表盘',
      sites: '站点管理',
      statistics: '访问统计',
      monitoring: '站点监控',
      settings: '系统设置'
    }
  },

  dashboard: {
    title: '仪表盘',
    welcome: '欢迎来到 MyHarbor 管理后台',
    stats: {
      todayVisits: '今日访问',
      totalSites: '站点总数',
      onlineSites: '在线站点',
      offlineSites: '离线站点'
    },
    quickActions: {
      title: '快捷操作',
      addSite: '添加新站点',
      checkAll: '检测所有站点',
      checking: '检测中...',
      viewStats: '查看统计',
      systemSettings: '系统设置'
    },
    recentSites: {
      title: '最近站点',
      noSites: '暂无站点'
    },
    trend: {
      title: '7天趋势'
    }
  },

  sites: {
    title: '站点管理',
    subtitle: '管理您的站点，检查状态并组织',
    addNew: '添加新站点',
    searchPlaceholder: '搜索站点...',
    checkAll: '检测全部',
    checking: '检测中...',
    filters: {
      all: '全部站点',
      publicOnly: '仅公开',
      hiddenOnly: '仅隐藏'
    },
    table: {
      sort: '排序',
      name: '名称',
      url: '网址',
      status: '状态',
      public: '公开',
      tags: '标签',
      actions: '操作'
    },
    actions: {
      edit: '编辑',
      check: '检测',
      delete: '删除'
    },
    orderChanged: '排序已更改',
    saveOrder: '保存排序',
    noSites: '未找到站点。点击"添加新站点"开始使用。',
    loadingSites: '加载站点中...',
    deleteConfirm: {
      title: '删除站点',
      message: '确定要删除站点 "{name}" 吗？此操作无法撤销。'
    }
  },

  siteForm: {
    titleEdit: '编辑站点',
    titleAdd: '添加新站点',
    fields: {
      name: '站点名称 *',
      namePlaceholder: '我的精彩站点',
      url: '网址 *',
      urlPlaceholder: 'https://example.com',
      logo: 'Logo 网址',
      logoPlaceholder: 'https://example.com/logo.png',
      sortOrder: '排序权重',
      sortOrderHint: '数字越小越靠前',
      tags: '标签',
      tagsPlaceholder: '工具, 文档, API (逗号分隔)',
      tagsHint: '使用逗号分隔多个标签',
      description: '描述',
      descriptionPlaceholder: '站点的简要描述',
      isPublic: '公开站点',
      isPublicHint: '公开站点将在首页显示'
    },
    buttons: {
      cancel: '取消',
      update: '更新站点',
      add: '添加站点',
      saving: '保存中...'
    }
  },

  settings: {
    title: '系统设置',
    subtitle: '配置系统参数和管理员账号',
    tabs: {
      siteConfig: '站点配置',
      adminAccount: '管理员账号',
      monitoring: '监控设置',
      backup: '数据备份'
    },
    siteConfig: {
      title: '站点标题',
      description: '站点描述',
      descriptionText: '配置公开展示的站点信息',
      copyright: '版权信息',
      icpNumber: 'ICP备案号',
      icpPlaceholder: 'ICP备案号（可选）',
      saveButton: '保存站点配置'
    },
    adminAccount: {
      username: '用户名',
      descriptionText: '更新管理员凭证和安全设置',
      newPassword: '新密码',
      passwordHint: '留空则保持当前密码不变',
      passwordNote: '仅在需要更改密码时填写',
      routeCode: '管理后台路由码',
      routeCodeWarning: '⚠️ 更改此项将更新管理后台的访问网址。保存后，您将被重定向到新网址。',
      saveButton: '保存管理员设置'
    },
    monitoring: {
      descriptionText: '配置站点状态检测间隔',
      checkInterval: '检测间隔（分钟）',
      checkIntervalHint: '站点状态检测频率（1-1440分钟）。默认为5分钟。',
      saveButton: '保存监控设置'
    },
    backup: {
      descriptionText: '导出和导入站点数据',
      export: {
        title: '导出备份',
        description: '下载所有站点数据为 JSON 文件',
        button: '导出备份',
        exporting: '导出中...',
        success: '备份导出成功！',
        error: '导出备份失败'
      },
      import: {
        title: '导入备份',
        description: '从 JSON 文件恢复站点数据',
        fileLabel: '备份文件',
        selectFile: '选择文件',
        strategyLabel: '导入策略',
        strategy: '导入策略',
        strategySkip: '跳过已存在的站点',
        strategyOverwrite: '覆盖已存在的站点',
        strategyHint: '选择如何处理已存在的站点',
        button: '导入备份',
        importing: '导入中...',
        noFile: '请先选择备份文件',
        noFileError: '请先选择备份文件',
        success: '备份导入成功！',
        error: '导入备份失败'
      },
      messages: {
        exportSuccess: '备份导出成功！',
        exportError: '导出备份失败',
        importSuccess: '备份导入成功！共 {total} 条，新建 {created} 条，更新 {updated} 条，跳过 {skipped} 条',
        importError: '导入备份失败'
      }
    },
    messages: {
      saveSuccess: '设置保存成功',
      saveError: '保存设置失败',
      siteConfigSaved: '站点配置保存成功！',
      siteConfigError: '保存站点配置失败',
      adminSettingsSaved: '管理员设置保存成功！',
      adminSettingsError: '保存管理员设置失败',
      redirecting: '正在重定向到新的管理后台网址...',
      monitoringSaved: '监控设置保存成功！',
      monitoringError: '保存监控设置失败'
    }
  },

  statistics: {
    title: '访问统计',
    subtitle: '查看站点访问数据和趋势',
    controls: {
      timeRange: '时间范围：',
      trendDays: '趋势天数：',
      topSites: '排行数量：',
      refresh: '刷新'
    },
    ranges: {
      day: '今日',
      month: '本月',
      year: '本年',
      total: '总计'
    },
    days: {
      7: '7天',
      30: '30天',
      60: '60天',
      90: '90天'
    },
    loading: '加载统计数据中...',
    error: '加载失败',
    retry: '重试',
    cards: {
      homeToday: '首页 - 今日',
      homeMonth: '首页 - 本月',
      homeYear: '首页 - 本年',
      homeTotal: '首页 - 总计',
      sitesTotal: '站点 - 总点击'
    },
    ranking: {
      title: '热门站点',
      noData: '暂无数据',
      clicks: '次点击'
    },
    trend: {
      title: '趋势',
      noData: '暂无数据',
      homeVisits: '首页访问',
      siteClicks: '站点点击'
    }
  },

  monitoring: {
    title: '站点监控',
    subtitle: '监控站点运行状态',
    controls: {
      selectSite: '选择站点：',
      days: '天数：',
      checkThisSite: '检测此站点',
      checking: '检测中...',
      checkAllSites: '检测全部站点',
      refresh: '刷新'
    },
    days: {
      1: '1天',
      7: '7天',
      14: '14天',
      30: '30天'
    },
    noSites: '暂无站点',
    emptyState: '请选择一个站点以查看其监控数据',
    loading: '加载监控数据中...',
    stats: {
      online: '在线',
      offline: '离线',
      unknown: '未知',
      noData: '无数据',
      uptime: '在线率'
    },
    calendar: {
      title: '在线日历',
      noData: '暂无监控数据',
      status: '状态：'
    },
    logs: {
      title: '最近状态日志',
      noLogs: '暂无日志',
      time: '时间',
      status: '状态',
      responseTime: '响应时间'
    },
    tooltip: {
      date: '日期',
      status: '状态',
      checks: '检测次数',
      avgResponse: '平均响应'
    }
  }
}
