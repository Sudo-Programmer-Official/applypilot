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
  ConfidenceSnapshot,
  DiffLine,
  ExperienceBulletComparison,
  ImportedJob,
  KeywordAnalysis,
  OptimizationDecision,
  OptimizationScoreAxes,
  OptimizationScoreRow,
  ParsedResume,
  PipelineResult,
  ReadinessBreakdown,
  ResumeLayoutDensity,
  ResumeDocument,
  ResumeExperienceItem,
  SkillInsight,
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

const optimizationAxisLabels: Record<keyof OptimizationScoreAxes, string> = {
  jd_keyword_match: 'ATS Alignment',
  technical_strength: 'System Complexity',
  metric_impact: 'Metric Impact',
  technology_density: 'Technology Density',
  action_verb_strength: 'Action Verb Strength',
  readability: 'Readability',
  credibility: 'Credibility',
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
const editingComparison = ref<ExperienceBulletComparison | null>(null)
const editInstruction = ref('')
const editError = ref('')
const applyingEdit = ref(false)
const applyingFixes = ref(false)
const layoutDensity = ref<ResumeLayoutDensity>('balanced')
const activeAction = ref<ActionMode>('analyze')
const loadingStageIndex = ref(0)

let loadingTimer: number | null = null

const uploadedFileName = computed(() => fileInput.value?.name ?? '')
const uploadedFileSize = computed(() => fileInput.value?.size ?? 0)
const loadingStages = computed(() => (activeAction.value === 'suggestions' ? suggestionLoadingStages : analyzeLoadingStages))
const currentLoadingStage = computed(() => loadingStages.value[loadingStageIndex.value] ?? loadingStages.value[0] ?? '')
const analysisMode = computed(() => result.value?.analysis?.mode ?? mode.value)
const isSuggestionMode = computed(() => analysisMode.value === 'suggestions')
const importedTopSkills = computed<SkillInsight[]>(() => (
  importedJob.value?.skills?.map((skillName) => ({
    name: skillName,
    category: 'imported',
    count: 1,
    score: 1,
    reason: 'Imported from the job posting.',
    suggested_sections: [],
  })) ?? []
))
const roleLabel = computed(() => {
  const detectedRole = result.value?.analysis?.role_type?.label?.trim()
  if (detectedRole && detectedRole.toLowerCase() !== 'software engineer') {
    return detectedRole
  }
  if (importedJob.value?.title?.trim()) {
    return importedJob.value.title.trim()
  }
  return parsedResume.value?.document?.title ?? detectedRole ?? 'Software Engineer'
})
const topSkills = computed(() => {
  const analyzedSkills = result.value?.analysis?.top_skills ?? []
  return analyzedSkills.length ? analyzedSkills : importedTopSkills.value
})
const missingSkills = computed(() => {
  const existing = result.value?.analysis?.missing_skills ?? []
  const latestMissingNames = new Set((optimizationKeywordAnalysis.value?.missing_keywords ?? []).map(normalizeIdentity))
  const matched = new Set(matchedSkillNames.value.map(normalizeIdentity))
  const filteredExisting = existing.filter((skill) => !matched.has(normalizeIdentity(skill.name)))

  if (!latestMissingNames.size) {
    return filteredExisting
  }

  const preferred = filteredExisting.filter((skill) => latestMissingNames.has(normalizeIdentity(skill.name)))
  return (preferred.length ? preferred : filteredExisting).slice(0, 8)
})
const appliedChanges = computed(() => analysisChangeList(result.value?.analysis))
const unresolvedSuggestions = computed(() => result.value?.analysis?.unresolved_suggestions ?? [])
const currentReadiness = computed(() => result.value?.application_readiness?.score ?? 0)
const projectedReadiness = computed(() => Math.max(
  result.value?.application_readiness?.projected_score ?? currentReadiness.value,
  currentReadiness.value,
))
const displayedReadiness = computed(() => (fixApplied.value ? projectedReadiness.value : currentReadiness.value))
const currentAts = computed(() => result.value?.ats_score?.score ?? 0)
const projectedAts = computed(() => Math.max(
  result.value?.ats_score?.projected_score ?? currentAts.value,
  currentAts.value,
))
const displayedAts = computed(() => (fixApplied.value ? projectedAts.value : currentAts.value))
const readinessDelta = computed(() => Math.max(projectedReadiness.value - currentReadiness.value, 0))
const optimizationMetadata = computed(() => result.value?.optimized?.metadata)
const currentVersionSnapshot = computed(() => optimizationMetadata.value?.version_snapshot ?? null)
const optimizationScores = computed(() => optimizationMetadata.value?.scores)
const optimizationKeptChanges = computed<OptimizationDecision[]>(() => optimizationMetadata.value?.kept_changes ?? [])
const optimizationRejectedChanges = computed<OptimizationDecision[]>(() => optimizationMetadata.value?.rejected_changes ?? [])
const optimizationMetricSignals = computed(() => (
  optimizationScores.value?.optimized?.metric_signals
  ?? optimizationScores.value?.original?.metric_signals
  ?? []
))
const optimizationKeywordAnalysis = computed<KeywordAnalysis | null>(() => (
  optimizationScores.value?.optimized?.keyword_analysis
  ?? optimizationScores.value?.original?.keyword_analysis
  ?? null
))
const optimizedDocument = computed<ResumeDocument | null>(() => result.value?.optimized?.document ?? null)
const exportDocument = computed<ResumeDocument | null>(() => (
  (fixApplied.value ? result.value?.optimized?.document : result.value?.parsed?.document)
  ?? result.value?.optimized?.document
  ?? result.value?.parsed?.document
  ?? null
))
const matchedSkillNames = computed(() => uniqueOrderedStrings([
  ...((result.value?.analysis?.matched_skills ?? []).map((skill) => skill.name)),
  ...(result.value?.analysis?.keywords?.matched ?? []),
  ...((optimizationKeywordAnalysis.value?.strong_matches ?? []).map((match) => match.keyword)),
  ...((optimizationKeywordAnalysis.value?.weak_matches ?? []).map((match) => match.keyword)),
]).slice(0, 8))
const missingSkillNames = computed(() => {
  const matched = new Set(matchedSkillNames.value.map(normalizeIdentity))
  return uniqueOrderedStrings([
    ...((result.value?.analysis?.missing_skills ?? []).map((skill) => skill.name)),
    ...(result.value?.analysis?.keywords?.missing ?? []),
    ...(optimizationKeywordAnalysis.value?.missing_keywords ?? []),
  ])
    .filter((skill) => !matched.has(normalizeIdentity(skill)))
    .slice(0, 8)
})
const extraStrengthNames = computed(() => {
  const tracked = new Set(
    uniqueOrderedStrings([
      ...matchedSkillNames.value,
      ...missingSkillNames.value,
      ...topSkills.value.map((skill) => skill.name),
    ]).map(normalizeIdentity),
  )
  const documentSkills = Object.values(result.value?.optimized?.document?.skills ?? result.value?.parsed?.document?.skills ?? {})
    .flat()
    .filter(Boolean)

  return uniqueOrderedStrings(documentSkills)
    .filter((skill) => !tracked.has(normalizeIdentity(skill)))
    .slice(0, 8)
})
const jobMatchTitle = computed(() => {
  if (importedJob.value?.company || importedJob.value?.title) {
    const company = importedJob.value?.company?.trim()
    const title = importedJob.value?.title?.trim()
    return [company, title].filter(Boolean).join(' - ')
  }
  return roleLabel.value
})
const jobMatchNarrative = computed(() => {
  const matched = matchedSkillNames.value
  const missing = missingSkillNames.value
  const extra = extraStrengthNames.value

  const matchedLine = matched.length
    ? `Your resume already shows ${matched.slice(0, 3).join(', ')}.`
    : 'The imported job still needs stronger signal extraction before we can confirm the strongest matches.'
  const missingLine = missing.length
    ? `To improve this application, surface ${missing.slice(0, 3).join(', ')} more explicitly.`
    : 'No major tracked gaps were detected in the current job match set.'
  const extraLine = extra.length
    ? `Extra strengths like ${extra.slice(0, 2).join(' and ')} make the profile more defensible for this role.`
    : ''

  return [matchedLine, missingLine, extraLine].filter(Boolean).join(' ')
})
const originalQualityScore = computed(() => Math.round(optimizationScores.value?.original?.total ?? 0))
const optimizedQualityScore = computed(() => Math.round(
  optimizationScores.value?.optimized?.total ?? optimizationScores.value?.original?.total ?? 0,
))
const optimizationScoreRows = computed<OptimizationScoreRow[]>(() => {
  const originalAxes = optimizationScores.value?.original?.axes ?? {}
  const optimizedAxes = optimizationScores.value?.optimized?.axes ?? originalAxes

  return (Object.keys(optimizationAxisLabels) as Array<keyof OptimizationScoreAxes>)
    .map((key) => ({
      key,
      label: optimizationAxisLabels[key],
      before: Math.round(originalAxes[key] ?? 0),
      after: Math.round(optimizedAxes[key] ?? originalAxes[key] ?? 0),
    }))
    .filter((row) => row.key !== 'credibility')
    .filter((row) => row.before > 0 || row.after > 0)
})
const metricImpactRow = computed(() => optimizationScoreRows.value.find((row) => row.key === 'metric_impact') ?? null)
const projectedBreakdown = computed(() => (
  result.value?.application_readiness?.projected_breakdown
  ?? result.value?.application_readiness?.breakdown
  ?? {}
))
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
    .filter((line) => (
      (line.startsWith('+') && !line.startsWith('+++'))
      || (line.startsWith('-') && !line.startsWith('---'))
    ))
    .slice(0, 8)
    .map((line) => ({
      type: line.startsWith('+') ? 'add' : 'remove',
      value: line.slice(1).trim(),
    }))
})
const displayedTopIssues = computed(() => {
  if (isSuggestionMode.value) {
    return appliedChanges.value.length ? appliedChanges.value : unresolvedSuggestions.value
  }
  if (!topSkills.value.length && importedJob.value) {
    return [
      "Imported posting needs richer JD text for deeper skill extraction.",
      "Paste the responsibilities or requirements section if you want stronger tailoring.",
      "You can still export the cleaned resume draft from the current pipeline.",
    ]
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
        entry_index: entryIndex,
        bullet_index: bulletIndex,
        role_heading: formatExperienceHeading(pair.optimized),
        original,
        optimized,
      })
    }
  }

  return pairs.slice(0, 6)
})

