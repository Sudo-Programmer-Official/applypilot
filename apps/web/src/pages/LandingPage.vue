<script setup lang="ts">
const features = [
  {
    title: 'Guided workflow',
    description: 'Move from upload to export with clear checkpoints instead of one noisy page.',
  },
  {
    title: 'ATS optimization',
    description: 'Review structure, coverage, and match signals before you rewrite anything.',
  },
  {
    title: 'AI bullet rewriting',
    description: 'Turn raw resume bullets into tighter, role-aware accomplishments.',
  },
]

const workflowSteps = ['Upload', 'Analyze', 'Optimize', 'Download']
</script>

<template>
  <main class="landing-shell">
    <header class="marketing-nav">
      <RouterLink class="brand-link" to="/">
        <span class="brand-mark-shell">
          <img class="brand-mark" src="/icons/icon-192x192.png" alt="ApplyPilot logo" width="76" height="76" />
        </span>
        <span class="brand-copy">
          <span class="brand-kicker">ApplyPilot</span>
          <strong>Resume Copilot</strong>
        </span>
      </RouterLink>

      <div class="nav-actions">
        <RouterLink class="nav-link" to="/dashboard">Dashboard</RouterLink>
        <RouterLink class="cta-button" to="/dashboard/wizard">Try ApplyPilot</RouterLink>
      </div>
    </header>

    <section class="hero-grid">
      <div class="hero-copy">
        <p class="eyebrow">AI resume workflow</p>
        <h1>Make every resume ATS-ready and recruiter-optimized.</h1>
        <p class="hero-summary">
          Upload once, analyze structure, optimize against a role target, and export a cleaner interview-ready version
          in minutes.
        </p>

        <div class="hero-actions">
          <RouterLink class="cta-button" to="/dashboard/wizard">Try it free</RouterLink>
          <RouterLink class="ghost-button" to="/dashboard">View dashboard</RouterLink>
        </div>
      </div>

      <article class="hero-card">
        <div class="hero-card-top">
          <div>
            <p class="eyebrow">Product preview</p>
            <h2>From raw resume to polished application</h2>
          </div>
          <span class="hero-pill">Live workspace</span>
        </div>

        <div class="workflow-rail">
          <div v-for="step in workflowSteps" :key="step" class="workflow-chip">
            <strong>{{ step }}</strong>
            <span>inside one clean flow</span>
          </div>
        </div>
      </article>
    </section>

    <section class="content-section">
      <div class="section-head">
        <p class="eyebrow">Features</p>
        <h2>Purpose-built for focused resume work</h2>
      </div>

      <div class="feature-grid">
        <article v-for="feature in features" :key="feature.title" class="feature-card">
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </article>
      </div>
    </section>

    <section class="content-section">
      <div class="section-head">
        <p class="eyebrow">How it works</p>
        <h2>Upload to download without leaving the workflow</h2>
      </div>

      <div class="process-grid">
        <article v-for="(step, index) in workflowSteps" :key="step" class="process-card">
          <span>{{ index + 1 }}</span>
          <h3>{{ step }}</h3>
        </article>
      </div>
    </section>

    <footer class="landing-footer">
      <div class="footer-copy">
        <p>ApplyPilot keeps marketing on the landing page and product work inside the dashboard.</p>
        <small>
          Launch support:
          <a href="mailto:hello@applypilot.com">hello@applypilot.com</a>
        </small>
      </div>

      <div class="footer-links">
        <RouterLink to="/dashboard">Enter the dashboard</RouterLink>
        <RouterLink to="/privacy">Privacy Policy</RouterLink>
        <RouterLink to="/terms">Terms of Service</RouterLink>
      </div>
    </footer>
  </main>
</template>

<style scoped>
.landing-shell {
  min-height: 100vh;
  padding: 28px 24px 64px;
  color: #14213d;
  background:
    radial-gradient(circle at top left, rgba(251, 191, 36, 0.18), transparent 24%),
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.16), transparent 24%),
    linear-gradient(180deg, #fbfaf6 0%, #f6f4ef 100%);
}

.marketing-nav,
.hero-grid,
.content-section,
.landing-footer {
  max-width: 1240px;
  margin: 0 auto;
}

.marketing-nav {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
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
  width: 92px;
  height: 92px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.brand-mark {
  width: 76px;
  height: 76px;
}

.brand-copy {
  display: grid;
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

.brand-copy strong {
  font-size: 1.1rem;
}

.nav-actions,
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.nav-link,
.cta-button,
.ghost-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  padding: 14px 18px;
  border-radius: 999px;
  font-weight: 700;
}

.nav-link,
.ghost-button {
  color: #14213d;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.cta-button {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 24px;
  align-items: stretch;
  margin-top: 40px;
}

.hero-copy,
.hero-card,
.feature-card,
.process-card,
.landing-footer {
  padding: 28px;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.hero-copy {
  background: rgba(255, 255, 255, 0.82);
}

.hero-copy h1,
.section-head h2,
.hero-card h2 {
  margin: 0;
  line-height: 0.96;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.hero-copy h1 {
  max-width: 11ch;
  font-size: clamp(3rem, 7vw, 5.6rem);
}

.hero-summary {
  max-width: 42rem;
  margin: 16px 0 0;
  color: #5f6c80;
  font-size: 1.06rem;
}

.hero-actions {
  margin-top: 24px;
}

.hero-card-top {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: start;
}

.hero-pill {
  padding: 8px 12px;
  border-radius: 999px;
  color: #124084;
  font-size: 0.84rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.9);
}

.hero-card h2 {
  font-size: clamp(1.8rem, 3vw, 2.4rem);
}

.workflow-rail {
  display: grid;
  gap: 12px;
  margin-top: 22px;
}

.workflow-chip {
  padding: 18px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
}

.workflow-chip strong,
.workflow-chip span {
  display: block;
}

.workflow-chip span {
  color: #5f6c80;
}

.content-section {
  margin-top: 24px;
}

.section-head {
  margin-bottom: 16px;
}

.feature-grid,
.process-grid {
  display: grid;
  gap: 18px;
}

.feature-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.process-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.feature-card h3,
.process-card h3 {
  margin: 0;
  font-size: 1.2rem;
}

.feature-card p,
.process-card span,
.landing-footer p,
.footer-copy small {
  margin: 10px 0 0;
  color: #5f6c80;
}

.process-card span:first-child {
  display: inline-grid;
  place-items: center;
  width: 38px;
  height: 38px;
  margin: 0 0 14px;
  border-radius: 50%;
  color: #fff;
  font-weight: 800;
  background: linear-gradient(135deg, #b45309, #2563eb);
}

.landing-footer {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  margin-top: 24px;
}

.footer-copy {
  max-width: 38rem;
}

.footer-copy small {
  display: block;
}

.footer-copy a {
  color: inherit;
  text-decoration: underline;
}

.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: flex-end;
}

.footer-links a {
  padding: 10px 14px;
  border-radius: 999px;
  color: #14213d;
  background: rgba(20, 33, 61, 0.05);
}

@media (max-width: 1100px) {
  .hero-grid,
  .feature-grid,
  .process-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .landing-shell {
    padding: 20px 16px 40px;
  }

  .marketing-nav,
  .landing-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .brand-link {
    align-items: flex-start;
  }

  .nav-actions,
  .hero-actions,
  .footer-links {
    width: 100%;
  }

  .nav-link,
  .cta-button,
  .ghost-button,
  .footer-links a {
    flex: 1 1 0;
  }

  .hero-copy,
  .hero-card,
  .feature-card,
  .process-card,
  .landing-footer {
    padding: 24px;
  }
}
</style>
