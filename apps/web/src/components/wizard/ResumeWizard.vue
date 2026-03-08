<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import axios from 'axios'

import StepDownload from './StepDownload.vue'
import StepJobInput from './StepJobInput.vue'
import StepOptimize from './StepOptimize.vue'
import StepReview from './StepReview.vue'
import StepUpload from './StepUpload.vue'
import StepperWizard from './StepperWizard.vue'
import type {
  ActionMode,
  DiffLine,
  ExperienceBulletComparison,
  ImportedJob,
  ParsedResume,
  PipelineResult,
  ReadinessBreakdown,
  ResumeDocument,
  ResumeExperienceItem,
  WizardStep,
} from '../../types/wizard'

const steps: WizardStep[] = [
  { id: 1, label: 'Upload', caption: 'Add the source resume' },
  { id: 2, label: 'Review', caption: 'Verify parsed data' },
  { id: 3, label: 'Job', caption: 'Add context or feedback' },
  { id: 4, label: 'Optimize', caption: 'Run the AI workflow' },
  { id: 5, label: 'Download', caption: 'Export the final PDF' },
]

const exampleJobDescription = `Senior Backend Engineer

We are hiring a backend engineer to build cloud services for a high-growth product. You will design microservices, improve distributed systems reliability, and partner with product and design teams.

Requirements:
- Strong Python experience with FastAPI or Django
- Experience with AWS, Docker, Kubernetes, CI/CD, and Terraform
- Familiarity with PostgreSQL, REST APIs, and distributed systems
- Ability to quantify impact, improve system reliability, and collaborate cross-functionally`

const exampleSuggestions = `- Add Go and TypeScript to technical skills
- Improve summary for backend platform roles
- Quantify AWS Lambda work in the Braintree internship
- Strengthen the first bullet in Braintree Health experience`

const breakdownLabels: Record<keyof ReadinessBreakdown, string> = {
  skill_match: 'Skill Match',
  experience_strength: 'Experience Strength',
  impact_metrics: 'Impact Metrics',
  keyword_coverage: 'Keyword Coverage',
}

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const analyzeLoadingStages = [
  'Parsing resume',
  'Cleaning job description',
  'Detecting role type',
  'Scoring readiness',
  'Generating fixes',
]
const suggestionLoadingStages = [
  'Parsing resume',
  'Reading suggestions',
  'Mapping resume sections',
  'Applying structured edits',
  'Preparing updated draft',
]

const currentStep = ref(1)
const fileInput = ref<File | null>(null)
const parsedResume = ref<ParsedResume | null>(null)
const jobUrl = ref('')
const jobDescription = ref('')
const suggestionsText = ref('')
const mode = ref<ActionMode>('analyze')
const loading = ref(false)
const parsing = ref(false)
const importingJob = ref(false)
const error = ref('')
const result = ref<PipelineResult | null>(null)
const importedJob = ref<ImportedJob | null>(null)
const editableResumeText = ref('')
const fixApplied = ref(false)
const downloadingPdf = ref(false)
const previewPreparing = ref(false)
const previewFailed = ref(false)
const previewErrorMessage = ref('')
const previewPdfUrl = ref('')
const previewPdfBlob = ref<Blob | null>(null)
const activeAction = ref<ActionMode>('analyze')
const loadingStageIndex = ref(0)

let loadingTimer: number | null = null

