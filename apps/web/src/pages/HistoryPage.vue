<script setup lang="ts">
import { previewResumeHistory } from '../content/productPreview'
</script>

<template>
  <section class="history-page">
    <header class="page-card history-header">
      <div>
        <p class="page-kicker">History</p>
        <h1>Recent resume versions</h1>
        <p>
          Review the saved resume versions attached to your workspace, then reopen the wizard or portfolio without
          losing account context.
        </p>
      </div>

      <div class="header-actions">
        <RouterLink class="header-button primary" to="/dashboard/wizard">New Optimization</RouterLink>
        <RouterLink class="header-button secondary" to="/dashboard/portfolio">Portfolio Workspace</RouterLink>
        <RouterLink class="header-button tertiary" to="/dashboard">Back to Dashboard</RouterLink>
      </div>
    </header>

    <div class="history-list">
      <article v-for="resume in previewResumeHistory" :key="resume.id" class="page-card history-item">
        <div class="item-head">
          <div>
            <p class="item-kicker">{{ resume.employer }}</p>
            <h2>{{ resume.title }}</h2>
          </div>
          <span class="status-pill">{{ resume.status }}</span>
        </div>

        <p class="item-date">Updated {{ resume.updatedOn }}</p>
        <p class="item-copy">{{ resume.summary }}</p>

        <div class="item-actions">
          <RouterLink to="/dashboard/wizard">Open Wizard</RouterLink>
          <RouterLink to="/dashboard/portfolio">Portfolio</RouterLink>
          <RouterLink to="/privacy">Privacy</RouterLink>
          <RouterLink to="/terms">Terms</RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.history-page {
  display: grid;
  gap: 18px;
  max-width: 1360px;
  height: 100%;
  margin: 0 auto;
  overflow-y: auto;
}

.page-card {
  padding: 28px;
  border: 1px solid rgba(20, 33, 61, 0.08);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.history-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
}

.page-kicker,
.item-kicker {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.history-header h1,
.history-item h2 {
  margin: 0;
  line-height: 1.02;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.history-header h1 {
  font-size: clamp(1.9rem, 2.4vw, 2.5rem);
}

.history-header p:last-child,
.item-date,
.item-copy {
  margin: 12px 0 0;
  color: #5f6c80;
}

.header-actions,
.item-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.header-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 14px 18px;
  border-radius: 999px;
  font-weight: 700;
}

.header-button.primary {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.header-button.secondary {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.92);
}

.header-button.tertiary {
  color: #124084;
  background: rgba(219, 234, 254, 0.9);
}

.history-list {
  display: grid;
  gap: 16px;
}

.item-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

.status-pill {
  padding: 8px 12px;
  border-radius: 999px;
  color: #124084;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.9);
}

.item-actions {
  margin-top: 18px;
}

.item-actions a {
  padding: 10px 14px;
  border-radius: 999px;
  color: #14213d;
  background: rgba(20, 33, 61, 0.05);
}

@media (max-width: 1100px) {
  .history-page {
    height: auto;
  }

  .history-header {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 720px) {
  .page-card {
    padding: 24px;
  }

  .header-actions,
  .item-actions {
    flex-direction: column;
  }

  .header-button,
  .item-actions a {
    width: 100%;
  }

  .item-head {
    flex-direction: column;
  }
}
</style>
