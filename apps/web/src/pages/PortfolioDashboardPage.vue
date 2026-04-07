<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import axios from 'axios'

import { portfolioPreview } from '../content/portfolioPreview'
import { authState, signInWithGoogle, waitForAuthReady } from '../lib/firebaseAuth'
import {
  bootstrapPortfolio,
  createPortfolioActivity,
  fetchPortfolioMe,
  updatePortfolioProfile,
} from '../lib/portfolioApi'
import type { PortfolioOverview, PortfolioProfile } from '../types/portfolio'

const loading = ref(true)
const bootstrapping = ref(false)
const savingProfile = ref(false)
const loggingActivity = ref(false)
const usingPreview = ref(false)
const needsBootstrap = ref(false)
const error = ref('')
const portfolio = ref<PortfolioOverview | null>(null)

const profileForm = reactive({
  profile_id: undefined as number | undefined,
  username: '',
  display_name: '',
  headline: '',
  summary: '',
  location: '',
  primary_role: '',
  contact_email: '',
  hiring_status: 'open',
  hero_statement: '',
})

const activityForm = reactive({
  project_id: '',
  title: '',
  detail: '',
  impact: '',
  happened_on: '',
  tags: '',
  links: '',
  claim: '',
  evidence: '',
  metric_label: '',
  metric_before: '',
  metric_after: '',
})

const metricCards = computed(() => {
  if (!portfolio.value) {
    return []
  }
  return [
    {
      label: 'Impact Score',
      value: String(portfolio.value.metrics.impact_score),
      detail: 'Weighted signal across proof density, recent activity, and project breadth.',
    },
    {
      label: 'Live Activity',
      value: `${portfolio.value.metrics.recent_activity_count} / 7d`,
      detail: 'How much real work surfaced publicly during the last seven days.',
    },
    {
      label: 'Proof Cards',
      value: String(portfolio.value.metrics.proof_count),
      detail: 'Claims tied to evidence, metrics, or iteration history.',
    },
    {
      label: 'Tech Diversity',
      value: String(portfolio.value.metrics.tech_diversity),
      detail: 'Distinct stack coverage detected across generated projects.',
    },
  ]
})

const firebaseUnavailable = computed(() => !authState.enabled)
const authReady = computed(() => authState.ready)
const signedInUser = computed(() => authState.user)
const isSignedIn = computed(() => Boolean(signedInUser.value))
const canManagePortfolio = computed(() => isSignedIn.value && !usingPreview.value)

const publicProfilePath = computed(() => `/public/${profileForm.username || portfolio.value?.profile.username || suggestedUsername.value}`)
const publicProfileUrl = computed(() => {
  if (typeof window === 'undefined') {
    return publicProfilePath.value
  }
  return `${window.location.origin}${publicProfilePath.value}`
})

const resumeSnapshotRows = computed(() => {
  const snapshot = portfolio.value?.profile.resume_snapshot ?? {}
  return [
    { label: 'Source Resume', value: String(snapshot.file_name ?? 'Not connected yet') },
    { label: 'Primary Role', value: String(snapshot.title ?? (profileForm.primary_role || 'Not set')) },
    { label: 'Last Sync', value: formatDate(String(snapshot.updated_at ?? '')) || 'Not synced yet' },
  ]
})

const activityFeed = computed(() => portfolio.value?.activity ?? [])
const proofCards = computed(() => portfolio.value?.proof_cards ?? [])
const projects = computed(() => portfolio.value?.projects ?? [])
const suggestedUsername = computed(() => {
  const emailSeed = signedInUser.value?.email?.split('@')[0] || ''
  const displaySeed = signedInUser.value?.displayName || ''
  return sanitizeUsername(emailSeed || displaySeed || 'builder')
})

function clonePreview() {
  return JSON.parse(JSON.stringify(portfolioPreview)) as PortfolioOverview
}

function hydrateProfileForm(profile: PortfolioProfile) {
  profileForm.profile_id = profile.id
  profileForm.username = profile.username
  profileForm.display_name = profile.display_name
  profileForm.headline = profile.headline
  profileForm.summary = profile.summary
  profileForm.location = profile.location
  profileForm.primary_role = profile.primary_role
  profileForm.contact_email = profile.contact_email
  profileForm.hiring_status = profile.hiring_status
  profileForm.hero_statement = profile.hero_statement
}