const uploadedFileName = computed(() => fileInput.value?.name ?? '')
const uploadedFileSize = computed(() => fileInput.value?.size ?? 0)
const loadingStages = computed(() => (activeAction.value === 'suggestions' ? suggestionLoadingStages : analyzeLoadingStages))
const currentLoadingStage = computed(() => loadingStages.value[loadingStageIndex.value] ?? loadingStages.value[0] ?? '')
const analysisMode = computed(() => result.value?.analysis?.mode ?? mode.value)
const isSuggestionMode = computed(() => analysisMode.value === 'suggestions')
const roleLabel = computed(() => result.value?.analysis?.role_type?.label ?? parsedResume.value?.document?.title ?? 'Software Engineer')
const topSkills = computed(() => result.value?.analysis?.top_skills ?? [])
const missingSkills = computed(() => result.value?.analysis?.missing_skills ?? [])
const appliedChanges = computed(() => result.value?.analysis?.applied_changes ?? result.value?.analysis?.suggested_changes ?? [])
const unresolvedSuggestions = computed(() => result.value?.analysis?.unresolved_suggestions ?? [])
const currentReadiness = computed(() => result.value?.application_readiness?.score ?? 0)
const projectedReadiness = computed(() => result.value?.application_readiness?.projected_score ?? currentReadiness.value)
const displayedReadiness = computed(() => (fixApplied.value ? projectedReadiness.value : currentReadiness.value))
const currentAts = computed(() => result.value?.ats_score?.score ?? 0)
const projectedAts = computed(() => result.value?.ats_score?.projected_score ?? currentAts.value)
const displayedAts = computed(() => (fixApplied.value ? projectedAts.value : currentAts.value))
const readinessDelta = computed(() => Math.max(projectedReadiness.value - currentReadiness.value, 0))
const canAdvanceFromJobStep = computed(() => (
  mode.value === 'analyze' ? Boolean(jobDescription.value.trim()) : Boolean(suggestionsText.value.trim())
))
const unlockedStep = computed(() => {
  if (result.value) {
    return 5
  }
  if (parsedResume.value && canAdvanceFromJobStep.value) {
    return 4
  }
  if (parsedResume.value) {
    return 3
  }
  return 1
})
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
const displayedTopIssues = computed(() => {
  if (isSuggestionMode.value) {
    return appliedChanges.value.length ? appliedChanges.value : unresolvedSuggestions.value
  }
  if (fixApplied.value) {
    return result.value?.application_readiness?.projected_top_issues ?? []
  }
  return result.value?.application_readiness?.top_issues ?? []
})
const readinessBreakdownRows = computed(() => {
  const breakdown = fixApplied.value
    ? result.value?.application_readiness?.projected_breakdown ?? {}
    : result.value?.application_readiness?.breakdown ?? {}

  return (Object.keys(breakdownLabels) as Array<keyof ReadinessBreakdown>).map((key) => ({
    key,
    label: breakdownLabels[key],
    value: breakdown[key] ?? 0,
  }))
})
const experienceEntryPairs = computed(() => matchExperienceEntries(
  result.value?.parsed?.document,
  result.value?.optimized?.document,
))
const preservedRoleCount = computed(() => experienceEntryPairs.value.filter((pair) => pair.original && pair.optimized).length)
const changedBulletComparisons = computed<ExperienceBulletComparison[]>(() => {
  const pairs: ExperienceBulletComparison[] = []

  for (const [entryIndex, pair] of experienceEntryPairs.value.entries()) {
    if (!pair.original || !pair.optimized) {
      continue
    }

    const maxBulletCount = Math.max(pair.original.bullets.length, pair.optimized.bullets.length)
    for (let bulletIndex = 0; bulletIndex < maxBulletCount; bulletIndex += 1) {
      const original = normalizeComparisonText(pair.original.bullets[bulletIndex] ?? '')
      const optimized = normalizeComparisonText(pair.optimized.bullets[bulletIndex] ?? '')

      if (!original || !optimized || original === optimized) {
        continue
      }

      pairs.push({
        id: `${entryIndex}-${bulletIndex}`,
        role_heading: formatExperienceHeading(pair.optimized),
        original,
        optimized,
      })
    }
  }

  return pairs.slice(0, 6)
})

function normalizeComparisonText(value: string) {
  return value.replace(/\s+/g, ' ').trim()
}

function normalizeIdentity(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
}

function formatExperienceHeading(entry: ResumeExperienceItem) {
  const role = entry.role?.trim()
  const company = entry.company?.trim()
  if (role && company) {
    return `${role} • ${company}`
  }
  return role || company || 'Experience update'
}

