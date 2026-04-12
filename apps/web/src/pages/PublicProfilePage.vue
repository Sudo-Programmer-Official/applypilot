<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import axios from 'axios'

import { portfolioPreview } from '../content/portfolioPreview'
import { fetchPublicPortfolio } from '../lib/portfolioApi'
import type {
  PortfolioActivity,
  PortfolioProject,
  PortfolioProofCard,
  PublicPortfolioOverview,
} from '../types/portfolio'

const props = defineProps<{
  username: string
}>()

const loading = ref(true)
const error = ref('')
const portfolio = ref<PublicPortfolioOverview | null>(null)
const usingPreview = ref(false)
const animatedMetrics = ref<Record<string, number>>({})

let metricAnimationFrame: number | null = null

const sectionLinks = [
  { label: 'Proof', href: '#proof' },
  { label: 'Systems', href: '#systems' },
  { label: 'Projects', href: '#projects' },
  { label: 'Activity', href: '#activity' },
]

const systemPrinciples = [
  {
    title: 'Scalability',
    description: 'Queue-backed execution keeps high-volume ETL and async workflows predictable under load.',
  },
  {
    title: 'Fault tolerance',
    description: 'Retries are batched and isolated so recovery paths stay targeted instead of noisy.',
  },
  {
    title: 'Observability',
    description: 'Metrics and event traces make slow paths and regressions visible before they become incidents.',
  },
]

const architectureFlow = [
  {
    step: '01',
    title: 'Client + Events',
    description: 'Requests, resume history, and work logs enter through clear boundaries.',
  },
  {
    step: '02',
    title: 'API Layer',
    description: 'Validation, identity, and routing shape traffic before execution fans out.',
  },
  {
    step: '03',
    title: 'Queue',
    description: 'Buffering and backpressure smooth spikes instead of pushing load downstream.',
  },
  {
    step: '04',
    title: 'Workers',
    description: 'Retries, batching, and orchestration isolate failures to the smallest safe unit.',
  },
  {
    step: '05',
    title: 'Data + Telemetry',
    description: 'Durable state and metrics make outcomes visible to operators and recruiters.',
  },
]

const sourceLabels: Record<string, string> = {
  manual_log: 'Live log',
  resume_project: 'Case study',
  resume_experience: 'Experience',
  resume_version: 'Signal refinement',
  resume_bootstrap: 'Profile launch',
}

const roleLabel = computed(() => portfolio.value?.profile.primary_role?.trim() || 'Backend Systems Engineer')

const headlineLabel = computed(() => portfolio.value?.profile.headline?.trim() || 'Distributed Systems | AI Infrastructure')

const summaryLine = computed(
  () => portfolio.value?.profile.summary?.trim() || 'I build scalable backend systems and real-time pipelines.',
)

const supportingLine = computed(() => {
  const heroStatement = portfolio.value?.profile.hero_statement?.trim() || ''
  if (heroStatement && heroStatement !== summaryLine.value) {
    return heroStatement
  }
  return 'Focused on scalability, fault tolerance, and observability.'
})

const availabilitySignal = computed(() => {
  if (!portfolio.value) {
    return 'Building public signal'
  }
  if (portfolio.value.metrics.recent_activity_count > 0) {
    return 'Actively shipping'
  }
  if (portfolio.value.metrics.project_count > 0) {
    return 'Proof-backed portfolio'
  }
  return 'Building public signal'
})

const sortedProjects = computed(() => {
  if (!portfolio.value) {
    return []
  }
  return [...portfolio.value.projects].sort(
    (left, right) => Number(right.featured) - Number(left.featured) || left.sort_order - right.sort_order,
  )
})

const sortedActivity = computed(() => {
  if (!portfolio.value) {
    return []
  }
  return [...portfolio.value.activity].sort(
    (left, right) =>
      parseDateValue(right.happened_on || right.created_at) - parseDateValue(left.happened_on || left.created_at),
  )
})

const projectIndex = computed(() => new Map(sortedProjects.value.map((project) => [project.id, project])))

