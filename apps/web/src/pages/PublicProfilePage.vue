<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

import PublicLayout from '../components/marketing/PublicLayout.vue'
import { portfolioPreview } from '../content/portfolioPreview'
import { fetchPublicPortfolio } from '../lib/portfolioApi'
import type { PublicPortfolioOverview } from '../types/portfolio'

const props = defineProps<{
  username: string
}>()

const loading = ref(true)
const error = ref('')
const portfolio = ref<PublicPortfolioOverview | null>(null)
const usingPreview = ref(false)

const statCards = computed(() => {
  if (!portfolio.value) {
    return []
  }
  return [
    {
      label: 'Impact score',
      value: String(portfolio.value.metrics.impact_score),
    },
    {
      label: 'Recent activity',
      value: `${portfolio.value.metrics.recent_activity_count} / 7d`,
    },
    {
      label: 'Proof cards',
      value: String(portfolio.value.metrics.proof_count),
    },
    {
      label: 'Tech diversity',
      value: String(portfolio.value.metrics.tech_diversity),
    },
  ]
})

const activityFeed = computed(() => portfolio.value?.activity ?? [])
const projects = computed(() => portfolio.value?.projects ?? [])
const proofCards = computed(() => portfolio.value?.proof_cards ?? [])
const opportunitySignal = computed(() => {
  if (!portfolio.value) {
    return ''
  }
  if (portfolio.value.metrics.recent_activity_count > 0) {
    return 'Actively shipping work'
  }
  if (portfolio.value.metrics.project_count > 0) {
    return 'Project portfolio available'
  }
  return 'Building public signal'
})

function clonePreview() {
  return JSON.parse(JSON.stringify(portfolioPreview)) as PublicPortfolioOverview
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

async function loadProfile() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchPublicPortfolio(props.username)
    portfolio.value = data
    usingPreview.value = false
  }
  catch (unknownError) {
    if (props.username === portfolioPreview.profile.username) {
      portfolio.value = clonePreview()
      usingPreview.value = true
      error.value = 'Showing preview profile because the live portfolio API is unavailable.'
    }
    else if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? 'Public profile not found.')
    }
    else {
      error.value = 'Public profile not found.'
    }
  }
  finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadProfile()
})
</script>

