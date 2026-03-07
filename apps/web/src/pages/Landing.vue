<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import axios from 'axios'

interface PipelineResult {
  parsed: { file_name?: string; text?: string }
  analysis: Record<string, unknown>
  optimized: { text?: string; metadata?: Record<string, unknown> }
  diff: { unified?: string }
  ats_score: { score?: number; matched_keywords?: string[]; missing_keywords?: string[]; notes?: string[] }
}

interface DiffLine {
  type: 'meta' | 'add' | 'remove' | 'context'
  value: string
}

const fileInput = ref<File | null>(null)
const jobDescription = ref('')
const loading = ref(false)
const error = ref('')
const result = ref<PipelineResult | null>(null)
const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const loadingStages = [
  'Parsing resume...',
  'Analyzing job...',
  'Optimizing resume...',
  'Calculating ATS score...',
]
const loadingStageIndex = ref(0)
let loadingTimer: number | null = null

const diffLines = computed<DiffLine[]>(() => {
  const rawDiff = result.value?.diff?.unified?.trim()
  if (!rawDiff) {
    return []
  }

  return rawDiff.split('\n').map((line) => {
    if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
      return { type: 'meta', value: line }
    }
    if (line.startsWith('+')) {
      return { type: 'add', value: line }
    }
    if (line.startsWith('-')) {
      return { type: 'remove', value: line }
    }
    return { type: 'context', value: line }
  })
})
const currentLoadingStage = computed(() => loadingStages[loadingStageIndex.value] ?? loadingStages[0])

function startLoadingTicker() {
  stopLoadingTicker()
  loadingStageIndex.value = 0
  loadingTimer = window.setInterval(() => {
    loadingStageIndex.value = (loadingStageIndex.value + 1) % loadingStages.length
  }, 900)
}

function stopLoadingTicker() {
  if (loadingTimer !== null) {
    window.clearInterval(loadingTimer)
    loadingTimer = null
  }
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  fileInput.value = target.files?.[0] || null
}

async function analyze() {
  error.value = ''
  result.value = null

  if (!fileInput.value) {
    error.value = 'Please select a resume file (PDF or DOCX).'
    return
  }

  const form = new FormData()
  form.append('file', fileInput.value)
  if (jobDescription.value) {
    form.append('job_description', jobDescription.value)
  }

  loading.value = true
  startLoadingTicker()
  try {
    const response = await axios.post(`${apiBase}/resume/analyze`, form)
    result.value = response.data?.result ?? null
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Failed to analyze resume.'
  } finally {
    stopLoadingTicker()
    loading.value = false
  }
}

onBeforeUnmount(() => {
  stopLoadingTicker()
})
</script>