const heroMetrics = computed(() => {
  if (!portfolio.value) {
    return []
  }
  return [
    {
      key: 'impact',
      value: portfolio.value.metrics.impact_score,
      label: 'Impact score',
    },
    {
      key: 'projects',
      value: portfolio.value.metrics.project_count,
      label: 'Case studies',
    },
    {
      key: 'activity',
      value: portfolio.value.metrics.recent_activity_count,
      label: 'Live updates',
    },
  ]
})

const proofHighlights = computed(() => {
  if (!portfolio.value) {
    return []
  }
  return [...portfolio.value.proof_cards]
    .sort(
      (left, right) =>
        Number(Boolean(right.metric_after || right.metric_before)) -
          Number(Boolean(left.metric_after || left.metric_before)) ||
        parseDateValue(right.created_at) - parseDateValue(left.created_at),
    )
    .slice(0, 3)
})

const heroOutcomes = computed(() =>
  proofHighlights.value.map((card) => ({
    id: card.id,
    label: card.metric_label || 'Measured impact',
    metric: formatMetricRange(card.metric_before, card.metric_after) || card.metric_after || card.metric_before,
    claim: card.claim,
    evidence: card.evidence,
  })),
)

const techHighlights = computed(() => {
  const counts = new Map<string, number>()

  for (const project of sortedProjects.value) {
    for (const tech of project.tech_stack) {
      counts.set(tech, (counts.get(tech) ?? 0) + 1)
    }
  }

  return [...counts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, 4)
    .map(([tech]) => tech)
})

const featuredProjects = computed(() => sortedProjects.value.slice(0, 3))

const recentActivity = computed(() => sortedActivity.value.slice(0, 5))

const lastUpdatedLabel = computed(() => {
  const latest = sortedActivity.value[0]
  return formatDate(latest?.happened_on || latest?.created_at) || 'Recently updated'
})

const profileInitials = computed(() => {
  const source = portfolio.value?.profile.display_name?.trim() || props.username
  return source
    .split(/\s+/)
    .map((part) => part.charAt(0))
    .join('')
    .slice(0, 2)
    .toUpperCase()
})

function clonePreview() {
  return JSON.parse(JSON.stringify(portfolioPreview)) as PublicPortfolioOverview
}

function parseDateValue(value?: string | null) {
  if (!value) {
    return 0
  }
  const parsed = Date.parse(value)
  return Number.isNaN(parsed) ? 0 : parsed
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

function formatSourceLabel(source: string) {
  if (sourceLabels[source]) {
    return sourceLabels[source]
  }
  return source
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function formatMetricRange(before?: string | null, after?: string | null) {
  if (before && after) {
    return `${before} -> ${after}`
  }
  return after || before || ''
}

function proofTags(card: PortfolioProofCard) {
  if (card.project_id) {
    return projectIndex.value.get(card.project_id)?.tech_stack.slice(0, 4) ?? []
  }
  return [formatSourceLabel(card.source)]
}

function projectSolution(project: PortfolioProject) {
  return project.proof_points[0] || project.bullets[1] || project.bullets[0] || project.impact_statement
}

function activityMetric(item: PortfolioActivity) {
  const metric = formatMetricRange(item.proof.metric_before, item.proof.metric_after)
  if (!metric) {
    return null
  }
  return {
    label: item.proof.metric_label || 'Measured impact',
    value: metric,
  }
}

function displayMetric(key: string) {
  return animatedMetrics.value[key] ?? 0
}

function cancelMetricAnimation() {
  if (metricAnimationFrame !== null) {
    window.cancelAnimationFrame(metricAnimationFrame)
    metricAnimationFrame = null
  }
}

function animateHeroMetrics() {
  if (!heroMetrics.value.length || typeof window === 'undefined') {
    return
  }

  cancelMetricAnimation()

  const startedAt = window.performance.now()
  const duration = 900

  const step = (timestamp: number) => {
    const progress = Math.min((timestamp - startedAt) / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    const nextValues: Record<string, number> = {}

    for (const metric of heroMetrics.value) {
      nextValues[metric.key] = Math.round(metric.value * eased)
    }

    animatedMetrics.value = nextValues

    if (progress < 1) {
      metricAnimationFrame = window.requestAnimationFrame(step)
    } else {
      metricAnimationFrame = null
    }
  }

  metricAnimationFrame = window.requestAnimationFrame(step)
}

async function loadProfile() {
  loading.value = true
  error.value = ''

  try {
    const data = await fetchPublicPortfolio(props.username)
    portfolio.value = data
    usingPreview.value = false
  } catch (unknownError) {
    if (props.username === portfolioPreview.profile.username) {
      portfolio.value = clonePreview()
      usingPreview.value = true
      error.value = 'Showing preview profile because the live portfolio API is unavailable.'
    } else if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? 'Public profile not found.')
    } else {
      error.value = 'Public profile not found.'
    }
  } finally {
    loading.value = false
  }
}

watch(
  () => portfolio.value?.metrics,
  (metrics) => {
    if (!metrics) {
      animatedMetrics.value = {}
      return
    }
    animateHeroMetrics()
  },
  { immediate: true },
)

onMounted(() => {
  void loadProfile()
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    cancelMetricAnimation()
  }
})
</script>

