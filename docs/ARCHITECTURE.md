# Internship Copilot Architecture

**Owner:** JP Davalos  
**Status:** Draft  
**Last Updated:** 2026-06-03  
**Version:** 1.0

---

# 1. System Overview

Internship Copilot is a single-user AI recruiting assistant that helps evaluate software engineering internships, generate application materials, and track applications.

The system should prioritize a fast MVP:

1. Upload or store a resume.
2. Paste a job posting or URL.
3. Parse the job.
4. Compare the job against the resume.
5. Generate a match report.
6. Generate application answers.
7. Save the job and application status.

Long-term, the app can run scheduled workers on an old MacBook to discover new internships and generate daily recommendations.

---

# 2. High-Level Architecture

```text
internship-copilot/
├── apps/
│   ├── web/                  # Next.js frontend
│   └── api/                  # Django + DRF backend
├── workers/
│   ├── agents/               # AI agent workflows
│   ├── scrapers/             # Job discovery workers
│   └── jobs/                 # Scheduled/background jobs
├── packages/
│   ├── shared/               # Shared types/config
│   └── prompts/              # Prompt templates
├── data/
│   ├── resume/               # Resume source files
│   └── samples/              # Sample job postings
├── docs/
│   ├── PRD.md
│   └── ARCHITECTURE.md
├── docker-compose.yml
├── README.md
└── .env.example
```

---

# 3. Tech Stack

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

## Backend

- Python
- Django
- Django REST Framework
- PostgreSQL

## AI / Agent Layer

- OpenAI API for structured outputs and generation
- Codex CLI for development assistance and long-running coding tasks
- Prompt templates stored in `packages/prompts`

## Infrastructure

- Old MacBook as the primary development and worker host
- Tailscale for secure remote access
- PostgreSQL running locally or through Docker
- Optional future deployment to AWS

---

# 4. Runtime Components

## 4.1 Web App

Location:

```text
apps/web
```

Responsibilities:

- Dashboard
- Job submission form
- Job detail page
- Match report viewer
- Generated answer viewer
- Application tracker

## 4.2 API Server

Location:

```text
apps/api
```

Responsibilities:

- Store jobs
- Store candidate profile
- Store applications
- Store generated content
- Trigger AI analysis workflows
- Serve data to frontend

## 4.3 Agent Workers

Location:

```text
workers/agents
```

Responsibilities:

- Parse resumes
- Parse job descriptions
- Generate match reports
- Generate application responses
- Generate interview prep

## 4.4 Scraper Workers

Location:

```text
workers/scrapers
```

Responsibilities:

- Future automated discovery
- Greenhouse scanning
- Lever scanning
- Ashby scanning
- Company career page monitoring

For MVP, scraper workers are not required.

---

# 5. Data Model

## 5.1 CandidateProfile

Represents JP's resume and structured background.

```text
CandidateProfile
- id: UUID
- resume_text: Text
- skills: JSON
- experiences: JSON
- projects: JSON
- education: JSON
- created_at: DateTime
- updated_at: DateTime
```

Example `skills`:

```json
[
  "React",
  "Next.js",
  "TypeScript",
  "Python",
  "Django",
  "PostgreSQL",
  "AWS Lambda",
  "DynamoDB"
]
```

---

## 5.2 Company

Represents a company.

```text
Company
- id: UUID
- name: String
- website: String
- careers_url: String
- notes: Text
- created_at: DateTime
- updated_at: DateTime
```

---

## 5.3 Job

Represents a job posting.

```text
Job
- id: UUID
- company: ForeignKey Company
- title: String
- url: URL
- location: String
- employment_type: String
- season: String
- raw_description: Text
- parsed_description: JSON
- requirements: JSON
- preferred_qualifications: JSON
- source: String
- created_at: DateTime
- updated_at: DateTime
```

Example `parsed_description`:

```json
{
  "responsibilities": [
    "Build backend services",
    "Design APIs",
    "Work with satellite control systems"
  ],
  "requirements": [
    "Python",
    "Backend development",
    "Databases"
  ],
  "preferred": [
    "Distributed systems",
    "Kubernetes"
  ]
}
```

---

## 5.4 MatchReport

Represents AI analysis comparing a job against the candidate profile.