function documentSurfaceCounts(document: ResumeDocument | null) {
  const experienceBullets = (document?.experience ?? []).reduce((count, entry) => count + entry.bullets.length, 0)
  const projectBullets = (document?.projects ?? []).reduce((count, entry) => count + entry.bullets.length, 0)
  const educationDetails = (document?.education ?? []).reduce((count, entry) => count + entry.details.length, 0)
  const skillCount = Object.values(document?.skills ?? {}).flat().filter(Boolean).length
  const totalLines = [
    document?.summary ? 2 : 0,
    document?.title ? 1 : 0,
    document?.contact_items?.length ?? 0,
    experienceBullets,
    projectBullets,
    educationDetails,
    skillCount > 0 ? Math.ceil(skillCount / 4) : 0,
  ].reduce((sum, value) => sum + value, 0)

  return {
    experienceBullets,
    projectBullets,
    skillCount,
    totalLines,
  }
}

function recommendLayoutDensity(document: ResumeDocument | null): ResumeLayoutDensity {
  const counts = documentSurfaceCounts(document)
  if (counts.totalLines >= 30 || counts.experienceBullets >= 14 || counts.skillCount >= 18) {
    return 'compact'
  }
  if (counts.totalLines <= 16 || counts.experienceBullets <= 6) {
    return 'spacious'
  }
  return 'balanced'
}