<template>
  <section class="profile-experience">
    <div class="page-glow glow-left" aria-hidden="true"></div>
    <div class="page-glow glow-right" aria-hidden="true"></div>

    <header class="portfolio-rail">
      <a class="rail-profile" href="#top">
        <span class="rail-mark">{{ profileInitials }}</span>
        <span class="rail-copy">
          <strong>{{ portfolio?.profile.display_name || 'Public Portfolio' }}</strong>
          <small>{{ roleLabel }}</small>
        </span>
      </a>

      <nav class="rail-links" aria-label="Section navigation">
        <a v-for="section in sectionLinks" :key="section.href" :href="section.href">
          {{ section.label }}
        </a>
      </nav>

      <span class="rail-status">{{ lastUpdatedLabel }}</span>
    </header>

    <main class="portfolio-stack">
      <section v-if="loading" class="stage-card">
        <p class="section-kicker">Loading profile</p>
        <h1>Collecting proof, activity, and project signals.</h1>
        <p>The public portfolio is pulling recent work history, impact metrics, and supporting evidence.</p>
      </section>

      <section v-else-if="!portfolio" class="stage-card">
        <p class="section-kicker">Profile unavailable</p>
        <h1>Public profile not found.</h1>
        <p>{{ error || 'This portfolio does not exist yet.' }}</p>
        <RouterLink class="inline-action" to="/dashboard/portfolio">Open portfolio workspace</RouterLink>
      </section>

      <template v-else>
        <article v-if="error" class="notice-banner" :data-tone="usingPreview ? 'preview' : 'warning'">
          <strong>{{ usingPreview ? 'Preview mode' : 'Notice' }}</strong>
          <span>{{ error }}</span>
        </article>

        <section id="top" class="hero-stage reveal" style="--delay: 0.04s">
          <div class="hero-copy">
            <p class="section-kicker">{{ roleLabel }}</p>
            <h1>{{ portfolio.profile.display_name }}</h1>
            <p class="hero-title">{{ headlineLabel }}</p>
            <p class="hero-summary">{{ summaryLine }}</p>
            <p class="hero-support">{{ supportingLine }}</p>

            <div class="hero-tags">
              <span v-if="portfolio.profile.location">{{ portfolio.profile.location }}</span>
              <span>{{ availabilitySignal }}</span>
              <span v-for="tech in techHighlights" :key="tech">{{ tech }}</span>
            </div>

            <div class="hero-metrics">
              <article v-for="metric in heroMetrics" :key="metric.key" class="hero-metric">
                <strong>{{ displayMetric(metric.key) }}</strong>
                <span>{{ metric.label }}</span>
              </article>
            </div>

            <div class="hero-actions">
              <a class="primary-link" href="#proof">View proof</a>
              <a class="secondary-link" href="#systems">See system design</a>
            </div>
          </div>

          <aside class="hero-panel">
            <p class="section-kicker light">Selected outcomes</p>

            <article v-for="item in heroOutcomes" :key="item.id" class="outcome-item">
              <div class="outcome-header">
                <span>{{ item.label }}</span>
                <strong>{{ item.metric }}</strong>
              </div>
              <p>{{ item.claim }}</p>
              <small>{{ item.evidence }}</small>
            </article>

            <div class="hero-note">
              <span>Current signal</span>
              <strong>{{ lastUpdatedLabel }}</strong>
              <p>Built around shipped work, measurable outcomes, and system-level reasoning.</p>
            </div>
          </aside>
        </section>

        <section id="proof" class="section-block reveal" style="--delay: 0.08s">
          <div class="section-heading">
            <div>
              <p class="section-kicker">Proof</p>
              <h2>Claims backed by shipped outcomes</h2>
            </div>
            <p class="section-note">Big numbers first. Minimal narrative. Clear evidence.</p>
          </div>

          <div class="proof-grid">
            <article v-for="card in proofHighlights" :key="card.id" class="proof-card">
              <p class="card-kicker">{{ card.project_title || formatSourceLabel(card.source) }}</p>

              <div v-if="formatMetricRange(card.metric_before, card.metric_after)" class="proof-metric">
                <span>{{ card.metric_label || 'Measured impact' }}</span>
                <strong>{{ formatMetricRange(card.metric_before, card.metric_after) }}</strong>
              </div>

              <h3>{{ card.claim }}</h3>
              <p>{{ card.evidence }}</p>

              <div v-if="proofTags(card).length" class="tag-row">
                <span v-for="tag in proofTags(card)" :key="`${card.id}-${tag}`">{{ tag }}</span>
              </div>
            </article>
          </div>
        </section>

        <section id="systems" class="systems-stage reveal" style="--delay: 0.12s">
          <div class="section-heading on-dark">
            <div>
              <p class="section-kicker light">System thinking</p>
              <h2>How I build systems</h2>
            </div>
            <p class="section-note">
              Scalability, fault tolerance, and observability shape the architecture before implementation detail does.
            </p>
          </div>

          <div class="systems-grid">
            <div class="architecture-flow">
              <article v-for="node in architectureFlow" :key="node.step" class="architecture-node">
                <span>{{ node.step }}</span>
                <strong>{{ node.title }}</strong>
                <p>{{ node.description }}</p>
              </article>
            </div>

            <div class="principle-grid">
              <article v-for="principle in systemPrinciples" :key="principle.title" class="principle-card">
                <h3>{{ principle.title }}</h3>
                <p>{{ principle.description }}</p>
              </article>
            </div>
          </div>
        </section>

        <section id="projects" class="section-block reveal" style="--delay: 0.16s">
          <div class="section-heading">
            <div>
              <p class="section-kicker">Case studies</p>
              <h2>Featured backend work translated into decisions and impact</h2>
            </div>
            <p class="section-note">Each project centers the problem, the system move, and the measurable result.</p>
          </div>

          <div class="case-study-list">
            <article v-for="project in featuredProjects" :key="project.id" class="case-study-card">
              <div class="case-study-head">
                <div>
                  <p class="card-kicker">{{ formatSourceLabel(project.source) }}</p>
                  <h3>{{ project.title }}</h3>
                </div>
                <span v-if="project.featured" class="featured-pill">Featured</span>
              </div>

              <div class="case-study-grid">
                <div class="case-study-block">
                  <span>Problem</span>
                  <p>{{ project.summary }}</p>
                </div>

                <div class="case-study-block">
                  <span>Solution</span>
                  <p>{{ projectSolution(project) }}</p>
                </div>

                <div class="case-study-block">
                  <span>Impact</span>
                  <p class="impact-copy">{{ project.impact_statement }}</p>
                </div>
              </div>

              <div class="case-study-footer">
                <div v-if="project.tech_stack.length" class="tag-row">
                  <span v-for="tech in project.tech_stack.slice(0, 5)" :key="`${project.id}-${tech}`">{{ tech }}</span>
                </div>
                <a class="inline-link" href="#systems">View architecture</a>
              </div>
            </article>
          </div>
        </section>

        <section id="activity" class="section-block reveal" style="--delay: 0.2s">
          <div class="section-heading">
            <div>
              <p class="section-kicker">Recent activity</p>
              <h2>Live signal tied to technical movement</h2>
            </div>
            <p class="section-note">Each update ties an engineering action to a visible outcome.</p>
          </div>

          <div class="activity-list">
            <article v-for="item in recentActivity" :key="item.id" class="activity-card">
              <div class="activity-meta">
                <span>{{ formatDate(item.happened_on || item.created_at) }}</span>
                <span>{{ formatSourceLabel(item.source) }}</span>
              </div>

              <div v-if="activityMetric(item)" class="activity-metric">
                <span>{{ activityMetric(item)?.label }}</span>
                <strong>{{ activityMetric(item)?.value }}</strong>
              </div>

              <h3>{{ item.title }}</h3>
              <p>{{ item.detail }}</p>
              <strong class="activity-impact">{{ item.impact }}</strong>

              <div v-if="item.tags.length" class="tag-row muted">
                <span v-for="tag in item.tags" :key="`${item.id}-${tag}`">{{ tag }}</span>
              </div>
            </article>
          </div>
        </section>

        <footer class="portfolio-footer reveal" style="--delay: 0.24s">
          <div class="footer-copy">
            <strong>{{ portfolio.profile.display_name }}</strong>
            <p>{{ roleLabel }} building scalable backend systems, ETL platforms, and live signal pipelines.</p>
          </div>

          <div class="footer-meta">
            <span>{{ availabilitySignal }}</span>
            <span>{{ lastUpdatedLabel }}</span>
          </div>
        </footer>
      </template>
    </main>
  </section>
