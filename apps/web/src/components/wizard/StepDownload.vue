<script setup lang="ts">
import type { DiffLine, ExperienceBulletComparison, ImportedJob, PipelineResult } from '../../types/wizard'

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
  previewPdfUrl: string
  previewPreparing: boolean
  previewFailed: boolean
  previewErrorMessage: string
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'download'): void
  (e: 'preview'): void
  (e: 'regenerate'): void
}>()
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
          <strong>{{ (result.analysis.applied_changes || result.analysis.suggested_changes || []).length }}</strong>
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
          <p class="comparison-heading">{{ comparison.role_heading }}</p>
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
.detail-card {
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

.comparison-heading {
  margin: 0;
  color: #14213d;
  font-weight: 700;
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

  .preview-frame {
    height: 700px;
  }

  .comparison-columns {
    grid-template-columns: 1fr;
  }
}
</style>
