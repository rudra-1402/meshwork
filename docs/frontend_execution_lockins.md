# MeshWork Frontend Execution Lock-ins

Last updated: 2026-02-20
Purpose: durable source-of-truth for implementation decisions when chat context shifts.

---

## 1) Delivery Objective

- Ship evaluation-ready frontend fast with minimal revision churn.
- Prioritize consistency, API contract correctness, and reusable components.
- Build pages/components in a way that can continue safely even if session context is truncated.

---

## 2) Locked Strategy Decisions

### 2.1 Build mode
- **Balanced mode** selected.
- Interpretation:
  - MVP-complete by default.
  - Include practical polish where cheap and low risk.

### 2.2 Implementation sequence
- **User journey first** selected for page rollout.
- Global sequence:
  1. Auth + onboarding/core entry flows
  2. Core dashboard/discovery flows
  3. Secondary/admin flows

### 2.3 Styling policy
- **Allow minor visual tweaks** selected.
- Guardrails:
  - Keep strict MeshWork design language.
  - No redesign drift; tweaks only for usability/consistency.

### 2.4 Contract strictness
- **Strict contract** selected.
- Must enforce for all new/refactored pages:
  - No localStorage/sessionStorage usage.
  - No HTML `<form>` usage for submission flow (use div/buttons and handlers).
  - JWT token must be supplied by app state (see token lock below).
  - API calls include `Authorization: Bearer <token>` header.
  - Always gate on `response.success` before consuming data.

### 2.5 Table/data depth
- **Core + filters** selected.
- Include loading/error/empty + pagination + useful filters for data-heavy pages.

### 2.6 Responsiveness depth
- **Auth and core flows fully responsive** selected.
- Secondary admin pages can be tablet/desktop-first if needed for time.

### 2.7 Done gate for each page
- Selected: **Plus tests for each page now**.
- Required completion checklist per page:
  - API wired
  - loading state
  - error state
  - empty state
  - toast feedback
  - core responsive layout
  - tests added

---

## 3) Token and State Lock-in

- User requested assistant to choose best option when uncertain.
- Chosen standard for this project sprint:
  - **Context-only in-memory token** (React context state).
  - No browser persistence storage.
  - Existing pages should be refactored to align before broad page sprint.

Rationale:
- Matches strict contract.
- Avoids security and consistency drift.
- Keeps one rule for old + new pages.

---

## 4) Backend Route Path Lock-in (Critical)

User explicitly requested:
- **Do NOT map frontend to current duplicated backend paths.**
- Map to **canonical normalized paths that backend will be changed to** before page creation.

### 4.1 Canonical path policy
- Frontend constants must target normalized paths only.
- Backend will be updated to match these canonical routes.
- Canonical frontend constants live at: `frontend/src/utils/apiRoutes.js`.

### 4.2 Duplicated-prefix hurdles identified
Current backend contains duplicated prefixes in some blueprints/registration pairs. Canonical targets below:

- Profile:
  - Current shape: `/api/profile/api/profile/*`
  - Canonical target: `/api/profile/*`

- Community:
  - Current shape: `/api/communities/api/communities/*`
  - Canonical target: `/api/communities/*`

- Personnel:
  - Current shape: `/api/personnel/api/personnel/*`
  - Canonical target: `/api/personnel/*`

- Admin:
  - Current shape: `/api/admin/api/admin/*`
  - Canonical target: `/api/admin/*`

- Leaderboard naming/prefix mismatch:
  - Current shape: `/api/leaderboard/api/leaderboards/*`
  - Canonical target: `/api/leaderboard/*`

---

## 5) Component Program Lock-in

### 5.1 Already available (do not rebuild)
- Form core and shell already exist and should be reused:
  - `FormStepContext`
  - `AuthShell`
  - `FormEngine`
  - `Field`, `StyledInput`, `PasswordInput`, `SubmitButton`, `ModeToggleLink`, `StepProgressBar`, `AnswerRegistry`
  - existing `EmailMetaCard`

### 5.2 Build order after lock-ins
- Continue with dependency-first system rollout, skipping already built components.
- Focus first on common reusable surfaces and feedback primitives, then navigation/layout, then advanced form/data components, then MeshWork-specific cards.

---

## 6) Non-negotiable UX/Tech Constraints (Carry Forward)

- React functional components + hooks.
- Tailwind for layout only; semantic CSS vars/classes from `index.css` for visuals.
- Framer Motion only for micro-interactions (not scroll-heavy page motion for standard app pages).
- Lucide icons.
- Single self-contained `.jsx` per page where requested.

---

## 7) Working Agreement for Future Sessions

When this document is present, treat it as authoritative unless user overrides explicitly.

Related operational blueprint:
- `docs/frontend_design_component_blueprint.md` (component backlog, build order, context-loss recovery protocol).

Session restart protocol:
1. Read this file first.
2. Read `docs/frontend_design_component_blueprint.md`.
3. Re-assert token + route-map lock-ins.
4. Continue from current phase without re-asking already locked decisions.
5. Ask only net-new blocking questions.

---

## 8) Open Items (Still Needs Explicit User Decision Later)

- Exact visual spec for each not-yet-built generic component where behavior can vary widely (e.g., DataGrid complexity, command palette scope).
- Exact backend completion timeline for canonical route normalization.

Until clarified, use balanced-mode defaults and strict contract constraints from this file.