function prefillProfileFromAuth() {
  profileForm.username = profileForm.username || suggestedUsername.value
  profileForm.display_name = profileForm.display_name || signedInUser.value?.displayName || ''
  profileForm.contact_email = profileForm.contact_email || signedInUser.value?.email || ''
}

async function loadPortfolio() {
  loading.value = true
  error.value = ''
  needsBootstrap.value = false
  portfolio.value = null

  await waitForAuthReady()

  if (firebaseUnavailable.value) {
    usingPreview.value = true
    error.value = 'Firebase is not configured in this frontend environment. Showing preview data.'
    const preview = clonePreview()
    portfolio.value = preview
    hydrateProfileForm(preview.profile)
    loading.value = false
    return
  }

  if (!isSignedIn.value) {
    usingPreview.value = false
    prefillProfileFromAuth()
    loading.value = false
    return
  }

  try {
    const data = await fetchPortfolioMe()
    portfolio.value = data
    hydrateProfileForm(data.profile)
    usingPreview.value = false
  }
  catch (unknownError) {
    if (axios.isAxiosError(unknownError) && unknownError.response?.status === 404) {
      needsBootstrap.value = true
      usingPreview.value = false
      error.value = String(unknownError.response?.data?.detail ?? 'No portfolio exists yet.')
      prefillProfileFromAuth()
    }
    else {
      usingPreview.value = true
      error.value = 'Portfolio API is unavailable. Showing preview data.'
      const preview = clonePreview()
      portfolio.value = preview
      hydrateProfileForm(preview.profile)
    }
  }
  finally {
    loading.value = false
  }
}

async function handleGoogleSignIn() {
  error.value = ''
  try {
    await signInWithGoogle()
  }
  catch (unknownError) {
    if (unknownError instanceof Error) {
      error.value = unknownError.message
      return
    }
    error.value = 'Google sign-in failed.'
  }
}

async function handleBootstrap() {
  if (!canManagePortfolio.value) {
    return
  }
  bootstrapping.value = true
  error.value = ''
  try {
    const data = await bootstrapPortfolio({
      username: profileForm.username.trim() || undefined,
    })
    portfolio.value = data
    usingPreview.value = false
    needsBootstrap.value = false
    hydrateProfileForm(data.profile)
  }
  catch (unknownError) {
    if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? 'Failed to bootstrap portfolio.')
      return
    }
    error.value = 'Failed to bootstrap portfolio.'
  }
  finally {
    bootstrapping.value = false
  }
}

async function saveProfile() {
  if (!canManagePortfolio.value) {
    return
  }

  savingProfile.value = true
  error.value = ''
  try {
    const updatedProfile = await updatePortfolioProfile({
      profile_id: profileForm.profile_id,
      username: sanitizeUsername(profileForm.username),
      display_name: profileForm.display_name.trim(),
      headline: profileForm.headline.trim(),
      summary: profileForm.summary.trim(),
      location: profileForm.location.trim(),
      primary_role: profileForm.primary_role.trim(),
      contact_email: profileForm.contact_email.trim(),
      hiring_status: profileForm.hiring_status,
      hero_statement: profileForm.hero_statement.trim(),
    })
    if (portfolio.value) {
      portfolio.value = {
        ...portfolio.value,
        profile: updatedProfile,
      }
    }
    hydrateProfileForm(updatedProfile)
  }
  catch (unknownError) {
    if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? 'Failed to save profile.')
      return
    }
    error.value = 'Failed to save profile.'
  }
  finally {
    savingProfile.value = false
  }
}

async function submitActivity() {
  if (!portfolio.value || !canManagePortfolio.value) {
    return
  }

  loggingActivity.value = true
  error.value = ''
  try {
    await createPortfolioActivity({
      profile_id: portfolio.value.profile.id,
      project_id: activityForm.project_id ? Number(activityForm.project_id) : undefined,
      title: activityForm.title.trim(),
      detail: activityForm.detail.trim(),
      impact: activityForm.impact.trim(),
      happened_on: activityForm.happened_on || undefined,
      tags: splitList(activityForm.tags),
      links: splitList(activityForm.links),
      proof: {
        claim: activityForm.claim.trim(),
        evidence: activityForm.evidence.trim(),
        metric_label: activityForm.metric_label.trim(),
        metric_before: activityForm.metric_before.trim(),
        metric_after: activityForm.metric_after.trim(),
      },
    })
    resetActivityForm()
    await loadPortfolio()
  }
  catch (unknownError) {
    if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? 'Failed to log activity.')
      return
    }
    error.value = 'Failed to log activity.'
  }
  finally {
    loggingActivity.value = false
  }
}

