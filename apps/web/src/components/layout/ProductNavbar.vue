<script setup lang="ts">
</script>

<template>
  <header class="product-nav">
    <div class="product-nav-inner">
      <RouterLink class="brand-link" to="/dashboard">
        <span class="brand-mark-shell">
          <img class="brand-mark" src="/icons/icon-96x96.png" alt="ApplyPilot logo" width="42" height="42" />
        </span>
        <span class="brand-copy">
          <span class="brand-kicker">ApplyPilot</span>
          <strong>Resume workspace</strong>
        </span>
      </RouterLink>

      <div class="nav-cluster">
        <nav class="nav-links" aria-label="Primary navigation">
          <RouterLink class="nav-link" to="/dashboard">Dashboard</RouterLink>
          <RouterLink class="nav-link" to="/dashboard/wizard">Optimize</RouterLink>
          <RouterLink class="nav-link" to="/dashboard/history">History</RouterLink>
          <RouterLink class="nav-link subtle" to="/">Landing</RouterLink>
        </nav>

        <div class="meta-links">
          <span class="mode-pill">Guest mode</span>
          <RouterLink class="meta-link" to="/privacy">Privacy</RouterLink>
          <RouterLink class="meta-link" to="/terms">Terms</RouterLink>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.product-nav {
  position: sticky;
  top: 0;
  z-index: 20;
  border-bottom: 1px solid rgba(20, 33, 61, 0.08);
  background: rgba(246, 244, 239, 0.9);
  backdrop-filter: blur(14px);
}

.product-nav-inner {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  max-width: 1360px;
  min-height: 80px;
  margin: 0 auto;
  padding: 14px 24px;
}

.brand-link {
  display: inline-flex;
  gap: 14px;
  align-items: center;
  color: inherit;
}

.brand-mark-shell {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.brand-mark {
  width: 42px;
  height: 42px;
}

.brand-copy {
  display: grid;
}

.brand-kicker {
  color: #8b5e34;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.brand-copy strong {
  font-size: 1rem;
}

.nav-cluster {
  display: grid;
  gap: 8px;
  justify-items: end;
}

.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.nav-link {
  padding: 10px 14px;
  border-radius: 999px;
  color: #4f5e75;
  font-size: 0.94rem;
  font-weight: 700;
}

.nav-link.router-link-exact-active {
  color: #14213d;
  background: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.nav-link.subtle {
  color: #8b5e34;
}

.meta-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.mode-pill,
.meta-link {
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 0.82rem;
}

.mode-pill {
  color: #124084;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.9);
}

.meta-link {
  color: #6b7280;
  background: rgba(255, 255, 255, 0.7);
}

@media (max-width: 720px) {
  .product-nav-inner {
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
  }

  .nav-cluster {
    justify-items: stretch;
  }

  .nav-links {
    justify-content: space-between;
  }

  .nav-link {
    flex: 1 1 calc(50% - 10px);
    text-align: center;
  }

  .meta-links {
    justify-content: stretch;
  }

  .mode-pill,
  .meta-link {
    flex: 1 1 calc(33.333% - 10px);
    text-align: center;
  }
}
</style>
