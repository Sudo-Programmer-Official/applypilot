<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import axios from 'axios'

interface SkillInsight {
  name: string
  category: string
  count: number
  score: number
  reason: string
  suggested_sections: string[]
}

interface ReadinessBreakdown {
  skill_match?: number
  experience_strength?: number
  impact_metrics?: number
  keyword_coverage?: number
}

interface AnalysisResult {
  summary?: string
  role_type?: { id: string; label: string }
  top_skills?: SkillInsight[]
  matched_skills?: SkillInsight[]
  missing_skills?: SkillInsight[]
  suggested_changes?: string[]
}

interface ReadinessResult {
  score?: number
  role_type?: { id: string; label: string }
  breakdown?: ReadinessBreakdown
  top_issues?: string[]
  projected_score?: number
  projected_breakdown?: ReadinessBreakdown
  projected_top_issues?: string[]
}

interface PipelineResult {
  parsed: { file_name?: string; text?: string }
  analysis: AnalysisResult
  optimized: {
    text?: string
    metadata?: { suggestions?: string[]; highlighted_keywords?: string[] }
  }
  diff: { unified?: string }
  ats_score: {
    score?: number
    projected_score?: number
    notes?: string[]
  }
  application_readiness: ReadinessResult
}

interface DiffLine {
  type: 'add' | 'remove'
  value: string
}

const exampleJobDescription = `Senior Backend Engineer

We are hiring a backend engineer to build cloud services for a high-growth product. You will design microservices, improve distributed systems reliability, and partner with product and design teams.

Requirements:
- Strong Python experience with FastAPI or Django
- Experience with AWS, Docker, Kubernetes, CI/CD, and Terraform
- Familiarity with PostgreSQL, REST APIs, and distributed systems
- Ability to quantify impact, improve system reliability, and collaborate cross-functionally`

const breakdownLabels: Record<keyof ReadinessBreakdown, string> = {
  skill_match: 'Skill Match',
  experience_strength: 'Experience Strength',
  impact_metrics: 'Impact Metrics',
  keyword_coverage: 'Keyword Coverage',
}

const fileInput = ref<File | null>(null)
const jobDescription = ref('')
const loading = ref(false)
const error = ref('')
const result = ref<PipelineResult | null>(null)
const editableResumeText = ref('')
const isEditingResume = ref(false)
const copied = ref(false)
const fixApplied = ref(false)
const selectedMissingSkillName = ref<string | null>(null)

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const loadingStages = [
  'Parsing resume',
  'Cleaning job description',
  'Detecting role type',
  'Scoring readiness',
  'Generating fixes',
]

const readinessRadius = 52
const readinessCircumference = 2 * Math.PI * readinessRadius
const loadingStageIndex = ref(0)

let loadingTimer: number | null = null
let copiedTimer: number | null = null

const roleLabel = computed(() => result.value?.analysis?.role_type?.label ?? 'Software Engineer')
const currentLoadingStage = computed(() => loadingStages[loadingStageIndex.value] ?? loadingStages[0])
const topSkills = computed(() => result.value?.analysis?.top_skills ?? [])
const matchedSkills = computed(() => result.value?.analysis?.matched_skills ?? [])
const missingSkills = computed(() => result.value?.analysis?.missing_skills ?? [])

const selectedMissingSkill = computed(() => {
  if (!selectedMissingSkillName.value) {
    return missingSkills.value[0] ?? null
  }
  return missingSkills.value.find((skill) => skill.name === selectedMissingSkillName.value) ?? missingSkills.value[0] ?? null
})

const currentReadiness = computed(() => result.value?.application_readiness?.score ?? 0)
const projectedReadiness = computed(
  () => result.value?.application_readiness?.projected_score ?? currentReadiness.value,
)
const displayedReadiness = computed(() => (fixApplied.value ? projectedReadiness.value : currentReadiness.value))
const readinessDelta = computed(() => Math.max(projectedReadiness.value - currentReadiness.value, 0))

const displayedBreakdown = computed<ReadinessBreakdown>(() => {
  if (fixApplied.value) {
    return result.value?.application_readiness?.projected_breakdown ?? {}
  }
  return result.value?.application_readiness?.breakdown ?? {}
})

const breakdownRows = computed(() =>
  (Object.keys(breakdownLabels) as Array<keyof ReadinessBreakdown>).map((key) => ({
    key,
    label: breakdownLabels[key],
    value: displayedBreakdown.value[key] ?? 0,
  })),
)

