<script setup lang="ts">
import { computed } from 'vue'
import OptimizationInsights from './OptimizationInsights.vue'
import type {
  ActionMode,
  ImportedJob,
  KeywordAnalysis,
  MetricSignal,
  OptimizationDecision,
  OptimizationScoreRow,
  PipelineResult,
  SkillInsight,
} from '../../types/wizard'

const props = defineProps<{
  mode: ActionMode
  loading: boolean
  currentStage: string
  loadingStages: string[]
  loadingStageIndex: number
  result: PipelineResult | null
  roleLabel: string
  topSkills: SkillInsight[]
  missingSkills: SkillInsight[]
  displayedTopIssues: string[]
  currentReadiness: number
  projectedReadiness: number
  currentAts: number
  projectedAts: number
  importedJob: ImportedJob | null
  fixApplied: boolean
  qualityBefore: number
  qualityAfter: number
  scoreRows: OptimizationScoreRow[]
  keptChanges: OptimizationDecision[]
  rejectedChanges: OptimizationDecision[]
  metricSignals: MetricSignal[]
  keywordAnalysis: KeywordAnalysis | null
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'run'): void
  (e: 'continue'): void
  (e: 'apply-fixes'): void
}>()

const modeCopy = computed(() => {
  if (props.mode === 'suggestions') {
    return {
      title: 'Apply structured suggestions',
      body: 'We map external feedback onto the structured resume model, strengthen the affected sections, and keep the layout ATS-safe.',
      action: 'Apply Suggestions',
    }
  }

  return {
    title: 'Generate tailored resume',
    body: 'We compare the resume against the job, rank the missing skills, score readiness, and draft the optimized version before export.',
    action: 'Generate Optimized Resume',
  }
})

const readinessDisplay = computed(() => (
  props.projectedReadiness > props.currentReadiness
    ? `${props.currentReadiness} → ${props.projectedReadiness}`
    : `${props.currentReadiness}`
))

const atsDisplay = computed(() => (
  props.projectedAts > props.currentAts
    ? `${props.currentAts} → ${props.projectedAts}`
    : `${props.currentAts}`
))

const topSkillsEmptyCopy = computed(() => {
  if (props.mode === 'suggestions') {
    return 'Suggestions mode does not require job-specific skill extraction.'
  }
  if (props.importedJob) {
    return 'Paste the requirements section if you want stronger skill extraction from this posting.'
  }
  return 'Add a richer job description to extract high-signal role skills.'
})
</script>

<template>
  <section class="step-panel">
    <div class="panel-header">
      <div>
        <p class="step-kicker">Step 4</p>
        <h3>{{ modeCopy.title }}</h3>
        <p class="panel-copy">{{ modeCopy.body }}</p>
      </div>
      <button class="ghost" type="button" @click="emit('back')">Back</button>
    </div>

    <section v-if="loading" class="loading-card">
      <p class="eyebrow">AI workflow</p>
      <h4>{{ currentStage }}</h4>
      <p>This usually takes 3 to 5 seconds.</p>
      <div class="loading-bar" aria-hidden="true">
        <span class="loading-fill"></span>
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

    <section v-else-if="!result" class="intro-card">
      <div>
        <p class="eyebrow">Optimization target</p>
        <h4>{{ mode === 'suggestions' ? 'Resume improvement mode' : 'Job-specific tailoring mode' }}</h4>
        <p>
          {{ mode === 'suggestions'
            ? 'Use this when you already have feedback and want ApplyPilot to make those edits cleanly.'
            : 'Use this when you want ApplyPilot to tailor the resume to a specific role and company.' }}
        </p>
      </div>
      <button class="primary" type="button" @click="emit('run')">{{ modeCopy.action }}</button>
    </section>

    <section v-else class="results-stack">
      <div class="summary-grid">
        <article class="summary-card accent">
          <p class="eyebrow">Detected role</p>
          <h4>{{ roleLabel }}</h4>
          <p v-if="importedJob && mode === 'analyze'">
            {{ importedJob.company }}{{ importedJob.title ? ` • ${importedJob.title}` : '' }}
          </p>
          <p v-else-if="result.analysis.summary">{{ result.analysis.summary }}</p>
          <p v-else>Structured optimization is ready for review before export.</p>
        </article>

        <article class="summary-card">
          <p class="eyebrow">Match score</p>
          <h4>{{ readinessDisplay }}</h4>
          <p>ATS compatibility: {{ atsDisplay }}</p>
        </article>
      </div>

      <div class="analysis-grid">
        <article class="analysis-card">
          <div class="card-head">
            <h4>Top skills</h4>
            <span>{{ topSkills.length }}</span>
          </div>
          <div v-if="topSkills.length" class="tag-list">
            <span v-for="skill in topSkills.slice(0, 8)" :key="skill.name" class="tag">{{ skill.name }}</span>
          </div>
          <p v-else class="empty-copy">{{ topSkillsEmptyCopy }}</p>
        </article>

        <article class="analysis-card">
          <div class="card-head">
            <h4>{{ mode === 'suggestions' ? 'Still missing' : 'Missing skills' }}</h4>
            <span>{{ missingSkills.length }}</span>
          </div>
          <div class="tag-list">
            <span v-for="skill in missingSkills.slice(0, 8)" :key="skill.name" class="tag warning">{{ skill.name }}</span>
            <p v-if="!missingSkills.length" class="empty-copy">No major gaps detected.</p>
          </div>
        </article>
      </div>

      <article class="analysis-card full-width">
        <div class="card-head">
          <h4>{{ mode === 'suggestions' ? 'Changes applied' : 'Fix plan' }}</h4>
          <span>{{ displayedTopIssues.length }}</span>
        </div>
        <ul class="issue-list">
          <li v-for="issue in displayedTopIssues" :key="issue">{{ issue }}</li>
        </ul>
      </article>

      <OptimizationInsights
        v-if="scoreRows.length || keptChanges.length || rejectedChanges.length || metricSignals.length || keywordAnalysis"
        title="Explainable optimization"
        subtitle="ApplyPilot only keeps edits that improve score without reducing credibility."
        :quality-before="qualityBefore"
        :quality-after="qualityAfter"
        :score-rows="scoreRows"
        :kept-changes="keptChanges"
        :rejected-changes="rejectedChanges"
        :metric-signals="metricSignals"
        :keyword-analysis="keywordAnalysis"
      />

      <div class="step-actions">
        <button
          v-if="mode === 'analyze' && !fixApplied"
          class="secondary"
          type="button"
          @click="emit('apply-fixes')"
        >
          Apply Fixes
        </button>
        <button class="primary" type="button" @click="emit('continue')">
          Continue to Download
        </button>
      </div>
    </section>
  </section>