</template>

<style scoped>
.profile-experience {
  position: relative;
  min-height: 100vh;
  padding: 22px 24px 64px;
  overflow: clip;
  color: #0f172a;
  background:
    radial-gradient(circle at top left, rgba(96, 165, 250, 0.22), transparent 28%),
    radial-gradient(circle at top right, rgba(251, 191, 36, 0.18), transparent 24%),
    linear-gradient(180deg, #edf3fb 0%, #f8f5ee 48%, #eff2f6 100%);
}

.page-glow {
  position: absolute;
  width: 420px;
  height: 420px;
  border-radius: 999px;
  filter: blur(56px);
  opacity: 0.44;
}

.glow-left {
  top: -80px;
  left: -140px;
  background: rgba(96, 165, 250, 0.3);
}

.glow-right {
  top: 160px;
  right: -120px;
  background: rgba(251, 191, 36, 0.24);
}

.portfolio-rail,
.portfolio-stack {
  position: relative;
  z-index: 1;
  max-width: 1180px;
  margin: 0 auto;
}

.portfolio-rail {
  position: sticky;
  top: 18px;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  padding: 14px 18px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(20px);
  box-shadow: 0 16px 44px rgba(15, 23, 42, 0.08);
}

.rail-profile {
  display: inline-flex;
  gap: 14px;
  align-items: center;
  color: inherit;
}

.rail-mark {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 16px;
  color: #f8fafc;
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  background: linear-gradient(135deg, #0f172a, #3b82f6);
  box-shadow: 0 14px 30px rgba(59, 130, 246, 0.24);
}

.rail-copy {
  display: grid;
}

.rail-copy strong {
  font-size: 0.98rem;
}

.rail-copy small,
.rail-status {
  color: #5b6679;
  font-size: 0.88rem;
}

.rail-links {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  justify-content: center;
}

.rail-links a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  color: #334155;
  background: rgba(255, 255, 255, 0.72);
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease;
}

.rail-links a:hover,
.rail-links a:focus-visible {
  transform: translateY(-1px);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
}

.portfolio-stack {
  display: grid;
  gap: 24px;
  padding-top: 26px;
}

.stage-card,
.section-block,
.hero-stage,
.portfolio-footer {
  padding: 34px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 32px;
  background: rgba(255, 255, 255, 0.76);
  backdrop-filter: blur(18px);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.08);
}