const displayedTopIssues = computed(() => {
  if (fixApplied.value) {
    return result.value?.application_readiness?.projected_top_issues ?? []
  }
  return result.value?.application_readiness?.top_issues ?? []
})

const currentAts = computed(() => result.value?.ats_score?.score ?? 0)
const projectedAts = computed(() => result.value?.ats_score?.projected_score ?? currentAts.value)
const displayedAts = computed(() => (fixApplied.value ? projectedAts.value : currentAts.value))

const scoreTone = computed(() => {
  if (displayedReadiness.value >= 90) {
    return { color: '#15803d', label: 'Strong match' }
  }
  if (displayedReadiness.value >= 70) {
    return { color: '#2563eb', label: 'Competitive' }
  }
  if (displayedReadiness.value >= 50) {
    return { color: '#d97706', label: 'Needs work' }
  }
  return { color: '#dc2626', label: 'High risk' }
})

const readinessDashOffset = computed(
  () =>
    readinessCircumference -
    (Math.min(Math.max(displayedReadiness.value, 0), 100) / 100) * readinessCircumference,
)

const diffLines = computed<DiffLine[]>(() => {
  const rawDiff = result.value?.diff?.unified?.trim()
  if (!rawDiff) {
    return []
  }

  return rawDiff
    .split('\n')
    .filter((line) => line.startsWith('+') || line.startsWith('-'))
    .slice(0, 8)
    .map((line) => ({
      type: line.startsWith('+') ? 'add' : 'remove',
      value: line,
    }))
})

const currentViewLabel = computed(() => (fixApplied.value ? 'After fixes' : 'Current resume'))

function startLoadingTicker() {
  stopLoadingTicker()
  loadingStageIndex.value = 0
  loadingTimer = window.setInterval(() => {
    if (loadingStageIndex.value < loadingStages.length - 1) {
      loadingStageIndex.value += 1
      return
    }
    stopLoadingTicker()
  }, 850)
}

function stopLoadingTicker() {
  if (loadingTimer !== null) {
    window.clearInterval(loadingTimer)
    loadingTimer = null
  }
}

function stopCopiedTicker() {
  if (copiedTimer !== null) {
    window.clearTimeout(copiedTimer)
    copiedTimer = null
  }
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  fileInput.value = target.files?.[0] || null
}

function useExampleJobDescription() {
  jobDescription.value = exampleJobDescription
}

function applyTopIssues() {
  if (!result.value) {
    return
  }
  fixApplied.value = true
  editableResumeText.value = result.value.optimized.text ?? result.value.parsed.text ?? ''
  isEditingResume.value = false
}

function showOriginalResume() {
  if (!result.value) {
    return
  }
  fixApplied.value = false
  editableResumeText.value = result.value.parsed.text ?? ''
  isEditingResume.value = false
}

async function analyze() {
  error.value = ''
  result.value = null

  if (!fileInput.value) {
    error.value = 'Choose a PDF or DOCX resume before running the analysis.'
    return
  }

  if (!jobDescription.value.trim()) {
    error.value = 'Paste a job description or use the example role before analyzing.'
    return
  }

  const form = new FormData()
  form.append('file', fileInput.value)
  form.append('job_description', jobDescription.value.trim())

  loading.value = true
  startLoadingTicker()

  try {
    const response = await axios.post<{ result: PipelineResult }>(`${apiBase}/resume/analyze`, form)
    result.value = response.data?.result ?? null
  } catch (unknownError: unknown) {
    if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? 'Failed to analyze resume.')
    } else {
      error.value = 'Failed to analyze resume.'
    }
  } finally {
    stopLoadingTicker()
    loading.value = false
  }
}

async function copyResume() {
  const text = editableResumeText.value.trim()
  if (!text) {
    return
  }

  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    stopCopiedTicker()
    copiedTimer = window.setTimeout(() => {
      copied.value = false
      copiedTimer = null
    }, 1600)
  } catch {
    error.value = 'Copy failed. Download the optimized resume instead.'
  }
}

function downloadResume() {
  const text = editableResumeText.value.trim()
  if (!text) {
    return
  }

  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = fixApplied.value ? 'optimized_resume.txt' : 'resume_preview.txt'
  link.click()
  URL.revokeObjectURL(link.href)
}