function matchExperienceEntries(parsed: ResumeDocument | undefined, optimized: ResumeDocument | undefined) {
  const originalEntries = [...(parsed?.experience ?? [])]
  const optimizedEntries = optimized?.experience ?? []
  const usedOriginalIndexes = new Set<number>()

  return optimizedEntries.map((optimizedEntry, optimizedIndex) => {
    const normalizedRole = normalizeIdentity(optimizedEntry.role ?? '')
    const normalizedCompany = normalizeIdentity(optimizedEntry.company ?? '')

    const matchedIndex = originalEntries.findIndex((candidate, candidateIndex) => {
      if (usedOriginalIndexes.has(candidateIndex)) {
        return false
      }

      const candidateRole = normalizeIdentity(candidate.role ?? '')
      const candidateCompany = normalizeIdentity(candidate.company ?? '')
      if (candidateRole && candidateCompany && candidateRole === normalizedRole && candidateCompany === normalizedCompany) {
        return true
      }
      return false
    })

    const fallbackIndex = matchedIndex >= 0
      ? matchedIndex
      : originalEntries.findIndex((_, candidateIndex) => (
        !usedOriginalIndexes.has(candidateIndex) && candidateIndex === optimizedIndex
      ))

    const resolvedIndex = matchedIndex >= 0 ? matchedIndex : fallbackIndex
    const original = resolvedIndex >= 0 ? originalEntries[resolvedIndex] : null
    if (resolvedIndex >= 0) {
      usedOriginalIndexes.add(resolvedIndex)
    }

    return {
      original,
      optimized: optimizedEntry,
    }
  })
}

function clearResultState() {
  result.value = null
  fixApplied.value = false
  editableResumeText.value = ''
  revokePreviewPdf()
  previewPreparing.value = false
  previewFailed.value = false
  previewErrorMessage.value = ''
  previewPdfBlob.value = null
}

function revokePreviewPdf() {
  if (previewPdfUrl.value) {
    URL.revokeObjectURL(previewPdfUrl.value)
    previewPdfUrl.value = ''
  }
}

function startLoadingTicker() {
  stopLoadingTicker()
  loadingStageIndex.value = 0
  loadingTimer = window.setInterval(() => {
    if (loadingStageIndex.value < loadingStages.value.length - 1) {
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

function selectFile(file: File | null) {
  fileInput.value = file
  parsedResume.value = null
  clearResultState()
  error.value = ''
  currentStep.value = 1
}

async function parseUploadedResume() {
  error.value = ''

  if (!fileInput.value) {
    error.value = 'Choose a PDF or DOCX resume before continuing.'
    return
  }

  parsing.value = true
  try {
    const form = new FormData()
    form.append('file', fileInput.value)
    const response = await axios.post<{ parsed: ParsedResume }>(`${apiBase}/resume/parse`, form)
    parsedResume.value = response.data.parsed
    currentStep.value = 2
  } catch (unknownError: unknown) {
    if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? 'Failed to parse resume.')
    } else {
      error.value = 'Failed to parse resume.'
    }
  } finally {
    parsing.value = false
  }
}

function goToStep(stepId: number) {
  if (stepId > unlockedStep.value) {
    return
  }
  currentStep.value = stepId
}

function useExampleJobDescription() {
  importedJob.value = null
  jobDescription.value = exampleJobDescription
}

function useExampleSuggestions() {
  suggestionsText.value = exampleSuggestions
}

async function importJob() {
  error.value = ''
  importedJob.value = null

  if (!jobUrl.value.trim()) {
    error.value = 'Paste a job URL before importing.'
    return
  }

  importingJob.value = true
  try {
    const response = await axios.post<ImportedJob>(`${apiBase}/job/import`, {
      url: jobUrl.value.trim(),
    })
    importedJob.value = response.data
    jobDescription.value = response.data.description
  } catch (unknownError: unknown) {
    if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? 'Failed to import job posting.')
    } else {
      error.value = 'Failed to import job posting.'
    }
  } finally {
    importingJob.value = false
  }
}

