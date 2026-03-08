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

export interface AnalysisResult {
  mode?: 'analysis' | 'suggestions'
  summary?: string
  role_type?: { id: string; label: string }
  top_skills?: SkillInsight[]
  matched_skills?: SkillInsight[]
  missing_skills?: SkillInsight[]
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
    metadata?: { suggestions?: string[]; highlighted_keywords?: string[] }
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