<template>
  <PublicLayout>
    <section class="public-profile">
      <section v-if="loading" class="profile-card loading-card">
        <h1>Loading profile…</h1>
        <p>Fetching projects, proof cards, and recent technical activity.</p>
      </section>

      <section v-else-if="!portfolio" class="profile-card loading-card">
        <h1>Profile not found</h1>
        <p>{{ error || 'This public profile does not exist yet.' }}</p>
        <RouterLink class="cta-button" to="/dashboard/portfolio">Open portfolio workspace</RouterLink>
      </section>

      <template v-else>
        <article v-if="error" class="profile-card notice-card" :data-tone="usingPreview ? 'preview' : 'warning'">
          <strong>{{ usingPreview ? 'Preview mode' : 'Notice' }}</strong>
          <p>{{ error }}</p>
        </article>

        <header class="hero-shell">
          <div class="hero-copy">
            <p class="hero-kicker">Live developer profile</p>
            <h1>{{ portfolio.profile.display_name }}</h1>
            <p class="headline">{{ portfolio.profile.headline }}</p>
            <p class="hero-statement">{{ portfolio.profile.hero_statement || portfolio.profile.summary }}</p>

            <div class="meta-row">
              <span>{{ portfolio.profile.primary_role }}</span>
              <span v-if="portfolio.profile.location">{{ portfolio.profile.location }}</span>
              <span>{{ opportunitySignal }}</span>
            </div>

            <div class="hero-actions">
              <RouterLink class="cta-button" to="/dashboard/portfolio">Open workspace</RouterLink>
              <RouterLink class="ghost-button" to="/dashboard/portfolio">Build your own profile</RouterLink>
            </div>
          </div>

          <div class="hero-panel">
            <article v-for="stat in statCards" :key="stat.label" class="stat-tile">
              <span>{{ stat.label }}</span>
              <strong>{{ stat.value }}</strong>
            </article>
          </div>
        </header>

        <div class="content-grid">
          <article class="profile-card">
            <div class="section-head">
              <div>
                <p class="section-kicker">Why this profile exists</p>
                <h2>Summary</h2>
              </div>
              <span class="pill">{{ props.username }}</span>
            </div>
            <p class="body-copy">{{ portfolio.profile.summary }}</p>
          </article>

          <article class="profile-card">
            <div class="section-head">
              <div>
                <p class="section-kicker">Signal</p>
                <h2>What this page emphasizes</h2>
              </div>
              <span class="pill">{{ portfolio.metrics.resume_versions }} versions</span>
            </div>
            <div class="snapshot-list">
              <article class="snapshot-item">
                <span>Recent activity</span>
                <strong>{{ portfolio.metrics.recent_activity_count }} entries in the last 7 days</strong>
              </article>
              <article class="snapshot-item">
                <span>Projects</span>
                <strong>{{ portfolio.metrics.project_count }} proof-backed project narratives</strong>
              </article>
              <article class="snapshot-item">
                <span>Proof density</span>
                <strong>{{ portfolio.metrics.proof_count }} evidence cards</strong>
              </article>
            </div>
          </article>
        </div>

        <article class="profile-card">
          <div class="section-head">
            <div>
              <p class="section-kicker">Recent activity</p>
              <h2>What changed recently</h2>
            </div>
            <span class="pill">{{ activityFeed.length }} updates</span>
          </div>

          <div class="activity-list">
            <article v-for="item in activityFeed" :key="item.id" class="activity-item">
              <div class="activity-topline">
                <strong>{{ item.title }}</strong>
                <span>{{ formatDate(item.happened_on || item.created_at) }}</span>
              </div>
              <p>{{ item.detail || item.impact }}</p>
              <small v-if="item.impact">{{ item.impact }}</small>

              <div v-if="item.tags.length" class="tag-row">
                <span v-for="tag in item.tags" :key="`${item.id}-${tag}`">{{ tag }}</span>
              </div>
            </article>
          </div>
        </article>

        <article class="profile-card">
          <div class="section-head">
            <div>
              <p class="section-kicker">Proof cards</p>
              <h2>Claims backed by evidence</h2>
            </div>
            <span class="pill">{{ proofCards.length }} cards</span>
          </div>

          <div class="proof-grid">
            <article v-for="card in proofCards" :key="card.id" class="proof-card">
              <span class="proof-label">{{ card.project_title || card.source }}</span>
              <h3>{{ card.claim }}</h3>
              <p>{{ card.evidence || 'Evidence was not attached to this card yet.' }}</p>

              <div v-if="card.metric_label || card.metric_after" class="metric-chip">
                <span>{{ card.metric_label || 'Measured impact' }}</span>
                <strong>{{ card.metric_before ? `${card.metric_before} → ${card.metric_after}` : card.metric_after }}</strong>
              </div>
            </article>
          </div>
        </article>

        <article class="profile-card">
          <div class="section-head">
            <div>
              <p class="section-kicker">Projects</p>
              <h2>Work history translated into proof-backed narratives</h2>
            </div>
            <span class="pill">{{ projects.length }} projects</span>
          </div>

          <div class="project-grid">
            <article v-for="project in projects" :key="project.id" class="project-card" :data-featured="project.featured">
              <div class="project-head">
                <div>
                  <span class="proof-label">{{ project.source.replace(/_/g, ' ') }}</span>
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
  </PublicLayout>
</template>

<style scoped>
.public-profile {
  display: grid;
  gap: 20px;
  max-width: 1240px;
  margin: 0 auto;
  padding: 32px 24px 56px;
}

.profile-card {
  padding: 28px;
  border: 1px solid rgba(20, 33, 61, 0.08);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 12px 34px rgba(20, 33, 61, 0.07);
}

.loading-card,
.notice-card {
  display: grid;
  gap: 6px;
}

.notice-card[data-tone='preview'] {
  background: rgba(219, 234, 254, 0.74);
}

.notice-card[data-tone='warning'] {
  background: rgba(255, 247, 237, 0.94);
}

