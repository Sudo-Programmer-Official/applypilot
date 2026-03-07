PROMPT-1:

You are Codex working inside a monorepo project.

Current directory:
sudo-programmer-official/applypilot

IMPORTANT RULES
- Only modify files inside the "applypilot" folder.
- Do NOT modify any other folders in the monorepo.
- Other folders (pt-referral-ai, salon-flow, etc.) may be used as reference patterns but must not be edited.

PROJECT GOAL
Build the foundation for ApplyPilot, an AI-powered resume optimization system.

FEATURES (future phases)
- Upload resume (PDF / DOCX)
- Paste job description
- AI analysis of resume vs job
- Resume optimization suggestions
- Diff viewer showing changes
- Resume editor with AI suggestions
- Export optimized resume

FIRST TASK
Create the initial monorepo project structure ONLY.
Do not implement features yet.

Create this structure:

applypilot/
  apps/
    web/
    api/
  packages/
    ai-engine/
    resume-parser/
    diff-engine/
    shared-types/
  docs/
  infra/
    scripts/

INSIDE apps/web
Initialize a Vue 3 + Vite + TypeScript project.

INSIDE apps/api
Initialize a Python FastAPI project with this structure:

apps/api/app
  main.py
  routes/
  services/
  agents/
  models/

INSTALL backend dependencies:
- fastapi
- uvicorn
- pydantic
- pdfplumber
- python-docx
- openai

INSTALL frontend dependencies:
- vue
- vite
- tailwindcss
- axios

ADD BASE FILES

Create:

apps/api/app/main.py
Simple FastAPI server with /health endpoint.

apps/web/src/pages/Landing.vue
Simple landing page placeholder.

packages/resume-parser/parser.py
Stub parser with function:
parse_resume(file_path)

packages/diff-engine/diff_engine.py
Stub diff generator using difflib.

packages/ai-engine/optimizer.py
Stub function:
optimize_resume(resume_text, job_description)

Do NOT implement AI logic yet.

OUTPUT FORMAT
After finishing:

1. List files created
2. Show folder structure
3. Provide command to run backend
4. Provide command to run frontend

------

PROMPT 2:

Nice — this is a very solid scaffold. What Codex produced is basically the correct phase-1 foundation. You now have:
	•	Vue frontend
	•	FastAPI backend
	•	modular packages
	•	isolated Python env
	•	clear monorepo structure

That’s exactly the right starting point. 👍

But before moving forward, there are 3 small architecture fixes that will save you pain later (especially if ApplyPilot becomes a full AI job agent).

⸻

1️⃣ Fix the Python Package Imports (Important)

Right now your structure is:

packages/
  ai-engine/
  diff-engine/
  resume-parser/

But Python will not automatically import these cleanly.

Instead do this:

packages/
  ai_engine/
  diff_engine/
  resume_parser/

Rename the folders to underscore style.

Then add:

packages/__init__.py
packages/ai_engine/__init__.py
packages/diff_engine/__init__.py
packages/resume_parser/__init__.py

Now in your API you can do:

from packages.resume_parser.parser import parse_resume
from packages.ai_engine.optimizer import optimize_resume

Codex often forgets this — you’ll hit import errors later if you don’t fix it early.

⸻

2️⃣ Add the “Orchestrator” Folder (Your Future AI Brain)

Right now you have:

services/
agents/

Add one more:

apps/api/app/orchestrator/

Example structure:

apps/api/app/orchestrator/
    resume_pipeline.py

This will control the whole flow:

upload resume
↓
parse resume
↓
analyze vs job
↓
generate improvements
↓
generate diff

Example skeleton:

def run_resume_pipeline(resume_text, job_description):

    parsed = parse_resume(resume_text)

    analysis = analyze_resume(parsed, job_description)

    optimized = optimize_resume(parsed, job_description)

    diff = generate_diff(parsed, optimized)

    return {
        "analysis": analysis,
        "optimized": optimized,
        "diff": diff
    }

This single file becomes the AI job pipeline engine later.

Very powerful.

⸻

3️⃣ Add a Job Model Now (Future AI Agent Expansion)

Create:

apps/api/app/models/job.py

Example:

class JobContext(BaseModel):
    title: str
    company: str
    description: str
    keywords: list[str]

Later your system becomes:

resume + job context

Instead of just raw text.

That’s how it eventually evolves into:

AI job search agent

⸻

4️⃣ One File Missing (Important for Your Product)

Add this:

packages/ats_score/scorer.py

This will compute:

ATS Score
Keyword match %
Missing keywords

Example stub:

def calculate_ats_score(resume_text, job_description):

    return {
        "score": 72,
        "matched_keywords": [],
        "missing_keywords": []
    }

Your UI will show:

ATS Score: 72

This is the hook that keeps users using the product.

⸻

5️⃣ Update Landing Page Placeholder

Your Landing.vue should already show the real value.

Example:

<h1>
Stop Applying With The Same Resume
</h1>

<p>
ApplyPilot automatically optimizes your resume for every job description.
Increase your interview chances in minutes.
</p>

<button>
Optimize My Resume
</button>

Simple.

But high conversion.

⸻

6️⃣ Next Codex Task (The Correct Next Step)

Give Codex this prompt next:

Implement resume parsing.

Requirements:
- Support PDF and DOCX
- Return clean plain text
- Use pdfplumber for PDF
- Use python-docx for DOCX

File:
packages/resume_parser/parser.py

Return format:

{
  "text": "...",
  "sections": []
}

This unlocks everything else.

⸻

7️⃣ Your Real Product Engine

Once parsing works you can implement:

resume analysis
keyword extraction
ATS scoring
AI improvement
diff generation

That becomes the ApplyPilot core loop.

⸻

Quick Evaluation of What You Built

Honestly?

Your architecture already looks better than most AI resume startups.

Most tools are just:

frontend
→ openai
→ return text

You already built:

parser
diff engine
AI engine
modular packages

This is real product architecture.

⸻

One Warning (Founders Often Miss This)

Do NOT ship with only:

resume rewrite

You must ship with:

ATS score
keyword gap
change explanation

Otherwise it feels like a generic GPT wrapper.

⸻

If you want, I can also show you the one feature that could make ApplyPilot explode on LinkedIn job seekers extremely fast (a built-in viral loop).