<template>
  <main class="landing">
    <section class="hero">
      <p class="eyebrow">ApplyPilot</p>
      <h1>Stop Applying With The Same Resume</h1>
      <p class="lede">
        Upload your resume and a job description. ApplyPilot shows exactly what to change to increase interview chances.
      </p>
      <div class="cta-row">
        <label class="file-btn" for="resume-input">Choose Resume</label>
        <input id="resume-input" type="file" accept=".pdf,.docx" @change="onFileChange" hidden />
        <button class="primary" @click="analyze" :disabled="loading">{{ loading ? 'Analyzing...' : 'Analyze Resume' }}</button>
      </div>
      <p v-if="fileInput" class="file-name">Selected: {{ fileInput?.name }}</p>
    </section>

    <section class="form-card">
      <h2>Job Description</h2>
      <textarea
        v-model="jobDescription"
        placeholder="Paste the target job description here"
        rows="6"
      ></textarea>
    </section>

    <section v-if="error" class="error">{{ error }}</section>

    <section v-if="loading" class="loading-panel">
      <div class="loading-copy">
        <p class="loading-label">Analysis in progress</p>
        <h3>{{ currentLoadingStage }}</h3>
        <p>We are running the full resume-vs-job pipeline now.</p>
      </div>
      <div class="loading-bar" aria-hidden="true">
        <span class="loading-bar-fill"></span>
      </div>
    </section>

    <section v-if="result" class="results">
      <div class="stat-card">
        <h3>ATS Score</h3>
        <p class="score">{{ result?.ats_score?.score ?? 0 }}%</p>
        <p class="note">{{ result?.ats_score?.notes?.[0] }}</p>
        <p class="meta">Parsed file: {{ result?.parsed?.file_name || fileInput?.name || 'resume' }}</p>
      </div>

      <div class="keywords">
        <div class="chip-group">
          <h4>Matched Keywords</h4>
          <div class="chips">
            <span v-if="!result?.ats_score?.matched_keywords?.length" class="chip muted">None yet</span>
            <span v-for="kw in result?.ats_score?.matched_keywords" :key="kw" class="chip">{{ kw }}</span>
          </div>
        </div>
        <div class="chip-group">
          <h4>Missing Keywords</h4>
          <div class="chips">
            <span v-if="!result?.ats_score?.missing_keywords?.length" class="chip success">None missing</span>
            <span v-for="kw in result?.ats_score?.missing_keywords" :key="kw" class="chip warning">{{ kw }}</span>
          </div>
        </div>
      </div>

      <div class="dual-pane">
        <div class="pane">
          <h4>Optimized Resume</h4>
          <pre>{{ result?.optimized?.text || 'Waiting for optimization output' }}</pre>
        </div>
        <div class="pane">
          <h4>Diff View</h4>
          <div v-if="diffLines.length" class="diff-viewer">
            <div v-for="(line, index) in diffLines" :key="`${line.type}-${index}`" class="diff-line" :data-type="line.type">
              <code>{{ line.value }}</code>
            </div>
          </div>
          <pre v-else class="diff empty">No diff available yet.</pre>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.landing {
  min-height: 100vh;
  padding: 64px 24px 96px;
  background: radial-gradient(circle at 20% 20%, #e3f2ff 0, transparent 35%),
    radial-gradient(circle at 80% 0%, #f3e8ff 0, transparent 30%),
    #f8fafc;
}

.hero {
  max-width: 860px;
  margin: 0 auto 24px;
  text-align: center;
}

.eyebrow {
  font-size: 0.95rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #2563eb;
  font-weight: 700;
  margin: 0 0 12px;
}

h1 {
  font-size: clamp(2.4rem, 4vw, 3.2rem);
  margin: 0 0 16px;
  color: #0f172a;
}

.lede {
  margin: 0 auto 24px;
  max-width: 720px;
  color: #334155;
  font-size: 1.05rem;
}

.cta-row {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

button,
.file-btn {
  border: none;
  border-radius: 999px;
  padding: 12px 20px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 150ms ease, box-shadow 150ms ease, background-color 150ms ease;
}

button:hover,
.file-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 30px rgba(37, 99, 235, 0.15);
}

button:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

button:focus-visible,
.file-btn:focus-visible {
  outline: 3px solid rgba(37, 99, 235, 0.35);
  outline-offset: 2px;
}

.primary {
  background-color: #2563eb;
  color: #ffffff;
  box-shadow: 0 10px 30px rgba(37, 99, 235, 0.15);
}

.file-btn {
  background-color: #e2e8f0;
  color: #0f172a;
}

.file-name {
  margin-top: 8px;
  color: #475569;
}

.form-card {
  max-width: 900px;
  margin: 16px auto 24px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.05);
}

.form-card h2 {
  margin: 0 0 12px;
  color: #0f172a;
}

textarea {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 12px;
  font-size: 1rem;
  font-family: inherit;
  resize: vertical;
  min-height: 120px;
  outline: none;
  transition: border-color 120ms ease;
}

textarea:focus {
  border-color: #2563eb;
}

.error {
  max-width: 900px;
  margin: 0 auto 16px;
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 12px;
  padding: 12px 16px;
}

.loading-panel {
  max-width: 900px;
  margin: 0 auto 16px;
  border-radius: 18px;
  padding: 22px;
  background: linear-gradient(135deg, #0f172a, #1d4ed8);
  color: #eff6ff;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
}

.loading-copy h3 {
  margin: 4px 0 8px;
  font-size: 1.4rem;
}

.loading-copy p {
  margin: 0;
  color: #dbeafe;
}

.loading-label {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.82rem;
  font-weight: 700;
}

.loading-bar {
  margin-top: 18px;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.16);
}

.loading-bar-fill {
  display: block;
  width: 42%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #bfdbfe, #ffffff, #93c5fd);
  animation: loading-slide 1.2s ease-in-out infinite;
}

.results {
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.05);
}

.score {
  font-size: 2.4rem;
  margin: 4px 0;
  color: #0f172a;
}

.note {
  margin: 0;
  color: #475569;
}

.meta {
  margin: 8px 0 0;
  color: #64748b;
}

.keywords {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
}

.chip-group h4 {
  margin: 0 0 8px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: #e2e8f0;
  color: #0f172a;
  font-size: 0.95rem;
}

.chip.warning {
  background: #fef3c7;
  color: #92400e;
}

.chip.success {
  background: #dcfce7;
  color: #166534;
}

.chip.muted {
  background: #e2e8f0;
  color: #475569;
}

.dual-pane {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px;
}

.pane {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.05);
}

.pane pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 12px;
  border-radius: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.9rem;
}

.diff {
  background: #0b1221;
  color: #cbd5e1;
  border-left: 4px solid #2563eb;
}

.diff.empty {
  min-height: 80px;
}

.diff-viewer {
  overflow: hidden;
  border-radius: 12px;
  background: #0b1221;
  border: 1px solid #1e293b;
}

.diff-line {
  padding: 10px 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.9rem;
}

.diff-line[data-type='meta'] {
  background: #172554;
  color: #dbeafe;
}

.diff-line[data-type='add'] {
  background: #052e16;
  color: #dcfce7;
}

.diff-line[data-type='remove'] {
  background: #450a0a;
  color: #fee2e2;
}

.diff-line[data-type='context'] {
  color: #cbd5e1;
}

@media (max-width: 640px) {
  .landing {
    padding: 48px 16px 72px;
  }

  button,
  .file-btn {
    width: 100%;
  }

  .cta-row {
    flex-direction: column;
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