function advanceFromJobInput() {
  error.value = ''
  if (!canAdvanceFromJobStep.value) {
    error.value = mode.value === 'analyze'
      ? 'Paste a job description or import a job link before continuing.'
      : 'Paste at least one suggestion before continuing.'
    return
  }
  currentStep.value = 4
}

async function submitResumeRequest(endpoint: string, form: FormData, nextMode: ActionMode) {
  loading.value = true
  activeAction.value = nextMode
  startLoadingTicker()

  try {
    const response = await axios.post<{ result: PipelineResult }>(`${apiBase}${endpoint}`, form)
    result.value = response.data?.result ?? null
    if (response.data?.result?.parsed) {
      parsedResume.value = response.data.result.parsed
    }
  } catch (unknownError: unknown) {
    const fallbackMessage = nextMode === 'suggestions' ? 'Failed to apply suggestions.' : 'Failed to analyze resume.'
    if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? fallbackMessage)
    } else {
      error.value = fallbackMessage
    }
  } finally {
    stopLoadingTicker()
    loading.value = false
  }
}

async function runOptimization() {
  error.value = ''
  clearResultState()

  if (!fileInput.value) {
    error.value = 'Choose a PDF or DOCX resume before running the workflow.'
    return
  }

  if (mode.value === 'analyze') {
    const description = jobDescription.value.trim()
    if (!description) {
      error.value = 'Paste a job description or import a job link before analyzing.'
      return
    }

    const form = new FormData()
    form.append('file', fileInput.value)
    form.append('job_description', description)
    if (importedJob.value?.url) {
      form.append('job_url', importedJob.value.url)
    }
    await submitResumeRequest('/resume/analyze', form, 'analyze')
    return
  }

  const suggestions = suggestionsText.value.trim()
  if (!suggestions) {
    error.value = 'Paste at least one suggestion before applying fixes.'
    return
  }

  const form = new FormData()
  form.append('file', fileInput.value)
  form.append('suggestions', suggestions)
  await submitResumeRequest('/resume/apply-suggestions', form, 'suggestions')
}

function applyTopIssues() {
  if (!result.value) {
    return
  }
  fixApplied.value = true
  editableResumeText.value = result.value.optimized.text ?? result.value.parsed.text ?? ''
}

function continueToDownload() {
  if (!result.value) {
    return
  }
  if (!fixApplied.value) {
    applyTopIssues()
  }
  currentStep.value = 5
  void preparePdfPreview()
}

function setMode(nextMode: ActionMode) {
  if (mode.value === nextMode) {
    return
  }
  mode.value = nextMode
  clearResultState()
}

async function downloadResume() {
  if (!result.value) {
    return
  }

  if (previewPdfBlob.value) {
    const objectUrl = previewPdfUrl.value || URL.createObjectURL(previewPdfBlob.value)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = fixApplied.value ? 'optimized_resume.pdf' : 'resume_preview.pdf'
    link.click()
    return
  }

  downloadingPdf.value = true
  try {
    const response = await axios.post(`${apiBase}/resume/download`, buildPdfPayload(), { responseType: 'blob' })

    const blob = new Blob([response.data], { type: 'application/pdf' })
    const objectUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = fixApplied.value ? 'optimized_resume.pdf' : 'resume_preview.pdf'
    link.click()
    URL.revokeObjectURL(objectUrl)
  } catch (unknownError: unknown) {
    if (axios.isAxiosError(unknownError) && unknownError.response?.data instanceof Blob) {
      try {
        const errorPayload = JSON.parse(await unknownError.response.data.text())
        error.value = String(errorPayload.detail ?? 'Failed to download resume PDF.')
      } catch {
        error.value = 'Failed to download resume PDF.'
      }
    } else {
      error.value = 'Failed to download resume PDF.'
    }
  } finally {
    downloadingPdf.value = false
  }
}

