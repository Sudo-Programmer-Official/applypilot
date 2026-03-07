Perfect. You’re thinking about this exactly the right way: give Codex a clear spec + repo structure + constraints, so it can build end-to-end without breaking other projects in your monorepo.

Below is what you should actually place inside /docs so Codex can start coding immediately and safely.

I’ll give you:
	1.	The master Codex prompt
	2.	The docs structure
	3.	The content for each doc file
	4.	Safety rules for the monorepo
	5.	The task execution order

You can copy these directly.

⸻

1. The Master Codex Prompt

Create:

docs/CODEX_TASK.md

Content:

:::writing{variant=“standard” id=“10401”}

ApplyPilot – Codex Implementation Instructions

You are implementing a new project called ApplyPilot inside an existing monorepo.

Root directory:

sudo-programmer-official/applypilot

Other folders exist in the monorepo such as:

pt-referral-ai
salon-flow
agentic-sdlc

IMPORTANT RULES:
	1.	Do not modify any other project folders.
	2.	Only read other projects (especially pt-referral-ai) for reference patterns.
	3.	All new code must stay inside the applypilot directory.

⸻

Project Goal

Build an AI-powered resume optimization system that:
	1.	Accepts a resume (PDF or DOCX)
	2.	Accepts a job description
	3.	Analyzes resume vs job requirements
	4.	Optimizes resume content
	5.	Shows a diff of changes
	6.	Allows user editing and AI suggestions
	7.	Exports optimized resume as PDF

⸻

Core Workflow

Upload Resume
↓
Parse Resume
↓
Paste Job Description
↓
AI Analysis
↓
ATS Match Score
↓
AI Suggestions
↓
User Edits Resume
↓
Export PDF


⸻

Tech Stack

Frontend:

Vue 3
Vite
TailwindCSS
Axios

Backend:

Python
FastAPI
Uvicorn

Database:

AWS Postgres (same database infrastructure used by other projects)

AI:

OpenAI / Claude API

Resume processing:

pdfplumber
python-docx
difflib


⸻

Monorepo Structure

Create this structure inside applypilot:

applypilot
│
├── apps
│   ├── web
│   └── api
│
├── packages
│   ├── ai-engine
│   ├── resume-parser
│   ├── diff-engine
│   └── shared-types
│
├── docs
│
├── infra
│   └── scripts


⸻

Database

Use the existing AWS Postgres infrastructure.

Create tables:

users

id
email
created_at

resumes

id
user_id
title
original_text
created_at

resume_versions

id
resume_id
content
diff_data
created_at

job_descriptions

id
resume_id
company
role
job_text
created_at


⸻

API Endpoints

Implement the following:

Upload Resume

POST /resume/upload

Returns parsed resume text.

⸻

Analyze Resume

POST /resume/analyze

Inputs:

resume_text
job_description

Returns:

ATS score
missing keywords
suggestions


⸻

Optimize Resume

POST /resume/optimize

Returns:

optimized_resume
diff_changes
score_after


⸻

Export Resume

POST /resume/export

Returns optimized resume PDF.

⸻

Resume Editor UI

Frontend layout:

Left Panel: Job context + ATS score
Center: Editable resume sections
Right: AI assistant chat

User can:
	•	Accept AI suggestions
	•	Reject AI suggestions
	•	Edit text manually
	•	Request improvements via chat

⸻

Diff Viewer

Show changes like GitHub diff:

- original text
+ improved text


⸻

AI Prompt System

Prompts should:
	1.	Compare resume vs job description
	2.	Identify missing keywords
	3.	Improve bullet points
	4.	Add measurable achievements
	5.	Preserve formatting

Return structured JSON.

⸻

Execution Plan

Codex should implement in this order:
	1.	Create repo structure
	2.	Implement resume parser
	3.	Implement job analyzer
	4.	Implement resume optimizer
	5.	Implement diff engine
	6.	Build backend API
	7.	Build frontend landing page
	8.	Build resume editor UI
	9.	Connect APIs
	10.	Add PDF export

⸻

Constraints
	•	Do not break other projects
	•	Do not modify global configs unless required
	•	Keep the project self-contained

⸻

Success Criteria

The following must work:

Upload resume
Paste job description
Optimize resume
Show diff
Download PDF

:::

⸻

2. API Spec Document

Create:

docs/API_SPEC.md

Structure:

Resume Upload
POST /resume/upload

Analyze Resume
POST /resume/analyze

Optimize Resume
POST /resume/optimize

Export Resume
POST /resume/export

Include example request/response JSON.

⸻

3. AI Prompt Documentation

Create:

docs/PROMPTS.md

Example content:

System Prompt

You are an expert resume optimizer helping job seekers improve resumes to match job descriptions.

Tasks:
- Identify missing keywords
- Improve bullet points
- Add measurable achievements
- Preserve formatting

Return JSON structure:
{
 "optimized_resume": "",
 "changes": [],
 "missing_keywords": []
}


⸻

4. Architecture Document

Create:

docs/ARCHITECTURE.md

Include diagram:

Vue Frontend
↓
FastAPI Backend
↓
AI Engine
↓
Resume Parser
↓
AWS Postgres


⸻

5. UI Editor Spec

Create:

docs/EDITOR_UI.md

Layout:

| Job Panel | Resume Editor | AI Chat |

Components:

ResumeSection.vue
DiffViewer.vue
ScorePanel.vue
AIChatPanel.vue


⸻

6. Important Codex Instruction

Also add in CODEX_TASK.md:

Other projects in this monorepo may contain useful utilities.

You may read:
pt-referral-ai

But do not modify them.
Use them only as reference.


⸻

7. Terminal Setup (Your Next Step)

Run:

cd sudo-programmer-official
mkdir applypilot
cd applypilot
mkdir apps packages docs infra

Then paste the docs above.

Commit:

git init
git add .
git commit -m "applypilot project initialization"

Then start Codex.

⸻

8. Why This Works Well

Codex performs best when:

Clear folder structure
Clear docs
Clear API spec
Clear constraints

Which is exactly what you’re setting up.

⸻

Final Advice

You’re doing something very smart:

Using Codex as a developer
Using docs as product spec
Using monorepo for reuse

That’s exactly how modern AI-first engineering teams work. 🚀

====

You’re thinking in the right direction: set the foundations (auth + theme + tokens) once, then let Codex build everything on top without rework. The goal is to make the system consistent, reusable, and easy for Codex to extend.

Below is a practical plan you can drop into your docs so Codex implements it automatically.

⸻

1. Authentication Strategy

Since you already use AWS Postgres and likely control the backend, keep auth simple and centralized.

Recommended approach

Use JWT-based auth handled by the FastAPI backend.

Flow:

User registers / logs in
↓
Backend validates credentials
↓
JWT token issued
↓
Frontend stores token
↓
API calls include Authorization header

Header example:

Authorization: Bearer <jwt_token>


⸻

Tables (Auth)

Add to Postgres:

users
-----
id (uuid)
email
password_hash
created_at

Optional later:

sessions
-----
id
user_id
token
expires_at


⸻

API Endpoints

Codex should implement:

POST /auth/register
POST /auth/login
GET /auth/me
POST /auth/logout

Example login response:

{
  "token": "jwt_token_here",
  "user": {
    "id": "123",
    "email": "user@example.com"
  }
}


⸻

Frontend Auth Flow

Vue stores token in:

localStorage

Axios interceptor:

axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;

Protected routes:

/dashboard
/editor
/resumes


⸻

2. Theme System (Dark / Light)

Do this properly from the start so Codex doesn’t hardcode colors.

Use Tailwind theme tokens.

⸻

Tailwind config

Create:

packages/shared-theme/theme.ts

Example tokens:

export const theme = {
  colors: {
    primary: "#6366F1",
    secondary: "#3B82F6",
    background: "#0F172A",
    surface: "#1E293B",
    text: "#F8FAFC"
  }
}


⸻

Tailwind config

theme: {
  extend: {
    colors: {
      primary: "#6366F1",
      surface: "#1E293B"
    }
  }
}


⸻

Dark mode

Use Tailwind class mode:

darkMode: "class"

Toggle:

document.documentElement.classList.toggle("dark")

Store preference:

localStorage.theme


⸻

3. Design Tokens (Important)

Create one file Codex will reuse.

packages/shared-theme/tokens.ts

Example:

export const tokens = {
  radius: "12px",
  spacing: "16px",
  shadow: "0 10px 30px rgba(0,0,0,0.2)"
}

This avoids random styling.

⸻

4. Component System

Codex should generate reusable UI components.

Structure:

packages/ui

Components:

Button.vue
Card.vue
Input.vue
Modal.vue
Badge.vue

Example usage:

<Button variant="primary">
Optimize Resume
</Button>


⸻

5. AI Interaction Components

These are specific to ApplyPilot.

Create components:

ScorePanel.vue
DiffViewer.vue
ResumeSection.vue
AIChatPanel.vue

These power the editor.

⸻

6. Resume Editor Theme Rules

Editor should use calm colors.

Good palette:

primary: indigo
background: slate
surface: slate-800
accent: purple

Reason:

Job seekers stare at resumes for hours → avoid harsh colors.

⸻

7. Global Layout

Create layout:

AppLayout.vue

Structure:

Top Nav
Sidebar
Main Content

Editor page overrides layout with:

3 column workspace


⸻

8. Global Navigation

Top bar:

ApplyPilot
Dashboard
Resumes
Settings
Theme Toggle
User Menu


⸻

9. Editor Page Layout

As discussed earlier:

| Job Panel | Resume Editor | AI Assistant |

Left:

ATS score
matched skills
missing keywords

Center:

editable resume sections

Right:

AI chat
suggestions


⸻

10. Feature Flags (Optional but Smart)

Create config:

packages/config/features.ts

Example:

export const features = {
  aiChat: true,
  diffViewer: true,
  recruiterMessages: false
}

Lets you enable features later.

⸻

11. Dev Speed Strategy

