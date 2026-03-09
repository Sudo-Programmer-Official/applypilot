<script setup lang="ts">
import { computed } from 'vue'

import type { ConfidenceCheck, ConfidenceSnapshot } from '../../types/wizard'

const props = defineProps<{
  title: string
  subtitle: string
  confidence: ConfidenceSnapshot
}>()

const displayedChecks = computed(() => props.confidence.checks.slice(0, 5))

function toneForCheck(check: ConfidenceCheck) {
  if (check.score >= 80) {
    return 'strong'
  }
  if (check.score >= 65) {
    return 'steady'
  }
  return 'needs-work'
}
</script>

<template>
  <article class="confidence-card">
    <div class="confidence-header">
      <div>
        <p class="eyebrow">Confidence layer</p>
        <h4>{{ title }}</h4>
        <p class="subtitle">{{ subtitle }}</p>
      </div>

      <div class="overall-score">
        <span>ATS compatibility</span>
        <strong>{{ confidence.optimized_score }} / 100</strong>
      </div>
    </div>

    <div class="comparison-row">
      <article class="comparison-tile">
        <span>Original</span>
        <strong>{{ confidence.original_score }}</strong>
      </article>
      <article class="comparison-tile improved">
        <span>ApplyPilot optimized</span>
        <strong>{{ confidence.optimized_score }}</strong>
      </article>
    </div>

    <div v-if="confidence.verification_items.length" class="verification-grid">
      <article v-for="item in confidence.verification_items" :key="item" class="verification-tile">
        <strong>Verified</strong>
        <span>{{ item }}</span>
      </article>
    </div>

    <div class="check-grid">
      <article
        v-for="check in displayedChecks"
        :key="check.key"
        class="check-card"
        :data-tone="toneForCheck(check)"
      >
        <div class="check-head">
          <h5>{{ check.label }}</h5>
          <strong>{{ check.score }}</strong>
        </div>
        <p>{{ check.detail }}</p>
      </article>
    </div>

    <div class="detail-grid">
      <article class="detail-panel">
        <div class="panel-head">
          <h5>Improvements recommended</h5>
          <span>{{ confidence.improvements.length }}</span>
        </div>
        <ul v-if="confidence.improvements.length" class="detail-list">
          <li v-for="item in confidence.improvements" :key="item">{{ item }}</li>
        </ul>
        <p v-else class="empty-copy">No major ATS blockers detected in the current draft.</p>
      </article>

      <article v-if="confidence.notes.length" class="detail-panel">
        <div class="panel-head">
          <h5>Verification notes</h5>
          <span>{{ confidence.notes.length }}</span>
        </div>
        <ul class="detail-list">
          <li v-for="note in confidence.notes" :key="note">{{ note }}</li>
        </ul>
      </article>
    </div>
  </article>
</template>

<style scoped>
.confidence-card {
  display: grid;
  gap: 16px;
  padding: 22px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(240, 249, 255, 0.88));
}

.confidence-header,
.panel-head,
.check-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: start;
}

.eyebrow {
  margin: 0 0 8px;
  color: #8b5e34;
  font-size: 0.74rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

h4,
h5 {
  margin: 0;
  font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Georgia, serif;
}

.subtitle,
.empty-copy,
.detail-list li,
.check-card p {
  margin: 10px 0 0;
  color: #5f6c80;
  line-height: 1.6;
}

.overall-score {
  min-width: 180px;
  display: grid;
  gap: 4px;
  padding: 16px 18px;
  border-radius: 20px;
  text-align: center;
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.92), rgba(255, 244, 214, 0.9));
}

.overall-score span,
.comparison-tile span,
.verification-tile strong {
  color: #5f6c80;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.overall-score strong,
.comparison-tile strong,
.check-head strong {
  color: #14213d;
  font-size: 1.35rem;
}

.comparison-row,
.check-grid,
.verification-grid,
.detail-grid {
  display: grid;
  gap: 12px;
}

.comparison-row {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.verification-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.check-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.detail-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.comparison-tile,
.verification-tile,
.check-card,
.detail-panel {
  padding: 16px;
  border-radius: 20px;
  background: rgba(20, 33, 61, 0.05);
}

.comparison-tile.improved {
  background: rgba(220, 252, 231, 0.72);
}

.verification-tile {
  display: grid;
  gap: 6px;
  background: rgba(255, 255, 255, 0.82);
}

.verification-tile span {
  color: #14213d;
  line-height: 1.45;
}

.check-card[data-tone='strong'] {
  background: rgba(220, 252, 231, 0.62);
}

.check-card[data-tone='steady'] {
  background: rgba(255, 247, 237, 0.82);
}

.check-card[data-tone='needs-work'] {
  background: rgba(219, 234, 254, 0.72);
}

.panel-head span {
  padding: 8px 10px;
  border-radius: 999px;
  color: #124084;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.86);
}

.detail-list {
  margin: 12px 0 0;
  padding-left: 18px;
}

@media (max-width: 1100px) {
  .check-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .confidence-header {
    flex-direction: column;
  }

  .comparison-row,
  .verification-grid,
  .detail-grid,
  .check-grid {
    grid-template-columns: 1fr;
  }
}
</style>
