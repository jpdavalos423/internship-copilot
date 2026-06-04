# Internship Copilot PRD

**Owner:** JP Davalos  
**Status:** Draft  
**Last Updated:** 2026-06-03  
**Version:** 1.0

---

# 1. Overview

## Product Name

Internship Copilot

## Vision

An AI-powered career assistant that helps students discover internships, evaluate fit, generate application materials, and prepare for interviews.

The long-term goal is to automate as much of the internship application process as possible while keeping the user in control of final decisions and submissions.

## Problem Statement

Applying for internships is highly repetitive.

Students spend significant time:

- Searching for opportunities
- Evaluating whether a role is a good fit
- Tailoring resumes
- Writing application responses
- Researching companies
- Preparing for interviews
- Tracking application status

The process becomes difficult to manage when applying to dozens or hundreds of positions.

Internship Copilot centralizes and automates these workflows.

---

# 2. Goals

## Primary Goal

Reduce the time required to evaluate and apply to internships by at least 80%.

## Success Metrics

### MVP Metrics

- Analyze a job posting in under 30 seconds
- Generate application materials in under 60 seconds
- Maintain a complete application tracking system
- Surface missing skills and keywords automatically

### Future Metrics

- Increase interview conversion rate
- Improve application response rate
- Discover internships automatically
- Generate interview preparation materials

---

# 3. Target Users

## Initial User

JP Davalos

Computer Science student seeking software engineering internships.

## Future Users

- Computer Science students
- New graduates
- Career changers
- Technical professionals

---

# 4. User Stories

## Job Discovery

As a student,

I want internships surfaced automatically,

so I don't have to manually search dozens of job boards.

---

## Fit Analysis

As a student,

I want to know whether I should apply to a role,

so I can prioritize my time effectively.

---

## Application Assistance

As a student,

I want personalized application responses,

so I can complete applications faster.

---

## Interview Preparation

As a student,

I want company-specific and role-specific preparation,

so I can perform better in interviews.

---

## Application Tracking

As a student,

I want all applications tracked in one place,

so I always know my recruiting status.

---

# 5. Product Scope

## MVP Scope

### Included

- Resume ingestion
- Job posting ingestion
- Match scoring
- Missing keyword detection
- Application answer generation
- Application tracking dashboard

### Excluded

- Automatic application submission
- Browser automation
- Multi-user support
- LinkedIn automation
- Recruiting outreach automation

---

# 6. Core Features

## Feature 1: Resume Profile

### Description

The system maintains a structured representation of the user's background.

### Inputs

- Resume PDF
- Resume Markdown
- Additional experience notes

### Outputs

Structured candidate profile.

### Example

```json
{
  "skills": [
    "React",
    "Next.js",
    "AWS",
    "Python",
    "PostgreSQL"
  ]
}
```

---

## Feature 2: Job Ingestion

### Description

Users can submit job postings for analysis.

### MVP Input

- Job URL
- Raw job description

### Extracted Data

- Company
- Title
- Location
- Description
- Requirements
- Preferred Qualifications

### Example

```json
{
  "company": "Astranis",
  "title": "Backend Software Engineer Intern",
  "location": "San Francisco, CA"
}
```

---

## Feature 3: Match Analysis

### Description

Compare the candidate profile against a job description.

### Outputs

- Match Score
- Strengths
- Missing Keywords
- Apply Recommendation

### Example

```text
Match Score: 92%

Strong Matches
- AWS
- PostgreSQL
- REST APIs

Missing Keywords
- Distributed Systems
- Kubernetes

Recommendation
HIGH PRIORITY APPLY
```

---

## Feature 4: Application Assistant

### Description

Generate recruiting materials tailored to a role.

### Supported Outputs

- Why This Company?
- Why This Role?
- Cover Letter
- Self Introduction
- Most Impressive Accomplishment
- Custom Application Questions

### Inputs

- Resume Profile
- Job Posting

---

## Feature 5: Application Tracker

### Description

Track recruiting progress.

### Stages

- Interested
- Applied
- OA
- Interview
- Final Round
- Offer
- Rejected
- Withdrawn

### Dashboard Metrics

