# MeshWork Frontend Design + Component Blueprint

Last updated: 2026-02-20
Purpose: execution-safe blueprint for what to build, in what order, and how to continue if chat context is lost.

---

## 1) Source of Truth Hierarchy

When there is any conflict, use this priority order:

1. User’s latest explicit instruction in chat.
2. `docs/frontend_execution_lockins.md` (locked decisions and constraints).
3. `frontend/src/utils/apiRoutes.js` (canonical route contracts).
4. This blueprint (`docs/frontend_design_component_blueprint.md`) for build order and component scope.
5. `docs/frontend_form_composition_recommendation.md` for rationale and endpoint/page mapping background.

---

## 2) Design System Rules (Non-Negotiable)

- Use semantic design tokens/classes already defined in `frontend/src/index.css`.
- Do not add new raw hex colors in components/pages.
- Use Tailwind for layout/spacing structure; keep visual language aligned with CSS variables/classes.
- Use Framer Motion only for lightweight interactions (no heavy page-motion choreography).
- Use Lucide icons for iconography consistency.
- Keep interactions fast and simple under balanced MVP mode.

---

## 3) Architecture to Reuse

### 3.1 Composition core (already created)

- `frontend/src/context/FormStepContext.jsx`
- `frontend/src/components/shell/AuthShell.jsx`
- `frontend/src/components/form/FormEngine.jsx`
- `frontend/src/components/form/AnswerRegistry.jsx`
- `frontend/src/components/form/Field.jsx`
- `frontend/src/components/form/StyledInput.jsx`
- `frontend/src/components/form/PasswordInput.jsx`
- `frontend/src/components/form/SubmitButton.jsx`
- `frontend/src/components/form/ModeToggleLink.jsx`
- `frontend/src/components/form/StepProgressBar.jsx`

### 3.2 Shared UI primitives (already created)

- `frontend/src/components/ui/Button.jsx`
- `frontend/src/components/ui/IconButton.jsx`
- `frontend/src/components/ui/Badge.jsx`
- `frontend/src/components/ui/Avatar.jsx`
- `frontend/src/components/ui/Chip.jsx`
- `frontend/src/components/ui/Divider.jsx`
- `frontend/src/components/ui/Spinner.jsx`
- `frontend/src/components/ui/Skeleton.jsx`
- `frontend/src/components/ui/ProgressBar.jsx`
- `frontend/src/components/ui/Alert.jsx`
- `frontend/src/components/ui/EmptyState.jsx`
- `frontend/src/components/ui/KbdShortcut.jsx`
- `frontend/src/components/ui/ToastStack.jsx`

### 3.3 Layout/navigation layer (already created)

- `frontend/src/components/layout/Container.jsx`
- `frontend/src/components/layout/Stack.jsx`
- `frontend/src/components/layout/Grid.jsx`
- `frontend/src/components/layout/Navbar.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/layout/MobileDrawer.jsx`
- `frontend/src/components/layout/PageShell.jsx`

---

## 4) Remaining Initial-Flow Component Backlog

Status: completed on 2026-02-20 for initial component sprint.

1. `Tabs` ✅
2. `Stat` ✅
3. `StatRow` ✅
4. `SearchInput` ✅
5. `RoleBadge` ✅
6. `InterestChip` ✅
7. `MotivationMeter` ✅
8. `ScoringStatusBanner` ✅
9. `LikertScale` ✅
10. `ScoringSummaryCard` ✅
11. `UserCard` ✅
12. `MatchCard` ✅

Implementation rules:
- Keep each component focused and composable.
- Prefer prop-driven variants over duplicated components.
- Export centrally from barrel files (`components/ui/index.js` or domain index).
- Add only behavior needed by initial pages (no speculative features).

---

## 5) Page Creation Flow (Execution Order)

Build pages in this sequence to minimize rework and unblock API wiring early:

### Phase A: Foundation hardening
1. Ensure token handling is context-only in-memory (no local/session storage).
2. Ensure every API call goes through canonical paths in `frontend/src/utils/apiRoutes.js`.
3. Ensure strict `response.success` gate pattern in API consumption helpers/pages.

Current status (2026-02-20):
- Phase A completed for core auth surfaces (`AuthContext`, `api.js`, college auth pages).

### Phase B: Initial user journey pages
1. Auth entry (`/auth`, college auth pages already in route set).
2. Core dashboard and profile slices.
3. Questionnaire + scoring display pages.
4. Leaderboard discovery views.

Current status (2026-02-20):
- Implemented and routed: `/auth`, `/dashboard`, `/profile`, `/questionnaire`, `/leaderboard`.
- College auth pages (`/college/register`, `/college/admin-login`) aligned to canonical API routes in Phase A.

### Phase C: Collaboration pages
1. Projects pages.
2. Events pages.
3. Communities pages.

Current status (2026-02-21):
- Implemented and routed: `/projects`, `/events`, `/communities/explore`.
- Added Phase C page tests in `frontend/src/__tests__/pages/PhaseCPages.test.jsx`.

### Phase D: Institutional/admin pages
1. Personnel pages.
2. Admin pages.

For exact route targets, use canonical constants in `frontend/src/utils/apiRoutes.js` and page list in `docs/frontend_form_composition_recommendation.md`.

---

## 6) Definition of Done (Per Page)

A page is complete only when all are true:

1. Uses canonical route constants (no inline endpoint strings).
2. Handles loading, error, and empty states.
3. Shows user feedback/toast for critical actions.
4. Meets locked responsive scope (auth/core fully responsive).
5. Uses shared components (no unnecessary one-off UI clone).
6. Includes page-level tests per lock-in.

---

## 7) Build Contract Checklist (Per API Integration)

Before connecting any endpoint:

1. Confirm endpoint exists in `apiRoutes.js`.
2. Confirm request/response shape expected by page.
3. Confirm auth header behavior for protected endpoints.
4. Confirm fallback UI for non-success responses.
5. Confirm optimistic/pessimistic behavior choice is explicit.

---

## 8) Context-Loss Recovery Protocol

If chat context resets, resume work with this exact process:

1. Read `docs/frontend_execution_lockins.md`.
2. Read `docs/frontend_design_component_blueprint.md`.
3. Read `frontend/src/utils/apiRoutes.js`.
4. Check current exports under `frontend/src/components/ui/index.js`, `frontend/src/components/layout/index.js`, and `frontend/src/components/form/index.js`.
5. Continue from the first unchecked item in Section 4 (remaining component backlog).
6. If Section 4 is fully complete, proceed directly to page creation flow in Section 5.
7. Run `npm run lint` after each component batch.
8. Only then proceed to page creation flow in Section 5.

This keeps implementation deterministic even when conversation state is truncated.

---

## 9) What Not to Do

- Do not map new pages to known duplicated backend path variants.
- Do not reintroduce token persistence storage.
- Do not add broad new UI systems beyond existing MeshWork language.
- Do not create page-specific bespoke primitives when shared ones already fit.
- Do not skip tests for completed pages.