```text
MatchReport
- id: UUID
- job: ForeignKey Job
- candidate_profile: ForeignKey CandidateProfile
- match_score: Integer
- recommendation: String
- strengths: JSON
- gaps: JSON
- missing_keywords: JSON
- resume_evidence: JSON
- reasoning: Text
- created_at: DateTime
- updated_at: DateTime
```

Example:

```json
{
  "match_score": 92,
  "recommendation": "HIGH_PRIORITY_APPLY",
  "strengths": [
    "Backend API experience through LocalArena",
    "AWS serverless experience through PokePredict",
    "Database experience with PostgreSQL and DynamoDB"
  ],
  "gaps": [
    "Limited explicit Kubernetes experience",
    "Limited production distributed systems experience"
  ],
  "missing_keywords": [
    "Kubernetes",
    "Distributed Systems"
  ]
}
```

---

## 5.5 Application

Tracks the status of a job application.

```text
Application
- id: UUID
- job: ForeignKey Job
- status: String
- priority: String
- applied_date: Date
- deadline: Date
- notes: Text
- created_at: DateTime
- updated_at: DateTime
```

Allowed statuses:

```text
INTERESTED
APPLIED
OA
INTERVIEW
FINAL_ROUND
OFFER
REJECTED
WITHDRAWN
```

Allowed priorities:

```text
LOW
MEDIUM
HIGH
URGENT
```

---

## 5.6 GeneratedContent

Stores AI-generated writing and prep material.

```text
GeneratedContent
- id: UUID
- job: ForeignKey Job
- content_type: String
- prompt: Text
- content: Text
- created_at: DateTime
- updated_at: DateTime
```

Allowed content types:

```text
WHY_COMPANY
WHY_ROLE
SELF_INTRODUCTION
MOST_IMPRESSIVE_ACCOMPLISHMENT
COVER_LETTER
CUSTOM_QUESTION
INTERVIEW_PREP
RESUME_SUGGESTIONS
```

---

# 6. API Design

Base URL:

```text
/api/v1
```

---

## 6.1 Candidate Profile Endpoints

### Create or update candidate profile

```http
POST /api/v1/candidate-profile/
```

Request:

```json
{
  "resume_text": "...",
  "skills": [],
  "experiences": [],
  "projects": []
}
```

Response:

```json
{
  "id": "uuid",
  "resume_text": "...",
  "skills": [],
  "experiences": [],
  "projects": []
}
```

### Get candidate profile

```http
GET /api/v1/candidate-profile/
```

---

## 6.2 Job Endpoints

### List jobs

```http
GET /api/v1/jobs/
```

### Create job manually

```http
POST /api/v1/jobs/
```

Request:

```json
{
  "company_name": "Astranis",
  "title": "Software Engineer Backend Intern",
  "url": "https://example.com/job",
  "location": "San Francisco, CA",
  "raw_description": "..."
}
```

### Get job detail

```http
GET /api/v1/jobs/{job_id}/
```

### Update job

```http
PATCH /api/v1/jobs/{job_id}/
```

### Delete job

```http
DELETE /api/v1/jobs/{job_id}/
```

---

## 6.3 Analysis Endpoints

### Analyze job fit

```http
POST /api/v1/jobs/{job_id}/analyze/
```

Response:

```json
{
  "match_report_id": "uuid",
  "match_score": 92,
  "recommendation": "HIGH_PRIORITY_APPLY",
  "strengths": [],
  "gaps": [],
  "missing_keywords": []
}
```

### Parse job description

```http
POST /api/v1/jobs/{job_id}/parse/
```

Response:

```json
{
  "parsed_description": {},
  "requirements": [],
  "preferred_qualifications": []
}
```

---

## 6.4 Generated Content Endpoints

### Generate content for a job

```http
POST /api/v1/jobs/{job_id}/generate-content/
```

Request:

```json
{
  "content_type": "WHY_COMPANY",
  "custom_question": "Why do you want to work here?"
}
```

Response:

```json
{
  "id": "uuid",
  "content_type": "WHY_COMPANY",
  "content": "..."
}
```

### List generated content for a job

```http
GET /api/v1/jobs/{job_id}/generated-content/
```

---

## 6.5 Application Endpoints

### List applications

```http
GET /api/v1/applications/
```

### Create application

```http
POST /api/v1/applications/
```

Request:

```json
{
  "job_id": "uuid",
  "status": "INTERESTED",
  "priority": "HIGH",
  "notes": "Strong backend match"
}
```

