<script setup lang="ts">
import OptimizationInsights from './OptimizationInsights.vue'
import type {
  DiffLine,
  ExperienceBulletComparison,
  ImportedJob,
  KeywordAnalysis,
  MetricSignal,
  OptimizationDecision,
  OptimizationScoreRow,
  PipelineResult,
  ResumeVersionSnapshot,
} from '../../types/wizard'

const props = defineProps<{
  result: PipelineResult
  roleLabel: string
  downloadingPdf: boolean
  diffLines: DiffLine[]
  displayedReadiness: number
  displayedAts: number
  readinessDelta: number
  importedJob: ImportedJob | null
  preservedRoleCount: number
  changedBulletComparisons: ExperienceBulletComparison[]
  editingComparison: ExperienceBulletComparison | null
  editInstruction: string
  editError: string
  applyingEdit: boolean
  previewPdfUrl: string
  previewPreparing: boolean
  previewFailed: boolean
  previewErrorMessage: string
  qualityBefore: number
  qualityAfter: number
  scoreRows: OptimizationScoreRow[]
  keptChanges: OptimizationDecision[]
  rejectedChanges: OptimizationDecision[]
  metricSignals: MetricSignal[]
  keywordAnalysis: KeywordAnalysis | null
  matchedSkillNames: string[]
  missingSkillNames: string[]
  extraStrengthNames: string[]
  jobMatchTitle: string
  jobMatchNarrative: string
  currentVersionSnapshot: ResumeVersionSnapshot | null
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'download'): void
  (e: 'preview'): void
  (e: 'regenerate'): void
  (e: 'open-edit', comparison: ExperienceBulletComparison, presetInstruction?: string): void
  (e: 'close-edit'): void
  (e: 'apply-edit'): void
  (e: 'update:edit-instruction', value: string): void
}>()

function onEditInput(event: Event) {
  emit('update:edit-instruction', (event.target as HTMLTextAreaElement).value)
}

function suggestionChips(comparison: ExperienceBulletComparison) {
  const suggestions = ['Improve impact', 'Tighten wording', 'Tailor to JD']
  const lowered = comparison.optimized.toLowerCase()
  if (!/\d/.test(comparison.optimized)) {
    suggestions.unshift('Add metrics')
  }
  if (lowered.includes('aws') || lowered.includes('lambda')) {
    suggestions.unshift('Highlight AWS')
  } else if (lowered.includes('api') || lowered.includes('backend')) {
    suggestions.unshift('Highlight backend ownership')
  }
  return suggestions.slice(0, 4)
}

function instructionForSuggestion(label: string) {
  const mapping: Record<string, string> = {
    'Add metrics': 'Add measurable impact and scale without inventing new results.',
    'Improve impact': 'Make the business impact and technical outcome more explicit.',
    'Tighten wording': 'Rewrite this bullet to be more concise and recruiter-friendly.',
    'Tailor to JD': 'Tailor this bullet more closely to the target job description language.',
    'Highlight AWS': 'Mention AWS Lambda and cloud context more clearly.',
    'Highlight backend ownership': 'Make backend ownership and API work more explicit.',
  }
  return mapping[label] ?? 'Rewrite this bullet to be clearer and stronger.'
}
</script>

