<script setup lang="ts">
import ResumeWizard from '../components/wizard/ResumeWizard.vue'
</script>

<template>
  <section class="wizard-page">
    <section class="dashboard-toolbar">
      <div class="toolbar-copy">
        <p class="toolbar-kicker">Optimize</p>
        <h1>Resume Optimization Wizard</h1>
        <p>
          Keep the viewport fixed while each step scrolls inside the workspace, so review and optimization feel closer
          to a product tool than a long marketing page.
        </p>
      </div>

      <div class="toolbar-actions">
        <RouterLink class="toolbar-button primary" to="/dashboard">Back to Dashboard</RouterLink>
        <RouterLink class="toolbar-button secondary" to="/dashboard/history">Resume History</RouterLink>
      </div>
    </section>

    <section id="wizard-workspace" class="dashboard-workspace">
      <ResumeWizard />
    </section>
  </section>
</template>

<style scoped>
.wizard-page {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 18px;
  max-width: 1360px;
  height: 100%;
  margin: 0 auto;
}

.dashboard-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  padding: 28px;
  border: 1px solid rgba(20, 33, 61, 0.08);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.toolbar-copy {
  max-width: 640px;
}

.toolbar-kicker {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.toolbar-copy h1 {
  margin: 0;
  font-size: clamp(1.55rem, 2vw, 2rem);
  line-height: 1.02;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.toolbar-copy p:last-child {
  margin: 10px 0 0;
  color: #5f6c80;
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
}

.toolbar-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  min-width: 170px;
  padding: 14px 18px;
  border: 0;
  border-radius: 999px;
  font-weight: 700;
}

.toolbar-button.primary {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.toolbar-button.secondary {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.92);
}

.dashboard-workspace {
  min-height: 0;
}

:deep(.wizard-layout) {
  height: 100%;
}

@media (max-width: 1100px) {
  .wizard-page {
    height: auto;
  }

  .dashboard-toolbar {
    flex-direction: column;
    align-items: stretch;
    padding: 24px;
  }

  .toolbar-actions {
    justify-content: stretch;
  }

  .toolbar-button {
    flex: 1 1 220px;
  }
}

@media (max-width: 720px) {
  .toolbar-actions {
    flex-direction: column;
  }

  .toolbar-button {
    width: 100%;
  }
}
</style>