### Update application

```http
PATCH /api/v1/applications/{application_id}/
```

### Delete application

```http
DELETE /api/v1/applications/{application_id}/
```

---

# 7. Agent Workflows

## 7.1 Resume Agent

Input:

```text
Raw resume text
```

Output:

```json
{
  "skills": [],
  "experiences": [],
  "projects": [],
  "education": []
}
```

Responsibilities:

- Extract technical skills
- Extract projects
- Extract work experience
- Extract education
- Normalize skill names

---

## 7.2 Job Parser Agent

Input:

```text
Raw job description
```

Output:

```json
{
  "company": "...",
  "title": "...",
  "responsibilities": [],
  "requirements": [],
  "preferred_qualifications": [],
  "technologies": []
}
```

Responsibilities:

- Extract key job fields
- Identify technologies
- Separate required vs preferred qualifications
- Identify internship season if present

---

## 7.3 Match Agent

Input:

```text
Candidate profile + parsed job description
```

Output:

```json
{
  "match_score": 0,
  "recommendation": "LOW | MEDIUM | HIGH | HIGH_PRIORITY_APPLY",
  "strengths": [],
  "gaps": [],
  "missing_keywords": [],
  "resume_evidence": [],
  "reasoning": "..."
}
```

Scoring factors:

- Skill overlap
- Experience relevance
- Project relevance
- Role type fit
- Location fit
- Internship season fit
- Missing required qualifications

Suggested scoring weights:

```text
Technical skill overlap: 35%
Relevant experience: 25%
Project relevance: 20%
Role/industry interest: 10%
Location/season fit: 10%
```

---

## 7.4 Writing Agent

Input:

```text
Candidate profile + job description + content type
```

Output:

```text
Generated application response
```

Responsibilities:

- Generate concise application answers
- Ground answers in resume evidence
- Avoid unsupported claims
- Match JP's tone
- Keep answers specific to company and role

---

## 7.5 Interview Agent

Input:

```text
Candidate profile + job description + match report
```

Output:

```json
{
  "technical_topics": [],
  "behavioral_questions": [],
  "resume_questions": [],
  "company_notes": [],
  "star_stories": []
}
```

Responsibilities:

- Suggest likely technical topics
- Generate behavioral questions
- Map questions to JP's existing stories
- Generate company-specific prep notes

---

# 8. Prompt Template Structure

Prompt files should live in:

```text
packages/prompts
```

Suggested files:

```text
resume_parse.md
job_parse.md
match_report.md
write_answer.md
interview_prep.md
resume_suggestions.md
```

Each prompt should define:

```text
Role
Inputs
Output format
Constraints
Examples
```

Example constraints for writing prompts:

```text
- Do not invent experience.
- Use only evidence from the candidate profile.
- Keep answers concise and specific.
- Prefer concrete projects and metrics.
- Avoid generic statements.
```

---

# 9. Frontend Pages

## Dashboard

Path:

```text
/
```

Shows:

- Total applications
- High-priority roles
- Interviews
- Offers
- Recent jobs
- Recent generated content

---

## Jobs List

Path:

```text
/jobs
```

Shows:

- Company
- Title
- Location
- Match score
- Recommendation
- Application status

Actions:

- Add job
- Analyze job
- Create application

---

## Job Detail

Path:

```text
/jobs/[id]
```

Shows:

- Job metadata
- Raw job description
- Parsed requirements
- Match report
- Missing keywords
- Generated answers
- Application status

Actions:

- Run analysis
- Generate content
- Update status

---

## Add Job

Path:

```text
/jobs/new
```

Fields:

- Company
- Title
- URL
- Location
- Raw description

---

## Applications

Path:

```text
/applications
```

Shows:

- Company
- Role
- Status
- Priority
- Applied date
- Notes

---

## Candidate Profile

Path:

```text
/profile
```

Shows:

- Resume text
- Skills
- Experiences
- Projects

Actions:

- Update resume
- Re-parse resume

---

# 10. Background Jobs

For MVP, background jobs are optional.

Future scheduled jobs:

```text
scan_jobs_daily
refresh_match_scores
generate_daily_recommendations
archive_old_roles
```

Example cron schedule:

```text
0 9 * * * cd ~/Developer/internship-copilot/apps/api && /usr/bin/env uv run python manage.py scan_job_sources
```