<template>
  <section class="step-panel">
    <div class="download-hero">
      <div class="hero-copy-block">
        <p class="step-kicker">Step 5</p>
        <h3>Your optimized resume is ready</h3>
        <p class="hero-copy">
          Review the PDF output generated from the structured resume document, then download the final ATS-safe file.
        </p>
        <p class="meta-line">Target role: {{ roleLabel }}</p>
        <p v-if="importedJob" class="meta-line">
          {{ importedJob.company }}{{ importedJob.title ? ` • ${importedJob.title}` : '' }}
        </p>
      </div>

      <div class="metric-cluster">
        <div class="metric-card">
          <span>Match score</span>
          <strong>{{ displayedReadiness }}%</strong>
          <small>+{{ readinessDelta }} from original</small>
        </div>
        <div class="metric-card">
          <span>ATS compatibility</span>
          <strong>{{ displayedAts }}%</strong>
        </div>
        <div class="metric-card">
          <span>Improvements applied</span>
          <strong>{{ keptChanges.length || (result.analysis.applied_changes || result.analysis.suggested_changes || []).length }}</strong>
        </div>
      </div>
    </div>

    <div class="action-row">
      <button class="secondary" type="button" :disabled="previewPreparing" @click="emit('preview')">
        {{ previewPreparing ? 'Preparing Preview...' : 'Preview' }}
      </button>
      <button class="primary" type="button" :disabled="downloadingPdf || previewPreparing" @click="emit('download')">
        {{ downloadingPdf ? 'Preparing PDF...' : 'Download PDF' }}
      </button>
      <button class="ghost" type="button" :disabled="previewPreparing || downloadingPdf" @click="emit('regenerate')">
        {{ previewPreparing ? 'Regenerating...' : 'Regenerate' }}
      </button>
      <button class="ghost" type="button" :disabled="previewPreparing || downloadingPdf" @click="emit('back')">Back</button>
    </div>

    <div class="trust-strip">
      <article class="trust-card">
        <strong>{{ preservedRoleCount }}</strong>
        <span>roles preserved</span>
      </article>
      <article class="trust-card">
        <strong>{{ changedBulletComparisons.length }}</strong>
        <span>bullets improved</span>
      </article>
      <article class="trust-card">
        <strong>ATS-safe</strong>
        <span>structured PDF export</span>
      </article>
      <article class="trust-card">
        <strong>
          {{ previewPdfUrl ? 'Preview ready' : (previewPreparing ? 'Preparing' : (previewFailed ? 'Download only' : 'Ready to preview')) }}
        </strong>
        <span>{{ previewFailed ? 'download fallback available' : 'same output as final PDF' }}</span>
      </article>
    </div>

    <article v-if="currentVersionSnapshot" class="version-card">
      <div class="card-head">
        <h4>Latest version snapshot</h4>
        <span>v{{ currentVersionSnapshot.version_number }}</span>
      </div>
      <div class="version-grid">
        <div>
          <strong>{{ currentVersionSnapshot.metadata?.edit_type || currentVersionSnapshot.source }}</strong>
          <p class="meta-line">
            {{ currentVersionSnapshot.metadata?.reason || 'Saved structured resume snapshot.' }}
          </p>
        </div>
        <div class="version-metric" v-if="currentVersionSnapshot.metadata?.score_delta !== undefined">
          <span>Score delta</span>
          <strong :data-positive="(currentVersionSnapshot.metadata?.score_delta || 0) >= 0">
            {{ (currentVersionSnapshot.metadata?.score_delta || 0) >= 0 ? '+' : '' }}{{ currentVersionSnapshot.metadata?.score_delta }}
          </strong>
        </div>
      </div>
    </article>

    <OptimizationInsights
      v-if="scoreRows.length || keptChanges.length || rejectedChanges.length || metricSignals.length || keywordAnalysis || matchedSkillNames.length || missingSkillNames.length || extraStrengthNames.length"
      title="Optimization results"
      subtitle="Review the score deltas, applied changes, rejected edits, and impact signals before exporting."
      :quality-before="qualityBefore"
      :quality-after="qualityAfter"
      :score-rows="scoreRows"
      :kept-changes="keptChanges"
      :rejected-changes="rejectedChanges"
      :metric-signals="metricSignals"
      :keyword-analysis="keywordAnalysis"
      :matched-skill-names="matchedSkillNames"
      :missing-skill-names="missingSkillNames"
      :extra-strength-names="extraStrengthNames"
      :job-match-title="jobMatchTitle"
      :job-match-narrative="jobMatchNarrative"
    />

    <article class="preview-card">
      <div class="card-head">
        <h4>PDF Preview</h4>
        <span>{{ result.parsed.file_name }}</span>
      </div>

      <div v-if="previewPreparing" class="preview-state loading-state">
        <div class="spinner" aria-hidden="true"></div>
        <strong>Preparing preview</strong>
        <p>Generating the PDF preview from the structured resume document.</p>
      </div>

      <div v-else-if="previewPdfUrl" class="preview-frame-wrap">
        <iframe class="preview-frame" :src="previewPdfUrl" title="Resume PDF preview"></iframe>
      </div>

      <div v-else class="preview-state empty-state">
        <strong>{{ previewFailed ? 'Preview unavailable' : 'Preview not ready' }}</strong>
        <p>
          {{ previewFailed
            ? (previewErrorMessage || 'Preview generation failed. You can still download the PDF directly.')
            : 'Click Preview to generate the PDF viewer.' }}
        </p>
      </div>
    </article>

    <article class="detail-card comparison-card">
      <div class="card-head">
        <h4>Changed bullets</h4>
        <span>{{ changedBulletComparisons.length }}</span>
      </div>
      <div v-if="changedBulletComparisons.length" class="comparison-list">
        <article
          v-for="comparison in changedBulletComparisons"
          :key="comparison.id"
          class="comparison-item"
        >
          <div class="comparison-headline">
            <p class="comparison-heading">{{ comparison.role_heading }}</p>
            <button class="ghost edit-trigger" type="button" @click="emit('open-edit', comparison)">Edit</button>
          </div>
          <div class="comparison-columns">
            <div class="comparison-column">
              <span>Original</span>
              <p>{{ comparison.original }}</p>
            </div>
            <div class="comparison-column optimized-column">
              <span>Optimized</span>
              <p>{{ comparison.optimized }}</p>
            </div>
          </div>
          <div class="chip-row">
            <button
              v-for="label in suggestionChips(comparison)"
              :key="`${comparison.id}-${label}`"
              class="chip-button"
              type="button"
              @click="emit('open-edit', comparison, instructionForSuggestion(label))"
            >
              {{ label }}
            </button>
          </div>
        </article>
      </div>
      <p v-else class="empty-copy">No bullet-level changes were detected for this run.</p>
    </article>

    <div class="detail-grid">
      <article class="detail-card">
        <div class="card-head">
          <h4>Why these changes</h4>
          <span>{{ (result.analysis.applied_changes || result.analysis.suggested_changes || []).length }}</span>
        </div>
        <ul class="change-list">
          <li v-for="item in result.analysis.applied_changes || result.analysis.suggested_changes || []" :key="item">
            {{ item }}
          </li>
        </ul>
      </article>

      <article class="detail-card">
        <div class="card-head">
          <h4>Change highlights</h4>
          <span>{{ diffLines.length }}</span>
        </div>
        <div v-if="diffLines.length" class="diff-list">
          <div v-for="(line, index) in diffLines" :key="`${line.type}-${index}`" class="diff-line" :data-type="line.type">
            <span class="diff-label">{{ line.type === 'add' ? 'Added' : 'Removed' }}</span>
            <code>{{ line.value.slice(1).trim() }}</code>
          </div>
        </div>
        <p v-else class="empty-copy">No line-level diff was generated for this run.</p>
      </article>
    </div>

    <div v-if="editingComparison" class="modal-backdrop" @click.self="emit('close-edit')">
      <article class="edit-modal">
        <div class="card-head">
          <h4>Edit bullet</h4>
          <button class="ghost" type="button" :disabled="applyingEdit" @click="emit('close-edit')">Close</button>
        </div>
        <p class="meta-line">{{ editingComparison.role_heading }}</p>
        <div class="comparison-column">
          <span>Current bullet</span>
          <p>{{ editingComparison.optimized }}</p>
        </div>
        <label class="edit-label" for="bullet-edit-instruction">How should this bullet change?</label>
        <textarea
          id="bullet-edit-instruction"
          class="edit-textarea"
          :value="editInstruction"
          placeholder="Example: Make AWS Lambda and scale more explicit."
          :disabled="applyingEdit"
          @input="onEditInput"
        />
        <p v-if="editError" class="edit-error">{{ editError }}</p>
        <div class="action-row modal-actions">
          <button class="primary" type="button" :disabled="applyingEdit" @click="emit('apply-edit')">
            {{ applyingEdit ? 'Applying edit...' : 'Apply edit' }}
          </button>
          <button class="ghost" type="button" :disabled="applyingEdit" @click="emit('close-edit')">Cancel</button>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.step-panel {
  display: grid;
  gap: 22px;
  padding: 32px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 24px 52px rgba(20, 33, 61, 0.08);
}