function toggleEdit() {
  isEditingResume.value = !isEditingResume.value
}

watch(result, (nextResult) => {
  fixApplied.value = false
  editableResumeText.value = nextResult?.parsed?.text ?? ''
  selectedMissingSkillName.value = nextResult?.analysis?.missing_skills?.[0]?.name ?? null
  isEditingResume.value = false
  copied.value = false
  stopCopiedTicker()
})

onBeforeUnmount(() => {
  stopLoadingTicker()
  stopCopiedTicker()
})
</script>

<template>
  <main class="landing">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">ApplyPilot</p>
        <h1>Resume vs Job Intelligence Engine</h1>
        <p class="lede">
          Upload your resume and a job description. ApplyPilot detects the role, ranks the skills that matter, scores readiness, and fixes the highest-impact gaps.
        </p>
        <div class="hero-actions">
          <button class="secondary" type="button" @click="useExampleJobDescription">Try Example Job</button>
          <span class="hero-note">Built for targeted applications, not generic rewriting.</span>
        </div>
      </div>

      <div class="hero-steps">
        <div class="hero-step">
          <span>1</span>
          <div>
            <strong>Upload Resume</strong>
            <p>PDF or DOCX, up to 5 MB.</p>
          </div>
        </div>
        <div class="hero-step">
          <span>2</span>
          <div>
            <strong>Paste Job Description</strong>
            <p>ApplyPilot cleans the JD before extracting skills.</p>
          </div>
        </div>
        <div class="hero-step">
          <span>3</span>
          <div>
            <strong>Fix Top Issues</strong>
            <p>See current readiness, then apply fixes to improve it.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="workspace">
      <article class="panel">
        <p class="panel-label">Step 1</p>
        <h2>Upload Resume</h2>
        <label class="file-drop" for="resume-input">
          <span class="file-title">{{ fileInput ? 'Resume attached' : 'Choose resume file' }}</span>
          <span class="file-subtitle">{{ fileInput?.name || 'PDF or DOCX only' }}</span>
        </label>
        <input id="resume-input" type="file" accept=".pdf,.docx" hidden @change="onFileChange" />
      </article>

      <article class="panel">
        <div class="panel-head">
          <div>
            <p class="panel-label">Step 2</p>
            <h2>Paste Job Description</h2>
          </div>
          <button class="ghost small" type="button" @click="useExampleJobDescription">Use Example</button>
        </div>
        <textarea
          v-model="jobDescription"
          rows="8"
          placeholder="Paste the job description here so ApplyPilot can detect the role and rank the critical skills."
        ></textarea>
      </article>
    </section>

    <section class="action-bar">
      <div>
        <p class="panel-label">Step 3</p>
        <p class="action-copy">Run JD cleaning, role detection, readiness scoring, and a fix plan in one pass.</p>
      </div>
      <button class="primary large" type="button" @click="analyze" :disabled="loading">
        {{ loading ? 'Analyzing Resume...' : 'Analyze Resume' }}
      </button>
    </section>

    <section v-if="loading" class="loading-panel">
      <p class="eyebrow inverse">Analysis in progress</p>
      <h2>{{ currentLoadingStage }}</h2>
      <p>This usually takes 3 to 5 seconds.</p>
      <div class="loading-bar" aria-hidden="true">
        <span class="loading-bar-fill"></span>
      </div>
      <div class="loading-steps">
        <div
          v-for="(stage, index) in loadingStages"
          :key="stage"
          class="loading-step"
          :data-active="index === loadingStageIndex"
        >
          {{ stage }}
        </div>
      </div>
    </section>

    <section v-if="error" class="error-card">
      <strong>Analysis blocked</strong>
      <p>{{ error }}</p>
    </section>

    <section v-if="result" class="results">
      <header class="results-head">
        <div>
          <p class="eyebrow">Analysis complete</p>
          <h2>{{ roleLabel }} readiness review</h2>
          <p class="summary">{{ result.analysis.summary }}</p>
        </div>
        <div class="results-actions">
          <button class="primary" type="button" @click="applyTopIssues" :disabled="fixApplied">Fix Top Issues</button>
          <button v-if="fixApplied" class="ghost" type="button" @click="showOriginalResume">View Original</button>
        </div>
      </header>

      <div class="results-grid">
        <article class="card readiness-card">
          <div class="readiness-ring">
            <svg viewBox="0 0 140 140" aria-hidden="true">
              <circle class="score-track" cx="70" cy="70" :r="readinessRadius"></circle>
              <circle
                class="score-progress"
                cx="70"
                cy="70"
                :r="readinessRadius"
                :stroke="scoreTone.color"
                :stroke-dasharray="readinessCircumference"
                :stroke-dashoffset="readinessDashOffset"
              ></circle>
            </svg>
            <div class="score-center">
              <strong>{{ displayedReadiness }}</strong>
              <span>/ 100</span>
            </div>
          </div>

          <div class="readiness-copy">
            <p class="metric-label">Application Readiness</p>
            <h3>{{ currentViewLabel }}</h3>
            <p>{{ scoreTone.label }} for this role.</p>
            <p class="projection">Current: {{ currentReadiness }} | Projected: {{ projectedReadiness }}</p>
            <p v-if="readinessDelta > 0" class="projection delta">Fixes improve readiness by {{ readinessDelta }} points.</p>
            <p class="projection">ATS Compatibility: {{ displayedAts }}</p>
          </div>
        </article>

        <article class="card breakdown-card">
          <div class="card-head">
            <h3>Readiness Breakdown</h3>
          </div>
          <div class="breakdown-list">
            <div v-for="row in breakdownRows" :key="row.key" class="breakdown-row">
              <div class="breakdown-top">
                <span>{{ row.label }}</span>
                <strong>{{ row.value }}%</strong>
              </div>
              <div class="bar-track">
                <span class="bar-fill" :style="{ width: `${row.value}%` }"></span>
              </div>
            </div>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <h3>Top Skills for this Role</h3>
            <span>{{ topSkills.length }}</span>
          </div>
          <div class="skill-stack">
            <div v-for="skill in topSkills" :key="skill.name" class="skill-row">
              <div>
                <strong>{{ skill.name }}</strong>
                <p>{{ skill.reason }}</p>
              </div>
              <small>{{ skill.category }}</small>
            </div>
          </div>
        </article>
      </div>

      <div class="detail-grid">
        <article class="card">
          <div class="card-head">
            <h3>Missing Skills</h3>
            <span>{{ missingSkills.length }}</span>
          </div>
          <div class="tag-list">
            <button
              v-for="skill in missingSkills"
              :key="skill.name"
              type="button"
              class="tag missing"
              :data-active="selectedMissingSkill?.name === skill.name"
              @click="selectedMissingSkillName = skill.name"
            >
              {{ skill.name }}
            </button>
            <span v-if="missingSkills.length === 0" class="empty-text">No major role-skill gaps detected.</span>
          </div>
          <div v-if="selectedMissingSkill" class="skill-detail">
            <strong>{{ selectedMissingSkill.name }}</strong>
            <p>{{ selectedMissingSkill.reason }}</p>
            <p>Add this in: {{ selectedMissingSkill.suggested_sections.join(', ') }}</p>
          </div>
        </article>

        <article class="card">
          <div class="card-head">
            <h3>Fix Plan</h3>
          </div>
          <ul class="change-list">
            <li v-for="issue in displayedTopIssues" :key="issue">{{ issue }}</li>
          </ul>
          <p class="meta-line">Matched skills already on the resume: {{ matchedSkills.map((skill) => skill.name).join(', ') || 'None yet' }}</p>
        </article>
      </div>

      <div class="detail-grid bottom-grid">
        <article class="card">
          <div class="card-head">
            <h3>Suggested Improvements</h3>
          </div>
          <div v-if="diffLines.length" class="diff-viewer">
            <div v-for="(line, index) in diffLines" :key="`${line.type}-${index}`" class="diff-line" :data-type="line.type">
              <code>{{ line.value }}</code>
            </div>
          </div>
          <p v-else class="empty-text">No line-level diff available yet. Review the fixed resume draft instead.</p>
        </article>

        <article class="card resume-card">
          <div class="card-head toolbar">
            <div>
              <h3>{{ fixApplied ? 'Optimized Resume' : 'Current Resume Preview' }}</h3>
              <p class="subtle">Apply fixes to switch from the current draft to the improved version.</p>
            </div>
            <div class="toolbar-actions">
              <button class="ghost small" type="button" @click="toggleEdit">{{ isEditingResume ? 'Preview' : 'Edit' }}</button>
              <button class="ghost small" type="button" @click="copyResume">{{ copied ? 'Copied' : 'Copy' }}</button>
              <button class="ghost small" type="button" @click="downloadResume">Download</button>
            </div>
          </div>

          <textarea v-if="isEditingResume" v-model="editableResumeText" class="resume-editor" rows="18"></textarea>
          <pre v-else class="resume-preview">{{ editableResumeText }}</pre>
        </article>
      </div>
    </section>
  </main>
