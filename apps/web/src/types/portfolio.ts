export interface PortfolioMetrics {
  impact_score: number
  project_count: number
  activity_count: number
  proof_count: number
  recent_activity_count: number
  tech_diversity: number
  resume_versions: number
}

export interface PortfolioResumeSnapshot {
  parsed_resume_id?: number
  file_name?: string
  format?: string
  parser_version?: string
  source_file_hash?: string
  name?: string
  title?: string
  summary?: string
  updated_at?: string | null
}

export interface PortfolioProject {
  id: number
  slug: string
  title: string
  summary: string
  impact_statement: string
  source: string
  tech_stack: string[]
  bullets: string[]
  proof_points: string[]
  links: string[]
  featured: boolean
  sort_order: number
}

export interface PortfolioActivityProof {
  claim?: string
  evidence?: string
  metric_label?: string
  metric_before?: string
  metric_after?: string
  links?: string[]
}

export interface PortfolioActivity {
  id: number
  project_id?: number | null
  event_type: string
  title: string
  detail: string
  impact: string
  source: string
  happened_on?: string | null
  tags: string[]
  links: string[]
  visibility: string
  proof: PortfolioActivityProof
  created_at?: string | null
}

export interface PortfolioProofCard {
  id: number
  project_id?: number | null
  project_title?: string | null
  title: string
  claim: string
  evidence: string
  metric_label: string
  metric_before: string
  metric_after: string
  source: string
  links: string[]
  metadata: Record<string, unknown>
  created_at?: string | null
}

export interface PortfolioProfile {
  id: number
  username: string
  display_name: string
  headline: string
  summary: string
  location: string
  primary_role: string
  contact_email: string
  email: string
  photo_url: string
  hiring_status: 'open' | 'selective' | 'closed' | string
  hero_statement: string
  resume_snapshot: PortfolioResumeSnapshot
  metadata: Record<string, unknown>
  created_at?: string | null
  updated_at?: string | null
}

export interface PublicPortfolioProfile {
  display_name: string
  headline: string
  summary: string
  location: string
  primary_role: string
  hero_statement: string
}

export interface PortfolioOverview {
  profile: PortfolioProfile
  metrics: PortfolioMetrics
  projects: PortfolioProject[]
  activity: PortfolioActivity[]
  proof_cards: PortfolioProofCard[]
}

export interface PublicPortfolioOverview {
  profile: PublicPortfolioProfile
  metrics: PortfolioMetrics
  projects: PortfolioProject[]
  activity: PortfolioActivity[]
  proof_cards: PortfolioProofCard[]
}

export interface PortfolioBootstrapPayload {
  username?: string
  parsed_resume_id?: number
}

export interface PortfolioProfileUpdatePayload {
  profile_id?: number
  username: string
  display_name: string
  headline: string
  summary: string
  location: string
  primary_role: string
  contact_email: string
  hiring_status: 'open' | 'selective' | 'closed' | string
  hero_statement: string
}

export interface PortfolioActivityCreatePayload {
  profile_id?: number
  project_id?: number
  event_type?: string
  title: string
  detail?: string
  impact?: string
  happened_on?: string
  tags?: string[]
  links?: string[]
  proof?: PortfolioActivityProof
}
