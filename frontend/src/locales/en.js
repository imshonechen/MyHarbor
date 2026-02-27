export default {
  common: {
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    saving: 'Saving...',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    search: 'Search',
    loading: 'Loading...',
    refresh: 'Refresh',
    back: 'Back',
    backToHome: '← Back to Home',
    logout: 'Logout',
    all: 'All',
    yes: 'Yes',
    no: 'No',
    online: 'Online',
    offline: 'Offline',
    unknown: 'Unknown'
  },

  home: {
    searchPlaceholder: 'Search by name or description...',
    allTags: 'All Tags',
    noDescription: 'No description'
  },

  login: {
    title: 'MyHarbor',
    subtitle: 'Admin Panel',
    username: 'Username',
    usernamePlaceholder: 'Enter your username',
    password: 'Password',
    passwordPlaceholder: 'Enter your password',
    loginButton: 'Login',
    loggingIn: 'Logging in...',
    errors: {
      tooManyAttempts: 'Too many login attempts. Please try again later.',
      invalidCredentials: 'Invalid username or password',
      loginFailed: 'Login failed. Please try again.'
    }
  },

  layout: {
    adminPanel: 'Admin Panel',
    menu: {
      dashboard: 'Dashboard',
      sites: 'Sites',
      statistics: 'Statistics',
      monitoring: 'Monitoring',
      settings: 'Settings'
    }
  },

  dashboard: {
    title: 'Dashboard',
    welcome: 'Welcome to MyHarbor Admin Panel',
    stats: {
      todayVisits: "Today's Visits",
      totalSites: 'Total Sites',
      onlineSites: 'Online Sites',
      offlineSites: 'Offline Sites'
    },
    quickActions: {
      title: 'Quick Actions',
      addSite: 'Add New Site',
      checkAll: 'Check All Sites',
      checking: 'Checking...',
      viewStats: 'View Statistics',
      systemSettings: 'System Settings'
    },
    recentSites: {
      title: 'Recent Sites',
      noSites: 'No sites yet'
    },
    trend: {
      title: '7-Day Trend'
    }
  },

  sites: {
    title: 'Sites Management',
    subtitle: 'Manage your sites, check status, and organize',
    addNew: 'Add New Site',
    searchPlaceholder: 'Search sites...',
    checkAll: 'Check All',
    checking: 'Checking...',
    filters: {
      all: 'All Sites',
      publicOnly: 'Public Only',
      hiddenOnly: 'Hidden Only'
    },
    table: {
      sort: 'Sort',
      name: 'Name',
      url: 'URL',
      status: 'Status',
      public: 'Public',
      tags: 'Tags',
      actions: 'Actions'
    },
    actions: {
      edit: 'Edit',
      check: 'Check',
      delete: 'Delete'
    },
    orderChanged: 'Order has been changed',
    saveOrder: 'Save Sort Order',
    noSites: 'No sites found. Click "Add New Site" to get started.',
    loadingSites: 'Loading sites...',
    deleteConfirm: {
      title: 'Delete Site',
      message: 'Are you sure you want to delete site "{name}"? This action cannot be undone.'
    }
  },

  siteForm: {
    titleEdit: 'Edit Site',
    titleAdd: 'Add New Site',
    fields: {
      name: 'Site Name *',
      namePlaceholder: 'My Awesome Site',
      url: 'URL *',
      urlPlaceholder: 'https://example.com',
      logo: 'Logo URL',
      logoPlaceholder: 'https://example.com/logo.png',
      sortOrder: 'Sort Order',
      sortOrderHint: 'Lower numbers appear first',
      tags: 'Tags',
      tagsPlaceholder: 'tool, docs, api (comma separated)',
      tagsHint: 'Separate multiple tags with commas',
      description: 'Description',
      descriptionPlaceholder: 'Brief description of the site',
      isPublic: 'Public Site',
      isPublicHint: 'Public sites are visible on the homepage'
    },
    buttons: {
      cancel: 'Cancel',
      update: 'Update Site',
      add: 'Add Site',
      saving: 'Saving...'
    }
  },

  settings: {
    title: 'System Settings',
    subtitle: 'Configure system parameters and admin account',
    tabs: {
      siteConfig: 'Site Configuration',
      adminAccount: 'Admin Account',
      monitoring: 'Monitoring',
      backup: 'Data Backup'
    },
    siteConfig: {
      title: 'Site Title',
      description: 'Site Description',
      descriptionText: 'Configure public-facing site information',
      copyright: 'Copyright',
      icpNumber: 'ICP Number',
      icpPlaceholder: 'ICP Number (optional)',
      saveButton: 'Save Site Configuration'
    },
    adminAccount: {
      username: 'Username',
      descriptionText: 'Update admin credentials and security settings',
      newPassword: 'New Password',
      passwordHint: 'Leave blank to keep current password',
      passwordNote: 'Only fill this if you want to change the password',
      routeCode: 'Admin Route Code',
      routeCodeWarning: '⚠️ Changing this will update the admin panel URL. After saving, you will be redirected to the new URL.',
      saveButton: 'Save Admin Settings'
    },
    monitoring: {
      descriptionText: 'Configure site status checking intervals',
      checkInterval: 'Check Interval (minutes)',
      checkIntervalHint: 'How often to check site status (1-1440 minutes). Default is 5 minutes.',
      saveButton: 'Save Monitoring Settings'
    },
    backup: {
      descriptionText: 'Export and import site data',
      export: {
        title: 'Export Backup',
        description: 'Download all site data as JSON file',
        button: 'Export Backup',
        exporting: 'Exporting...',
        success: 'Backup exported successfully!',
        error: 'Failed to export backup'
      },
      import: {
        title: 'Import Backup',
        description: 'Restore site data from JSON file',
        fileLabel: 'Backup File',
        selectFile: 'Select File',
        strategyLabel: 'Import Strategy',
        strategy: 'Import Strategy',
        strategySkip: 'Skip existing sites',
        strategyOverwrite: 'Overwrite existing sites',
        strategyHint: 'Choose how to handle existing sites',
        button: 'Import Backup',
        importing: 'Importing...',
        noFile: 'Please select a backup file first',
        noFileError: 'Please select a backup file first',
        success: 'Backup imported successfully!',
        error: 'Failed to import backup'
      },
      messages: {
        exportSuccess: 'Backup exported successfully!',
        exportError: 'Failed to export backup',
        importSuccess: 'Backup imported successfully! Total: {total}, Created: {created}, Updated: {updated}, Skipped: {skipped}',
        importError: 'Failed to import backup'
      }
    },
    messages: {
      saveSuccess: 'Settings saved successfully',
      saveError: 'Failed to save settings',
      siteConfigSaved: 'Site configuration saved successfully!',
      siteConfigError: 'Failed to save site configuration',
      adminSettingsSaved: 'Admin settings saved successfully!',
      adminSettingsError: 'Failed to save admin settings',
      redirecting: 'Redirecting to new admin URL...',
      monitoringSaved: 'Monitoring settings saved successfully!',
      monitoringError: 'Failed to save monitoring settings'
    }
  },

  statistics: {
    title: 'Statistics',
    subtitle: 'View site visit data and trends'
  },

  monitoring: {
    title: 'Site Monitoring',
    subtitle: 'Monitor site status',
    controls: {
      selectSite: 'Select Site:',
      days: 'Days:',
      checkThisSite: 'Check This Site',
      checking: 'Checking...',
      checkAllSites: 'Check All Sites',
      refresh: 'Refresh'
    },
    days: {
      1: '1 Day',
      7: '7 Days',
      14: '14 Days',
      30: '30 Days'
    },
    noSites: 'No sites available',
    emptyState: 'Please select a site to view its monitoring data',
    loading: 'Loading monitoring data...',
    stats: {
      online: 'Online',
      offline: 'Offline',
      unknown: 'Unknown',
      noData: 'No Data',
      uptime: 'Uptime'
    },
    calendar: {
      title: 'Uptime Calendar',
      noData: 'No monitoring data available',
      status: 'Status:'
    },
    logs: {
      title: 'Recent Status Logs',
      noLogs: 'No logs available',
      time: 'Time',
      status: 'Status',
      responseTime: 'Response Time'
    },
    tooltip: {
      date: 'Date',
      status: 'Status',
      checks: 'Checks',
      avgResponse: 'Avg Response'
    }
  }
}
