export interface SkillInsight {
  name: string
  category: string
  count: number
  score: number
  reason: string
  suggested_sections: string[]
}

export interface ReadinessBreakdown {
  skill_match?: number
  experience_strength?: number
  impact_metrics?: number
  keyword_coverage?: number
}

export interface MetricSignal {
  metric: string
  category: 'scale' | 'performance' | 'business_impact' | 'quantity' | string
  descriptor: string
  label: string
  impact_weight: number
  context?: string
}

export interface KeywordMatchInsight {
  keyword: string
  score: number
  level: 'strong' | 'weak' | 'missing' | string
  section?: string
  related_terms?: string[]
  clusters?: string[]
  metric_support?: boolean
}

export interface KeywordAnalysis {
  strong_matches?: KeywordMatchInsight[]
  weak_matches?: KeywordMatchInsight[]
  missing_keywords?: string[]
  cluster_matches?: string[]
}

export interface OptimizationScoreAxes {
  jd_keyword_match?: number
  technical_strength?: number
  metric_impact?: number
  technology_density?: number
  action_verb_strength?: number
  readability?: number
  credibility?: number
}

export interface OptimizationScoreSnapshot {
  total?: number
  axes?: OptimizationScoreAxes
  matched_job_keywords?: string[]
  metric_signals?: MetricSignal[]
  metric_breakdown?: Record<string, number>
  keyword_analysis?: KeywordAnalysis
}

export interface OptimizationDecision {
  id?: string
  action?: string
  type?: string
  target_section?: string
  value?: string
  reason?: string
  decision?: 'kept' | 'rejected' | string
  decision_reason?: string
  verification?: {
    passed?: boolean
    reasons?: string[]
    codes?: string[]
  }
  scores?: {
    before?: OptimizationScoreSnapshot
    after?: OptimizationScoreSnapshot
  }
}

export interface OptimizationScoreRow {
  key: keyof OptimizationScoreAxes
  label: string
  before: number
  after: number
}

export interface AnalysisResult {
  mode?: 'analysis' | 'suggestions'
  summary?: string
  role_type?: { id: string; label: string }
  top_skills?: SkillInsight[]
  matched_skills?: SkillInsight[]
  missing_skills?: SkillInsight[]
  keywords?: {
    job?: string[]
    matched?: string[]
    missing?: string[]
  }
  job_alignment?: {
    job_description_provided?: boolean
    matched_count?: number
    missing_count?: number
  }
  suggested_changes?: string[]
  applied_changes?: string[]
  unresolved_suggestions?: string[]
}

export interface ReadinessResult {
  score?: number
  role_type?: { id: string; label: string }
  breakdown?: ReadinessBreakdown
  top_issues?: string[]
  projected_score?: number
  projected_breakdown?: ReadinessBreakdown
  projected_top_issues?: string[]
}

export interface ResumeEducationItem {
  school: string
  degree: string
  date: string
  details: string[]
}

export interface ResumeExperienceItem {
  role: string
  company: string
  date: string
  start_date: string
  end_date: string
  bullets: string[]
}

export interface ResumeProjectItem {
  name: string
  details: string
  bullets: string[]
}

export interface ResumeDocument {
  name?: string
  title?: string
  contact_items?: string[]
  summary?: string
  education?: ResumeEducationItem[]
  skills?: Record<string, string[]>
  experience?: ResumeExperienceItem[]
  projects?: ResumeProjectItem[]
}

export interface ExperienceBulletComparison {
  id: string
  entry_index: number
  bullet_index: number
  role_heading: string
  original: string
  optimized: string
}

export interface ResumeVersionSnapshot {
  id: number
  parsed_resume_id: number
  parent_version_id?: number | null
  version_number: number
  source: string
  metadata?: {
    edit_type?: string
    target_section?: string
    target_path?: string
    reason?: string
    instruction?: string
    score_delta?: number
  }
  created_at?: string | null
}

export interface ResumeSectionSummary {
  name: string
  items: number
}

export interface ParsedResume {
  id?: number
  file_name?: string
  text?: string
  sections?: ResumeSectionSummary[]
  document?: ResumeDocument
  metadata?: {
    format?: string
    parser_mode?: string
    parser_version?: string
    layout_block_count?: number
    source_file_hash?: string
  }
}

export interface PipelineResult {
  parsed: ParsedResume
  analysis: AnalysisResult
  optimized: {
    text?: string
    document?: ResumeDocument
    metadata?: {
      source?: string
      suggestions?: string[]
      highlighted_keywords?: string[]
      optimization_plan?: OptimizationDecision[]
      kept_changes?: OptimizationDecision[]
      rejected_changes?: OptimizationDecision[]
      version_snapshot?: ResumeVersionSnapshot
      scores?: {
        original?: OptimizationScoreSnapshot
        optimized?: OptimizationScoreSnapshot
      }
    }
  }
  diff: { unified?: string }
  ats_score: {
    score?: number
    projected_score?: number
    notes?: string[]
  }
  application_readiness: ReadinessResult
}

export interface DiffLine {
  type: 'add' | 'remove'
  value: string
}

export interface ImportedJob {
  url: string
  source: string
  title: string
  company: string
  location?: string
  description: string
  skills: string[]
}

export type ActionMode = 'analyze' | 'suggestions'

export interface WizardStep {
  id: number
  label: string
  caption: string
}
