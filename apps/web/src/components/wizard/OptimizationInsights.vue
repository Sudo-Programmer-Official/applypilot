<script setup lang="ts">
import { computed } from 'vue'

import type { KeywordAnalysis, KeywordMatchInsight, MetricSignal, OptimizationDecision, OptimizationScoreRow } from '../../types/wizard'

const props = defineProps<{
  title: string
  subtitle: string
  qualityBefore: number
  qualityAfter: number
  scoreRows: OptimizationScoreRow[]
  keptChanges: OptimizationDecision[]
  rejectedChanges: OptimizationDecision[]
  metricSignals: MetricSignal[]
  keywordAnalysis: KeywordAnalysis | null
}>()

const showQualityChip = computed(() => props.qualityBefore > 0 || props.qualityAfter > 0 || props.scoreRows.length > 0)
const qualityDelta = computed(() => props.qualityAfter - props.qualityBefore)

const displayedAppliedChanges = computed(() => props.keptChanges.slice(0, 4).map((change) => formatDecision(change, 'kept')))
const displayedRejectedChanges = computed(() => props.rejectedChanges.slice(0, 4).map((change) => formatDecision(change, 'rejected')))
const displayedMetricSignals = computed(() => props.metricSignals.slice(0, 6))
const displayedStrongMatches = computed(() => props.keywordAnalysis?.strong_matches?.slice(0, 4) ?? [])
const displayedWeakMatches = computed(() => props.keywordAnalysis?.weak_matches?.slice(0, 4) ?? [])
const displayedMissingKeywords = computed(() => props.keywordAnalysis?.missing_keywords?.slice(0, 4) ?? [])
const displayedKeywordClusters = computed(() => props.keywordAnalysis?.cluster_matches?.slice(0, 3) ?? [])

function formatDecision(change: OptimizationDecision, mode: 'kept' | 'rejected') {
  const action = change.action ?? ''
  const value = change.value?.trim()
  const decisionReason = normalizeReason(change.decision_reason || change.reason || 'No additional reason was provided.')

  if (mode === 'rejected') {
    if (action === 'rewrite_summary') {
      return `Skipped summary rewrite because ${decisionReason.toLowerCase()}`
    }
    if (action === 'add_skill' || action === 'add_derived_skill') {
      return value ? `Did not add ${value} because ${decisionReason.toLowerCase()}` : `Rejected a skill addition because ${decisionReason.toLowerCase()}`
    }
    if (action === 'rewrite_experience_bullet') {
      return `Left an experience bullet unchanged because ${decisionReason.toLowerCase()}`
    }
    return `Rejected this change because ${decisionReason.toLowerCase()}`
  }

  if (action === 'rewrite_summary') {
    return value ? `Reworked summary around ${value}.` : 'Adjusted the summary when it improved the score.'
  }
  if (action === 'add_skill' || action === 'add_derived_skill') {
    return value ? `Added ${value} to the skills surface.` : 'Added a resume-backed skill keyword.'
  }
  if (action === 'rewrite_experience_bullet') {
    return 'Strengthened an experience bullet without reducing credibility.'
  }
  if (action === 'reorder_skill_sections') {
    return 'Reordered skill sections for faster recruiter scanning.'
  }
  if (action?.startsWith('clean_project')) {
    return 'Cleaned project wording for clearer PDF rendering.'
  }
  return decisionReason
}

function normalizeReason(reason: string) {
  return reason
    .replace(/^Rejected because\s+/i, '')
    .replace(/^Rejected because the change\s+/i, '')
    .replace(/^Rejected\s+/i, '')
    .replace(/^Kept because\s+/i, '')
    .replace(/\.$/, '')
    .trim()
}

function formatKeywordMatch(match: KeywordMatchInsight) {
  const section = keywordSectionLabel(match.section)
  if (section) {
    return `${match.keyword} • ${section}`
  }
  return match.keyword
}

function keywordSectionLabel(section?: string) {
  if (!section) {
    return ''
  }
  const labels: Record<string, string> = {
    title: 'title context',
    summary: 'summary context',
    skills: 'skills only',
    experience_first_bullet: 'first bullet context',
    experience: 'experience context',
    projects: 'project context',
    education: 'education context',
  }
  return labels[section] ?? section.replace(/_/g, ' ')
}
</script>