function buildPdfPayload() {
  const documentPayload = fixApplied.value ? result.value?.optimized?.document : result.value?.parsed?.document

  return {
    resume_text: editableResumeText.value.trim(),
    document: documentPayload,
    file_name: result.value?.parsed?.file_name,
    role_label: roleLabel.value,
    use_optimized: fixApplied.value,
  }
}

async function preparePdfPreview(force = false) {
  if (!result.value) {
    return
  }
  if (previewPreparing.value) {
    return
  }
  if (previewPdfUrl.value && !force) {
    return
  }

  previewPreparing.value = true
  previewFailed.value = false
  previewErrorMessage.value = ''
  previewPdfBlob.value = null
  revokePreviewPdf()

  try {
    const response = await axios.post(`${apiBase}/resume/download`, buildPdfPayload(), { responseType: 'blob' })
    const blob = new Blob([response.data], { type: 'application/pdf' })
    previewPdfBlob.value = blob
    previewPdfUrl.value = URL.createObjectURL(blob)
  } catch (unknownError: unknown) {
    previewFailed.value = true
    if (axios.isAxiosError(unknownError) && unknownError.response?.data instanceof Blob) {
      try {
        const errorPayload = JSON.parse(await unknownError.response.data.text())
        previewErrorMessage.value = String(errorPayload.detail ?? 'Preview generation failed.')
      } catch {
        previewErrorMessage.value = 'Preview generation failed.'
      }
    } else {
      previewErrorMessage.value = 'Preview generation failed.'
    }
  } finally {
    previewPreparing.value = false
  }
}

async function regenerateOptimization() {
  currentStep.value = 4
  await runOptimization()
  if (!result.value) {
    return
  }
  if (!fixApplied.value) {
    applyTopIssues()
  }
  currentStep.value = 5
  await preparePdfPreview(true)
}

watch(result, (nextResult) => {
  if (!nextResult) {
    return
  }
  fixApplied.value = nextResult.analysis.mode === 'suggestions'
  editableResumeText.value = fixApplied.value
    ? nextResult.optimized.text ?? nextResult.parsed.text ?? ''
    : nextResult.parsed.text ?? ''
})

watch([jobDescription, suggestionsText, jobUrl, mode], () => {
  if (result.value) {
    clearResultState()
  }
})

onBeforeUnmount(() => {
  stopLoadingTicker()
  revokePreviewPdf()
})
</script>

