# Folder Audit Remediation Plan (Concrete Implementation Guide)

## 1) Purpose and Scope
This document translates findings from [docs/folder_audit.md](docs/folder_audit.md) into concrete implementation work.

Primary goal:
- Complete migration from mixed Jinja2 + API backend behavior to React SPA + JSON API boundary.

Secondary goals:
- Eliminate identified data-integrity, migration-chain, contract, and test coverage risks.
- Apply fixes in a safe sequence with explicit verification gates.

Out of scope:
- New product features unrelated to audited defects.
- UI redesign beyond route/API parity needs.

---

## 2) Ground Rules (Best Practices)
- Keep routes thin: validation + auth + service call + normalized JSON response.
- Keep all business logic in services, not route modules.
- Treat schema changes as migrations only, never ad-hoc DB edits.
- Use one response contract per endpoint and avoid mode-dependent behavior.
- Keep backward-compatibility shims time-boxed with explicit removal milestones.

---

## 3) Workstreams and Concrete Fixes

## Workstream A — Enforce SPA API Boundary (Critical)

### A1. Stop server-rendered behavior under /api/*
Files:
- [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py)
- [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py)
- [backend/app/routes/personnel_dashboard_routes.py](backend/app/routes/personnel_dashboard_routes.py)
- [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py)
- [backend/app/routes/college_auth_routes.py](backend/app/routes/college_auth_routes.py)

Concrete solution:
1. Replace all render_template/flash/redirect paths in API blueprints with JSON responses.
2. For each route, return shape:
   - success boolean
   - message string
   - data object or list
   - error object for non-2xx
3. Remove request mode branching in API routes (no form vs JSON dual contract).

### A2. Legacy route policy
Files:
- [backend/app/__init__.py](backend/app/__init__.py)
- [backend/app/routes/main_routes.py](backend/app/routes/main_routes.py)

