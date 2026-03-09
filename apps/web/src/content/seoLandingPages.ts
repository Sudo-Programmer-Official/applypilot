export type SeoLandingPageContent = {
  benefits: string[]
  checklist: string[]
  checklistTitle: string
  ctaDescription: string
  ctaTitle: string
  description: string
  faq: Array<{ answer: string; question: string }>
  intro: string
  metaDescription: string
  metaTitle: string
  navLabel: string
  proofLabel: string
  proofValue: string
  relatedPosts: string[]
  sections: Array<{ paragraphs: string[]; title: string }>
  slug: string
  title: string
  workflowSteps: Array<{ description: string; title: string }>
}

export const seoLandingPages: SeoLandingPageContent[] = [
  {
    slug: 'ats-resume-checker',
    navLabel: 'ATS Resume Checker',
    metaTitle: 'ATS Resume Checker | Scan Resume Keywords and Formatting | ApplyPilot',
    metaDescription:
      'Check your resume against ATS expectations. ApplyPilot flags missing keywords, weak formatting, and relevance gaps before you apply.',
    title: 'Scan your resume like an applicant tracking system before a recruiter does.',
    description:
      'ApplyPilot reviews keyword coverage, section structure, and readability so you can fix the issues that keep strong candidates out of interview loops.',
    proofLabel: 'Why candidates get filtered',
    proofValue: 'Low keyword coverage, messy formatting, and weak role targeting.',
    intro:
      'Most resumes do not fail because the candidate lacks experience. They fail because the experience is buried in bullets, written in vague language, or formatted in a way an ATS cannot classify cleanly.',
    benefits: [
      'Spot missing skills and phrases from the target job description.',
      'Catch formatting choices that make sections harder to parse.',
      'See whether your strongest experience is obvious in the first screen.',
      'Move from generic resume edits to role-specific fixes.',
    ],
    checklistTitle: 'What a useful ATS resume checker should review',
    checklist: [
      'Role-specific keywords and skill clusters',
      'Clear section labels and ordering',
      'Bullets with outcomes instead of task lists',
      'Readable formatting without tables or visual clutter',
      'Contact and summary sections that parse cleanly',
    ],
    sections: [
      {
        title: 'What is an ATS resume checker?',
        paragraphs: [
          'An ATS resume checker compares your resume against patterns that applicant tracking systems and recruiters both rely on. That includes terminology, section structure, chronology, and whether your bullets show evidence that matches the role.',
          'A good checker does not promise a magic score. It helps you understand why a resume looks weak for a specific job and what to rewrite before you send the application.',
        ],
      },
      {
        title: 'How ATS systems evaluate resumes',
        paragraphs: [
          'Most ATS tools parse a resume into fields like title, company, dates, skills, and education. If that parse is noisy because the layout is inconsistent or the wording is too vague, your resume becomes harder to match and search.',
          'After parsing, recruiters and hiring teams still review the actual document. That means you need both machine-readable structure and human-readable impact. Optimizing for only one side usually creates a weaker resume.',
        ],
      },
      {
        title: 'Common ATS mistakes candidates make',
        paragraphs: [
          'Candidates often over-design the document, hide critical keywords inside dense paragraphs, or use bullets that describe responsibilities without measurable outcomes. Those choices reduce clarity even when the experience itself is strong.',
          'Another frequent mistake is sending one generic resume to every role. ATS screening is context-sensitive. The right keywords for a backend platform role are not the same as the ones for an ML infrastructure role.',
        ],
      },
      {
        title: 'How ApplyPilot helps',
        paragraphs: [
          'ApplyPilot gives you a guided workflow: upload the resume, compare it against the role target, review keyword and structure gaps, then rewrite the weak bullets before export.',
          'That makes the checker actionable. Instead of seeing a score and guessing what changed it, you get concrete edits tied to ATS coverage and recruiter readability.',
        ],
      },
    ],
    workflowSteps: [
      {
        title: 'Upload your current resume',
        description: 'Start with the version you actually send so the feedback matches the real risk.',
      },
      {
        title: 'Add the role target',
        description: 'Paste the job description or job link to surface the language that matters.',
      },
      {
        title: 'Review ATS and recruiter gaps',
        description: 'See weak sections, missing terms, and bullets that undersell scope or outcomes.',
      },
      {
        title: 'Rewrite and export',
        description: 'Generate stronger bullets, improve alignment, and download a cleaner resume version.',
      },
    ],
    faq: [
      {
        question: 'Can an ATS resume checker guarantee interviews?',
        answer:
          'No. It can only improve how clearly your experience maps to the role and how easily the resume can be parsed and reviewed.',
      },
      {
        question: 'Should I optimize for ATS or recruiters first?',
        answer:
          'You need both. If the structure is hard to parse, matching suffers. If the writing is generic, recruiters still pass even when the ATS parse succeeds.',
      },
      {
        question: 'Do I need a different resume for each job?',
        answer:
          'You usually need a role-focused version for each job family. The fastest wins come from adjusting keywords, summary emphasis, and the order of your strongest evidence.',
      },
    ],
    ctaTitle: 'Run your ATS review inside ApplyPilot',
    ctaDescription:
      'Upload a resume, compare it against a job target, and fix the specific gaps that keep qualified candidates out of interviews.',
    relatedPosts: ['how-to-pass-ats-resume-screening-2026', 'how-recruiters-read-resumes'],
  },
  {
    slug: 'resume-optimizer',
    navLabel: 'Resume Optimizer',
    metaTitle: 'AI Resume Optimizer | Improve ATS Match and Recruiter Readability | ApplyPilot',
    metaDescription:
      'Use ApplyPilot to optimize your resume for ATS screening and recruiter review with guided analysis, AI rewriting, and job-targeted suggestions.',
    title: 'Optimize your resume for the role you want, not the job market in general.',
    description:
      'A strong resume optimizer helps you tighten bullets, emphasize relevant evidence, and align your document with the exact job family you are targeting.',
    proofLabel: 'What optimization should do',
    proofValue: 'Make your evidence easier to match, easier to scan, and easier to trust.',
    intro:
      'Resume optimization is not about stuffing keywords or inflating claims. It is about selecting the right evidence, presenting it clearly, and making the document easy to understand in under a minute.',
    benefits: [
      'Prioritize experience that actually matches the role target.',
      'Rewrite weak bullets into clearer accomplishment statements.',
      'Balance ATS alignment with recruiter readability.',
      'Turn one baseline resume into focused versions for each search lane.',
    ],
    checklistTitle: 'What to optimize on a modern resume',
    checklist: [
      'Headline and summary that reflect the target role',
      'Bullets that connect work to outcomes and scale',
      'Skills grouped around the stack recruiters expect',
      'Experience ordering that highlights the strongest evidence first',
      'Language that mirrors the market without sounding copied',
    ],
    sections: [
      {
        title: 'Why most resume optimization advice feels shallow',
        paragraphs: [
          'Generic advice usually says to quantify results, tailor keywords, and keep the layout simple. That is directionally correct, but it does not tell you which bullets to cut, which projects to expand, or how to tailor the language for a specific role family.',
          'The hard part is prioritization. A resume optimizer should help you decide what belongs on the page, what can be condensed, and where the evidence is still too weak to trust.',
        ],
      },
      {
        title: 'How to optimize for both ATS and human review',
        paragraphs: [
          'ATS alignment starts with the vocabulary and structure that let your resume parse cleanly and match relevant searches. Human review starts with evidence. Recruiters need to see scope, impact, and relevance fast.',
          'The best approach is to optimize your wording around the role while preserving plain English. If a phrase feels unnatural to a recruiter, it will not become more persuasive just because it matches a keyword list.',
        ],
      },
      {
        title: 'What a resume optimizer should change first',
        paragraphs: [
          'Start with the top third of the page. Your summary, latest title, strongest bullets, and skills section should tell a coherent story about the role you want next.',
          'Then review the bullets that consume the most space. If they describe tasks instead of outcomes, or if they hide the stack and scope, they are the fastest place to improve conversion.',
        ],
      },
      {
        title: 'How ApplyPilot structures the work',
        paragraphs: [
          'ApplyPilot separates optimization into steps so you can review the parse, the job target, the missing keywords, and the rewrite suggestions instead of trying to do everything on one noisy screen.',
          'That structure matters because resume optimization is a judgment task. The tool should speed up iteration, not force opaque edits you cannot evaluate.',
        ],
      },
    ],
    workflowSteps: [
      {
        title: 'Start with the current draft',
        description: 'Use your working resume instead of rebuilding from zero.',
      },
      {
        title: 'Target a role or company',
        description: 'Set the optimization goal before making any edits.',
      },
      {
        title: 'Refine bullets and keyword coverage',
        description: 'Improve phrasing, evidence, and alignment in the areas that matter most.',
      },
      {
        title: 'Export a focused version',
        description: 'Keep a cleaner resume variant for each search lane or target company.',
      },
    ],
    faq: [
      {
        question: 'What is the difference between a resume optimizer and a resume builder?',
        answer:
          'A builder helps you create the document structure. An optimizer improves how an existing resume communicates fit for a specific role.',
      },
      {
        question: 'How often should I optimize my resume?',
        answer:
          'Any time you move into a new job family, seniority band, or company cluster. Your base resume can stay stable while the targeted version changes.',
      },
      {
        question: 'Does optimization always mean adding more keywords?',
        answer:
          'No. Sometimes the right move is removing generic text so the relevant evidence is easier to notice.',
      },
    ],
    ctaTitle: 'Optimize a real resume in a guided workflow',
    ctaDescription:
      'Use ApplyPilot to review the draft, target the role, and rewrite the sections that matter instead of guessing your way through edits.',
    relatedPosts: ['best-resume-format-for-software-engineers', 'how-to-optimize-your-resume-for-google'],
  },
  {
    slug: 'ai-resume-builder',
    navLabel: 'AI Resume Builder',
    metaTitle: 'AI Resume Builder | Generate and Refine Job-Targeted Resume Content | ApplyPilot',
    metaDescription:
      'Build and refine stronger resume content with AI. ApplyPilot helps turn raw experience into clearer, job-targeted bullets without losing accuracy.',
    title: 'Use AI to build sharper resume content without turning your experience into generic filler.',
    description:
      'The right AI resume builder helps you phrase accomplishments, tighten summaries, and create role-focused versions while keeping your actual experience intact.',
    proofLabel: 'What weak AI output looks like',
    proofValue: 'Buzzwords, inflated claims, and bullets that sound interchangeable.',
    intro:
      'AI can speed up resume writing, but raw generation is not enough. If the tool does not understand the role target and your real work history, it produces polished nonsense that recruiters spot immediately.',
    benefits: [
      'Turn rough experience notes into clearer accomplishment bullets.',
      'Generate summaries that match the target role without sounding templated.',
      'Keep your own facts while improving phrasing and structure.',
      'Create faster first drafts for each application variant.',
    ],
    checklistTitle: 'What an AI resume builder should help you do',
    checklist: [
      'Convert tasks into accomplishment-oriented bullets',
      'Mirror the role language without copying the posting',
      'Preserve technical accuracy and scope',
      'Surface the strongest projects and leadership signals',
      'Edit faster while keeping human review in the loop',
    ],
    sections: [
      {
        title: 'Where AI helps most in resume writing',
        paragraphs: [
          'AI is useful when you know the work you did but struggle to phrase it clearly. It can suggest stronger verbs, compress long explanations, and expose missing context like scale, latency, revenue, or team impact.',
          'It also helps when you need multiple variants quickly. Once the baseline facts are structured, AI can help tailor the emphasis for backend, platform, ML, or product-facing roles without rewriting from scratch each time.',
        ],
      },
      {
        title: 'Where AI creates risk',
        paragraphs: [
          'The biggest risk is confidence without accuracy. Generated bullets often sound polished enough to pass a quick read, but they may exaggerate ownership, invent metrics, or flatten distinct experiences into generic corporate language.',
          'That is why the best AI resume builder is an editing partner, not an autonomous resume generator. You still need to review claims, metrics, and technical wording before sending the document.',
        ],
      },
      {
        title: 'How to get better output from AI',
        paragraphs: [
          'Start with structured inputs. Give the tool the role target, the original resume content, and any notes about scope, systems, or outcomes you want to preserve. Better inputs reduce hallucinations and produce edits that feel specific.',
          'Then review the result like an editor. Cut anything inflated, restore missing detail, and check whether the new bullet actually improves the signal for the role you are targeting.',
        ],
      },
      {
        title: 'How ApplyPilot uses AI inside a resume workflow',
        paragraphs: [
          'ApplyPilot uses AI after the resume and job target are already in context. That means rewrite suggestions are anchored to an actual resume draft and a specific role, not generated in a vacuum.',
          'The result is more practical: better summaries, sharper bullets, and role-aware phrasing that still reflects the real work you did.',
        ],
      },
    ],
    workflowSteps: [
      {
        title: 'Upload your existing resume',
        description: 'Use your current draft as the source of truth for facts and chronology.',
      },
      {
        title: 'Set the job target',
        description: 'Tell the tool what type of role the rewritten content should support.',
      },
      {
        title: 'Review AI suggestions',
        description: 'Accept, reject, or refine the rewrites instead of copying them blindly.',
      },
      {
        title: 'Export the improved version',
        description: 'Keep a better draft that is clearer, stronger, and easier to adapt again later.',
      },
    ],
    faq: [
      {
        question: 'Can an AI resume builder write my whole resume from scratch?',
        answer:
          'It can, but that is usually the weakest use case. The better workflow is using AI to refine structured experience you have already provided.',
      },
      {
        question: 'How do I keep AI output from sounding generic?',
        answer:
          'Give the tool concrete inputs and keep a human review step. Specific systems, metrics, and scope details are what stop the output from sounding interchangeable.',
      },
      {
        question: 'Is AI resume writing safe for technical roles?',
        answer:
          'Yes, if you verify the details. Technical resumes benefit from AI-assisted clarity, but the claims still need to stay grounded in the work you actually shipped.',
      },
    ],
    ctaTitle: 'Build stronger resume content with AI and guardrails',
    ctaDescription:
      'Use ApplyPilot to rewrite weak bullets, sharpen summaries, and keep role-targeted edits anchored to the real work in your resume.',
    relatedPosts: ['resume-tips-for-ai-engineer-roles', 'how-recruiters-read-resumes'],
  },
]

export const seoLandingPagesBySlug = Object.fromEntries(seoLandingPages.map((page) => [page.slug, page]))
