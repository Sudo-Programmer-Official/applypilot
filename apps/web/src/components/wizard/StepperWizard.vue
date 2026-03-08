<script setup lang="ts">
import { computed } from 'vue'
import type { WizardStep } from '../../types/wizard'

const props = defineProps<{
  steps: WizardStep[]
  activeStep: number
  unlockedStep: number
}>()

const emit = defineEmits<{
  (e: 'select', stepId: number): void
}>()

const progressPercent = computed(() => {
  if (!props.steps.length) {
    return 0
  }
  return Math.round((props.activeStep / props.steps.length) * 100)
})

function selectStep(stepId: number) {
  if (stepId > props.unlockedStep) {
    return
  }
  emit('select', stepId)
}
</script>

<template>
  <div class="stepper-shell">
    <div class="stepper-topline">
      <div>
        <p class="stepper-kicker">Resume Optimization Wizard</p>
        <h2>Step {{ activeStep }} of {{ steps.length }}</h2>
      </div>
      <strong>{{ progressPercent }}%</strong>
    </div>

    <div class="stepper-track" aria-hidden="true">
      <span class="stepper-track-fill" :style="{ width: `${progressPercent}%` }"></span>
    </div>

    <div class="stepper-list">
      <button
        v-for="step in steps"
        :key="step.id"
        type="button"
        class="step-pill"
        :data-active="step.id === activeStep"
        :data-complete="step.id < activeStep"
        :disabled="step.id > unlockedStep"
        @click="selectStep(step.id)"
      >
        <span class="step-index">{{ step.id }}</span>
        <span class="step-copy">
          <strong>{{ step.label }}</strong>
          <small>{{ step.caption }}</small>
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.stepper-shell {
  position: sticky;
  top: 18px;
  z-index: 5;
  padding: 22px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(14px);
  box-shadow: 0 18px 40px rgba(20, 33, 61, 0.08);
}

.stepper-topline {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: end;
}

.stepper-kicker {
  margin: 0 0 6px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h2 {
  margin: 0;
  font-size: 1.4rem;
  line-height: 1.05;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.stepper-track {
  height: 10px;
  margin-top: 18px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.08);
}

.stepper-track-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #b45309 0%, #2563eb 100%);
}

.stepper-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 10px;
  margin-top: 18px;
}

.step-pill {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  width: 100%;
  min-width: 0;
  padding: 12px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 18px;
  color: #14213d;
  text-align: left;
  background: rgba(255, 255, 255, 0.72);
}

.step-pill:disabled {
  cursor: not-allowed;
  opacity: 0.52;
}

.step-pill[data-active='true'] {
  border-color: rgba(37, 99, 235, 0.34);
  background: rgba(219, 234, 254, 0.78);
}

.step-pill[data-complete='true'] {
  border-color: rgba(21, 128, 61, 0.24);
  background: rgba(220, 252, 231, 0.74);
}

.step-index {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  border-radius: 50%;
  font-weight: 800;
  background: rgba(20, 33, 61, 0.08);
}

.step-pill[data-active='true'] .step-index {
  background: linear-gradient(135deg, #f59e0b, #2563eb);
  color: #fff;
}

.step-pill[data-complete='true'] .step-index {
  background: #15803d;
  color: #fff;
}

.step-copy {
  display: grid;
  min-width: 0;
}

.step-copy strong {
  font-size: 0.94rem;
  overflow-wrap: anywhere;
}

.step-copy small {
  color: #5f6c80;
  font-size: 0.72rem;
  overflow-wrap: anywhere;
}

@media (max-width: 980px) {
  .stepper-shell {
    position: static;
  }
}
</style>
