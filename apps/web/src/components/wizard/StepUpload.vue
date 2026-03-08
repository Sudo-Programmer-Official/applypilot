<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  fileName: string
  fileSize: number
  parsing: boolean
}>()

const emit = defineEmits<{
  (e: 'file-selected', file: File | null): void
  (e: 'parse'): void
}>()

const picker = ref<HTMLInputElement | null>(null)
const dragging = ref(false)

const fileSizeLabel = computed(() => {
  if (!props.fileSize) {
    return 'PDF or DOCX, up to 5 MB'
  }
  return `${(props.fileSize / 1024 / 1024).toFixed(2)} MB • ready for parser review`
})

function openPicker() {
  picker.value?.click()
}

function handleChange(event: Event) {
  const target = event.target as HTMLInputElement
  emit('file-selected', target.files?.[0] ?? null)
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  dragging.value = false
  const file = event.dataTransfer?.files?.[0] ?? null
  emit('file-selected', file)
}
</script>

<template>
  <section class="step-panel upload-step">
    <div class="step-copy">
      <p class="step-kicker">Step 1</p>
      <h3>Upload your resume</h3>
      <p>
        Start with the original resume file. ApplyPilot parses it once, keeps the structured document model,
        and reuses that model throughout the workflow.
      </p>
    </div>

    <div
      class="upload-dropzone"
      :data-dragging="dragging"
      @click="openPicker"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop="handleDrop"
    >
      <input
        ref="picker"
        class="hidden-input"
        type="file"
        accept=".pdf,.docx"
        @change="handleChange"
      />

      <span class="upload-icon">+</span>
      <strong>{{ fileName || 'Drag and drop your resume' }}</strong>
      <p>{{ fileSizeLabel }}</p>
      <button class="ghost" type="button">Choose File</button>
    </div>

    <div class="upload-notes">
      <article>
        <strong>Supported formats</strong>
        <p>PDF and DOCX resumes only. The parser preserves section structure and spacing.</p>
      </article>
      <article>
        <strong>What happens next</strong>
        <p>We extract a structured resume model so you can review the data before tailoring it.</p>
      </article>
    </div>

    <div class="step-actions">
      <button class="primary" type="button" :disabled="!fileName || parsing" @click="$emit('parse')">
        {{ parsing ? 'Parsing Resume...' : 'Continue to Review' }}
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

.step-kicker {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h3 {
  margin: 0;
  font-size: clamp(2rem, 3vw, 2.8rem);
  line-height: 0.96;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.step-copy p:last-child {
  max-width: 60ch;
  margin: 14px 0 0;
  color: #5f6c80;
}

.upload-dropzone {
  display: grid;
  justify-items: center;
  gap: 10px;
  padding: 46px 24px;
  border: 1.5px dashed rgba(20, 33, 61, 0.18);
  border-radius: 26px;
  text-align: center;
  cursor: pointer;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(244, 241, 232, 0.92));
}

.upload-dropzone[data-dragging='true'] {
  border-color: rgba(37, 99, 235, 0.48);
  box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.2);
}

.hidden-input {
  display: none;
}

.upload-icon {
  display: grid;
  place-items: center;
  width: 68px;
  height: 68px;
  border-radius: 22px;
  color: #fff;
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, #b45309, #2563eb);
}

.upload-dropzone strong {
  font-size: 1.2rem;
}

.upload-dropzone p {
  max-width: 42ch;
  margin: 0;
  color: #5f6c80;
}

.upload-notes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.upload-notes article {
  padding: 18px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.7);
}

.upload-notes p {
  margin: 8px 0 0;
  color: #5f6c80;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
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

.ghost {
  color: #14213d;
  background: rgba(20, 33, 61, 0.08);
}

@media (max-width: 720px) {
  .step-panel {
    padding: 24px;
  }

  .upload-notes {
    grid-template-columns: 1fr;
  }
}
</style>