.step-kicker {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
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

.hero-copy,
.meta-line,
.empty-copy,
.change-list li,
.preview-state p {
  margin: 10px 0 0;
  color: #5f6c80;
  line-height: 1.6;
}

.download-hero {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: start;
}

.hero-copy-block {
  max-width: 60ch;
}

.metric-cluster {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  min-width: 340px;
}

.metric-card {
  padding: 16px;
  border-radius: 20px;
  text-align: center;
  background: linear-gradient(180deg, rgba(219, 234, 254, 0.92), rgba(255, 244, 214, 0.82));
}

.metric-card span {
  display: block;
  color: #5f6c80;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.metric-card strong {
  display: block;
  margin-top: 6px;
  font-size: 1.9rem;
}

.metric-card small {
  display: block;
  margin-top: 6px;
  color: #5f6c80;
  font-size: 0.8rem;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.trust-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.trust-card {
  display: grid;
  gap: 4px;
  padding: 14px 16px;
  border-radius: 20px;
  text-align: center;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95), rgba(219, 234, 254, 0.55));
  border: 1px solid rgba(20, 33, 61, 0.08);
}

.trust-card strong {
  font-size: 1rem;
  color: #14213d;
}

.trust-card span {
  color: #5f6c80;
  font-size: 0.84rem;
  line-height: 1.4;
}

