<script setup lang="ts">
import { computed } from 'vue'
import type { ParsedResume } from '../../types/wizard'

const props = defineProps<{
  parsed: ParsedResume
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'next'): void
}>()

const document = computed(() => props.parsed.document ?? {})
const skillEntries = computed(() => Object.entries(document.value.skills ?? {}).slice(0, 4))
const experienceItems = computed(() => (document.value.experience ?? []).slice(0, 4))
const contactLine = computed(() => (document.value.contact_items ?? []).join(' • '))
</script>

<template>
  <section class="step-panel review-step">
    <div class="panel-header">
      <div>
        <p class="step-kicker">Step 2</p>
        <h3>Review parsed resume data</h3>
      </div>
      <div class="status-badges">
        <span class="status-pill">{{ parsed.metadata?.parser_mode || 'layout_aware' }}</span>
        <span class="status-pill subtle">{{ parsed.metadata?.layout_block_count || 0 }} blocks</span>
      </div>
    </div>

    <div class="overview-grid">
      <article class="overview-card hero-card">
        <p class="eyebrow">Candidate profile</p>
        <h4>{{ document.name || 'Candidate' }}</h4>
        <p class="headline">{{ document.title || 'Role title not detected yet' }}</p>
        <p v-if="contactLine" class="meta-line">{{ contactLine }}</p>
        <p class="summary-copy">{{ document.summary || 'No summary block was detected in the uploaded resume.' }}</p>
      </article>

      <article class="overview-card sections-card">
        <p class="eyebrow">Section coverage</p>
        <div class="section-grid">
          <div v-for="section in parsed.sections || []" :key="section.name" class="section-chip">
            <strong>{{ section.items }}</strong>
            <span>{{ section.name }}</span>
          </div>
        </div>
      </article>
    </div>

    <div class="detail-grid">
      <article class="detail-card">
        <div class="detail-head">
          <h4>Detected skills</h4>
          <span>{{ skillEntries.length }}</span>
        </div>
        <div v-if="skillEntries.length" class="skill-groups">
          <div v-for="[category, values] in skillEntries" :key="category" class="skill-group">
            <strong>{{ category }}</strong>
            <p>{{ values.join(', ') }}</p>
          </div>
        </div>
        <p v-else class="empty-copy">No structured skill groups detected. You can still continue to job tailoring.</p>
      </article>

      <article class="detail-card">
        <div class="detail-head">
          <h4>Detected experience</h4>
          <span>{{ experienceItems.length }}</span>
        </div>
        <div v-if="experienceItems.length" class="timeline">
          <div v-for="item in experienceItems" :key="`${item.company}-${item.role}-${item.date}`" class="timeline-item">
            <div class="timeline-top">
              <strong>{{ item.role || item.company }}</strong>
              <span>{{ item.date }}</span>
            </div>
            <p>{{ item.company }}</p>
            <ul v-if="item.bullets?.length">
              <li v-for="bullet in item.bullets.slice(0, 2)" :key="bullet">{{ bullet }}</li>
            </ul>
          </div>
        </div>
        <p v-else class="empty-copy">Experience entries were not clearly classified. Re-upload if the file is malformed.</p>
      </article>
    </div>

    <div class="step-actions">
      <button class="ghost" type="button" @click="emit('back')">Back</button>
      <button class="primary" type="button" @click="emit('next')">Looks Good</button>
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
.detail-head,
.timeline-top,
.step-actions {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
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

h4 {
  font-size: 1.35rem;
}

.status-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.status-pill {
  padding: 8px 12px;
  border-radius: 999px;
  color: #124084;
  font-size: 0.84rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.86);
}

.status-pill.subtle {
  color: #8b5e34;
  background: rgba(255, 244, 214, 0.86);
}

.overview-grid,
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.overview-card,
.detail-card {
  padding: 22px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.72);
}

.hero-card {
  background: linear-gradient(135deg, rgba(251, 243, 221, 0.95), rgba(219, 234, 254, 0.9));
}

.headline,
.meta-line,
.summary-copy,
.skill-group p,
.timeline-item p,
.timeline-item li,
.empty-copy {
  margin: 0;
  color: #5f6c80;
  line-height: 1.6;
}

.headline {
  margin-top: 6px;
  font-size: 1.05rem;
  color: #14213d;
}

.meta-line,
.summary-copy {
  margin-top: 10px;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.section-chip {
  padding: 14px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.05);
}

.section-chip strong {
  display: block;
  font-size: 1.4rem;
}

.skill-groups,
.timeline {
  display: grid;
  gap: 14px;
  margin-top: 12px;
}

.skill-group,
.timeline-item {
  padding: 16px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.05);
}

.skill-group p,
.timeline-item p,
.timeline-item ul {
  margin-top: 8px;
}

.timeline-item ul {
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

.ghost {
  color: #14213d;
  background: rgba(20, 33, 61, 0.08);
}

@media (max-width: 840px) {
  .step-panel {
    padding: 24px;
  }

  .overview-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .panel-header,
  .step-actions {
    flex-direction: column;
  }
}
</style>