---

# 11. Local Development Setup

## Environment Variables

Create `.env.example`:

```env
DATABASE_URL=postgres://postgres:postgres@localhost:5432/internship_copilot
OPENAI_API_KEY=
DJANGO_SECRET_KEY=dev-secret-key
DJANGO_DEBUG=true
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Recommended Commands

Install frontend:

```bash
cd apps/web
pnpm install
pnpm dev
```

Install backend:

```bash
cd apps/api
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Run database:

```bash
docker compose up -d db
```

---

# 12. Docker Compose

Initial `docker-compose.yml` should include PostgreSQL only.

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: internship_copilot
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

---

# 13. Build Order

## Step 1: Backend Foundation

- Create Django project
- Configure PostgreSQL
- Add models
- Add serializers
- Add CRUD endpoints

## Step 2: Frontend Foundation

- Create Next.js app
- Add navigation
- Add jobs list
- Add job detail page
- Add add-job form

## Step 3: Resume Profile

- Add candidate profile model
- Add profile page
- Add resume text upload/paste
- Add basic skill extraction placeholder

## Step 4: Job Analysis MVP

- Add job parser function
- Add match report function
- Store match reports
- Display match report on job detail page

## Step 5: Generated Content

- Add content generation endpoint
- Add writing prompt templates
- Add generated content UI

## Step 6: Application Tracker

- Add application model
- Add application status dropdown
- Add applications dashboard

## Step 7: Remote Mac Setup

- Install Tailscale
- Enable SSH
- Run API and workers on old Mac
- Access app from primary Mac through Tailscale

---

# 14. MVP Acceptance Criteria

The MVP is complete when JP can:

1. Open the dashboard.
2. Add a job manually.
3. Store his resume profile.
4. Run job analysis.
5. View a match score.
6. View strengths and gaps.
7. Generate at least one application answer.
8. Track application status.

---

# 15. Future Architecture Considerations

## Authentication

MVP can be single-user without login.

Future options:

- Basic auth
- Auth.js
- Clerk
- Google OAuth

## Deployment

MVP:

- Self-hosted on old MacBook
- Access through Tailscale

Future:

- AWS ECS or EC2
- RDS PostgreSQL
- S3 file storage
- CloudFront frontend

## Queue System

MVP can run agents synchronously.

Future options:

- Celery + Redis
- Django Q
- RQ
- Temporal

## Scraping

MVP should avoid scraping complexity.

Future:

- Start with public ATS platforms
- Respect robots.txt and site terms
- Store source and fetched timestamp
- Prefer user-provided URLs and raw descriptions

---

# 16. Codex Implementation Notes

When using Codex, start with small, reviewable tasks.

Good first tasks:

```text
Create the Django project and define the initial models from ARCHITECTURE.md.
```

```text
Create the Next.js app with pages for jobs list, add job, and job detail.
```

```text
Implement the POST /api/v1/jobs endpoint and connect it to the add-job form.
```

```text
Implement a placeholder match scoring function that compares skill keywords from the candidate profile against the job description.
```

Avoid asking Codex to build the entire project at once.

---

# 17. Initial GitHub Issues

## Issue 1: Initialize Repository

Create monorepo structure with `apps/web`, `apps/api`, `workers`, `packages`, `docs`, and root config files.

## Issue 2: Create Django API

Set up Django, DRF, PostgreSQL config, and base API routing.

## Issue 3: Add Core Models

Implement `CandidateProfile`, `Company`, `Job`, `MatchReport`, `Application`, and `GeneratedContent`.

## Issue 4: Add Job CRUD Endpoints

Implement list, create, retrieve, update, and delete endpoints for jobs.

## Issue 5: Add Candidate Profile Endpoint

Implement create/update and retrieve endpoint for the single candidate profile.

## Issue 6: Create Next.js Web App

Set up frontend with Tailwind, shadcn/ui, and base navigation.

## Issue 7: Build Add Job Flow

Create form to add company, title, URL, location, and raw job description.

## Issue 8: Build Job Detail Page

Display job metadata, raw description, match report, generated content, and application status.

## Issue 9: Implement Match Report MVP

Create a basic keyword-based match scoring system and store results.

## Issue 10: Implement Generated Content MVP

Generate and save one content type: `WHY_COMPANY`.