function layoutDensityLabel(value: ResumeLayoutDensity) {
  const labels: Record<ResumeLayoutDensity, string> = {
    compact: 'Compact',
    balanced: 'Balanced',
    spacious: 'Spacious',
  }
  return labels[value]
}

const recommendedLayoutDensity = computed<ResumeLayoutDensity>(() => recommendLayoutDensity(exportDocument.value))
const layoutDensitySummary = computed(() => {
  const counts = documentSurfaceCounts(exportDocument.value)
  if (recommendedLayoutDensity.value === 'compact') {
    return `This resume is content-heavy, so a compact layout keeps it one-page without changing the wording. Current surface: ${counts.experienceBullets} experience bullets.`
  }
  if (recommendedLayoutDensity.value === 'spacious') {
    return 'This draft is relatively short, so a more spacious layout reduces dead space and makes the page feel more balanced.'
  }
  return 'Balanced layout is the default for this draft. It adds a little breathing room without making the page feel sparse.'
})

const keywordCoverageScore = computed(() => Math.round(projectedBreakdown.value.keyword_coverage ?? projectedAts.value ?? 0))
const metricsCoverageScore = computed(() => Math.round(projectedBreakdown.value.impact_metrics ?? 0))
const actionVerbScore = computed(() => Math.round(
  optimizationScores.value?.optimized?.axes?.action_verb_strength
  ?? optimizationScores.value?.original?.axes?.action_verb_strength
  ?? projectedBreakdown.value.experience_strength
  ?? 0,
))
const sectionCompletenessScore = computed(() => {
  const document = optimizedDocument.value ?? exportDocument.value
  if (!document) {
    return 0
  }

  const checks = [
    Boolean(document.summary?.trim()),
    Boolean(Object.keys(document.skills ?? {}).length),
    Boolean((document.experience ?? []).length),
    Boolean((document.projects ?? []).length || (document.education ?? []).length),
  ]
  return Math.round((checks.filter(Boolean).length / checks.length) * 100)
})
const confidenceImprovements = computed(() => {
  const suggestions: string[] = []

  if (keywordCoverageScore.value < 70) {
    if (missingSkillNames.value.length) {
      suggestions.push(`Increase job-description keyword match by surfacing ${missingSkillNames.value.slice(0, 2).join(' and ')} more explicitly.`)
    } else {
      suggestions.push('Increase job-description keyword match with clearer role-specific terms in the summary and skills section.')
    }
  }
  if (metricsCoverageScore.value < 70) {
    suggestions.push('Add 1 to 2 more measurable metrics to the strongest experience bullets.')
  }
  if (actionVerbScore.value < 70) {
    suggestions.push('Strengthen weak bullets with clearer action verbs at the start of each line.')
  }
  if (sectionCompletenessScore.value < 75) {
    suggestions.push('Round out the section structure with summary, skills, and at least one supporting projects or education section.')
  }
  if (recommendedLayoutDensity.value === 'spacious') {
    suggestions.push('Resume length is slightly light, so use a balanced or spacious layout for a fuller one-page export.')
  }

  return suggestions.slice(0, 4)
})
const confidenceSnapshot = computed<ConfidenceSnapshot | null>(() => {
  if (!result.value) {
    return null
  }

  return {
    overall_score: projectedAts.value,
    original_score: currentAts.value,
    optimized_score: projectedAts.value,
    checks: [
      {
        key: 'keyword-alignment',
        label: 'Keyword alignment',
        score: keywordCoverageScore.value,
        detail: hasJobContext.value
          ? 'Compares the optimized resume against the imported or pasted job description.'
          : 'Uses the available resume signals because no job description was attached to this run.',
      },
      {
        key: 'metrics-usage',
        label: 'Metrics usage',
        score: metricsCoverageScore.value,
        detail: 'Measures how often experience bullets include concrete scale, impact, or performance numbers.',
      },
      {
        key: 'action-verbs',
        label: 'Action verbs',
        score: actionVerbScore.value,
        detail: 'Checks whether bullets start with strong, recruiter-friendly verbs instead of passive phrasing.',
      },
      {
        key: 'section-completeness',
        label: 'Section structure',
        score: sectionCompletenessScore.value,
        detail: 'Verifies that the core ATS-readable sections are present and well-formed.',
      },
      {
        key: 'ats-formatting',
        label: 'ATS formatting',
        score: exportDocument.value ? 100 : 0,
        detail: 'PDF export is generated from the structured resume document to preserve ATS-safe formatting.',
      },
    ],
    improvements: confidenceImprovements.value,
    verification_items: [
      'ATS-safe formatting verified',
      `Keyword coverage: ${keywordCoverageScore.value}%`,
      `Metrics coverage: ${metricsCoverageScore.value}%`,
      `Resume length optimized: ${layoutDensityLabel(layoutDensity.value)} density`,
    ],
    notes: result.value.ats_score?.notes ?? [],
  }
})
const appliedFixes = computed(() => (
  result.value?.optimized?.metadata?.applied_fixes
  ?? result.value?.fixes?.applied
  ?? []
))
const hasJobContext = computed(() => Boolean(
  jobDescription.value.trim()
  || importedJob.value?.description?.trim()
  || result.value?.analysis?.job_alignment?.job_description_provided,
))