.stage-card h1,
.hero-copy h1,
.section-heading h2,
.proof-card h3,
.case-study-card h3,
.activity-card h3,
.principle-card h3 {
  margin: 0;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
  line-height: 0.98;
}

.stage-card h1 {
  font-size: clamp(2.2rem, 5vw, 3.4rem);
}

.stage-card p:last-child {
  max-width: 42rem;
  color: #5b6679;
}

.notice-banner {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 14px 18px;
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  background: rgba(255, 255, 255, 0.74);
  box-shadow: 0 12px 34px rgba(15, 23, 42, 0.06);
}

.notice-banner[data-tone='preview'] {
  background: rgba(219, 234, 254, 0.82);
}

.notice-banner[data-tone='warning'] {
  background: rgba(255, 247, 237, 0.92);
}

.hero-stage {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 22px;
  align-items: stretch;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(255, 255, 255, 0.74));
}

.hero-copy {
  display: grid;
  gap: 16px;
}

.section-kicker,
.card-kicker {
  display: block;
  margin: 0;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.section-kicker.light {
  color: rgba(251, 191, 36, 0.92);
}

.hero-copy h1 {
  font-size: clamp(3.6rem, 8vw, 5.6rem);
  letter-spacing: -0.05em;
}

.hero-title {
  margin: 0;
  color: #1e3a5f;
  font-size: clamp(1.2rem, 2.4vw, 1.6rem);
  font-weight: 700;
}

.hero-summary,
.hero-support,
.proof-card p,
.case-study-block p,
.activity-card p,
.principle-card p,
.outcome-item p,
.outcome-item small,
.section-note,
.portfolio-footer p {
  margin: 0;
  color: #5b6679;
}

.hero-summary {
  max-width: 34rem;
  color: #0f172a;
  font-size: 1.18rem;
  font-weight: 600;
}

.hero-support {
  max-width: 36rem;
}

.hero-tags,
.tag-row,
.hero-actions,
.case-study-footer,
.footer-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.hero-tags span,
.tag-row span,
.featured-pill,
.activity-metric,
.inline-action,
.primary-link,
.secondary-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0 14px;
  border-radius: 999px;
  font-size: 0.84rem;
  font-weight: 700;
}

