<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import axios from 'axios'

interface AnalysisKeywords {
  job?: string[]
  matched?: string[]
  missing?: string[]
}

interface AnalysisResult {
  summary?: string
  keywords?: AnalysisKeywords
  job_alignment?: {
    job_description_provided?: boolean
    matched_count?: number
    missing_count?: number
  }
}

interface OptimizedMetadata {
  suggestions?: string[]
  highlighted_keywords?: string[]
}

interface PipelineResult {
  parsed: { file_name?: string; text?: string }
  analysis: AnalysisResult
  optimized: { text?: string; metadata?: OptimizedMetadata }
  diff: { unified?: string }
  ats_score: {
    score?: number
    projected_score?: number
    matched_keywords?: string[]
    missing_keywords?: string[]
    projected_matched_keywords?: string[]
    projected_missing_keywords?: string[]
    notes?: string[]
  }
}

interface DiffLine {
  type: 'add' | 'remove' | 'context'
  value: string
}

const exampleJobDescription = `Senior Backend Engineer

We are looking for a backend engineer to build and scale cloud services for a high-growth platform. You will design microservices, improve ATS-style data pipelines, and partner with product and design teams.

Requirements:
- Strong Python experience with FastAPI or Django
- Experience with AWS, Docker, Kubernetes, CI/CD, and Terraform
- Familiarity with PostgreSQL, REST APIs, and distributed systems
- Ability to quantify impact, improve system reliability, and collaborate cross-functionally`

const fileInput = ref<File | null>(null)
const jobDescription = ref('')
const loading = ref(false)
const error = ref('')
const result = ref<PipelineResult | null>(null)
const editableOptimizedText = ref('')
const isEditingResume = ref(false)
const copied = ref(false)
const selectedMissingKeyword = ref<string | null>(null)

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const loadingStages = [
  'Parsing resume',
  'Analyzing job description',
  'Matching keywords',
  'Generating optimized resume',
  'Calculating ATS score',
]

const scoreRadius = 54
const scoreCircumference = 2 * Math.PI * scoreRadius
const loadingStageIndex = ref(0)

let loadingTimer: number | null = null
let copiedTimer: number | null = null

const currentScore = computed(() => result.value?.ats_score?.score ?? 0)
const projectedScore = computed(() => result.value?.ats_score?.projected_score ?? currentScore.value)
const scoreDelta = computed(() => Math.max(projectedScore.value - currentScore.value, 0))
const currentLoadingStage = computed(() => loadingStages[loadingStageIndex.value] ?? loadingStages[0])

const scoreTone = computed(() => {
  if (currentScore.value >= 90) {
    return { color: '#15803d', accent: '#dcfce7', label: 'Strong match' }
  }
  if (currentScore.value >= 70) {
    return { color: '#2563eb', accent: '#dbeafe', label: 'Competitive' }
  }
  if (currentScore.value >= 50) {
    return { color: '#d97706', accent: '#fef3c7', label: 'Needs work' }
  }
  return { color: '#dc2626', accent: '#fee2e2', label: 'High risk' }
})

const scoreDashOffset = computed(
  () => scoreCircumference - (Math.min(Math.max(currentScore.value, 0), 100) / 100) * scoreCircumference,
)

const diffLines = computed<DiffLine[]>(() => {
  const rawDiff = result.value?.diff?.unified?.trim()
  if (!rawDiff) {
    return []
  }

  return rawDiff
    .split('\n')
    .filter((line) => !line.startsWith('+++') && !line.startsWith('---') && !line.startsWith('@@'))
    .map((line) => {
      if (line.startsWith('+')) {
        return { type: 'add', value: line }
      }
      if (line.startsWith('-')) {
        return { type: 'remove', value: line }
      }
      return { type: 'context', value: line }
    })
})

const improvementBullets = computed(() => {
  const suggestions = result.value?.optimized?.metadata?.suggestions ?? []
  if (suggestions.length > 0) {
    return suggestions
  }
  return ['ApplyPilot generated an optimized draft based on keyword coverage and impact language.']
})

const selectedKeywordGuidance = computed(() => {
  if (!selectedMissingKeyword.value) {
    return 'Select a missing keyword to see where it should appear in your resume.'
  }
  return `Add "${selectedMissingKeyword.value}" in a bullet about real experience, tools, or measurable outcomes.`
})

const hasResult = computed(() => result.value !== null)

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
  const text = editableOptimizedText.value.trim()
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
  const text = editableOptimizedText.value.trim()
  if (!text) {
    return
  }

  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = 'optimized_resume.txt'
  link.click()
  URL.revokeObjectURL(link.href)
}

