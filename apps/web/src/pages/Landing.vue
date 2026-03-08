<script setup lang="ts">
import ResumeWizard from '../components/wizard/ResumeWizard.vue'
</script>

<template>
  <main class="landing-shell">
    <header class="topbar">
      <div class="brand-block">
        <p class="brand-kicker">ApplyPilot</p>
        <h1>Optimize every resume with a guided workflow.</h1>
      </div>
      <div class="status-pill">Production pipeline online</div>
    </header>

    <section class="hero-grid">
      <article class="hero-card feature-card">
        <p class="eyebrow">Resume vs Job Intelligence</p>
        <p class="hero-copy">
          Upload once, review the parsed structure, add job context, run optimization, and export an ATS-safe PDF
          without leaving the flow.
        </p>
        <div class="hero-stats">
          <div>
            <strong>5 steps</strong>
            <span>guided wizard</span>
          </div>
          <div>
            <strong>1 parser</strong>
            <span>layout-aware</span>
          </div>
          <div>
            <strong>PDF out</strong>
            <span>ready to submit</span>
          </div>
        </div>
      </article>

      <article class="hero-card checklist-card">
        <p class="eyebrow">How it works</p>
        <ul>
          <li><strong>Upload</strong> the source resume file.</li>
          <li><strong>Review</strong> the parsed structure before AI changes anything.</li>
          <li><strong>Add</strong> a job description, link, or external suggestions.</li>
          <li><strong>Generate</strong> the optimized draft and export a PDF.</li>
        </ul>
      </article>
    </section>

    <ResumeWizard />
  </main>
</template>

<style scoped>
.landing-shell {
  min-height: 100vh;
  padding: 34px 24px 88px;
  color: #14213d;
  background:
    radial-gradient(circle at top left, rgba(251, 191, 36, 0.2), transparent 28%),
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.18), transparent 26%),
    linear-gradient(180deg, #fbfaf6 0%, #f1eee5 100%);
}

.topbar,
.hero-grid,
:deep(.wizard-layout) {
  max-width: 1240px;
  margin-left: auto;
  margin-right: auto;
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: end;
}

.brand-kicker,
.eyebrow {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

h1 {
  max-width: 12ch;
  margin: 0;
  font-size: clamp(3.2rem, 6vw, 5rem);
  line-height: 0.92;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.status-pill {
  padding: 12px 16px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 999px;
  color: #124084;
  font-size: 0.92rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.84);
  box-shadow: 0 12px 28px rgba(20, 33, 61, 0.08);
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
  margin-top: 22px;
  margin-bottom: 24px;
}

.hero-card {
  padding: 24px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(10px);
  box-shadow: 0 18px 44px rgba(20, 33, 61, 0.08);
}

.hero-copy,
.checklist-card li,
.hero-stats span {
  margin: 0;
  color: #5f6c80;
  line-height: 1.65;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 20px;
}

.hero-stats div {
  padding: 16px;
  border-radius: 20px;
  background: rgba(20, 33, 61, 0.05);
}

.hero-stats strong,
.hero-stats span {
  display: block;
}

.hero-stats strong {
  font-size: 1.25rem;
}

.checklist-card ul {
  display: grid;
  gap: 12px;
  margin: 12px 0 0;
  padding-left: 18px;
}

@media (max-width: 1100px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .landing-shell {
    padding: 24px 16px 72px;
  }

  .topbar {
    flex-direction: column;
    align-items: start;
  }

  .hero-stats {
    grid-template-columns: 1fr;
  }
}
</style>