</template>

<style scoped>
.landing {
  --panel: rgba(255, 255, 255, 0.86);
  --line: rgba(15, 23, 42, 0.12);
  --ink: #14213d;
  --muted: #5f6c80;
  --shadow: 0 24px 60px rgba(20, 33, 61, 0.08);
  min-height: 100vh;
  padding: 40px 24px 88px;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(251, 191, 36, 0.2), transparent 32%),
    radial-gradient(circle at top right, rgba(59, 130, 246, 0.18), transparent 28%),
    linear-gradient(180deg, #fbfaf6 0%, #f1eee5 100%);
}

.hero,
.workspace,
.action-bar,
.loading-panel,
.error-card,
.results {
  max-width: 1160px;
  margin-left: auto;
  margin-right: auto;
}

.hero {
  display: grid;
  grid-template-columns: 1.2fr 0.9fr;
  gap: 22px;
}

.hero-copy,
.hero-steps,
.panel,
.action-bar,
.loading-panel,
.error-card,
.card {
  border: 1px solid var(--line);
  border-radius: 24px;
  background: var(--panel);
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow);
}

.hero-copy,
.hero-steps,
.panel,
.loading-panel,
.card,
.action-bar {
  padding: 24px;
}

.eyebrow {
  margin: 0 0 10px;
  color: #b45309;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.eyebrow.inverse {
  color: #eff6ff;
}