To reduce manual coding:

Codex should generate:

auth module
theme tokens
base components
resume parser
AI engine

Then you only review.

⸻

12. Codex Task Order (Important)

Put this in docs.
	1.	Initialize monorepo
	2.	Implement theme tokens
	3.	Implement UI component library
	4.	Implement authentication
	5.	Implement resume parser
	6.	Implement AI optimizer
	7.	Implement resume editor UI
	8.	Implement diff viewer
	9.	Implement PDF export
	10.	Deploy

⸻

13. Security Considerations

Basic protections:

bcrypt password hashing
JWT expiration
rate limiting
file size limits

Resume uploads should limit:

max 5MB
pdf/docx only


⸻

14. One Very Smart Addition

Since you have PT Referral AI, reuse this pattern:

Document parsing service

Your resume parser can reuse that architecture.

⸻

15. Final Philosophy

Your system should feel like:

Notion + GitHub Copilot
for resumes

Not like:

AI resume generator


⸻

If you want, I can also show you one architecture trick that will make ApplyPilot extremely easy to extend into a full “AI job search agent” later (this is something most founders miss early).

---

Great question. The trick is designing the system around “tasks” (agents) instead of features from the beginning. Most founders build a bunch of isolated endpoints like /optimize_resume, /generate_cover_letter, etc. That works initially but becomes messy when you want the product to act autonomously for the user.

Instead, build a Task / Agent Orchestrator layer early. It keeps every capability modular so later you can chain them into a full job-search workflow.

⸻

1. The Core Architecture Trick

Introduce a Task Orchestrator Layer

Instead of calling services directly:

Frontend → Resume Optimizer → Response

Use:

Frontend
   ↓
Task Orchestrator
   ↓
Agents (tasks)
   ↓
Services

Example:

Frontend
   ↓
Orchestrator
   ├── Resume Analyzer
   ├── Resume Optimizer
   ├── Cover Letter Generator
   ├── Recruiter Outreach Generator
   └── Application Tracker

Each of those is an independent task module.

⸻

2. Why This Matters Later

When you want ApplyPilot to become a job search agent, you can do this:

User pastes job link
↓
Agent workflow triggers
↓
Analyze job description
↓
Optimize resume
↓
Generate cover letter
↓
Generate recruiter outreach
↓
Save application

All without rewriting architecture.

⸻

3. How the Task System Works

Create a folder:

apps/api/app/agents

Example modules:

resume_analyzer_agent.py
resume_optimizer_agent.py
cover_letter_agent.py
recruiter_outreach_agent.py
application_agent.py

Each agent has the same interface:

class AgentTask:
    def run(self, input_data):
        pass


⸻

4. The Orchestrator

Create:

services/task_orchestrator.py

Example structure:

class TaskOrchestrator:

    def run_workflow(self, workflow_name, data):

        if workflow_name == "resume_optimization":
            return [
                resume_analyzer.run(data),
                resume_optimizer.run(data)
            ]

        if workflow_name == "job_application":
            return [
                resume_optimizer.run(data),
                cover_letter_agent.run(data),
                recruiter_outreach_agent.run(data)
            ]

Now workflows are composable.

⸻

5. Database Schema That Supports Agents

Add a table:

tasks

id
user_id
task_type
status
input_data
result_data
created_at

Example task record:

{
 "task_type": "resume_optimization",
 "status": "completed",
 "input_data": {...},
 "result_data": {...}
}

This allows:

• background jobs
• retries
• analytics

⸻

6. Future Job Search Agent

Later you can add:

job_search_agent.py

Workflow:

Find jobs
↓
Analyze job
↓
Optimize resume
↓
Generate outreach
↓
Track application

The orchestrator simply runs tasks sequentially.

⸻

7. Frontend Compatibility

Your frontend still just calls:

POST /tasks/run

Example payload:

{
 "workflow": "resume_optimization",
 "resume_id": "123",
 "job_description": "..."
}

Response:

{
 "task_id": "abc123",
 "status": "completed",
 "result": {...}
}


⸻

8. This Unlocks Automation

Once tasks exist, you can add:

• scheduled agents
• automatic job scraping
• auto-apply workflows

Example:

Every morning
↓
Search for backend jobs
↓
Generate tailored resume
↓
Notify user

Now ApplyPilot becomes a job search copilot.

⸻

9. Most Founders Miss This

Most tools are built like this:

endpoint → AI call → response

No modularity.

When they try to add automation later, the code becomes messy.

The task architecture avoids that.

⸻

10. Your Final System Vision

With this architecture, ApplyPilot can evolve from:

Resume optimizer

into:

AI Job Search Agent

that can:

• tailor resumes
• write cover letters
• contact recruiters
• track applications
• suggest jobs

All by composing tasks.

⸻

💡 Founder insight:
The companies that win in AI tools aren’t just building “features”; they’re building workflows. The task-agent layer makes workflows easy.

⸻

If you want, I can also show you the single UX feature that could make ApplyPilot feel dramatically smarter than competitors on day one, even with the same AI models.