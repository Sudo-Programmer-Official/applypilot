<script setup lang="ts">
import { authState, signInWithGoogle } from '../lib/firebaseAuth'
import { previewResumeHistory } from '../content/productPreview'

const launchNotes = [
  'Start a new optimization in the guided wizard.',
  'Sync that history into a live public profile.',
  'Keep privacy, terms, and product surfaces split cleanly.',
]

const portfolioNotes = [
  'Bootstrap projects from the latest structured resume.',
  'Log work in plain language instead of filling long forms.',
  'Publish a public profile with activity, proof cards, and stack signals.',
]

async function handleGoogleSignIn() {
  try {
    await signInWithGoogle()
  } catch {
    // Resume wizard and portfolio workspace surface detailed auth errors.
  }
}
</script>

<template>
  <section class="dashboard-home">
    <header class="page-card page-hero">
      <div class="hero-copy">
        <p class="page-kicker">Dashboard</p>
        <h1>Career signal workspace</h1>
        <p>
          Optimize the resume, turn it into a living public profile, and keep proof of work in one focused product
          shell.
        </p>
      </div>

      <div class="hero-actions">
        <button
          v-if="authState.enabled && !authState.user"
          class="hero-button auth"
          type="button"
          :disabled="authState.busy"
          @click="handleGoogleSignIn"
        >
          {{ authState.busy ? 'Signing in…' : 'Continue with Google' }}
        </button>
        <span v-else-if="authState.user" class="account-pill">
          {{ authState.user.displayName || authState.user.email || 'Signed in' }}
        </span>
        <RouterLink class="hero-button primary" to="/dashboard/wizard">New Optimization</RouterLink>
        <RouterLink class="hero-button secondary" to="/dashboard/portfolio">Portfolio Workspace</RouterLink>
        <RouterLink class="hero-button tertiary" to="/dashboard/history">Resume History</RouterLink>
      </div>
    </header>

    <article v-if="authState.enabled" class="page-card account-card" :data-state="authState.user ? 'ready' : 'locked'">
      <div>
        <p class="section-kicker">Account workspace</p>
        <h2>{{ authState.user ? 'Resume and portfolio are linked' : 'Sign in before you start' }}</h2>
        <p class="card-copy">
          {{ authState.user
            ? `New resume uploads, optimization history, and portfolio proof now save to ${authState.user.displayName || authState.user.email || 'your account'}.`
            : 'ApplyPilot now stores resume history and portfolio activity together. Sign in once so every optimization and public profile update belongs to the same workspace.' }}
        </p>
      </div>
      <button
        v-if="!authState.user"
        class="inline-button"
        type="button"
        :disabled="authState.busy"
        @click="handleGoogleSignIn"
      >
        {{ authState.busy ? 'Signing in…' : 'Continue with Google' }}
      </button>
    </article>

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
            <p class="section-kicker">Living profile</p>
            <h2>Portfolio workspace</h2>
          </div>
          <span class="status-pill">New</span>
        </div>

        <p class="card-copy">
          Convert resume data and daily work logs into a shareable developer profile with activity, proof cards, and
          generated projects.
        </p>

        <ul class="check-list">
          <li v-for="note in portfolioNotes" :key="note">{{ note }}</li>
        </ul>

        <RouterLink class="inline-button" to="/dashboard/portfolio">Open Portfolio Workspace</RouterLink>
      </article>
    </div>

    <div class="bottom-grid">
      <article class="page-card compact-card">
        <div class="card-head">
          <div>
            <p class="section-kicker">Recent resumes</p>
            <h2>History-ready layout</h2>
          </div>
          <span class="status-pill">Preview</span>
        </div>

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

.hero-button.auth {
  border: 0;
  color: #14213d;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
}

.hero-button.tertiary {
  color: #124084;
  background: rgba(219, 234, 254, 0.9);
}

.account-card {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
}

.account-card[data-state='locked'] {
  border-color: rgba(37, 99, 235, 0.18);
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.96), rgba(255, 250, 235, 0.9));
}

.account-card[data-state='ready'] {
  border-color: rgba(16, 185, 129, 0.16);
  background: linear-gradient(135deg, rgba(236, 253, 245, 0.96), rgba(255, 255, 255, 0.94));
}

.account-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 46px;
  padding: 12px 16px;
  border-radius: 999px;
  color: #124084;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.92);
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

  .account-card {
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