<template>
  <article class="insights-card">
    <div class="insights-header">
      <div>
        <p class="eyebrow">Optimization insights</p>
        <h4>{{ title }}</h4>
        <p class="subtitle">{{ subtitle }}</p>
      </div>

      <div v-if="showQualityChip" class="quality-chip" :data-improved="qualityDelta > 0">
        <span>Recruiter scan score</span>
        <strong>{{ qualityBefore }} → {{ qualityAfter }}</strong>
        <small>{{ qualityDelta > 0 ? `▲ +${qualityDelta}` : 'No score gain' }}</small>
      </div>
    </div>

    <div v-if="scoreRows.length" class="score-grid">
      <article v-for="row in scoreRows" :key="row.key" class="score-tile">
        <span>{{ row.label }}</span>
        <strong>{{ row.before }} → {{ row.after }}</strong>
        <small :data-positive="row.after > row.before">{{ row.after > row.before ? `▲ +${row.after - row.before}` : 'No change' }}</small>
      </article>
    </div>

    <div class="insight-columns">
      <article class="insight-panel">
        <div class="panel-head">
          <h5>Changes applied</h5>
          <span>{{ keptChanges.length }}</span>
        </div>
        <ul v-if="displayedAppliedChanges.length" class="insight-list positive-list">
          <li v-for="item in displayedAppliedChanges" :key="item">{{ item }}</li>
        </ul>
        <p v-else class="empty-copy">No verified optimizer changes were applied for this run.</p>
      </article>

      <article class="insight-panel">
        <div class="panel-head">
          <h5>Changes rejected</h5>
          <span>{{ rejectedChanges.length }}</span>
        </div>
        <ul v-if="displayedRejectedChanges.length" class="insight-list caution-list">
          <li v-for="item in displayedRejectedChanges" :key="item">{{ item }}</li>
        </ul>
        <p v-else class="empty-copy">No optimizer changes needed to be rejected.</p>
      </article>

      <article class="insight-panel">
        <div class="panel-head">
          <h5>Metric signals detected</h5>
          <span>{{ metricSignals.length }}</span>
        </div>
        <ul v-if="displayedMetricSignals.length" class="insight-list signal-list">
          <li v-for="signal in displayedMetricSignals" :key="`${signal.category}-${signal.label}`">{{ signal.label }}</li>
        </ul>
        <p v-else class="empty-copy">No standout impact metrics were detected in the current resume.</p>
      </article>
    </div>

    <article
      v-if="displayedStrongMatches.length || displayedWeakMatches.length || displayedMissingKeywords.length"
      class="keyword-panel"
    >
      <div class="panel-head">
        <div>
          <h5>ATS keyword analysis</h5>
          <p v-if="displayedKeywordClusters.length" class="keyword-meta">
            Cluster signals: {{ displayedKeywordClusters.join(', ') }}
          </p>
        </div>
        <span>{{ displayedStrongMatches.length + displayedWeakMatches.length + displayedMissingKeywords.length }}</span>
      </div>

      <div class="keyword-grid">
        <article class="keyword-column">
          <h6>Strong matches</h6>
          <ul v-if="displayedStrongMatches.length" class="insight-list positive-list">
            <li v-for="match in displayedStrongMatches" :key="`strong-${match.keyword}`">{{ formatKeywordMatch(match) }}</li>
          </ul>
          <p v-else class="empty-copy">No high-context ATS matches detected yet.</p>
        </article>

        <article class="keyword-column">
          <h6>Weak matches</h6>
          <ul v-if="displayedWeakMatches.length" class="insight-list caution-list">
            <li v-for="match in displayedWeakMatches" :key="`weak-${match.keyword}`">{{ formatKeywordMatch(match) }}</li>
          </ul>
          <p v-else class="empty-copy">No weak keyword-only matches were detected.</p>
        </article>

        <article class="keyword-column">
          <h6>Missing signals</h6>
          <ul v-if="displayedMissingKeywords.length" class="insight-list neutral-list">
            <li v-for="keyword in displayedMissingKeywords" :key="`missing-${keyword}`">{{ keyword }}</li>
          </ul>
          <p v-else class="empty-copy">All tracked job keywords have at least some resume presence.</p>
        </article>
      </div>
    </article>
  </article>
</template>

<style scoped>
.insights-card {
  display: grid;
  gap: 18px;
  padding: 22px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(248, 250, 252, 0.92));
}

.insights-header,
.panel-head {
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
.insight-list li {
  margin: 10px 0 0;
  color: #5f6c80;
  line-height: 1.6;
}

.quality-chip {
  min-width: 210px;
  display: grid;
  gap: 4px;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(20, 33, 61, 0.06);
}

.quality-chip[data-improved='true'] {
  background: linear-gradient(135deg, rgba(219, 234, 254, 0.92), rgba(255, 244, 214, 0.88));
}

.quality-chip span,
.score-tile span {
  color: #5f6c80;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.quality-chip strong,
.score-tile strong {
  color: #14213d;
  font-size: 1.35rem;
}

.quality-chip small,
.score-tile small {
  color: #5f6c80;
}

.score-tile small[data-positive='true'] {
  color: #166534;
}

.score-grid,
.insight-columns {
  display: grid;
  gap: 12px;
}

.score-grid {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.insight-columns {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.score-tile,
.insight-panel {
  padding: 16px;
  border-radius: 20px;
  background: rgba(20, 33, 61, 0.05);
}

.panel-head span {
  padding: 8px 10px;
  border-radius: 999px;
  color: #124084;
  font-size: 0.82rem;
  font-weight: 700;
  background: rgba(219, 234, 254, 0.86);
}

.insight-list {
  margin: 12px 0 0;
  padding-left: 18px;
}

.keyword-panel,
.keyword-column {
  padding: 16px;
  border-radius: 20px;
  background: rgba(20, 33, 61, 0.05);
}

.keyword-meta {
  margin: 8px 0 0;
  color: #5f6c80;
  line-height: 1.5;
}

.keyword-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.keyword-column h6 {
  margin: 0;
  color: #14213d;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.positive-list li::marker,
.signal-list li::marker {
  color: #166534;
}

.caution-list li::marker {
  color: #9a3412;
}

.neutral-list li::marker {
  color: #124084;
}

@media (max-width: 1100px) {
  .score-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .insight-columns,
  .keyword-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .insights-header {
    flex-direction: column;
  }

  .quality-chip,
  .score-grid {
    min-width: 0;
  }

  .score-grid {
    grid-template-columns: 1fr;
  }
}
</style>