Concrete solution:
- Keep only JSON routes mounted in /api/*.
- If legacy pages must temporarily exist, mount them under non-API prefix such as /legacy/*.
- Remove landing template dependency from API runtime path.

Acceptance checks:
- Grep check on backend route files shows no render_template, flash, redirect under /api blueprints.
- Calling /api routes always returns JSON content-type.

---

## Workstream B — Auth Endpoint Contract Consolidation (High)

### B1. Single auth surface
Files:
- [backend/app/routes/unified_auth_routes.py](backend/app/routes/unified_auth_routes.py)
- [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py)
- [backend/app/__init__.py](backend/app/__init__.py)

Concrete solution:
1. Keep unified endpoints as canonical:
   - POST /api/auth/validate-email
   - POST /api/auth/login
   - POST /api/auth/signup
   - POST /api/auth/check-username
2. Remove or remap legacy nested endpoints that currently become /api/auth/api/*.
3. Normalize error schema for auth:
   - success false
   - message
   - optional code

### B2. Frontend 401 handling behavior
File:
- [frontend/src/utils/api.js](frontend/src/utils/api.js)

Concrete solution:
- Update response interceptor:
  - Do not hard-redirect on all 401.
  - Allow login/signup/validate-email to handle 401 in page-level handlers.
  - Redirect only when token exists and request is to protected resource.

Acceptance checks:
- Invalid credentials stay on auth page and show inline error.
- Expired token on protected pages clears session and routes to auth once.

---

## Workstream C — Whitelist Multi-Tenant Integrity (High)

### C1. Scope whitelist mutations by college
Files:
- [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py)
- [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py)
- [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py)

Concrete solution:
1. Change service signatures:
   - check_if_whitelisted(email, college_id)
   - mark_email_registered(email, college_id, user_id)
2. Update all call sites to pass college_id.
3. In student signup, ignore client-submitted college_id for persistence and use validated email college_id.

### C2. Migration alignment for whitelist uniqueness
Files:
- [backend/migrations/versions/9b69ae95562e_enhanced_auth_system.py](backend/migrations/versions/9b69ae95562e_enhanced_auth_system.py)
- new migration revision

Concrete solution:
- Add corrective migration:
  - Drop global unique(email) on whitelisted_emails.
  - Add composite unique(email, college_id).

Acceptance checks:
- Duplicate email across two colleges inserts successfully.
- Registration marking updates only one target row for (email, college_id).

---

## Workstream D — Event Identity Model Correction (Critical)

Problem:
- Personnel creator id is being persisted into field constrained to users.id.

Files:
- [backend/app/models/event_models.py](backend/app/models/event_models.py)
- [backend/app/services/event_service.py](backend/app/services/event_service.py)
- [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py)
- new migration revision

Concrete solution:
1. Add explicit creator fields:
   - created_by_user_id FK users.id nullable
   - created_by_personnel_id FK college_personnel.id nullable
2. Keep creator_type as source-of-truth discriminator.
3. On create:
   - student/community creator => set created_by_user_id
   - college/personnel creator => set created_by_personnel_id
4. Update submit/approve/cancel/complete ownership checks to use creator_type and matching creator field.
5. Add personnel-compatible submit path for college-created events.

Acceptance checks:
- Personnel-created event persists without FK conflict.
- Personnel creator can submit/publish through defined flow.
- Student ownership rules remain intact.

---

## Workstream E — Event State Machine Enforcement (Medium)

Files:
- [backend/app/services/event_service.py](backend/app/services/event_service.py)
- [backend/app/constants/event_constants.py](backend/app/constants/event_constants.py)

Concrete solution:
1. Add helper:
   - can_transition(current_status, target_status, VALID_EVENT_TRANSITIONS)
2. Replace hardcoded equality checks with transition-map enforcement.
3. Return deterministic 400 on invalid transition with from/to details.

Acceptance checks:
- All lifecycle transitions validated through one helper path.
- Invalid transition test cases fail predictably.

---

## Workstream F — Constants and Schema Validation Drift (Medium)

Files:
- [backend/app/models/user.py](backend/app/models/user.py)
- [backend/app/models/user_skill.py](backend/app/models/user_skill.py)
- [backend/app/schemas/questionnaire_schema.py](backend/app/schemas/questionnaire_schema.py)
- [backend/app/constants/gamification.py](backend/app/constants/gamification.py)

Concrete solution:
1. Use LEVEL_FORMULA_DIVISOR constant in level formulas.
2. Reject bool in integer schema fields using explicit check:
   - if isinstance(value, bool): invalid
3. Add min_items: 1 to q2_team_roles.

Acceptance checks:
- Questionnaire rejects booleans in numeric fields.
- Empty q2_team_roles list fails validation.
- Level behavior unchanged for current divisor value.

---

## Workstream G — Frontend Contract and Test Parity (Medium)

Files:
- [frontend/src/test/handlers.js](frontend/src/test/handlers.js)
- [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx)
- [frontend/src/pages/Auth.jsx](frontend/src/pages/Auth.jsx)

Concrete solution:
1. Align MSW validate-email response with backend contract:
   - valid
   - is_registered
   - user_type
   - college_id where applicable
2. Keep AuthContext decisioning based on same canonical fields.
3. Expand SPA route surface based on backend JSON domains in staged manner:
   - /profile
   - /leaderboard
   - /projects
   - /events
   - /communities

Acceptance checks:
- Auth tests assert backend field names.
- Route transitions in Auth page follow valid/is_registered contract.

---

## Workstream H — Test Coverage and Reliability (High)

Files:
- [backend/tests/conftest.py](backend/tests/conftest.py)
- [backend/tests/test_community.py](backend/tests/test_community.py)
- [backend/tests/test_auth.py](backend/tests/test_auth.py)
- new [backend/tests/test_events.py](backend/tests/test_events.py)

Concrete solution:
1. Add migration smoke test path (Alembic upgrade on test DB) in CI job.
2. Fix personnel_auth_headers identity to personnel_<id>.
3. Correct stale community endpoint paths in auth checks.
4. Tighten broad status assertions to exact expected statuses where deterministic.
5. Add event auth/authority coverage:
   - creator identity handling
   - college authority checks
   - submit path behavior for personnel/student

Acceptance checks:
- Event path has dedicated tests.
- No tests passing by accepting irrelevant 404 fallback on malformed paths.

---

## Workstream I — Migration Chain Repair (Critical)

The migration strategy depends on environment reality. Use one path only.

### Path I-A (No production/shared DB yet)
Concrete solution:
1. Freeze current models as source-of-truth.
2. Archive broken revision chain files to backup folder outside Alembic versions.
3. Generate a clean baseline migration from current schema.
4. Stamp test/dev DBs to new baseline and validate full upgrade/downgrade cycle.

### Path I-B (Production/shared DB exists)
Concrete solution:
1. Do not rewrite already-applied historical revisions.
2. Add forward-only corrective revisions to neutralize drift:
   - whitelist unique constraint fix
   - enum normalization strategy
   - safe handling for duplicate table create history
3. Add CI migration test that upgrades from a representative prior revision state.

Required decision gate before implementation:
- Confirm whether any shared/production environment has already applied the current revision chain.

Acceptance checks:
- flask db upgrade succeeds from empty DB and from representative prior state.
- No duplicate-relation failures in chain path used by CI.

> **Actual path taken (2026-02-20):** Path I-A was not applicable — the dev DB already had all tables, created via db.create_all() and stamped to db67220b1b6b. Path I-B approach used instead: one forward-only corrective migration `0797b04af0db_add_event_dual_identity_fks` was generated and applied, adding created_by_user_id, created_by_personnel_id FKs to events and making created_by nullable. Round-trip (downgrade → upgrade) verified. The legacy broken revisions remain in versions/ for historical reference but are non-critical since dev DB is ahead of them via stamp. For new installs: flask db stamp db67220b1b6b; flask db upgrade.

---

## 4) Recommended Execution Order
1. Workstream A (API boundary)
2. Workstream B (auth contract)
3. Workstream C (whitelist integrity)
4. Workstream D (event identity)
5. Workstream F (schema/constants)
6. Workstream G (frontend parity)
7. Workstream H (tests)
8. Workstream I (migration chain finalization)

Reason:
- Frontend contract and API boundary must stabilize first.
- Data integrity and identity correctness next.
- Migrations finalized after schema intent is settled.

---

## 5) Verification Matrix

### API contract
- All /api routes respond with JSON only.
- Auth endpoints produce one canonical payload shape.

### Data integrity
- Whitelist operations are scoped by (email, college_id).
- Event creator fields remain relationally valid for both user and personnel creators.

### Test health
- Backend tests pass with tightened assertions.
- New event coverage present.
- Migration smoke test included in CI.

### SPA behavior
- Invalid login shows inline error without forced navigation loop.
- Protected-resource 401 still clears auth and routes correctly.

---

## 6) Change Management Notes
- Apply changes by workstream in separate PRs for review clarity.
- For each PR, include:
  - Scope statement
  - API contract delta
  - Migration impact statement
  - Rollback plan
- Keep temporary compatibility shims behind explicit TODO markers with removal date.

---

## 7) Immediate Next Action
Start with Workstream A + B in one implementation cycle:
- Convert remaining /api HTML behavior to JSON-only.
- Consolidate auth endpoint surface.
- Update frontend 401 interceptor behavior.

This gives the highest reduction in migration risk with lowest schema impact.