function toggleEdit() {
  isEditingResume.value = !isEditingResume.value
}

watch(result, (nextResult) => {
  editableOptimizedText.value = nextResult?.optimized?.text ?? ''
  selectedMissingKeyword.value = nextResult?.ats_score?.missing_keywords?.[0] ?? null
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
        <h1>Optimize Your Resume for ATS Systems</h1>
        <p class="lede">
          Upload your resume and a job description. ApplyPilot shows exactly what to improve, highlights keyword gaps, and generates an optimized draft you can act on.
        </p>
        <div class="hero-actions">
          <button class="secondary" type="button" @click="useExampleJobDescription">Try Example Job</button>
          <span class="hero-note">Resume vs job intelligence, not generic resume rewriting.</span>
        </div>
      </div>

      <div class="hero-side">
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
            <p>Use your target role or the built-in example.</p>
          </div>
        </div>
        <div class="hero-step">
          <span>3</span>
          <div>
            <strong>See What To Change</strong>
            <p>ATS score, keyword gaps, optimized resume, and diff.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="workspace">
      <article class="panel upload-panel">
        <div class="panel-head">
          <p class="panel-label">Step 1</p>
          <h2>Upload Resume</h2>
        </div>
        <label class="file-drop" for="resume-input">
          <span class="file-title">{{ fileInput ? 'Resume attached' : 'Choose resume file' }}</span>
          <span class="file-subtitle">{{ fileInput?.name || 'PDF or DOCX only' }}</span>
        </label>
        <input id="resume-input" type="file" accept=".pdf,.docx" hidden @change="onFileChange" />
      </article>

      <article class="panel job-panel">
        <div class="panel-head split">
          <div>
            <p class="panel-label">Step 2</p>
            <h2>Paste Job Description</h2>
          </div>
          <button class="ghost small" type="button" @click="useExampleJobDescription">Use Example</button>
        </div>
        <textarea
          v-model="jobDescription"
          rows="8"
          placeholder="Paste the role description here so ApplyPilot can match keywords and optimize the resume."
        ></textarea>
      </article>
    </section>

    <section class="action-bar">
      <div>
        <p class="action-label">Step 3</p>
        <p class="action-copy">Run parsing, keyword matching, optimization, and ATS scoring in one pass.</p>
      </div>
      <button class="primary large" type="button" @click="analyze" :disabled="loading">
        {{ loading ? 'Analyzing Resume...' : 'Analyze Resume' }}
      </button>
    </section>

    <section v-if="loading" class="loading-panel">
      <div class="loading-heading">
        <p class="eyebrow inverse">Analysis in progress</p>
        <h2>{{ currentLoadingStage }}</h2>
        <p>This usually takes 3 to 5 seconds.</p>
      </div>

      <div class="loading-bar" aria-hidden="true">
        <span class="loading-bar-fill"></span>
      </div>

      <div class="loading-steps">
        <div
          v-for="(stage, index) in loadingStages"
          :key="stage"
          class="loading-step"
          :data-state="index < loadingStageIndex ? 'done' : index === loadingStageIndex ? 'active' : 'pending'"
        >
          <span class="loading-dot"></span>
          <span>{{ stage }}</span>
        </div>
      </div>
    </section>

    <section v-if="error" class="error-card">
      <strong>Analysis blocked</strong>
      <p>{{ error }}</p>
    </section>

    <section v-if="hasResult" class="results">
      <header class="results-head">
        <div>
          <p class="eyebrow">Analysis complete</p>
          <h2>Your Resume vs The Job</h2>
          <p class="summary">{{ result?.analysis?.summary }}</p>
        </div>
        <div class="results-head-actions">
          <button class="ghost" type="button" @click="analyze">Improve Resume</button>
          <button class="primary" type="button" @click="downloadResume">Download Optimized Resume</button>
        </div>
      </header>

      <div class="results-grid">
        <article class="card score-card">
          <div class="score-ring">
            <svg viewBox="0 0 140 140" aria-hidden="true">
              <circle class="score-track" cx="70" cy="70" :r="scoreRadius"></circle>
              <circle
                class="score-progress"
                cx="70"
                cy="70"
                :r="scoreRadius"
                :stroke="scoreTone.color"
                :stroke-dasharray="scoreCircumference"
                :stroke-dashoffset="scoreDashOffset"
              ></circle>
            </svg>
            <div class="score-center">
              <strong>{{ currentScore }}</strong>
              <span>/ 100</span>
            </div>
          </div>

          <div class="score-copy">
            <p class="metric-label">ATS Compatibility</p>
            <h3>{{ scoreTone.label }}</h3>
            <p class="metric-note">{{ result?.ats_score?.notes?.[0] }}</p>
            <p class="metric-projection">
              Projected after optimization: <strong>{{ projectedScore }}%</strong>
              <span v-if="scoreDelta > 0">(+{{ scoreDelta }} points)</span>
            </p>
            <p class="meta-line">Parsed file: {{ result?.parsed?.file_name || fileInput?.name || 'resume' }}</p>
          </div>
        </article>

        <article class="card keyword-card">
          <div class="card-head">
            <h3>Matched Keywords</h3>
            <span>{{ result?.ats_score?.matched_keywords?.length || 0 }}</span>
          </div>
          <div class="tag-list">
            <span
              v-for="keyword in result?.ats_score?.matched_keywords"
              :key="keyword"
              class="tag positive"
            >
              {{ keyword }}
            </span>
            <span v-if="!(result?.ats_score?.matched_keywords?.length)" class="empty-state">
              No matches yet. Try a more detailed resume or job description.
            </span>
          </div>
        </article>

        <article class="card keyword-card">
          <div class="card-head">
            <h3>Missing Keywords</h3>
            <span>{{ result?.ats_score?.missing_keywords?.length || 0 }}</span>
          </div>
          <div class="tag-list">
            <button
              v-for="keyword in result?.ats_score?.missing_keywords"
              :key="keyword"
              type="button"
              class="tag actionable"
              :data-active="selectedMissingKeyword === keyword"
              @click="selectedMissingKeyword = keyword"
            >
              {{ keyword }}
            </button>
            <span v-if="!(result?.ats_score?.missing_keywords?.length)" class="empty-state success-text">
              No missing keywords detected in the extracted job description.
            </span>
          </div>
          <p class="keyword-guidance">{{ selectedKeywordGuidance }}</p>
        </article>
      </div>

      <div class="content-grid">
        <article class="card resume-card">
          <div class="card-head toolbar">
            <div>
              <h3>Optimized Resume</h3>
              <p class="subtle">Formatted draft based on the uploaded resume and target role.</p>
            </div>
            <div class="toolbar-actions">
              <button class="ghost small" type="button" @click="toggleEdit">
                {{ isEditingResume ? 'Preview' : 'Edit' }}
              </button>
              <button class="ghost small" type="button" @click="copyResume">
                {{ copied ? 'Copied' : 'Copy' }}
              </button>
              <button class="ghost small" type="button" @click="downloadResume">Download</button>
            </div>
          </div>

          <textarea
            v-if="isEditingResume"
            v-model="editableOptimizedText"
            class="resume-editor"
            rows="18"
          ></textarea>
          <pre v-else class="resume-preview">{{ editableOptimizedText }}</pre>
        </article>

        <article class="card diff-card">
          <div class="card-head">
            <div>
              <h3>Suggested Improvements</h3>
              <p class="subtle">Green adds, red removes, neutral lines preserve context.</p>
            </div>
          </div>

          <div v-if="diffLines.length" class="diff-viewer">
            <div
              v-for="(line, index) in diffLines"
              :key="`${line.type}-${index}`"
              class="diff-line"
              :data-type="line.type"
            >
              <code>{{ line.value }}</code>
            </div>
          </div>
          <div v-else class="empty-block">
            <p>No line-level diff generated yet, but you can still review the optimized draft and the improvement suggestions.</p>
          </div>
        </article>
      </div>

      <div class="results-grid secondary-grid">
        <article class="card suggestion-card">
          <div class="card-head">
            <h3>Changes Suggested</h3>
          </div>
          <ul class="suggestion-list">
            <li v-for="suggestion in improvementBullets" :key="suggestion">{{ suggestion }}</li>
          </ul>
        </article>

        <article class="card suggestion-card">
          <div class="card-head">
            <h3>Next Move</h3>
          </div>
          <p class="next-move">
            Your current ATS score is {{ currentScore }}. Keep the keywords truthful, review the optimized draft, and then download the improved resume for the application.
          </p>
        </article>
      </div>
    </section>
  </main>
</template>

<style scoped>
.landing {
  --bg: #f7f6f0;
  --panel: rgba(255, 255, 255, 0.84);
  --panel-strong: #ffffff;
  --ink: #14213d;
  --muted: #5c677d;
  --line: rgba(20, 33, 61, 0.12);
  --shadow: 0 24px 60px rgba(20, 33, 61, 0.08);
  min-height: 100vh;
  padding: 40px 24px 96px;
  color: var(--ink);
  background:
    radial-gradient(circle at top left, rgba(255, 196, 140, 0.38), transparent 32%),
    radial-gradient(circle at top right, rgba(129, 195, 215, 0.34), transparent 28%),
    linear-gradient(180deg, #fbfaf6 0%, #f1efe6 100%);
}

.hero,
.workspace,
.action-bar,
.loading-panel,
.error-card,
.results {
  max-width: 1180px;
  margin-left: auto;
  margin-right: auto;
}

.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 420px);
  gap: 24px;
  align-items: stretch;
}

.hero-copy,
.hero-side,
.panel,
.action-bar,
.loading-panel,
.error-card,
.card {
  border: 1px solid var(--line);
  border-radius: 24px;
  background: var(--panel);
  backdrop-filter: blur(12px);
  box-shadow: var(--shadow);
}

.hero-copy {
  padding: 36px;
}

.hero-side {
  padding: 28px;
  display: grid;
  gap: 14px;
}

.eyebrow {
  margin: 0 0 10px;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #b45309;
}

.eyebrow.inverse {
  color: #f8fafc;
}

h1,
h2,
h3 {
  margin: 0;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

h1 {
  max-width: 12ch;
  font-size: clamp(3rem, 5vw, 4.8rem);
  line-height: 0.95;
}

.lede {
  max-width: 58ch;
  margin: 18px 0 0;
  color: var(--muted);
  font-size: 1.05rem;
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: center;
  margin-top: 28px;
}

.hero-note {
  color: var(--muted);
  font-size: 0.95rem;
}

.hero-step {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 14px;
  align-items: start;
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
}

.hero-step span {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  font-weight: 700;
  color: #0f172a;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}

.hero-step strong,
.card-head h3 {
  display: block;
  margin-bottom: 4px;
}

.hero-step p,
.subtle,
.summary,
.next-move,
.keyword-guidance,
.action-copy,
.metric-note,
.meta-line {
  margin: 0;
  color: var(--muted);
  line-height: 1.6;
}

.workspace {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
  margin-top: 28px;
}

.panel {
  padding: 24px;
}

.panel-head {
  margin-bottom: 16px;
}

.panel-head.split {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.panel-label,
.action-label,
.metric-label {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.file-drop {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 24px;
  border: 1.5px dashed rgba(20, 33, 61, 0.2);
  border-radius: 18px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.68);
  transition: transform 180ms ease, border-color 180ms ease;
}

.file-drop:hover {
  transform: translateY(-1px);
  border-color: rgba(37, 99, 235, 0.44);
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
  border: 1px solid rgba(20, 33, 61, 0.14);
  border-radius: 18px;
  padding: 16px;
  font: inherit;
  line-height: 1.7;
  color: var(--ink);
  background: rgba(255, 255, 255, 0.82);
  resize: vertical;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

textarea:focus,
.resume-editor:focus {
  outline: none;
  border-color: rgba(37, 99, 235, 0.48);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
}

.action-bar {
  margin-top: 20px;
  padding: 22px 24px;
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
}

.action-copy {
  max-width: 56ch;
}

button {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  transition: transform 160ms ease, box-shadow 160ms ease, opacity 160ms ease;
}

button:hover {
  transform: translateY(-1px);
}

button:disabled {
  opacity: 0.68;
  cursor: not-allowed;
  transform: none;
}

.primary {
  color: #f8fafc;
  background: linear-gradient(135deg, #1d4ed8, #0f172a);
  box-shadow: 0 16px 36px rgba(29, 78, 216, 0.24);
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
  padding: 28px;
  color: #eff6ff;
  background: linear-gradient(135deg, #0f172a, #1d4ed8 58%, #3b82f6);
}

.loading-heading h2 {
  margin-top: 6px;
  font-size: clamp(1.8rem, 3vw, 2.4rem);
}

.loading-heading p {
  margin: 8px 0 0;
  color: rgba(239, 246, 255, 0.84);
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
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 22px;
}

.loading-step {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
}

.loading-step[data-state='active'] {
  background: rgba(255, 255, 255, 0.16);
}

.loading-step[data-state='done'] {
  background: rgba(187, 247, 208, 0.16);
}

.loading-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.48);
}

.loading-step[data-state='active'] .loading-dot {
  background: #ffffff;
}

.loading-step[data-state='done'] .loading-dot {
  background: #86efac;
}

.error-card {
  margin-top: 20px;
  padding: 18px 22px;
  color: #991b1b;
  background: #fff7ed;
  border-color: rgba(220, 38, 38, 0.18);
}

.error-card p {
  margin: 6px 0 0;
}

.results {
  margin-top: 28px;
}

.results-head {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: end;
  margin-bottom: 18px;
}

.results-head h2 {
  font-size: clamp(2rem, 3.2vw, 2.8rem);
}

.results-head-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.results-grid,
.content-grid {
  display: grid;
  gap: 18px;
}

.results-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.secondary-grid {
  margin-top: 18px;
  grid-template-columns: 1.4fr 1fr;
}

.content-grid {
  grid-template-columns: 1.15fr 0.85fr;
  margin-top: 18px;
}

.card {
  padding: 22px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: start;
  margin-bottom: 14px;
}

.card-head span {
  color: #8b5e34;
  font-weight: 700;
}

.score-card {
  display: grid;
  grid-template-columns: 170px minmax(0, 1fr);
  gap: 16px;
  align-items: center;
}

.score-ring {
  position: relative;
  width: 148px;
  height: 148px;
}

.score-ring svg {
  width: 148px;
  height: 148px;
  transform: rotate(-90deg);
}

.score-track,
.score-progress {
  fill: none;
  stroke-width: 14;
  stroke-linecap: round;
}

.score-track {
  stroke: rgba(20, 33, 61, 0.08);
}

.score-progress {
  transition: stroke-dashoffset 500ms ease;
}

.score-center {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  text-align: center;
}

.score-center strong {
  font-size: 2.2rem;
  line-height: 1;
}

.score-center span {
  color: var(--muted);
}

.metric-projection {
  margin: 14px 0 0;
  color: var(--ink);
}

.metric-projection strong {
  font-size: 1.1rem;
}

.meta-line {
  margin-top: 12px;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag {
  padding: 8px 12px;
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.94rem;
}

.tag.positive {
  background: #dcfce7;
  color: #166534;
}

.tag.actionable {
  color: #92400e;
  background: #ffedd5;
  border: 1px solid transparent;
}

.tag.actionable[data-active='true'] {
  border-color: #f97316;
  background: #fed7aa;
}

.empty-state {
  color: var(--muted);
  line-height: 1.6;
}

.success-text {
  color: #166534;
}

.keyword-guidance {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}

.toolbar {
  align-items: center;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.resume-preview,
.resume-editor,
.diff-line code {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.93rem;
}

.resume-preview {
  min-height: 460px;
  margin: 0;
  padding: 18px;
  overflow: auto;
  border-radius: 20px;
  color: #e2e8f0;
  background: linear-gradient(180deg, #111827, #0f172a);
  white-space: pre-wrap;
  line-height: 1.7;
}

.resume-editor {
  min-height: 460px;
  line-height: 1.7;
}

.diff-viewer {
  overflow: hidden;
  border-radius: 20px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  background: #0f172a;
}

.diff-line {
  padding: 12px 14px;
  white-space: pre-wrap;
}

.diff-line code {
  color: #dbeafe;
}

.diff-line[data-type='add'] {
  background: rgba(22, 101, 52, 0.42);
}

.diff-line[data-type='remove'] {
  background: rgba(153, 27, 27, 0.42);
}

.diff-line[data-type='context'] {
  background: rgba(15, 23, 42, 0.92);
}

.empty-block {
  display: grid;
  place-items: center;
  min-height: 240px;
  padding: 20px;
  text-align: center;
  border-radius: 20px;
  color: var(--muted);
  background: rgba(20, 33, 61, 0.04);
}

.suggestion-list {
  margin: 0;
  padding-left: 18px;
  color: var(--muted);
}

.suggestion-list li + li {
  margin-top: 10px;
}

@media (max-width: 1080px) {
  .hero,
  .workspace,
  .results-grid,
  .content-grid,
  .secondary-grid {
    grid-template-columns: 1fr;
  }

  .action-bar,
  .results-head {
    flex-direction: column;
    align-items: stretch;
  }

  .score-card {
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
  .hero-side,
  .panel,
  .action-bar,
  .loading-panel,
  .card {
    padding: 20px;
  }

  h1 {
    font-size: 2.7rem;
  }

  .hero-actions,
  .results-head-actions,
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