h1,
h2,
h3 {
  margin: 0;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

h1 {
  max-width: 11ch;
  font-size: clamp(3rem, 5vw, 4.4rem);
  line-height: 0.95;
}

.lede,
.hero-note,
.summary,
.action-copy,
.subtle,
.readiness-copy p,
.skill-row p,
.skill-detail p,
.meta-line,
.empty-text {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}

.lede {
  margin-top: 18px;
  max-width: 58ch;
  font-size: 1.04rem;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  margin-top: 24px;
}

.hero-steps {
  display: grid;
  gap: 14px;
}

.hero-step {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 14px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
}

.hero-step span {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  font-weight: 800;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}

.hero-step strong {
  display: block;
  margin-bottom: 4px;
}

.hero-step p {
  margin: 0;
  color: var(--muted);
}

.workspace {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
  margin-top: 26px;
}

.panel-label,
.metric-label {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.panel-head,
.card-head,
.toolbar,
.results-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

.panel-head,
.card-head,
.toolbar {
  margin-bottom: 14px;
}

.file-drop {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 24px;
  border: 1.5px dashed rgba(20, 33, 61, 0.18);
  border-radius: 18px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.72);
}

.file-title {
  font-weight: 700;
}

.file-subtitle {
  color: var(--muted);
}

textarea,
.resume-editor {
  width: 100%;
  border: 1px solid rgba(15, 23, 42, 0.14);
  border-radius: 18px;
  padding: 16px;
  font: inherit;
  color: var(--ink);
  background: rgba(255, 255, 255, 0.84);
  resize: vertical;
}

textarea:focus,
.resume-editor:focus {
  outline: none;
  border-color: rgba(37, 99, 235, 0.44);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.action-bar {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
}

button {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition: transform 160ms ease, opacity 160ms ease;
}

button:hover {
  transform: translateY(-1px);
}

button:disabled {
  opacity: 0.66;
  cursor: not-allowed;
  transform: none;
}

.primary {
  color: #f8fafc;
  background: linear-gradient(135deg, #1d4ed8, #0f172a);
}

.secondary,
.ghost {
  color: var(--ink);
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(20, 33, 61, 0.12);
}

.large {
  padding: 14px 24px;
}

.small {
  padding: 10px 14px;
  font-size: 0.92rem;
}

.loading-panel {
  margin-top: 20px;
  color: #eff6ff;
  background: linear-gradient(135deg, #0f172a, #1d4ed8 58%, #3b82f6);
}

.loading-panel h2 {
  margin-top: 6px;
  font-size: clamp(1.8rem, 3vw, 2.3rem);
}

.loading-panel p {
  margin-top: 8px;
}

.loading-bar {
  margin-top: 18px;
  height: 12px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
}

.loading-bar-fill {
  display: block;
  width: 34%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #dbeafe, #ffffff, #bfdbfe);
  animation: loading-slide 1.3s ease-in-out infinite;
}

.loading-steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  margin-top: 18px;
}

.loading-step {
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
}

.loading-step[data-active='true'] {
  background: rgba(255, 255, 255, 0.18);
}

.error-card {
  margin-top: 20px;
  padding: 18px 22px;
  color: #991b1b;
  background: #fff7ed;
}

.error-card p {
  margin: 6px 0 0;
}

.results {
  margin-top: 28px;
}

.results-head {
  margin-bottom: 18px;
}

.results-actions,
.toolbar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.results-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr 1fr;
  gap: 18px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
  margin-top: 18px;
}

.bottom-grid {
  align-items: stretch;
}

.readiness-card {
  display: grid;
  grid-template-columns: 150px 1fr;
  gap: 16px;
  align-items: center;
}

.readiness-ring {
  position: relative;
  width: 140px;
  height: 140px;
}

.readiness-ring svg {
  width: 140px;
  height: 140px;
  transform: rotate(-90deg);
}

.score-track,
.score-progress {
  fill: none;
  stroke-width: 14;
  stroke-linecap: round;
}

.score-track {
  stroke: rgba(15, 23, 42, 0.08);
}

.score-progress {
  transition: stroke-dashoffset 500ms ease;
}

.score-center {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
}

.score-center strong {
  font-size: 2.1rem;
  line-height: 1;
}

.projection {
  margin-top: 10px;
}

.projection.delta {
  color: #166534;
}

.breakdown-list {
  display: grid;
  gap: 14px;
}

.breakdown-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.bar-track {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.08);
}

.bar-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, #3b82f6, #0f172a);
}

