<script setup lang="ts">
import type { DiffLine, ImportedJob, PipelineResult } from '../../types/wizard'

const props = defineProps<{
  result: PipelineResult
  roleLabel: string
  editableResumeText: string
  isEditingResume: boolean
  copied: boolean
  downloadingPdf: boolean
  diffLines: DiffLine[]
  fixApplied: boolean
  displayedReadiness: number
  displayedAts: number
  readinessDelta: number
  importedJob: ImportedJob | null
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'toggle-edit'): void
  (e: 'copy'): void
  (e: 'download'): void
  (e: 'restart-job'): void
  (e: 'restart-resume'): void
  (e: 'show-original'): void
  (e: 'update:text', value: string): void
}>()

function updateText(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:text', target.value)
}
</script>

<template>
  <section class="step-panel">
    <div class="download-hero">
      <div>
        <p class="step-kicker">Step 5</p>
        <h3>Your optimized resume is ready</h3>
        <p class="hero-copy">
          Review the final draft, download the ATS-safe PDF, or start another tailoring pass for a different role.
        </p>
        <p class="meta-line">Target role: {{ roleLabel }}</p>
        <p v-if="importedJob" class="meta-line">
          {{ importedJob.company }}{{ importedJob.title ? ` • ${importedJob.title}` : '' }}
        </p>
      </div>
      <div class="metric-cluster">
        <div class="metric-card">
          <span>Readiness</span>
          <strong>{{ displayedReadiness }}</strong>
        </div>
        <div class="metric-card">
          <span>ATS Score</span>
          <strong>{{ displayedAts }}</strong>
        </div>
        <div class="metric-card">
          <span>Delta</span>
          <strong>+{{ readinessDelta }}</strong>
        </div>
      </div>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <button class="ghost small" type="button" @click="emit('back')">Back</button>
        <button class="ghost small" type="button" @click="emit('show-original')">
          {{ fixApplied ? 'View Original' : 'View Optimized' }}
        </button>
      </div>
      <div class="toolbar-actions">
        <button class="ghost small" type="button" @click="emit('toggle-edit')">
          {{ isEditingResume ? 'Preview' : 'Edit' }}
        </button>
        <button class="ghost small" type="button" @click="emit('copy')">
          {{ copied ? 'Copied' : 'Copy' }}
        </button>
        <button class="primary small" type="button" :disabled="downloadingPdf" @click="emit('download')">
          {{ downloadingPdf ? 'Preparing PDF...' : 'Download PDF' }}
        </button>
      </div>
    </div>

    <div class="content-grid">
      <article class="resume-card">
        <div class="card-head">
          <h4>{{ fixApplied ? 'Optimized Resume Preview' : 'Current Resume Preview' }}</h4>
          <span>{{ result.parsed.file_name }}</span>
        </div>

        <textarea
          v-if="isEditingResume"
          class="resume-editor"
          rows="20"
          :value="editableResumeText"
          @input="updateText"
        ></textarea>
        <pre v-else class="resume-preview">{{ editableResumeText }}</pre>
      </article>

      <aside class="side-stack">
        <article class="side-card">
          <div class="card-head">
            <h4>Changes applied</h4>
            <span>{{ (result.analysis.applied_changes || result.analysis.suggested_changes || []).length }}</span>
          </div>
          <ul class="change-list">
            <li v-for="item in result.analysis.applied_changes || result.analysis.suggested_changes || []" :key="item">
              {{ item }}
            </li>
          </ul>
        </article>

        <article class="side-card">
          <div class="card-head">
            <h4>Diff highlights</h4>
            <span>{{ diffLines.length }}</span>
          </div>
          <div v-if="diffLines.length" class="diff-list">
            <div v-for="(line, index) in diffLines" :key="`${line.type}-${index}`" class="diff-line" :data-type="line.type">
              <code>{{ line.value }}</code>
            </div>
          </div>
          <p v-else class="empty-copy">No line-level diff was generated for this run.</p>
        </article>
      </aside>
    </div>

    <div class="step-actions">
      <button class="ghost" type="button" @click="emit('restart-job')">Try Another Job</button>
      <button class="secondary" type="button" @click="emit('restart-resume')">Upload New Resume</button>
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
.change-list li {
  margin: 10px 0 0;
  color: #5f6c80;
  line-height: 1.6;
}

.download-hero,
.toolbar,
.card-head,
.step-actions {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
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

.toolbar-left,
.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.content-grid {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr;
  gap: 18px;
}

.resume-card,
.side-card {
  padding: 22px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.74);
}

.card-head span {
  padding: 8px 10px;
  border-radius: 999px;
  color: #124084;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.86);
}

.resume-preview,
.resume-editor {
  width: 100%;
  margin-top: 14px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 18px;
  padding: 18px;
  font: inherit;
  color: #14213d;
  background: rgba(248, 250, 252, 0.92);
}

.resume-preview {
  min-height: 720px;
  overflow: auto;
  white-space: pre-wrap;
}

.resume-editor {
  resize: vertical;
}

.resume-editor:focus {
  outline: none;
  border-color: rgba(37, 99, 235, 0.44);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.side-stack {
  display: grid;
  gap: 18px;
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

button {
  border: none;
  border-radius: 999px;
  padding: 12px 18px;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}

.small {
  padding: 10px 14px;
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

button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

@media (max-width: 960px) {
  .step-panel {
    padding: 24px;
  }

  .download-hero,
  .toolbar,
  .step-actions {
    flex-direction: column;
  }

  .metric-cluster,
  .content-grid {
    grid-template-columns: 1fr;
    min-width: 0;
  }
}
</style>