button {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.primary {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.secondary {
  color: #14213d;
  background: rgba(251, 191, 36, 0.22);
}

.ghost {
  color: #14213d;
  background: rgba(20, 33, 61, 0.08);
}

.preview-card,
.detail-card,
.version-card {
  width: 100%;
  max-width: 980px;
  justify-self: center;
  padding: 22px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.74);
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.card-head span {
  padding: 8px 10px;
  border-radius: 999px;
  color: #124084;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.86);
}

.preview-state {
  display: grid;
  justify-items: center;
  gap: 10px;
  min-height: 720px;
  padding: 48px 24px;
  text-align: center;
  border: 1px dashed rgba(20, 33, 61, 0.16);
  border-radius: 20px;
  background: rgba(248, 250, 252, 0.92);
}

.preview-frame-wrap {
  margin: 18px auto 0;
  max-width: 920px;
}

.preview-frame {
  width: 100%;
  height: 1120px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 16px 34px rgba(20, 33, 61, 0.12);
}

.spinner {
  width: 42px;
  height: 42px;
  border: 3px solid rgba(20, 33, 61, 0.14);
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.comparison-card {
  display: grid;
  gap: 16px;
}

.comparison-list {
  display: grid;
  gap: 14px;
}

.comparison-item {
  display: grid;
  gap: 10px;
  padding: 16px;
  border-radius: 20px;
  background: rgba(248, 250, 252, 0.92);
}

.comparison-headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.comparison-heading {
  margin: 0;
  color: #14213d;
  font-weight: 700;
}

.edit-trigger {
  padding-inline: 16px;
}

.comparison-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.comparison-column {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
}

.comparison-column span {
  color: #5f6c80;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.comparison-column p {
  margin: 0;
  color: #14213d;
  line-height: 1.55;
}

.optimized-column {
  background: rgba(220, 252, 231, 0.68);
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.chip-button {
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(219, 234, 254, 0.78);
  color: #124084;
  font-size: 0.88rem;
  font-weight: 700;
}

.version-grid {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: center;
  margin-top: 14px;
}

.version-metric {
  min-width: 120px;
  display: grid;
  gap: 4px;
  justify-items: end;
}

.version-metric span {
  color: #5f6c80;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.version-metric strong {
  font-size: 1.4rem;
  color: #14213d;
}

.version-metric strong[data-positive='true'] {
  color: #166534;
}

.change-list {
  margin: 14px 0 0;
  padding-left: 18px;
}

.diff-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
}

.diff-line {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
}

.diff-line[data-type='add'] {
  background: rgba(220, 252, 231, 0.9);
}

.diff-line[data-type='remove'] {
  background: rgba(254, 226, 226, 0.9);
}

.diff-line code {
  font-size: 0.86rem;
  white-space: pre-wrap;
}

.diff-label {
  color: #14213d;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.42);
  z-index: 40;
}

.edit-modal {
  width: min(680px, 100%);
  display: grid;
  gap: 18px;
  padding: 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.24);
}

.edit-label {
  font-weight: 700;
  color: #14213d;
}

.edit-textarea {
  min-height: 140px;
  resize: vertical;
  padding: 14px 16px;
  border: 1px solid rgba(20, 33, 61, 0.14);
  border-radius: 18px;
  font: inherit;
  color: #14213d;
  background: #fff;
}

.edit-error {
  margin: 0;
  color: #b91c1c;
}

.modal-actions {
  justify-content: flex-end;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 960px) {
  .step-panel {
    padding: 24px;
  }

  .download-hero {
    flex-direction: column;
  }

  .metric-cluster,
  .trust-strip,
  .detail-grid {
    grid-template-columns: 1fr;
    min-width: 0;
  }

  .version-grid {
    flex-direction: column;
    align-items: start;
  }

  .version-metric {
    justify-items: start;
  }

  .preview-frame {
    height: 700px;
  }

  .comparison-columns {
    grid-template-columns: 1fr;
  }
}
</style>