.skill-stack {
  display: grid;
  gap: 12px;
}

.skill-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}

.skill-row:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.skill-row small {
  color: #8b5e34;
  text-transform: uppercase;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag {
  padding: 8px 12px;
  border-radius: 999px;
  font-weight: 700;
  background: #ffedd5;
  color: #92400e;
}

.tag.missing[data-active='true'] {
  background: #fed7aa;
  border: 1px solid #f97316;
}

.skill-detail {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}

.change-list {
  margin: 0;
  padding-left: 18px;
}

.change-list li + li {
  margin-top: 10px;
}

.diff-viewer {
  overflow: hidden;
  border-radius: 18px;
  background: #0f172a;
}

.diff-line {
  padding: 12px 14px;
}

.diff-line[data-type='add'] {
  background: rgba(22, 101, 52, 0.4);
}

.diff-line[data-type='remove'] {
  background: rgba(153, 27, 27, 0.4);
}

.diff-line code,
.resume-preview,
.resume-editor {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.93rem;
}

.diff-line code {
  color: #dbeafe;
}

.resume-card {
  min-height: 100%;
}

.resume-preview {
  min-height: 420px;
  margin: 0;
  padding: 18px;
  overflow: auto;
  border-radius: 18px;
  color: #e2e8f0;
  background: linear-gradient(180deg, #111827, #0f172a);
  white-space: pre-wrap;
  line-height: 1.7;
}

.resume-editor {
  min-height: 420px;
  line-height: 1.7;
}

@media (max-width: 1080px) {
  .hero,
  .workspace,
  .results-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .action-bar,
  .results-head,
  .readiness-card {
    flex-direction: column;
    align-items: stretch;
  }

  .readiness-card {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }
}

@media (max-width: 720px) {
  .landing {
    padding: 24px 16px 72px;
  }

  .hero-copy,
  .hero-steps,
  .panel,
  .action-bar,
  .loading-panel,
  .card {
    padding: 20px;
  }

  h1 {
    font-size: 2.8rem;
  }

  .hero-actions,
  .results-actions,
  .toolbar-actions {
    flex-direction: column;
    align-items: stretch;
  }

  button {
    width: 100%;
  }
}

@keyframes loading-slide {
  0% {
    transform: translateX(-100%);
  }

  100% {
    transform: translateX(280%);
  }
}
</style>