.hero-shell,
.content-grid,
.proof-grid,
.project-grid,
.snapshot-list,
.hero-panel {
  display: grid;
  gap: 18px;
}

.hero-shell {
  grid-template-columns: 1.1fr 0.9fr;
  align-items: stretch;
}

.hero-copy,
.hero-panel {
  padding: 30px;
  border-radius: 30px;
}

.hero-copy {
  background:
    radial-gradient(circle at top left, rgba(245, 158, 11, 0.18), transparent 30%),
    linear-gradient(135deg, rgba(255, 252, 245, 0.96), rgba(255, 255, 255, 0.98));
  border: 1px solid rgba(20, 33, 61, 0.08);
}

.hero-panel {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  background: linear-gradient(180deg, rgba(20, 33, 61, 0.95), rgba(26, 77, 170, 0.96));
}

.hero-kicker,
.section-kicker,
.proof-label {
  display: block;
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.hero-copy h1,
.profile-card h2,
.proof-card h3,
.project-card h3 {
  margin: 0;
  line-height: 1.02;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.hero-copy h1 {
  font-size: clamp(2.4rem, 4vw, 3.4rem);
}

.headline {
  margin: 14px 0 0;
  font-size: 1.18rem;
  color: #14213d;
}

.hero-statement,
.body-copy,
.activity-item p,
.activity-item small,
.proof-card p,
.project-card p,
.loading-card p,
.notice-card p {
  margin: 14px 0 0;
  color: #5f6c80;
}

.meta-row,
.hero-actions,
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.meta-row {
  margin-top: 18px;
}

.meta-row span,
.tag-row span,
.pill,
.metric-chip,
.featured-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
}

.meta-row span,
.pill,
.tag-row span {
  color: #124084;
  background: rgba(219, 234, 254, 0.86);
}

.hero-actions {
  margin-top: 24px;
}

.cta-button,
.ghost-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48px;
  padding: 12px 18px;
  border-radius: 999px;
  font-weight: 700;
}

.cta-button {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.ghost-button {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.94);
}

.stat-tile {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.08);
}

.stat-tile span {
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.stat-tile strong {
  color: #fff;
  font-size: 2rem;
}

.content-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.section-head,
.activity-topline,
.project-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.snapshot-list {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 18px;
}

.snapshot-item,
.activity-item,
.proof-card,
.project-card {
  padding: 18px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.05);
}

.snapshot-item span,
.metric-chip span {
  color: #5f6c80;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.snapshot-item strong {
  display: block;
  margin-top: 10px;
}

.activity-list {
  display: grid;
  gap: 14px;
  margin-top: 18px;
}

.activity-topline span {
  color: #5f6c80;
  font-size: 0.9rem;
}

.proof-grid,
.project-grid {
  margin-top: 18px;
}

.proof-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.proof-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 247, 237, 0.9));
}

.proof-card h3 {
  margin-top: 10px;
  font-size: 1.18rem;
}

.metric-chip {
  width: fit-content;
  gap: 8px;
  margin-top: 16px;
  background: rgba(255, 255, 255, 0.86);
  color: #124084;
}

.project-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.project-card[data-featured='true'] {
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.12), transparent 34%),
    rgba(20, 33, 61, 0.05);
}

.impact-line {
  display: block;
  margin-top: 16px;
  color: #14213d;
}

.featured-pill {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.94);
}

.bullet-list {
  display: grid;
  gap: 10px;
  margin: 16px 0 0;
  padding-left: 18px;
  color: #4f5e75;
}

@media (max-width: 1100px) {
  .hero-shell,
  .content-grid,
  .proof-grid,
  .project-grid {
    grid-template-columns: 1fr;
  }

  .snapshot-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .public-profile {
    padding: 24px 16px 40px;
  }

  .profile-card,
  .hero-copy,
  .hero-panel {
    padding: 22px;
  }

  .hero-panel {
    grid-template-columns: 1fr;
  }

  .section-head,
  .activity-topline,
  .project-head {
    flex-direction: column;
  }

  .hero-actions {
    flex-direction: column;
  }

  .cta-button,
  .ghost-button {
    width: 100%;
  }
}
</style>
