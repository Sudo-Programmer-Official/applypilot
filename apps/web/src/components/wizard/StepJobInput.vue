<script setup lang="ts">
import type { ActionMode, ImportedJob } from '../../types/wizard'

const props = defineProps<{
  mode: ActionMode
  jobUrl: string
  jobDescription: string
  suggestionsText: string
  importedJob: ImportedJob | null
  importingJob: boolean
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'next'): void
  (e: 'set-mode', value: ActionMode): void
  (e: 'update:jobUrl', value: string): void
  (e: 'update:jobDescription', value: string): void
  (e: 'update:suggestionsText', value: string): void
  (e: 'import-job'): void
  (e: 'use-example-job'): void
  (e: 'use-example-suggestions'): void
}>()

function updateText(event: Event, key: 'jobUrl' | 'jobDescription' | 'suggestionsText') {
  const target = event.target as HTMLInputElement | HTMLTextAreaElement
  if (key === 'jobUrl') {
    emit('update:jobUrl', target.value)
    return
  }
  if (key === 'jobDescription') {
    emit('update:jobDescription', target.value)
    return
  }
  emit('update:suggestionsText', target.value)
}
</script>

<template>
  <section class="step-panel">
    <div class="panel-header">
      <div>
        <p class="step-kicker">Step 3</p>
        <h3>Add job context</h3>
        <p class="panel-copy">
          Choose whether you want to tailor the resume to a job posting or apply external feedback from a mentor,
          recruiter, or ChatGPT.
        </p>
      </div>
      <div class="mode-switch" role="tablist" aria-label="Optimization mode">
        <button type="button" class="mode-button" :data-active="mode === 'analyze'" @click="emit('set-mode', 'analyze')">
          Job tailoring
        </button>
        <button type="button" class="mode-button" :data-active="mode === 'suggestions'" @click="emit('set-mode', 'suggestions')">
          External suggestions
        </button>
      </div>
    </div>

    <div v-if="mode === 'analyze'" class="input-layout">
      <article class="input-card">
        <div class="card-head">
          <div>
            <p class="eyebrow">Import link</p>
            <h4>Paste a job URL</h4>
          </div>
          <button class="ghost small" type="button" @click="emit('use-example-job')">Use Example</button>
        </div>
        <div class="job-import-row">
          <input
            :value="jobUrl"
            class="text-input"
            type="url"
            placeholder="https://company.com/jobs/backend-engineer"
            @input="updateText($event, 'jobUrl')"
          />
          <button class="ghost" type="button" :disabled="importingJob" @click="emit('import-job')">
            {{ importingJob ? 'Importing...' : 'Import Job' }}
          </button>
        </div>
        <div v-if="importedJob" class="import-card">
          <strong>Imported from {{ importedJob.source }}</strong>
          <p>{{ importedJob.company }}{{ importedJob.company && importedJob.title ? ' • ' : '' }}{{ importedJob.title }}</p>
          <p v-if="importedJob.skills.length">Top skills: {{ importedJob.skills.slice(0, 6).join(', ') }}</p>
        </div>
      </article>

      <article class="input-card">
        <div class="card-head">
          <div>
            <p class="eyebrow">Paste text</p>
            <h4>Job description</h4>
          </div>
        </div>
        <textarea
          :value="jobDescription"
          rows="12"
          placeholder="Paste the job description here. ApplyPilot will clean the text, detect the role, and rank the skills that matter most."
          @input="updateText($event, 'jobDescription')"
        ></textarea>
      </article>
    </div>

    <div v-else class="input-layout single-column">
      <article class="input-card">
        <div class="card-head">
          <div>
            <p class="eyebrow">Paste feedback</p>
            <h4>Improvement suggestions</h4>
          </div>
          <button class="ghost small" type="button" @click="emit('use-example-suggestions')">Use Example</button>
        </div>
        <textarea
          :value="suggestionsText"
          rows="12"
          placeholder="Example:
- Add Go and TypeScript to technical skills
- Quantify AWS Lambda work in the Braintree internship
- Improve the summary for backend platform roles"
          @input="updateText($event, 'suggestionsText')"
        ></textarea>
        <p class="panel-copy">These suggestions are mapped onto the structured resume model before the PDF is rendered.</p>
      </article>
    </div>

    <div class="step-actions">
      <button class="ghost" type="button" @click="emit('back')">Back</button>
      <button class="primary" type="button" @click="emit('next')">
        {{ mode === 'analyze' ? 'Continue to Optimize' : 'Continue to Apply Fixes' }}
      </button>
    </div>
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

h3,
h4 {
  margin: 0;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

h3 {
  font-size: clamp(2rem, 3vw, 2.7rem);
  line-height: 0.96;
}

.panel-header,
.card-head,
.step-actions,
.job-import-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
}

.panel-copy,
.import-card p {
  margin: 12px 0 0;
  color: #5f6c80;
  line-height: 1.6;
}

.mode-switch {
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.06);
}

.mode-button {
  border: none;
  border-radius: 999px;
  padding: 10px 14px;
  color: #5f6c80;
  font: inherit;
  font-weight: 700;
  background: transparent;
}

.mode-button[data-active='true'] {
  color: #fff;
  background: linear-gradient(135deg, #14213d, #2563eb);
}

.input-layout {
  display: grid;
  grid-template-columns: 0.95fr 1.2fr;
  gap: 18px;
}

.input-layout.single-column {
  grid-template-columns: 1fr;
}

.input-card {
  padding: 22px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.72);
}

.text-input,
textarea {
  width: 100%;
  border: 1px solid rgba(20, 33, 61, 0.14);
  border-radius: 18px;
  padding: 14px 16px;
  font: inherit;
  color: #14213d;
  background: rgba(255, 255, 255, 0.84);
}

textarea {
  resize: vertical;
  margin-top: 12px;
}

.text-input:focus,
textarea:focus {
  outline: none;
  border-color: rgba(37, 99, 235, 0.44);
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.1);
}

.job-import-row {
  margin-top: 12px;
  align-items: stretch;
}

.job-import-row .text-input {
  flex: 1;
}

.import-card {
  margin-top: 14px;
  padding: 14px 16px;
  border: 1px solid rgba(37, 99, 235, 0.12);
  border-radius: 18px;
  background: rgba(219, 234, 254, 0.42);
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

.ghost {
  color: #14213d;
  background: rgba(20, 33, 61, 0.08);
}

@media (max-width: 900px) {
  .step-panel {
    padding: 24px;
  }

  .panel-header,
  .job-import-row,
  .step-actions {
    flex-direction: column;
  }

  .input-layout {
    grid-template-columns: 1fr;
  }
}
</style>