.hero-tags span,
.tag-row span {
  color: #1f4e8c;
  background: rgba(219, 234, 254, 0.88);
}

.tag-row.muted span {
  color: #46546a;
  background: rgba(226, 232, 240, 0.9);
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-top: 6px;
}

.hero-metric {
  display: grid;
  gap: 6px;
  padding-top: 14px;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
}

.hero-metric strong {
  font-size: clamp(2rem, 4vw, 2.8rem);
  line-height: 1;
}

.hero-metric span {
  color: #5b6679;
  font-size: 0.92rem;
}

.primary-link,
.secondary-link,
.inline-action,
.inline-link {
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    background-color 180ms ease,
    color 180ms ease;
}

.primary-link,
.inline-action {
  color: #f8fafc;
  background: linear-gradient(135deg, #0f172a, #2563eb);
  box-shadow: 0 16px 36px rgba(37, 99, 235, 0.24);
}

.secondary-link {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.92);
}

.inline-link {
  color: #1d4ed8;
}

.primary-link:hover,
.secondary-link:hover,
.inline-action:hover,
.inline-link:hover,
.primary-link:focus-visible,
.secondary-link:focus-visible,
.inline-action:focus-visible,
.inline-link:focus-visible {
  transform: translateY(-1px);
}

.hero-panel,
.systems-stage {
  color: #f8fafc;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.18), transparent 28%),
    linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(15, 23, 42, 0.88));
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.22);
}

.hero-panel {
  display: grid;
  gap: 16px;
  padding: 28px;
}

.outcome-item {
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.outcome-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.outcome-header span,
.hero-note span,
.activity-metric span,
.proof-metric span,
.case-study-block span,
.architecture-node span {
  color: rgba(226, 232, 240, 0.74);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.proof-metric span,
.case-study-block span {
  color: #64748b;
}

.outcome-header strong,
.hero-note strong,
.proof-metric strong,
.activity-metric strong {
  font-size: 1.16rem;
}

.outcome-item p,
.outcome-item small,
.hero-note p {
  color: rgba(226, 232, 240, 0.72);
}

.hero-note {
  display: grid;
  gap: 6px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(15, 23, 42, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: end;
  margin-bottom: 24px;
}

.section-heading h2 {
  font-size: clamp(2rem, 4vw, 3.1rem);
}

.section-heading.on-dark h2,
.section-heading.on-dark .section-note {
  color: #f8fafc;
}

.proof-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.proof-card,
.case-study-card,
.activity-card,
.principle-card {
  transition:
    transform 180ms ease,
    box-shadow 180ms ease,
    border-color 180ms ease;
}

.proof-card:hover,
.case-study-card:hover,
.activity-card:hover,
.principle-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 48px rgba(15, 23, 42, 0.1);
}

.proof-card {
  display: grid;
  gap: 16px;
  padding: 26px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.92)),
    rgba(255, 255, 255, 0.82);
}

