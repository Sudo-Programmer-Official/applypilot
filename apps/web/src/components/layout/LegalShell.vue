<script setup lang="ts">
defineProps<{
  title: string
  summary: string
  updatedOn: string
}>()
</script>

<template>
  <div class="legal-shell">
    <header class="legal-nav">
      <div class="legal-nav-inner">
        <RouterLink class="brand-link" to="/">
          <span class="brand-mark-shell">
            <img class="brand-mark" src="/icons/icon-96x96.png" alt="ApplyPilot logo" width="42" height="42" />
          </span>
          <span class="brand-copy">
            <span class="brand-kicker">ApplyPilot</span>
            <strong>Launch essentials</strong>
          </span>
        </RouterLink>

        <nav class="nav-links" aria-label="Legal navigation">
          <RouterLink class="nav-link" to="/">Landing</RouterLink>
          <RouterLink class="nav-link" to="/dashboard">Dashboard</RouterLink>
          <RouterLink class="nav-link" to="/privacy">Privacy</RouterLink>
          <RouterLink class="nav-link" to="/terms">Terms</RouterLink>
        </nav>
      </div>
    </header>

    <main class="legal-main">
      <section class="legal-hero">
        <p class="legal-kicker">Last updated {{ updatedOn }}</p>
        <h1>{{ title }}</h1>
        <p>{{ summary }}</p>
      </section>

      <article class="legal-body">
        <slot />
      </article>
    </main>

    <footer class="legal-footer">
      <p>Questions about legal or launch setup can be sent to hello@applypilot.com.</p>
      <a href="mailto:hello@applypilot.com">hello@applypilot.com</a>
    </footer>
  </div>
</template>

<style scoped>
.legal-shell {
  min-height: 100vh;
  padding: 24px;
  color: #14213d;
  background:
    radial-gradient(circle at top left, rgba(251, 191, 36, 0.14), transparent 24%),
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.12), transparent 24%),
    linear-gradient(180deg, #fbfaf6 0%, #f6f4ef 100%);
}

.legal-nav-inner,
.legal-main,
.legal-footer {
  max-width: 980px;
  margin: 0 auto;
}

.legal-nav-inner {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
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

.brand-kicker,
.legal-kicker {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.nav-links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.nav-link {
  padding: 10px 14px;
  border-radius: 999px;
  color: #4f5e75;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.nav-link.router-link-exact-active {
  color: #14213d;
  background: #fff;
}

.legal-main {
  display: grid;
  gap: 18px;
  margin-top: 24px;
}

.legal-hero,
.legal-body,
.legal-footer {
  padding: 28px;
  border: 1px solid rgba(20, 33, 61, 0.08);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.legal-hero h1 {
  margin: 0;
  font-size: clamp(2rem, 4vw, 3rem);
  line-height: 0.96;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.legal-hero p:last-child,
.legal-body p,
.legal-body li,
.legal-footer p {
  color: #5f6c80;
}

.legal-body {
  display: grid;
  gap: 22px;
}

:deep(.legal-section h2) {
  margin: 0 0 10px;
  font-size: 1.45rem;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

:deep(.legal-section p) {
  margin: 0;
}

:deep(.legal-section ul) {
  margin: 12px 0 0;
  padding-left: 20px;
}

.legal-footer {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-top: 18px;
}

@media (max-width: 720px) {
  .legal-shell {
    padding: 16px;
  }

  .legal-nav-inner,
  .legal-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .nav-links {
    justify-content: space-between;
  }

  .nav-link {
    flex: 1 1 calc(50% - 10px);
    text-align: center;
  }

  .legal-hero,
  .legal-body,
  .legal-footer {
    padding: 24px;
  }
}
</style>