function resetActivityForm() {
  activityForm.project_id = ''
  activityForm.title = ''
  activityForm.detail = ''
  activityForm.impact = ''
  activityForm.happened_on = ''
  activityForm.tags = ''
  activityForm.links = ''
  activityForm.claim = ''
  activityForm.evidence = ''
  activityForm.metric_label = ''
  activityForm.metric_before = ''
  activityForm.metric_after = ''
}

function splitList(value: string) {
  return value
    .split(/[\n,]/g)
    .map((entry) => entry.trim())
    .filter(Boolean)
}

function sanitizeUsername(value: string) {
  return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'builder'
}

function formatDate(value?: string | null) {
  if (!value) {
    return ''
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(parsed)
}

async function copyPublicUrl() {
  if (typeof navigator === 'undefined' || !navigator.clipboard) {
    return
  }
  await navigator.clipboard.writeText(publicProfileUrl.value)
}

onMounted(() => {
  void loadPortfolio()
})

watch(() => signedInUser.value?.uid || '', () => {
  void loadPortfolio()
})
</script>

<template>
  <section class="portfolio-page">
    <header class="page-card hero-card">
      <div class="hero-copy">
        <p class="page-kicker">Portfolio OS</p>
        <h1>Build a living developer identity, not another static portfolio.</h1>
        <p>
          ApplyPilot now turns resume structure, optimization history, and daily work logs into a public profile that
          stays current.
        </p>
      </div>

      <div class="hero-actions">
        <button class="hero-button primary" type="button" :disabled="bootstrapping || !canManagePortfolio" @click="handleBootstrap">
          {{ bootstrapping ? 'Syncing latest resume…' : 'Sync From Latest Resume' }}
        </button>
        <RouterLink class="hero-button secondary" :to="publicProfilePath">Open Public Profile</RouterLink>
        <button
          v-if="!firebaseUnavailable && !isSignedIn"
          class="hero-button tertiary"
          type="button"
          :disabled="authState.busy || !authReady"
          @click="handleGoogleSignIn"
        >
          {{ authState.busy ? 'Signing in…' : 'Continue With Google' }}
        </button>
      </div>
    </header>

    <article v-if="error" class="page-card status-card" :data-tone="usingPreview ? 'preview' : 'warning'">
      <strong>{{ usingPreview ? 'Preview mode' : 'Portfolio notice' }}</strong>
      <p>{{ error }}</p>
    </article>

    <section v-if="loading" class="page-card empty-state">
      <h2>Loading portfolio workspace…</h2>
      <p>Fetching your latest profile, projects, proof cards, and activity feed.</p>
    </section>

    <section v-else-if="!firebaseUnavailable && !isSignedIn" class="page-card empty-state">
      <p class="section-kicker">Secure access</p>
      <h2>Sign in before loading private portfolio data.</h2>
      <p>
        Private portfolio data is now protected with Firebase Google sign-in. Resume sync, profile edits, and activity
        logging only unlock after authentication.
      </p>

      <button class="inline-button" type="button" :disabled="authState.busy || !authReady" @click="handleGoogleSignIn">
        {{ authState.busy ? 'Signing in…' : 'Continue With Google' }}
      </button>
    </section>

    <section v-else-if="needsBootstrap && !portfolio" class="page-card empty-state">
      <p class="section-kicker">First run</p>
      <h2>No portfolio has been generated yet.</h2>
      <p>
        Run the resume workflow first, then bootstrap a live profile from the latest structured resume and version
        history.
      </p>

      <label class="field">
        <span>Public username</span>
        <input v-model="profileForm.username" type="text" placeholder="abhishek-jha" />
      </label>

      <button class="inline-button" type="button" :disabled="bootstrapping" @click="handleBootstrap">
        {{ bootstrapping ? 'Creating profile…' : 'Create Portfolio From Latest Resume' }}
      </button>
    </section>

    <template v-else-if="portfolio">
      <div class="metric-grid">
        <article v-for="metric in metricCards" :key="metric.label" class="metric-card">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
          <p>{{ metric.detail }}</p>
        </article>
      </div>

      <div class="portfolio-grid">
        <article class="page-card form-card">
          <div class="card-head">
            <div>
              <p class="section-kicker">Identity</p>
              <h2>Profile settings</h2>
            </div>
            <span class="status-pill" :data-tone="portfolio.profile.hiring_status">{{ portfolio.profile.hiring_status }}</span>
          </div>

          <div class="form-grid">
            <label class="field">
              <span>Display name</span>
              <input v-model="profileForm.display_name" type="text" />
            </label>

            <label class="field">
              <span>Username</span>
              <input v-model="profileForm.username" type="text" @blur="profileForm.username = sanitizeUsername(profileForm.username)" />
            </label>

            <label class="field field-wide">
              <span>Headline</span>
              <input v-model="profileForm.headline" type="text" />
            </label>

            <label class="field field-wide">
              <span>Hero statement</span>
              <textarea v-model="profileForm.hero_statement" rows="2"></textarea>
            </label>

            <label class="field field-wide">
              <span>Summary</span>
              <textarea v-model="profileForm.summary" rows="5"></textarea>
            </label>

            <label class="field">
              <span>Primary role</span>
              <input v-model="profileForm.primary_role" type="text" />
            </label>

            <label class="field">
              <span>Location</span>
              <input v-model="profileForm.location" type="text" />
            </label>

            <label class="field">
              <span>Email</span>
              <input v-model="profileForm.contact_email" type="email" />
            </label>

            <label class="field">
              <span>Hiring status</span>
              <select v-model="profileForm.hiring_status">
                <option value="open">Open</option>
                <option value="selective">Selective</option>
                <option value="closed">Closed</option>
              </select>
            </label>
          </div>

          <div class="card-actions">
            <button class="inline-button" type="button" :disabled="savingProfile || !canManagePortfolio" @click="saveProfile">
              {{ savingProfile ? 'Saving…' : 'Save Profile' }}
            </button>
            <button class="ghost-button" type="button" :disabled="!canManagePortfolio" @click="handleBootstrap">
              Refresh From Resume
            </button>
          </div>
        </article>

        <article class="page-card sync-card">
          <p class="section-kicker">Public URL</p>
          <h2>{{ publicProfilePath }}</h2>
          <p class="card-copy">
            Keep the profile current from ApplyPilot history, then share a single link that shows projects, proof, and
            recent work.
          </p>

          <div class="link-shell">
            <strong>{{ publicProfileUrl }}</strong>
            <button type="button" class="chip-button" @click="copyPublicUrl">Copy link</button>
          </div>

          <div class="snapshot-grid">
            <article v-for="item in resumeSnapshotRows" :key="item.label" class="snapshot-tile">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </article>
          </div>

          <RouterLink class="inline-button" :to="publicProfilePath">Preview Public Page</RouterLink>
        </article>
      </div>

      <div class="portfolio-grid">
        <article class="page-card form-card">
          <div class="card-head">
            <div>
              <p class="section-kicker">Daily signal</p>
              <h2>Log your work today</h2>
            </div>
            <span class="status-pill neutral">Manual log</span>
          </div>

          <div class="form-grid">
            <label class="field">
              <span>Project</span>
              <select v-model="activityForm.project_id">
                <option value="">Select a project</option>
                <option v-for="project in projects" :key="project.id" :value="String(project.id)">
                  {{ project.title }}
                </option>
              </select>
            </label>

            <label class="field">
              <span>Date</span>
              <input v-model="activityForm.happened_on" type="date" />
            </label>

            <label class="field field-wide">
              <span>Title</span>
              <input v-model="activityForm.title" type="text" placeholder="Shipped orchestration retry fix" />
            </label>

            <label class="field field-wide">
              <span>What changed?</span>
              <textarea v-model="activityForm.detail" rows="4" placeholder="Describe the work in concrete technical language."></textarea>
            </label>

            <label class="field field-wide">
              <span>Impact</span>
              <input v-model="activityForm.impact" type="text" placeholder="Reduced noisy retry failures by 42%." />
            </label>

            <label class="field field-wide">
              <span>Tags</span>
              <input v-model="activityForm.tags" type="text" placeholder="aws, etl, reliability" />
            </label>

            <label class="field field-wide">
              <span>Links</span>
              <textarea v-model="activityForm.links" rows="2" placeholder="https://github.com/..., https://docs..." />
            </label>

            <label class="field field-wide">
              <span>Proof claim</span>
              <input v-model="activityForm.claim" type="text" placeholder="Reduced ETL failures by 42%." />
            </label>

            <label class="field field-wide">
              <span>Evidence</span>
              <textarea v-model="activityForm.evidence" rows="3" placeholder="What backs up the claim?" />
            </label>

            <label class="field">
              <span>Metric label</span>
              <input v-model="activityForm.metric_label" type="text" placeholder="Failure rate" />
            </label>

            <label class="field">
              <span>Before</span>
              <input v-model="activityForm.metric_before" type="text" placeholder="19%" />
            </label>

            <label class="field">
              <span>After</span>
              <input v-model="activityForm.metric_after" type="text" placeholder="11%" />
            </label>
          </div>

          <div class="card-actions">
            <button class="inline-button" type="button" :disabled="loggingActivity || !canManagePortfolio" @click="submitActivity">
              {{ loggingActivity ? 'Logging…' : 'Publish Activity Entry' }}
            </button>
          </div>
        </article>

        <article class="page-card feed-card">
          <div class="card-head">
            <div>
              <p class="section-kicker">Live feed</p>
              <h2>Recent activity</h2>
            </div>
            <span class="status-pill neutral">{{ activityFeed.length }} items</span>
          </div>

          <div class="feed-list">
            <article v-for="item in activityFeed" :key="item.id" class="feed-item">
              <div class="feed-meta">
                <strong>{{ item.title }}</strong>
                <span>{{ formatDate(item.happened_on || item.created_at) }}</span>
              </div>
              <p>{{ item.detail || item.impact }}</p>
              <small v-if="item.impact">{{ item.impact }}</small>

              <div v-if="item.tags.length" class="tag-row">
                <span v-for="tag in item.tags" :key="`${item.id}-${tag}`">{{ tag }}</span>
              </div>

              <div v-if="item.proof?.claim" class="proof-inline">
                <strong>Proof</strong>
                <p>{{ item.proof.claim }}</p>
              </div>
            </article>
          </div>
        </article>
      </div>

      <article class="page-card">
        <div class="card-head">
          <div>
            <p class="section-kicker">Proof cards</p>
            <h2>Claims backed by evidence</h2>
          </div>
          <span class="status-pill neutral">{{ proofCards.length }} cards</span>
        </div>

        <div class="proof-grid">
          <article v-for="card in proofCards" :key="card.id" class="proof-card">
            <span class="proof-source">{{ card.project_title || card.source }}</span>
            <h3>{{ card.claim }}</h3>
            <p>{{ card.evidence || 'Attach clearer evidence to sharpen the card.' }}</p>

            <div v-if="card.metric_label || card.metric_after" class="metric-chip">
              <span>{{ card.metric_label || 'Measured impact' }}</span>
              <strong>{{ card.metric_before ? `${card.metric_before} → ${card.metric_after}` : card.metric_after }}</strong>
            </div>
          </article>
        </div>
      </article>

      <article class="page-card">
        <div class="card-head">
          <div>
            <p class="section-kicker">Generated projects</p>
            <h2>Portfolio structure from resume plus live logs</h2>
          </div>
          <span class="status-pill neutral">{{ projects.length }} projects</span>
        </div>

        <div class="project-grid">
          <article v-for="project in projects" :key="project.id" class="project-card" :data-featured="project.featured">
            <div class="project-head">
              <div>
                <span class="project-source">{{ project.source.replace(/_/g, ' ') }}</span>
                <h3>{{ project.title }}</h3>
              </div>
              <span v-if="project.featured" class="featured-pill">Featured</span>
            </div>

            <p>{{ project.summary }}</p>
            <strong class="impact-line">{{ project.impact_statement }}</strong>

            <div v-if="project.tech_stack.length" class="tag-row">
              <span v-for="tech in project.tech_stack" :key="`${project.id}-${tech}`">{{ tech }}</span>
            </div>

            <ul v-if="project.proof_points.length" class="bullet-list">
              <li v-for="point in project.proof_points" :key="point">{{ point }}</li>
            </ul>
          </article>
        </div>
      </article>
    </template>
  </section>
</template>

<style scoped>
.portfolio-page {
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
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 10px 30px rgba(20, 33, 61, 0.07);
}

.hero-card {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: center;
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.14), transparent 28%),
    radial-gradient(circle at bottom left, rgba(245, 158, 11, 0.12), transparent 30%),
    linear-gradient(135deg, rgba(255, 248, 235, 0.94), rgba(255, 255, 255, 0.98));
}

