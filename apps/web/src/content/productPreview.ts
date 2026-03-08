export interface PreviewResume {
  id: string
  title: string
  employer: string
  updatedOn: string
  status: string
  summary: string
}

export const previewResumeHistory: PreviewResume[] = [
  {
    id: 'amazon-backend',
    title: 'Amazon Backend Engineer',
    employer: 'Amazon',
    updatedOn: 'March 8, 2026',
    status: 'Optimized',
    summary: 'Strengthened distributed systems bullets and tightened ATS keyword coverage.',
  },
  {
    id: 'stripe-platform',
    title: 'Stripe Platform SWE',
    employer: 'Stripe',
    updatedOn: 'March 6, 2026',
    status: 'Reviewed',
    summary: 'Refined platform reliability achievements and clarified infrastructure ownership.',
  },
  {
    id: 'uber-infra',
    title: 'Uber Infrastructure',
    employer: 'Uber',
    updatedOn: 'March 4, 2026',
    status: 'Draft',
    summary: 'Prepared a recruiter-ready version focused on systems scale and operational impact.',
  },
]
