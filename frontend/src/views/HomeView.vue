<template>
  <main class="aurora-page">
    <div class="glass-shell spacer-stack home-shell">
      <header class="home-header">
        <h1 class="hero-title home-title">{{ config.site_title }}</h1>
        <p class="hero-desc home-desc">{{ config.site_description }}</p>
      </header>

      <div class="home-toolbar">
        <nav class="home-filter-bar">
          <button
            v-for="item in categoryFilters"
            :key="item.value"
            type="button"
            class="pill-btn secondary home-filter-btn"
            :class="{ active: activeCategory === item.value }"
            @click="activeCategory = item.value"
          >
            {{ item.label }}
          </button>
        </nav>

        <div class="home-search-row">
          <input
            v-model.trim="keyword"
            type="text"
            :placeholder="t('home.searchPlaceholder')"
            class="pill-input"
          />
          <select v-model="selectedTag" class="pill-select home-select">
            <option value="all">{{ t('home.allTags') }}</option>
            <option v-for="tag in allTags" :key="tag" :value="tag">{{ tag }}</option>
          </select>
        </div>
      </div>

      <div v-if="loading" class="text-muted" style="text-align: center; padding: 2rem;">{{ t('common.loading') }}</div>
      <div v-else-if="error" class="error-text" style="text-align: center; padding: 2rem;">{{ error }}</div>

      <div v-else class="site-grid home-grid">
        <article v-for="site in filteredSites" :key="site.id" class="site-card-horizontal">
          <a :href="site.url" target="_blank" rel="noreferrer" class="site-card-link" @click="handleSiteClick(site.id)">
            <div class="site-card-logo-wrapper">
              <img v-if="site.logo" :src="site.logo" :alt="site.name" class="site-card-logo" />
              <div v-else class="site-card-logo-fallback">{{ site.name[0]?.toUpperCase() }}</div>
            </div>
            <div class="site-card-content">
              <div class="site-card-header">
                <h2 class="site-card-title">{{ site.name }}</h2>
                <span class="site-status-dot" :class="site.status"></span>
              </div>
              <p class="site-card-desc">{{ site.description || t('home.noDescription') }}</p>
              <div class="site-card-tags">
                <span v-for="tag in site.tags_list" :key="tag" class="site-tag">{{ tag }}</span>
              </div>
            </div>
          </a>
        </article>
      </div>

      <footer class="small-text text-muted home-footer">
        <div>{{ config.copyright }}</div>
        <div v-if="config.icp_number" style="margin-top:0.32rem;">{{ config.icp_number }}</div>
      </footer>
    </div>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { fetchPublicConfig, fetchPublicSites, recordSiteVisit, recordHomeVisit } from "../api/public";

const { t } = useI18n();

const config = ref({
  site_title: "MyHarbor",
  site_description: "",
  copyright: "",
  icp_number: ""
});
const sites = ref([]);
const loading = ref(true);
const error = ref("");
const keyword = ref("");
const selectedTag = ref("all");
const activeCategory = ref("all");

const allTags = computed(() => {
  const set = new Set();
  for (const site of sites.value) {
    for (const tag of site.tags_list || []) {
      set.add(tag);
    }
  }
  return [...set].sort((a, b) => a.localeCompare(b));
});

const categoryFilters = computed(() => [
  { value: "all", label: t('common.all') },
  ...allTags.value.map((tag) => ({ value: tag, label: tag }))
]);

const filteredSites = computed(() => {
  const q = keyword.value.toLowerCase();
  const tag = selectedTag.value;
  const category = activeCategory.value;
  return sites.value.filter((site) => {
    const text = `${site.name} ${site.description || ""}`.toLowerCase();
    const matchKeyword = q ? text.includes(q) : true;
    const tags = site.tags_list || [];
    const matchTag = tag === "all" ? true : tags.includes(tag);
    const matchCategory = category === "all" ? true : tags.includes(category);
    return matchKeyword && matchTag && matchCategory;
  });
});

async function loadPageData() {
  try {
    loading.value = true;
    error.value = "";
    const [publicConfig, publicSites] = await Promise.all([fetchPublicConfig(), fetchPublicSites()]);
    config.value = publicConfig;
    sites.value = publicSites.items || [];
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to load data";
  } finally {
    loading.value = false;
  }
}

function handleSiteClick(siteId) {
  // 检查是否在当前会话中已记录过此站点访问
  const sessionKey = `site_visit_${siteId}`;
  const lastVisit = sessionStorage.getItem(sessionKey);
  const now = Date.now();

  // 如果5分钟内已访问过，不重复记录
  if (lastVisit && now - parseInt(lastVisit) < 5 * 60 * 1000) {
    return;
  }

  recordSiteVisit(siteId).then(() => {
    sessionStorage.setItem(sessionKey, now.toString());
  }).catch(err => {
    console.error("Failed to record site visit:", err);
  });
}

onMounted(() => {
  loadPageData();

  // 检查是否在当前会话中已记录过首页访问
  const homeVisitKey = 'home_visit';
  const lastHomeVisit = sessionStorage.getItem(homeVisitKey);
  const now = Date.now();

  // 如果5分钟内已访问过，不重复记录
  if (!lastHomeVisit || now - parseInt(lastHomeVisit) >= 5 * 60 * 1000) {
    recordHomeVisit().then(() => {
      sessionStorage.setItem(homeVisitKey, now.toString());
    }).catch(err => {
      console.error("Failed to record home visit:", err);
    });
  }
});
</script>
