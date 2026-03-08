<script setup lang="ts">
import { previewResumeHistory } from '../content/productPreview'

const launchNotes = [
  'Start a new optimization in the guided wizard.',
  'Keep space reserved for resume history before auth arrives.',
  'Ship with Privacy Policy and Terms linked from the product.',
]
</script>

<template>
  <section class="dashboard-home">
    <header class="page-card page-hero">
      <div class="hero-copy">
        <p class="page-kicker">Dashboard</p>
        <h1>Resume workspace</h1>
        <p>
          Start a new optimization, keep future history in one place, and preserve a clean separation between
          marketing and product UX.
        </p>
      </div>

      <div class="hero-actions">
        <RouterLink class="hero-button primary" to="/dashboard/wizard">New Optimization</RouterLink>
        <RouterLink class="hero-button secondary" to="/dashboard/history">Resume History</RouterLink>
      </div>
    </header>

    <div class="dashboard-grid">
      <article class="page-card primary-card">
        <p class="section-kicker">New optimization</p>
        <h2>Launch the guided workflow</h2>
        <p class="card-copy">
          Upload a resume, review the parsed structure, tailor it to a target role, and export a cleaner ATS-safe
          version in one flow.
        </p>

        <ul class="check-list">
          <li v-for="note in launchNotes" :key="note">{{ note }}</li>
        </ul>

        <RouterLink class="inline-button" to="/dashboard/wizard">Open Wizard</RouterLink>
      </article>

      <article class="page-card">
        <div class="card-head">
          <div>
            <p class="section-kicker">Recent resumes</p>
            <h2>History-ready layout</h2>
          </div>
          <span class="status-pill">Preview</span>
        </div>

        <p class="card-copy">
          Saved optimizations will live here after authentication. This preview keeps the dashboard structure stable
          before accounts ship.
        </p>

        <div class="resume-list">
          <article v-for="resume in previewResumeHistory" :key="resume.id" class="resume-item">
            <div class="resume-topline">
              <strong>{{ resume.title }}</strong>
              <span>{{ resume.status }}</span>
            </div>
            <p>{{ resume.employer }} · {{ resume.updatedOn }}</p>
            <small>{{ resume.summary }}</small>
          </article>
        </div>
      </article>
    </div>

    <div class="bottom-grid">
      <article class="page-card compact-card">
        <p class="section-kicker">Responsive</p>
        <h2>Desktop, iPad, and mobile ready</h2>
        <p class="card-copy">
          The product shell uses fixed-height desktop workspace behavior, then drops back to natural page flow on
          narrower screens for easier touch interaction.
        </p>
      </article>

      <article class="page-card compact-card">
        <p class="section-kicker">Launch links</p>
        <h2>Legal and support</h2>
        <div class="link-row">
          <RouterLink to="/privacy">Privacy Policy</RouterLink>
          <RouterLink to="/terms">Terms of Service</RouterLink>
          <a href="mailto:hello@applypilot.com">hello@applypilot.com</a>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.dashboard-home {
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

.page-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
}

.hero-copy {
  max-width: 700px;
}

.page-kicker,
.section-kicker {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.page-hero h1,
.page-card h2 {
  margin: 0;
  line-height: 1.02;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.page-hero h1 {
  font-size: clamp(1.9rem, 2.4vw, 2.6rem);
}

.hero-copy p:last-child,
.card-copy,
.resume-item p,
.resume-item small {
  margin: 12px 0 0;
  color: #5f6c80;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
}

.hero-button,
.inline-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 14px 18px;
  border-radius: 999px;
  font-weight: 700;
}

.hero-button.primary,
.inline-button {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.hero-button.secondary {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.92);
}

.dashboard-grid,
.bottom-grid {
  display: grid;
  gap: 18px;
}

.dashboard-grid {
  grid-template-columns: 1.1fr 0.9fr;
}

.bottom-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.primary-card {
  background: linear-gradient(135deg, rgba(251, 243, 221, 0.96), rgba(255, 255, 255, 0.98));
}

.check-list {
  display: grid;
  gap: 12px;
  margin: 18px 0 22px;
  padding-left: 18px;
  color: #4f5e75;
}

.card-head,
.resume-topline {
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

.resume-list {
  display: grid;
  gap: 12px;
  margin-top: 18px;
}

.resume-item {
  padding: 18px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
}

.resume-item strong {
  font-size: 1rem;
}

.resume-topline span {
  color: #8b5e34;
  font-size: 0.84rem;
  font-weight: 700;
}

.resume-item small {
  display: block;
}

.link-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}

.link-row a {
  padding: 10px 14px;
  border-radius: 999px;
  color: #14213d;
  background: rgba(20, 33, 61, 0.05);
}

@media (max-width: 1100px) {
  .dashboard-home {
    height: auto;
  }

  .page-hero {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-actions {
    justify-content: stretch;
  }

  .dashboard-grid,
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .page-card {
    padding: 24px;
  }

  .hero-actions,
  .link-row {
    flex-direction: column;
  }

  .hero-button,
  .inline-button,
  .link-row a {
    width: 100%;
  }

  .card-head,
  .resume-topline {
    flex-direction: column;
  }
}
</style>