</template>

<style scoped>
.step-panel {
  display: grid;
  gap: 24px;
  padding: 32px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 24px 52px rgba(20, 33, 61, 0.08);
}

.step-kicker,
.eyebrow {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.panel-header,
.card-head,
.step-actions,
.summary-grid,
.analysis-grid {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.summary-grid,
.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

h3,
h4 {
  margin: 0;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

h3 {
  font-size: clamp(2rem, 3vw, 2.7rem);
  line-height: 0.96;
}

.panel-copy,
.intro-card p,
.summary-card p,
.empty-copy,
.issue-list li {
  margin: 12px 0 0;
  color: #5f6c80;
  line-height: 1.6;
}

.loading-card,
.intro-card,
.summary-card,
.analysis-card {
  padding: 22px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.72);
}

.loading-card,
.intro-card {
  background: linear-gradient(135deg, rgba(251, 243, 221, 0.95), rgba(219, 234, 254, 0.9));
}

.loading-bar {
  height: 10px;
  margin-top: 16px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.08);
}

.loading-fill {
  display: block;
  width: 68%;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #b45309, #2563eb);
  animation: shimmer 1.2s ease-in-out infinite alternate;
}

.loading-steps {
  display: grid;
  gap: 10px;
  margin-top: 18px;
}

.loading-step {
  padding: 12px 14px;
  border-radius: 16px;
  color: #5f6c80;
  background: rgba(20, 33, 61, 0.05);
}

.loading-step[data-active='true'] {
  color: #14213d;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.86);
}

.intro-card {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: end;
}

.summary-card.accent {
  background: linear-gradient(135deg, rgba(255, 245, 213, 0.96), rgba(236, 244, 255, 0.92));
}

.card-head span {
  padding: 8px 10px;
  border-radius: 999px;
  font-size: 0.84rem;
  font-weight: 700;
  color: #124084;
  background: rgba(219, 234, 254, 0.86);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.tag {
  padding: 10px 12px;
  border-radius: 999px;
  color: #14213d;
  font-size: 0.9rem;
  font-weight: 700;
  background: rgba(20, 33, 61, 0.08);
}

.tag.warning {
  color: #9a3412;
  background: rgba(254, 215, 170, 0.52);
}

.issue-list {
  margin: 12px 0 0;
  padding-left: 20px;
}

button {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.primary {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.secondary {
  color: #14213d;
  background: rgba(20, 33, 61, 0.08);
}

.ghost {
  color: #14213d;
  background: rgba(20, 33, 61, 0.08);
}

@keyframes shimmer {
  from {
    transform: translateX(-8%);
  }

  to {
    transform: translateX(8%);
  }
}

@media (max-width: 900px) {
  .step-panel {
    padding: 24px;
  }

  .panel-header,
  .intro-card,
  .step-actions {
    flex-direction: column;
  }

  .summary-grid,
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}
</style>
