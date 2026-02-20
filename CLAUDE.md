# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MeshWork** is a full-stack educational collaboration platform with gamification. It has a React SPA frontend and a Flask REST API backend connected to PostgreSQL.

## Development Commands

### Frontend (`frontend/`)

```bash
npm install          # Install dependencies
npm run dev          # Dev server on http://localhost:3000
npm run build        # Production build to dist/
npm run lint         # ESLint (max-warnings 0, must pass cleanly)
npm run preview      # Preview production build
```

### Backend (`backend/`)

```bash
# Activate venv first (from repo root)
source venv/Scripts/activate   # Windows Git Bash
source venv/bin/activate       # Linux/Mac

# Run dev server (port 5000)
python run.py

# Database migrations
flask db migrate -m "description"
flask db upgrade
flask db downgrade
```

### Running Both Together

Frontend dev server proxies `/api/*` to `http://localhost:5000`, so start both servers simultaneously for full-stack development.

## Architecture

### Frontend (`frontend/src/`)

- **`pages/`** — Full page components (one per route)
- **`context/`** — React Context providers for global state (auth, user info)
- **`utils/`** — Axios API client with JWT auto-injection
- **`index.css`** — Design system primitive layer (CSS variable definitions)

**Key patterns:**
- React Router DOM 6 for client-side navigation
- Framer Motion for all animations (max 600ms, no bounce — see design system)
- Tailwind CSS with semantic color tokens from CSS variables (never use raw hex in components)
- Dark mode toggled via `classList` on `<html>`

### Backend (`backend/app/`)

Flask application factory pattern (`create_app()` in `__init__.py`):

- **`models/`** — SQLAlchemy ORM models (define schema + relationships)
- **`routes/`** — Flask blueprints (thin — delegate logic to services), all registered with `/api` prefix
- **`services/`** — Business logic layer (routes call services, not models directly)
- **`utils/`** — Decorators (`@auth_required`, `@admin_required`), validators, JWT helpers
- **`schemas/`** — Request/response data structures
- **`constants/gamification.py`** — XP values, level thresholds

**Key patterns:**
- JWT Bearer tokens in `Authorization` header (not cookies), 24h expiry
- Single `/api/auth/validate-email` → `/api/auth/login` or `/api/auth/signup` flow that handles both students and personnel
- Email domain detection determines user type (student vs. personnel)
- Services dedicated to gamification: `xp_service.py`, `streak_service.py`, `skill_service.py`
- Custom exceptions in `exceptions.py`; global handlers in `error_handlers.py` return consistent JSON

### Auth Flow (Unified)

1. Client POSTs email to `/api/auth/validate-email` → backend detects user type
2. Client POSTs credentials to `/api/auth/login` or `/api/auth/signup`
3. Backend returns JWT; client stores it and injects into all subsequent requests
4. Students → main dashboard; Personnel → personnel dashboard

### Design System

The design system lives in two places:
- **`frontend/tailwind.config.js`** — maps Tailwind class names to CSS variable references
- **`frontend/src/index.css`** — defines the CSS variable values (primitive + semantic tokens)

**Rules:**
- Typography: `Clash Display` (headings), `Satoshi` (body), `JetBrains Mono` (code)
- Spacing: 8px grid
- Buttons morph border-radius on hover: `12px → 999px`
- Animations: predefined easing curves (`mesh`, `mesh-out`, `mesh-in`), no spring/bounce
- Documented in `mesh_work_design_system_v_1.md` (at repo root)

## Environment

Backend expects a `.env` file in `backend/` with:
- `DATABASE_URL` — PostgreSQL connection string (default: `postgresql://postgres:...@localhost:5432/meshwork`)
- `JWT_SECRET_KEY`

Frontend reads `VITE_API_URL` if set; otherwise Vite's dev proxy handles `/api` routing.

## API Testing

See `QUICK_TEST_GUIDE.md` and `UNIFIED_AUTH_TEST_COMMANDS.md` at the repo root for curl commands covering the auth and scoring endpoints.

## Page Status

See `FRONTEND_PAGES_CHECKLIST.md` for the full list of ~29 pages and their implementation status.