.proof-metric {
  display: grid;
  gap: 6px;
}

.proof-metric strong {
  color: #0f172a;
  font-size: clamp(1.8rem, 4vw, 2.4rem);
  line-height: 1;
}

.proof-card h3,
.case-study-card h3,
.activity-card h3 {
  font-size: clamp(1.5rem, 2.4vw, 2rem);
}

.systems-stage {
  padding: 34px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.systems-grid {
  display: grid;
  gap: 20px;
}

.architecture-flow {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.architecture-node {
  position: relative;
  display: grid;
  gap: 8px;
  padding: 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.architecture-node:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 50%;
  right: -12px;
  width: 12px;
  height: 1px;
  background: rgba(226, 232, 240, 0.4);
}

.architecture-node strong {
  font-size: 1.02rem;
}

.architecture-node p,
.principle-card p {
  color: rgba(226, 232, 240, 0.72);
}

.principle-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.principle-card {
  padding: 22px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
}

.principle-card h3 {
  margin-bottom: 10px;
  font-size: 1.5rem;
  color: #f8fafc;
}

.case-study-list,
.activity-list {
  display: grid;
  gap: 18px;
}

.case-study-card,
.activity-card {
  display: grid;
  gap: 20px;
  padding: 28px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 16px 44px rgba(15, 23, 42, 0.06);
}

.case-study-head,
.case-study-footer,
.activity-meta {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.featured-pill {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.94);
}

.case-study-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.case-study-block {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 22px;
  background: rgba(15, 23, 42, 0.04);
}

.impact-copy,
.activity-impact {
  color: #0f172a;
}

.activity-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.activity-meta span {
  color: #64748b;
  font-size: 0.88rem;
}

.activity-metric {
  width: fit-content;
  gap: 8px;
  color: #1f4e8c;
  background: rgba(219, 234, 254, 0.88);
}

.portfolio-footer {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  background: rgba(255, 255, 255, 0.68);
}

.footer-copy strong {
  display: block;
  font-size: 1.14rem;
}

.footer-meta span {
  color: #5b6679;
  font-size: 0.9rem;
}

.reveal {
  opacity: 0;
  transform: translateY(22px);
  animation: rise 720ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: var(--delay, 0s);
}

@keyframes rise {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1120px) {
  .hero-stage,
  .proof-grid,
  .case-study-grid,
  .activity-list,
  .principle-grid {
    grid-template-columns: 1fr;
  }

  .architecture-flow {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero-stage {
    padding: 30px;
  }
}

@media (max-width: 860px) {
  .profile-experience {
    padding: 16px 16px 48px;
  }

  .portfolio-rail {
    flex-direction: column;
    align-items: stretch;
    top: 12px;
  }

  .rail-links {
    justify-content: flex-start;
  }

  .rail-status {
    display: none;
  }

  .section-heading,
  .case-study-head,
  .case-study-footer,
  .activity-meta,
  .portfolio-footer {
    flex-direction: column;
    align-items: start;
  }

  .stage-card,
  .section-block,
  .hero-stage,
  .systems-stage,
  .portfolio-footer {
    padding: 24px;
    border-radius: 26px;
  }

  .hero-metrics {
    grid-template-columns: 1fr;
  }

  .hero-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .primary-link,
  .secondary-link,
  .inline-action {
    width: 100%;
  }
}

@media (max-width: 640px) {
  .architecture-flow {
    grid-template-columns: 1fr;
  }

  .architecture-node:not(:last-child)::after {
    top: auto;
    right: auto;
    bottom: -10px;
    left: 50%;
    width: 1px;
    height: 10px;
    transform: translateX(-50%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .reveal {
    opacity: 1;
    transform: none;
    animation: none;
  }

  .proof-card,
  .case-study-card,
  .activity-card,
  .principle-card,
  .rail-links a,
  .primary-link,
  .secondary-link,
  .inline-action,
  .inline-link {
    transition: none;
  }
}
</style>