- Applications Submitted
- Interviews
- Offers
- Response Rate

---

# 7. Future Features

## Automated Job Discovery

Automatically monitor:

- Greenhouse
- Lever
- Ashby
- Simplify
- Company Career Pages

---

## Resume Optimization

Generate role-specific suggestions.

Example:

```text
Current:
Built AWS Lambda ingestion pipelines.

Suggested:
Built event-driven AWS Lambda ingestion pipelines.
```

---

## Interview Preparation

Generate:

- Technical topics
- Behavioral questions
- STAR story recommendations
- Company research summaries

---

## Recruiting Analytics

Track:

- Response rates
- Offer rates
- Industry breakdown
- Application effectiveness

---

## Agent Workflows

Long-running AI agents can:

- Research companies
- Monitor new openings
- Generate interview prep
- Refresh application materials
- Suggest recruiting priorities

---

# 8. Technical Architecture

## Frontend

### Framework

Next.js

### Responsibilities

- Dashboard
- Job Analysis Views
- Application Tracker
- Generated Content Viewer

### Location

```text
apps/web
```

---

## Backend

### Framework

Django + Django REST Framework

### Responsibilities

- Job Management
- Resume Profile Management
- Application Tracking
- AI Workflow Orchestration

### Location

```text
apps/api
```

---

## Database

### Database

PostgreSQL

### Responsibilities

- Jobs
- Applications
- Generated Content
- Candidate Profile

---

## AI Layer

### Location

```text
workers/agents
```

### Agents

#### Resume Agent

Build candidate profile.

#### Job Parser Agent

Extract structured information.

#### Match Agent

Calculate fit scores.

#### Writing Agent

Generate application materials.

#### Interview Agent

Generate preparation content.

---

# 9. Remote Infrastructure

## Host Machine

Old MacBook

### Responsibilities

- PostgreSQL
- Django API
- AI Workers
- Codex CLI
- Scheduled Jobs

### Access

Tailscale + SSH

---

## Client Devices

- Primary MacBook
- iPad
- Phone

Access through browser.

---

# 10. Database Schema

## jobs

```sql
id UUID PRIMARY KEY
company TEXT
title TEXT
url TEXT
location TEXT
description TEXT
requirements TEXT
created_at TIMESTAMP
updated_at TIMESTAMP
```

---

## applications

```sql
id UUID PRIMARY KEY
job_id UUID
status TEXT
applied_date TIMESTAMP
notes TEXT
created_at TIMESTAMP
updated_at TIMESTAMP
```

---

## generated_content

```sql
id UUID PRIMARY KEY
job_id UUID
content_type TEXT
content TEXT
created_at TIMESTAMP
```

---

## candidate_profile

```sql
id UUID PRIMARY KEY
resume_text TEXT
skills JSONB
experience JSONB
projects JSONB
updated_at TIMESTAMP
```

---

# 11. Development Roadmap

## Phase 0

### Goal

Prove core value.

### Deliverables

- Upload resume
- Paste job URL
- Match score
- Missing keywords
- Apply recommendation

---

## Phase 1

### Goal

Application workflow.

### Deliverables

- Application tracking
- AI-generated responses
- Saved analyses

---

## Phase 2

### Goal

Recruiting assistant.

### Deliverables

- Company research
- Interview prep
- Resume optimization

---

## Phase 3

### Goal

Automation.

### Deliverables

- Job discovery agents
- Daily scans
- Ranking system
- Personalized recommendations

---

# 12. Open Questions

## Match Scoring

How should fit be calculated?

Potential inputs:

- Skill overlap
- Experience overlap
- Industry relevance
- Technology stack relevance

---

## LLM Strategy

Should generation use:

- OpenAI API
- Codex CLI
- Hybrid architecture

---

## Authentication

Will the MVP require login?

Current assumption:

Single-user application.

---

## Hosting

Should production remain:

- Self-hosted on old Mac
- AWS deployment
- Hybrid architecture

---

# 13. Definition of Success

A successful MVP allows JP to:

1. Paste a job posting.
2. Receive a fit score.
3. See missing keywords.
4. Get tailored application answers.
5. Track application progress.

All within a few minutes and from a single dashboard.