function normalizeComparisonText(value: string) {
  return value.replace(/\s+/g, ' ').trim()
}

function normalizeIdentity(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim()
}

function uniqueOrderedStrings(values: string[]) {
  const seen = new Set<string>()
  return values.filter((value) => {
    const normalized = normalizeIdentity(value)
    if (!normalized || seen.has(normalized)) {
      return false
    }
    seen.add(normalized)
    return true
  })
}

function analysisChangeList(analysis?: PipelineResult['analysis'] | null) {
  const applied = analysis?.applied_changes ?? []
  if (applied.length) {
    return applied
  }
  return analysis?.suggested_changes ?? []
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
  editingComparison.value = null
  editInstruction.value = ''
  editError.value = ''
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

async function applyTopIssues() {
  if (!result.value) {
    return false
  }
  if (!parsedResume.value?.document || !result.value.optimized?.document || !jobDescription.value.trim()) {
    error.value = 'A parsed resume, optimized draft, and job description are required before applying fixes.'
    return false
  }

  applyingFixes.value = true
  error.value = ''

  try {
    const response = await axios.post<{
      result: {
        optimized: PipelineResult['optimized']
        analysis: PipelineResult['analysis']
        diff: PipelineResult['diff']
        ats_score: PipelineResult['ats_score']
        application_readiness: PipelineResult['application_readiness']
        fixes?: PipelineResult['fixes']
      }
    }>(`${apiBase}/resume/apply_fixes`, {
      original_document: parsedResume.value.document,
      current_document: result.value.optimized.document,
      job_description: jobDescription.value.trim(),
      analysis: result.value.analysis,
      missing_signals: missingSkillNames.value,
      parsed_resume_id: result.value.parsed.id,
      parent_version_id: currentVersionSnapshot.value?.id,
    })

    const nextResult = response.data.result
    const currentMetadata = result.value.optimized.metadata ?? {}
    const nextMetadata = nextResult.optimized.metadata ?? {}

    result.value = {
      ...result.value,
      analysis: {
        ...result.value.analysis,
        ...(nextResult.analysis ?? {}),
      },
      optimized: {
        ...result.value.optimized,
        ...nextResult.optimized,
        metadata: {
          ...currentMetadata,
          ...nextMetadata,
          kept_changes: [
            ...(currentMetadata.kept_changes ?? []),
            ...(nextMetadata.kept_changes ?? []),
          ],
          rejected_changes: [
            ...(currentMetadata.rejected_changes ?? []),
            ...(nextMetadata.rejected_changes ?? []),
          ],
          applied_fixes: nextMetadata.applied_fixes ?? currentMetadata.applied_fixes,
          rejected_fixes: nextMetadata.rejected_fixes ?? currentMetadata.rejected_fixes,
          scores: nextMetadata.scores ?? currentMetadata.scores,
          version_snapshot: nextMetadata.version_snapshot ?? currentMetadata.version_snapshot,
        },
      },
      diff: nextResult.diff ?? result.value.diff,
      ats_score: nextResult.ats_score ?? result.value.ats_score,
      application_readiness: nextResult.application_readiness
        ? {
            ...nextResult.application_readiness,
            projected_score: nextResult.application_readiness.projected_score ?? nextResult.application_readiness.score,
            projected_breakdown:
              nextResult.application_readiness.projected_breakdown ?? nextResult.application_readiness.breakdown,
            projected_top_issues:
              nextResult.application_readiness.projected_top_issues ?? nextResult.application_readiness.top_issues,
          }
        : result.value.application_readiness,
      fixes: nextResult.fixes ?? result.value.fixes,
    }

    fixApplied.value = true
    editableResumeText.value = nextResult.optimized.text ?? result.value.optimized.text ?? result.value.parsed.text ?? ''
    await preparePdfPreview(true)
    return true
  } catch (unknownError: unknown) {
    if (axios.isAxiosError(unknownError)) {
      error.value = String(unknownError.response?.data?.detail ?? 'Failed to apply ATS fixes.')
    } else {
      error.value = 'Failed to apply ATS fixes.'
    }
    return false
  } finally {
    applyingFixes.value = false
  }
}

async function continueToDownload() {
  if (!result.value) {
    return
  }
  // Keep export aligned with the latest verified draft by running the separate
  // fix pass before download when the user has not triggered it manually.
  if (!fixApplied.value) {
    const applied = await applyTopIssues()
    if (!applied) {
      return
    }
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
    layout_density: layoutDensity.value,
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
    const applied = await applyTopIssues()
    if (!applied) {
      return
    }
  }
  currentStep.value = 5
  await preparePdfPreview(true)
}

function updateLayoutDensity(nextDensity: ResumeLayoutDensity) {
  if (layoutDensity.value === nextDensity) {
    return
  }
  layoutDensity.value = nextDensity
  if (currentStep.value === 5 && result.value) {
    void preparePdfPreview(true)
  }
}

function openBulletEdit(comparison: ExperienceBulletComparison, presetInstruction = '') {
  editingComparison.value = comparison
  editInstruction.value = presetInstruction
  editError.value = ''
}

function closeBulletEdit() {
  if (applyingEdit.value) {
    return
  }
  editingComparison.value = null
  editInstruction.value = ''
  editError.value = ''
}

function mergeUniqueStrings(existing: string[] = [], incoming: string[] = []) {
  return [...new Set([...existing, ...incoming].filter(Boolean))]
}

async function applyBulletEdit() {
  if (!result.value || !parsedResume.value?.document || !result.value.optimized?.document || !editingComparison.value) {
    return
  }
  if (!editInstruction.value.trim()) {
    editError.value = 'Describe how the bullet should change.'
    return
  }

  applyingEdit.value = true
  editError.value = ''

  try {
    const response = await axios.post<{
      result: {
        optimized: PipelineResult['optimized']
        diff: PipelineResult['diff']
        ats_score: PipelineResult['ats_score']
        application_readiness: PipelineResult['application_readiness']
        edit: {
          instruction: string
          after: string
          reason?: string
          score_delta?: number
        }
      }
    }>(`${apiBase}/resume/edit`, {
      original_document: parsedResume.value.document,
      current_document: result.value.optimized.document,
      instruction: editInstruction.value.trim(),
      job_description: jobDescription.value.trim(),
      parsed_resume_id: result.value.parsed.id,
      parent_version_id: currentVersionSnapshot.value?.id,
      target: {
        section: 'experience',
        entry_index: editingComparison.value.entry_index,
        bullet_index: editingComparison.value.bullet_index,
      },
    })

    const nextResult = response.data.result
    const currentMetadata = result.value.optimized.metadata ?? {}
    const nextMetadata = nextResult.optimized.metadata ?? {}
    const nextKeywordAnalysis = nextMetadata.scores?.optimized?.keyword_analysis

    result.value = {
      ...result.value,
      analysis: {
        ...result.value.analysis,
        keywords: nextKeywordAnalysis ? {
          ...(result.value.analysis.keywords ?? {}),
          matched: [
            ...(nextKeywordAnalysis.strong_matches ?? []).map((match) => match.keyword),
            ...(nextKeywordAnalysis.weak_matches ?? []).map((match) => match.keyword),
          ],
          missing: nextKeywordAnalysis.missing_keywords ?? [],
        } : result.value.analysis.keywords,
        applied_changes: mergeUniqueStrings(
          analysisChangeList(result.value.analysis),
          [
            `Edited ${editingComparison.value.role_heading} bullet${typeof nextResult.edit.score_delta === 'number' ? ` (${nextResult.edit.score_delta >= 0 ? '+' : ''}${nextResult.edit.score_delta})` : ''}: ${nextResult.edit.reason || nextResult.edit.instruction}`,
          ],
        ),
      },
      optimized: {
        ...result.value.optimized,
        ...nextResult.optimized,
        metadata: {
          ...currentMetadata,
          ...nextMetadata,
          kept_changes: [
            ...(currentMetadata.kept_changes ?? []),
            ...(nextMetadata.kept_changes ?? []),
          ],
          rejected_changes: [
            ...(currentMetadata.rejected_changes ?? []),
            ...(nextMetadata.rejected_changes ?? []),
          ],
          scores: nextMetadata.scores ?? currentMetadata.scores,
          version_snapshot: nextMetadata.version_snapshot ?? currentMetadata.version_snapshot,
        },
      },
      diff: nextResult.diff ?? result.value.diff,
      ats_score: nextResult.ats_score ?? result.value.ats_score,
      application_readiness: nextResult.application_readiness
        ? {
            ...nextResult.application_readiness,
            projected_score: nextResult.application_readiness.projected_score ?? nextResult.application_readiness.score,
            projected_breakdown:
              nextResult.application_readiness.projected_breakdown ?? nextResult.application_readiness.breakdown,
            projected_top_issues:
              nextResult.application_readiness.projected_top_issues ?? nextResult.application_readiness.top_issues,
          }
        : result.value.application_readiness,
    }

    fixApplied.value = true
    editableResumeText.value = nextResult.optimized.text ?? editableResumeText.value
    closeBulletEdit()
    await preparePdfPreview(true)
  } catch (unknownError: unknown) {
    if (axios.isAxiosError(unknownError)) {
      editError.value = String(unknownError.response?.data?.detail ?? 'Failed to apply bullet edit.')
    } else {
      editError.value = 'Failed to apply bullet edit.'
    }
  } finally {
    applyingEdit.value = false
  }
}

watch(result, (nextResult) => {
  if (!nextResult) {
    return
  }
  fixApplied.value = fixApplied.value || nextResult.analysis.mode === 'suggestions'
  layoutDensity.value = recommendLayoutDensity(nextResult.optimized.document ?? nextResult.parsed.document ?? null)
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
        <div v-if="optimizedQualityScore" class="mini-metric">
          <span>Quality</span>
          <strong>{{ originalQualityScore }} → {{ optimizedQualityScore }}</strong>
        </div>
        <div class="mini-metric">
          <span>Readiness</span>
          <strong>{{ displayedReadiness }}</strong>
        </div>
        <div class="mini-metric">
          <span>ATS</span>
          <strong>{{ displayedAts }}</strong>
        </div>
        <div v-if="metricImpactRow" class="mini-metric">
          <span>Metric impact</span>
          <strong>{{ metricImpactRow.before }} → {{ metricImpactRow.after }}</strong>
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
        :applying-fixes="applyingFixes"
        :quality-before="originalQualityScore"
        :quality-after="optimizedQualityScore"
        :score-rows="optimizationScoreRows"
        :kept-changes="optimizationKeptChanges"
        :rejected-changes="optimizationRejectedChanges"
        :confidence="confidenceSnapshot"
        :applied-fixes="appliedFixes"
        :metric-signals="optimizationMetricSignals"
        :keyword-analysis="optimizationKeywordAnalysis"
        :matched-skill-names="matchedSkillNames"
        :missing-skill-names="missingSkillNames"
        :extra-strength-names="extraStrengthNames"
        :job-match-title="jobMatchTitle"
        :job-match-narrative="jobMatchNarrative"
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
        :editing-comparison="editingComparison"
        :edit-instruction="editInstruction"
        :edit-error="editError"
        :applying-edit="applyingEdit"
        :preview-pdf-url="previewPdfUrl"
        :preview-preparing="previewPreparing"
        :preview-failed="previewFailed"
        :preview-error-message="previewErrorMessage"
        :quality-before="originalQualityScore"
        :quality-after="optimizedQualityScore"
        :score-rows="optimizationScoreRows"
        :kept-changes="optimizationKeptChanges"
        :rejected-changes="optimizationRejectedChanges"
        :applied-changes="appliedChanges"
        :confidence="confidenceSnapshot"
        :metric-signals="optimizationMetricSignals"
        :keyword-analysis="optimizationKeywordAnalysis"
        :matched-skill-names="matchedSkillNames"
        :missing-skill-names="missingSkillNames"
        :extra-strength-names="extraStrengthNames"
        :job-match-title="jobMatchTitle"
        :job-match-narrative="jobMatchNarrative"
        :current-version-snapshot="currentVersionSnapshot"
        :layout-density="layoutDensity"
        :recommended-layout-density="recommendedLayoutDensity"
        :layout-density-summary="layoutDensitySummary"
        @back="goToStep(4)"
        @preview="preparePdfPreview(true)"
        @download="downloadResume"
        @regenerate="regenerateOptimization"
        @open-edit="openBulletEdit"
        @close-edit="closeBulletEdit"
        @apply-edit="applyBulletEdit"
        @update:edit-instruction="editInstruction = $event"
        @update:layout-density="updateLayoutDensity"
      />
    </div>
  </section>
</template>

<style scoped>
.wizard-layout {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 24px;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.wizard-sidebar {
  display: grid;
  align-content: start;
  gap: 18px;
  min-height: 0;
  overflow-y: auto;
  padding-right: 6px;
}

.sidebar-card {
  padding: 28px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
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
  min-height: 0;
  overflow-y: auto;
  padding-right: 6px;
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
    height: auto;
    min-height: auto;
    overflow: visible;
  }

  .wizard-sidebar,
  .wizard-main {
    overflow: visible;
    padding-right: 0;
  }
}
</style>
