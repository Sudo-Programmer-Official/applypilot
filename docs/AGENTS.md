Perfect. This is a very real productivity trick when working with Codex or any AI coding agent. Most people don’t do this, but it dramatically improves code quality and speed.

The trick is creating a single source of truth file for the repo so Codex doesn’t have to “guess” how the project works.

⸻

The Repo Trick: Add AGENTS.md at the Root

Create this file:

applypilot/AGENTS.md

This file becomes the instruction manual for Codex every time it reads the repo.

Instead of re-explaining the architecture in prompts, Codex reads this file first.

Think of it like:

README for AI developers


⸻

Example AGENTS.md

Paste something like this:

:::writing{variant=“standard” id=“20491”}

ApplyPilot – Agent Instructions

This repository is part of a monorepo located at:

sudo-programmer-official/

The current project is located in:

sudo-programmer-official/applypilot

Other folders in the monorepo include:
	•	pt-referral-ai
	•	salon-flow
	•	agentic-sdlc
	•	sudo-programmer-official-website

These projects may be referenced for patterns, but must not be modified.

⸻

Project Goal

ApplyPilot is an AI-powered resume optimization platform.

The product helps users:
	•	Upload a resume
	•	Paste a job description
	•	Analyze resume vs job
	•	Improve resume content
	•	Show AI change explanations
	•	Export optimized resume

⸻

Architecture

Frontend

Vue 3 + Vite + Tailwind

Backend

FastAPI

Database

AWS Postgres (shared infrastructure)

AI

OpenAI / Claude APIs

⸻

Repository Structure

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

⸻

Coding Principles
	1.	Do not modify code outside the applypilot folder.
	2.	Keep packages modular and reusable.
	3.	Avoid duplicating logic.
	4.	Reuse utilities when possible.
	5.	Prefer clear architecture over quick hacks.

⸻

Agents

The system uses task-based agents.

Agents include:

resume_analyzer_agent
resume_optimizer_agent
cover_letter_agent
recruiter_outreach_agent

Agents are orchestrated via a central task orchestrator.

⸻

UI Layout

Editor layout:

Left Panel → Job context + ATS score
Center → Resume editor
Right Panel → AI assistant chat

⸻

AI Output Format

All AI services should return structured JSON.

Example:

{
“suggestion”: “…”,
“reason”: “…”,
“keywords_added”: []
}
:::

⸻

Why This Makes Codex Much Faster

Without this file, Codex has to infer:
	•	repo architecture
	•	coding rules
	•	project scope
	•	allowed folders

With this file, Codex immediately knows:

how the project works
what it can modify
how modules interact

So it produces better code with fewer iterations.

⸻

Second Small Trick (Also Very Powerful)

Create this file:

docs/CONVENTIONS.md

Example:

Naming rules:

agents → *_agent.py
services → *_service.py
database models → *_model.py
frontend pages → *Page.vue
components → PascalCase.vue

Codex will automatically follow naming patterns.

⸻

Third Trick (For Monorepos Like Yours)

Add this at the root of applypilot:

CONTEXT.md

Example:

Other projects in the monorepo contain useful utilities.

pt-referral-ai:
- document parsing
- AI extraction patterns

Use as reference but do not modify.

Now Codex can borrow patterns safely.

⸻

Your Final Docs Folder Should Look Like This

docs
│
API_SPEC.md
BUILD_PLAN.md
PROMPTS.md
UX.md
CONVENTIONS.md

Root folder:

applypilot
│
AGENTS.md
CONTEXT.md

Now Codex has everything it needs.

⸻

Your Development Flow Now
	1.	You define product logic in docs
	2.	Codex reads repo rules
	3.	Codex implements modules
	4.	You review and adjust

This is AI-assisted architecture, not just AI code generation.

⸻

One Important Observation

Your workspace screenshot already shows you’re doing something very close to how top AI startups build products:
	•	spec-driven development
	•	modular architecture
	•	monorepo reuse
	•	AI agent assistance

That’s exactly how teams building AI-first developer workflows operate.

⸻

If you want, I can also show you one feature that could make ApplyPilot feel like a “10x tool” to job seekers immediately (and it’s surprisingly simple to build).