.hero-copy {
  max-width: 760px;
}

.page-kicker,
.section-kicker,
.proof-source,
.project-source {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h1,
h2,
h3 {
  margin: 0;
  line-height: 1.02;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

h1 {
  font-size: clamp(2rem, 3vw, 3rem);
}

.hero-copy p:last-child,
.card-copy,
.feed-item p,
.feed-item small,
.proof-card p,
.project-card p,
.empty-state p,
.status-card p {
  margin: 12px 0 0;
  color: #5f6c80;
}

.hero-actions,
.card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.hero-button,
.inline-button,
.ghost-button,
.chip-button {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  min-height: 48px;
  padding: 12px 18px;
  border: 0;
  border-radius: 999px;
  font-weight: 700;
  cursor: pointer;
}

.hero-button.primary,
.inline-button,
.chip-button {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.hero-button.secondary,
.ghost-button {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.94);
}

.hero-button.tertiary {
  color: #124084;
  background: rgba(219, 234, 254, 0.9);
}

.hero-button:disabled,
.inline-button:disabled,
.ghost-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.status-card {
  display: grid;
  gap: 4px;
}

.status-card[data-tone='warning'] {
  background: rgba(255, 247, 237, 0.92);
}

.status-card[data-tone='preview'] {
  background: rgba(219, 234, 254, 0.66);
}

.empty-state {
  display: grid;
  gap: 18px;
  justify-items: start;
}

.metric-grid,
.portfolio-grid,
.proof-grid,
.project-grid,
.snapshot-grid,
.form-grid {
  display: grid;
  gap: 16px;
}

.metric-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.metric-card,
.snapshot-tile,
.proof-card,
.project-card,
.feed-item {
  padding: 18px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.05);
}

.metric-card span,
.snapshot-tile span,
.metric-chip span {
  color: #5f6c80;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.metric-card strong {
  display: block;
  margin-top: 10px;
  font-size: 2rem;
}

.metric-card p {
  margin: 10px 0 0;
  color: #5f6c80;
}

.portfolio-grid {
  grid-template-columns: 1.15fr 0.85fr;
}

.card-head,
.feed-meta,
.project-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.status-pill,
.featured-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
}

