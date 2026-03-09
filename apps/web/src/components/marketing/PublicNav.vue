<script setup lang="ts">
import { seoLandingPages } from '../../content/seoLandingPages'

const toolLinks = seoLandingPages.map((page) => ({
  label: page.navLabel,
  to: `/${page.slug}`,
}))
</script>

<template>
  <header class="public-nav">
    <div class="public-nav-inner">
      <RouterLink class="brand-link" to="/">
        <span class="brand-mark-shell">
          <img class="brand-mark" src="/icons/icon-192x192.png" alt="ApplyPilot logo" width="58" height="58" />
        </span>
        <span class="brand-copy">
          <span class="brand-kicker">ApplyPilot</span>
          <strong>Resume growth engine</strong>
        </span>
      </RouterLink>

      <div class="nav-cluster">
        <nav class="nav-links" aria-label="Public navigation">
          <RouterLink v-for="link in toolLinks" :key="link.to" class="nav-link" :to="link.to">
            {{ link.label }}
          </RouterLink>
          <RouterLink class="nav-link" to="/blog">Blog</RouterLink>
          <RouterLink class="nav-link muted" to="/dashboard">Dashboard</RouterLink>
        </nav>

        <RouterLink class="cta-button" to="/dashboard/wizard">Try ApplyPilot</RouterLink>
      </div>
    </div>
  </header>
</template>

<style scoped>
.public-nav {
  position: sticky;
  top: 0;
  z-index: 30;
  border-bottom: 1px solid rgba(20, 33, 61, 0.08);
  background: rgba(251, 250, 246, 0.84);
  backdrop-filter: blur(14px);
}

.public-nav-inner {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  max-width: 1240px;
  margin: 0 auto;
  padding: 16px 24px;
}

.brand-link {
  display: inline-flex;
  gap: 16px;
  align-items: center;
  color: inherit;
}

.brand-mark-shell {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 12px 34px rgba(20, 33, 61, 0.08);
}

.brand-mark {
  width: 58px;
  height: 58px;
}

.brand-copy {
  display: grid;
}

.brand-kicker {
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.brand-copy strong {
  font-size: 1.06rem;
}

.nav-cluster {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
}

.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: flex-end;
}

.nav-link,
.cta-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 16px;
  border-radius: 999px;
  font-size: 0.94rem;
  font-weight: 700;
}

.nav-link {
  color: #4f5e75;
  background: rgba(255, 255, 255, 0.72);
}

.nav-link.router-link-exact-active {
  color: #14213d;
  background: #fff;
  box-shadow: 0 12px 28px rgba(20, 33, 61, 0.08);
}

.nav-link.muted {
  color: #8b5e34;
}

.cta-button {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
  box-shadow: 0 12px 28px rgba(37, 99, 235, 0.24);
}

@media (max-width: 960px) {
  .public-nav-inner {
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
  }

  .nav-cluster {
    justify-content: stretch;
  }

  .nav-links,
  .cta-button {
    width: 100%;
  }

  .cta-button {
    min-height: 48px;
  }
}

@media (max-width: 720px) {
  .brand-link {
    align-items: flex-start;
  }

  .nav-link {
    flex: 1 1 calc(50% - 10px);
    text-align: center;
  }
}
</style>
