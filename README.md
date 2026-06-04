# Internship Copilot

Phase 0 MVP for deterministic internship match analysis.

## Workspace Layout

- `apps/api`: Django + DRF backend using SQLite
- `apps/web`: Next.js frontend using direct browser calls to the Django API
- `data/samples`: deterministic resume and job fixtures

## Requirements

- Python 3.13+
- `uv`
- Node.js 20+
- `pnpm` via Corepack

## Initial Setup

### Backend

```bash
cd apps/api
uv sync
uv run python manage.py migrate
```

### Frontend

```bash
pnpm install
cp apps/web/.env.local.example apps/web/.env.local
```

The default frontend API target is:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Running Locally

Run the backend:

```bash
cd apps/api
uv run python manage.py runserver 127.0.0.1:8000
```

Run the frontend from the repo root:

```bash
pnpm dev:web
```

The frontend will be available at `http://127.0.0.1:3000`.

## Helpful Commands

Backend tests:

```bash
cd apps/api
uv run pytest
```

Frontend lint:

```bash
pnpm lint:web
```

Frontend production build:

```bash
pnpm build:web
```

## Phase 0 Manual Flow

1. Open `http://127.0.0.1:3000/profile`
2. Paste resume text and save the profile
3. Open `http://127.0.0.1:3000/jobs/new`
4. Create a job with company, title, location, and raw job text
5. Open the new job detail page
6. Run analysis
7. Review match score, recommendation, reasoning, strengths, gaps, missing keywords, category-grouped skills, and score breakdown