.status-pill[data-tone='open'] {
  color: #166534;
  background: rgba(220, 252, 231, 0.9);
}

.status-pill[data-tone='selective'] {
  color: #92400e;
  background: rgba(255, 247, 237, 0.92);
}

.status-pill[data-tone='closed'],
.status-pill.neutral {
  color: #124084;
  background: rgba(219, 234, 254, 0.86);
}

.form-card,
.feed-card,
.sync-card {
  display: grid;
  gap: 18px;
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  font-size: 0.88rem;
  font-weight: 700;
}

.field input,
.field textarea,
.field select {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.92);
  color: #14213d;
}

.field textarea {
  resize: vertical;
}

.field-wide {
  grid-column: 1 / -1;
}

.link-shell {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.05);
}

.link-shell strong {
  max-width: 100%;
  overflow-wrap: anywhere;
}

.snapshot-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.snapshot-tile strong {
  margin-top: 10px;
}

.feed-list,
.bullet-list {
  display: grid;
  gap: 12px;
}

.feed-meta span {
  color: #5f6c80;
  font-size: 0.9rem;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.tag-row span,
.metric-chip {
  display: inline-flex;
  gap: 8px;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  color: #124084;
  font-size: 0.82rem;
  font-weight: 700;
}

.proof-inline {
  margin-top: 14px;
  padding: 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
}

.proof-inline p {
  margin: 6px 0 0;
}

.proof-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 18px;
}

.proof-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 247, 237, 0.9));
}

.proof-card h3 {
  margin-top: 10px;
  font-size: 1.2rem;
}

.metric-chip {
  width: fit-content;
  margin-top: 16px;
}

.project-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 18px;
}

.project-card[data-featured='true'] {
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.1), transparent 35%),
    rgba(20, 33, 61, 0.05);
}

.impact-line {
  display: block;
  margin-top: 14px;
  color: #14213d;
}

.featured-pill {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.92);
}

.bullet-list {
  margin: 16px 0 0;
  padding-left: 18px;
  color: #4f5e75;
}

@media (max-width: 1200px) {
  .metric-grid,
  .proof-grid,
  .project-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .portfolio-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .portfolio-page {
    height: auto;
  }

  .hero-card {
    flex-direction: column;
    align-items: stretch;
  }

  .form-grid,
  .snapshot-grid,
  .metric-grid,
  .proof-grid,
  .project-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .page-card {
    padding: 22px;
  }

  .hero-actions,
  .card-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-button,
  .inline-button,
  .ghost-button,
  .chip-button {
    width: 100%;
  }

  .card-head,
  .feed-meta,
  .project-head,
  .link-shell {
    flex-direction: column;
  }
}
</style>
