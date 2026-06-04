# AGENTS.md

## Purpose

This document defines how AI agents (Codex, ChatGPT, Claude, Cursor, and future coding agents) should contribute to Internship Copilot.

Before making code changes, agents must understand:

1. What the product is trying to accomplish.
2. How the system is architected.
3. The current development phase.
4. Existing implementation patterns.

Agents should prioritize maintainability, simplicity, and consistency over introducing new abstractions.

---

# Required Reading Order

Before implementing any feature, read:

1. docs/PRD.md
2. docs/ARCHITECTURE.md
3. docs/AGENTS.md
4. Relevant code files

Do not begin implementation until all required documents have been reviewed.

---

# Product Overview

Internship Copilot is an AI-powered recruiting assistant that helps students:

- Discover internship opportunities
- Evaluate role fit
- Generate application materials
- Track applications
- Prepare for interviews

The system is intentionally designed to solve real recruiting workflows for a single user before expanding into a multi-user platform.

---

# Core Product Principles

## Solve Real Problems

Every feature should directly reduce recruiting effort.

Avoid features that are technically interesting but provide little user value.

Ask:

> Does this help the user discover, evaluate, apply, or interview?

If not, reconsider implementation.

---

## Prefer Simplicity

Choose the simplest implementation that satisfies requirements.

Avoid:

- Premature optimization
- Unnecessary abstractions
- Over-engineering

The MVP should remain easy to understand and maintain.

---

## Single Source of Truth

Do not duplicate:

- Business logic
- Data models
- API contracts

Extend existing systems whenever possible.

---

# Technology Stack

## Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

## Backend

- Django
- Django REST Framework

## Database

- PostgreSQL

## Infrastructure

- Docker
- Tailscale
- Self-hosted Mac

## AI

- OpenAI API
- Codex

---

# Repository Structure

```text
apps/
├── web/
└── api/

workers/
└── agents/

docs/
├── PRD.md
├── ARCHITECTURE.md
└── AGENTS.md
```

---

# Coding Standards

## General

- Prefer readable code over clever code.
- Use descriptive variable names.
- Avoid unnecessary comments.
- Keep functions small.
- Eliminate dead code.

---

## TypeScript

### Required

- Strict TypeScript mode
- Explicit typing when helpful
- Strongly typed API responses

### Forbidden

- any
- Large utility files
- Unused exports

### Preferred

- Server Components when possible
- Feature-based organization
- Reusable UI components

---

## Django

### Required

- Thin views
- Business logic in services
- DRF serializers for validation
- Type annotations where practical

### Preferred Structure

```text
api/
├── models/
├── serializers/
├── services/
├── views/
└── tests/
```

---

# Database Rules

## IDs

Use UUIDs for all primary keys.

## Timestamps

Every table should include:

- created_at
- updated_at

## Migrations

Never edit old migrations.

Always create new migrations.

## Deletes

Prefer soft deletes when practical.

---

# API Design Rules

## REST First

Use predictable REST conventions.

Examples:

```text
GET /jobs
GET /jobs/{id}
POST /jobs
PATCH /jobs/{id}
DELETE /jobs/{id}
```

---

## Response Consistency

Successful responses should be predictable.

Errors should be structured.

Example:

```json
{
  "error": {
    "message": "Job not found"
  }
}
```

---

# AI Development Rules

## Ground Outputs

Generated content should always be based on:

- Candidate profile
- Resume data
- Job description

Never invent candidate experience.

Never fabricate metrics.

---

## Explain Recommendations

Every recommendation should include reasoning.

Bad:

```text
Match Score: 85
```

Good:

```text
Match Score: 85

Strong matches:
- React
- AWS
- PostgreSQL

Missing:
- Kubernetes
```

---

## Preserve User Data

Resume data is authoritative.

Job descriptions are authoritative.

AI-generated content is supplemental.

---

# Agent Workflow

Before implementing:

1. Understand the feature.
2. Review existing code.
3. Create a plan.
4. Implement incrementally.
5. Verify functionality.
6. Update documentation.

---

# Feature Development Process

## Step 1

Review requirements.

## Step 2

Identify affected systems.

## Step 3

Implement backend changes.

## Step 4

Implement frontend changes.

## Step 5

Add tests.

## Step 6

Update documentation.

---

# Testing Expectations

All new features should include tests where practical.

## Backend

- Model tests
- Service tests
- API tests

## Frontend

- Component tests
- Integration tests when appropriate

---

# Current Development Phase

Current Phase:

**Phase 0 MVP**

Primary Goal:

> Determine whether a user should apply to a role.

Required MVP Features:

- Resume ingestion
- Job ingestion
- Match scoring
- Missing keyword detection
- Apply recommendation
- Analysis dashboard

Avoid building future features until the MVP is complete.

---

# Definition of Done

A task is complete when:

- Code builds successfully
- Tests pass
- Lint passes
- Documentation is updated
- Architecture remains consistent
- No obvious technical debt is introduced

---

# When Unsure

If requirements are unclear:

- Do not invent requirements.
- Leave a TODO.
- Document assumptions.
- Favor minimal implementation.

The goal is consistent forward progress, not perfect prediction.