<template>
  <section class="wizard-layout">
    <aside class="wizard-sidebar">
      <StepperWizard
        :steps="steps"
        :active-step="currentStep"
        :unlocked-step="unlockedStep"
        @select="goToStep"
      />

      <article class="sidebar-card">
        <p class="sidebar-kicker">System state</p>
        <h3>Structured resume pipeline</h3>
        <ul>
          <li><strong>Parser:</strong> {{ parsedResume?.metadata?.parser_mode || 'Waiting for upload' }}</li>
          <li><strong>Version:</strong> {{ parsedResume?.metadata?.parser_version || 'layout_v1' }}</li>
          <li><strong>Role:</strong> {{ roleLabel }}</li>
        </ul>
      </article>

      <article v-if="result" class="sidebar-card metrics-card">
        <p class="sidebar-kicker">Live metrics</p>
        <div class="mini-metric">
          <span>Readiness</span>
          <strong>{{ displayedReadiness }}</strong>
        </div>
        <div class="mini-metric">
          <span>ATS</span>
          <strong>{{ displayedAts }}</strong>
        </div>
        <div class="mini-metric" v-for="row in readinessBreakdownRows" :key="row.key">
          <span>{{ row.label }}</span>
          <strong>{{ row.value }}%</strong>
        </div>
      </article>
    </aside>

    <div class="wizard-main">
      <section v-if="error" class="error-card">
        <strong>Workflow blocked</strong>
        <p>{{ error }}</p>
      </section>

      <StepUpload
        v-if="currentStep === 1"
        :file-name="uploadedFileName"
        :file-size="uploadedFileSize"
        :parsing="parsing"
        @file-selected="selectFile"
        @parse="parseUploadedResume"
      />

      <StepReview
        v-else-if="currentStep === 2 && parsedResume"
        :parsed="parsedResume"
        @back="goToStep(1)"
        @next="goToStep(3)"
      />

      <StepJobInput
        v-else-if="currentStep === 3"
        :mode="mode"
        :job-url="jobUrl"
        :job-description="jobDescription"
        :suggestions-text="suggestionsText"
        :imported-job="importedJob"
        :importing-job="importingJob"
        @back="goToStep(2)"
        @next="advanceFromJobInput"
        @set-mode="setMode"
        @update:job-url="jobUrl = $event"
        @update:job-description="jobDescription = $event"
        @update:suggestions-text="suggestionsText = $event"
        @import-job="importJob"
        @use-example-job="useExampleJobDescription"
        @use-example-suggestions="useExampleSuggestions"
      />

      <StepOptimize
        v-else-if="currentStep === 4"
        :mode="mode"
        :loading="loading"
        :current-stage="currentLoadingStage"
        :loading-stages="loadingStages"
        :loading-stage-index="loadingStageIndex"
        :result="result"
        :role-label="roleLabel"
        :top-skills="topSkills"
        :missing-skills="missingSkills"
        :displayed-top-issues="displayedTopIssues"
        :current-readiness="currentReadiness"
        :projected-readiness="projectedReadiness"
        :current-ats="currentAts"
        :projected-ats="projectedAts"
        :imported-job="importedJob"
        :fix-applied="fixApplied"
        @back="goToStep(3)"
        @run="runOptimization"
        @continue="continueToDownload"
        @apply-fixes="applyTopIssues"
      />

      <StepDownload
        v-else-if="currentStep === 5 && result"
        :result="result"
        :role-label="roleLabel"
        :downloading-pdf="downloadingPdf"
        :diff-lines="diffLines"
        :displayed-readiness="displayedReadiness"
        :displayed-ats="displayedAts"
        :readiness-delta="readinessDelta"
        :imported-job="importedJob"
        :preserved-role-count="preservedRoleCount"
        :changed-bullet-comparisons="changedBulletComparisons"
        :preview-pdf-url="previewPdfUrl"
        :preview-preparing="previewPreparing"
        :preview-failed="previewFailed"
        :preview-error-message="previewErrorMessage"
        @back="goToStep(4)"
        @preview="preparePdfPreview(true)"
        @download="downloadResume"
        @regenerate="regenerateOptimization"
      />
    </div>
  </section>
</template>

<style scoped>
.wizard-layout {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 24px;
}

.wizard-sidebar {
  display: grid;
  align-content: start;
  gap: 18px;
}

.sidebar-card {
  padding: 22px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 42px rgba(20, 33, 61, 0.08);
}

.sidebar-kicker {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.sidebar-card h3 {
  margin: 0;
  font-size: 1.45rem;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.sidebar-card ul {
  margin: 14px 0 0;
  padding-left: 18px;
  color: #5f6c80;
}

.sidebar-card li + li {
  margin-top: 8px;
}

.metrics-card {
  display: grid;
  gap: 10px;
}

.mini-metric {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
}

.mini-metric span {
  color: #5f6c80;
}

.wizard-main {
  min-width: 0;
}

.error-card {
  margin-bottom: 16px;
  padding: 16px 18px;
  border: 1px solid rgba(220, 38, 38, 0.18);
  border-radius: 20px;
  color: #991b1b;
  background: rgba(254, 242, 242, 0.9);
}

.error-card p {
  margin: 6px 0 0;
}

@media (max-width: 1100px) {
  .wizard-layout {
    grid-template-columns: 1fr;
  }
}
</style>
