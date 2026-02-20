# Frontend Form Composition Recommendation (MeshWork)

## Objective

Adopt a reusable form composition system that reduces duplicated page logic, keeps visual consistency with the existing MeshWork design language, and prepares the frontend for backend API coverage without building every page immediately.

---

## Recommendation

Implement the **config-driven composition architecture** now, and defer page-by-page migration until requested:

- `FormStepContext` (shared current step + mode state)
- `AuthShell` (split layout + left panel modes)
- `FormEngine` (state, validation, step flow, submission, terminal states)
- form primitives under `components/form/`
- answer plugin registry (`AnswerRegistry`) and progress primitive (`StepProgressBar`)

This gives us a stable foundation so new pages are assembled from config instead of duplicated JSX logic.

---

## What to Keep

Use these as the baseline patterns/components:

1. Existing reusable auth primitives in `frontend/src/components/auth/AuthFormPrimitives.jsx`
   - `Field`
   - `StyledInput`
   - `PasswordInput`
   - `SubmitButton`
   - `ModeToggleLink`
   - `EmailMetaCard`

2. Existing split layout primitives in `frontend/src/components/layout/PagePanels.jsx`
   - `MultiPaneLayout`
   - `PaneSurface`

3. Existing cross-page UX utilities in `frontend/src/components/auth/AuthPageScaffold.jsx`
   - `ToastMessage`
   - `SkeletonBlock`
   - `InlineErrorState`

These are already aligned with the current UI language and should be reused or wrapped rather than discarded.

---

## What to Replace / Refactor

1. Replace monolithic page logic in `frontend/src/pages/Auth.jsx` with composition:
   - move form behavior into `FormEngine`
   - move left panel/layout behavior into `AuthShell`
   - move per-page behavior into config file(s)

2. Replace duplicated flow logic currently repeated across pages:
   - loading/error/empty handling variants
   - field-level validation and global error handling
   - per-step navigation and submit behavior

3. Refactor token drift from hard-coded values to semantic tokens only:
   - remove raw colors where they still exist in component/page styles
   - use `var(--bg-*)`, `var(--text-*)`, `var(--accent-*)`, `var(--color-error)`

4. Normalize route consumption:
   - maintain a frontend endpoint map with **actual current paths** and **normalized target paths** for future backend cleanup.

---

## Backend Route Inventory → Concrete Frontend Page List

> Source: `backend/app/routes/*.py` + blueprint registration in `backend/app/__init__.py`.
>
> Note: Some current endpoints are registered with duplicated path segments (e.g., `/api/profile/api/profile/...`).

### A) Auth and Entry Flows

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/auth/validate-email` | POST | `/auth` |
| `/api/auth/login` | POST | `/auth` |
| `/api/auth/signup` | POST | `/auth` |
| `/api/auth/check-username` | POST | `/auth` |
| `/api/college-auth/signup` | POST | `/college/register` |
| `/api/college-auth/login` | POST | `/college/admin-login` |

### B) Dashboard Flows

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/dashboard/dashboard` | GET | `/dashboard` |
| `/api/dashboard/profile` | GET | `/dashboard/profile` (or profile section in `/dashboard`) |
| `/api/dashboard/dashboard/college` | GET | `/dashboard/college` |

### C) Profile Flows (actual current paths)

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/profile/api/profile/` | GET | `/profile` |
| `/api/profile/api/profile/<user_id>` | GET | `/profile/:userId` |
| `/api/profile/api/profile/xp-history` | GET | `/profile/xp-history` |
| `/api/profile/api/profile/level-progress` | GET | `/profile` |
| `/api/profile/api/profile/streak-status` | GET | `/profile` |
| `/api/profile/api/profile/skills` | GET | `/profile/skills` |
| `/api/profile/api/profile/stats` | GET | `/profile` |

### D) Scoring / Questionnaire

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/scoring/questionnaire` | GET | `/questionnaire` |
| `/api/scoring/submit` | POST | `/questionnaire` |
| `/api/scoring/profile` | GET | `/profile/scoring` (or `/profile`) |
| `/api/scoring/history` | GET | `/profile/scoring-history` |
| `/api/scoring/retake` | POST | `/questionnaire` |

### E) Leaderboard (actual current paths)

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/leaderboard/api/leaderboards/xp` | GET | `/leaderboard` |
| `/api/leaderboard/api/leaderboards/streak` | GET | `/leaderboard` |
| `/api/leaderboard/api/leaderboards/skill/<skill_name>` | GET | `/leaderboard/skills/:skill` |
| `/api/leaderboard/api/leaderboards/skills/available` | GET | `/leaderboard` |
| `/api/leaderboard/api/leaderboards/all` | GET | `/leaderboard` |
| `/api/leaderboard/api/leaderboards/my-rank` | GET | `/leaderboard` |

### F) Project Flows

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/projects` | GET | `/projects` |
| `/api/projects` | POST | `/projects/new` |
| `/api/projects/<project_id>` | GET | `/projects/:projectId` |
| `/api/projects/<project_id>` | PATCH | `/projects/:projectId/edit` |
| `/api/projects/<project_id>` | DELETE | `/projects/:projectId` |
| `/api/projects/<project_id>/fork` | POST | `/projects/:projectId` |
| `/api/projects/<project_id>/members` | POST | `/projects/:projectId/members` |
| `/api/projects/<project_id>/members/<target_user_id>` | PATCH | `/projects/:projectId/members` |
| `/api/projects/<project_id>/members/<target_user_id>` | DELETE | `/projects/:projectId/members` |

### G) Event Flows

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/events/` | GET | `/events` |
| `/api/events/create` | POST | `/events/create` |
| `/api/events/<event_id>` | GET | `/events/:eventId` |
| `/api/events/<event_id>/submit` | POST | `/events/:eventId` |
| `/api/events/<event_id>/approve` | POST | `/events/pending` |
| `/api/events/<event_id>/reject` | POST | `/events/pending` |
| `/api/events/<event_id>/cancel` | POST | `/events/:eventId` |
| `/api/events/<event_id>/complete` | POST | `/events/:eventId` |
| `/api/events/<event_id>/register` | POST | `/events/:eventId` |
| `/api/events/<event_id>/confirm-attendance` | POST | `/events/:eventId` |
| `/api/events/<event_id>/drop` | POST | `/events/:eventId` |
| `/api/events/<event_id>/participants` | GET | `/events/:eventId/participants` |
| `/api/events/<event_id>/tasks` | GET, POST | `/events/:eventId/tasks` |
| `/api/events/tasks/<task_id>/submit-action` | POST | `/events/tasks/:taskId` |
| `/api/events/tasks/<task_id>/summary` | GET | `/events/tasks/:taskId` |
| `/api/events/pending` | GET | `/events/pending` |

### H) Community Flows (actual current paths)

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/communities/api/communities/explore` | GET | `/communities/explore` |
| `/api/communities/api/communities/create` | POST | `/communities/create` |
| `/api/communities/api/communities/view/<community_id>` | GET | `/communities/:communityId` |
| `/api/communities/api/communities/join/<community_id>` | POST | `/communities/:communityId` |
| `/api/communities/api/communities/message/<community_id>` | POST | `/communities/:communityId` |
| `/api/communities/api/communities/<community_id>/tasks` | GET | `/communities/:communityId/tasks` |
| `/api/communities/api/communities/<community_id>/tasks/create` | POST | `/communities/:communityId/tasks` |

### I) Personnel Flows (actual current paths)

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/personnel/api/personnel/dashboard` | GET | `/personnel/dashboard` |
| `/api/personnel/api/personnel/students` | GET | `/personnel/students` |
| `/api/personnel/api/personnel/whitelist` | GET | `/personnel/whitelist` |
| `/api/personnel/api/personnel/whitelist/add-single` | POST | `/personnel/whitelist` |
| `/api/personnel/api/personnel/whitelist/bulk-add` | POST | `/personnel/whitelist` |
| `/api/personnel/api/personnel/whitelist/remove/<email_id>` | POST | `/personnel/whitelist` |
| `/api/personnel/api/personnel/profile` | GET | `/personnel/profile` |
| `/api/personnel/api/personnel/college/email-config` | GET, PATCH | `/personnel/college/email-config` |

### J) Admin Flows (actual current paths)

| Backend endpoint | Methods | Suggested frontend page |
|---|---|---|
| `/api/admin/api/admin/user-stats/<user_id>` | GET | `/admin/users/:userId` |
| `/api/admin/api/admin/penalty/<user_id>` | POST | `/admin/users/:userId/moderation` |
| `/api/admin/api/admin/bonus/<user_id>` | POST | `/admin/users/:userId/rewards` |
| `/api/admin/api/admin/skill-xp/<user_id>` | POST | `/admin/users/:userId/rewards` |
| `/api/admin/api/admin/bulk-bonus` | POST | `/admin/rewards/bulk` |

---

## Concrete Deduplicated Frontend Page List

1. `/`
2. `/auth`
3. `/college/register`
4. `/college/admin-login`
5. `/dashboard`
6. `/dashboard/profile`
7. `/dashboard/college`
8. `/questionnaire`
9. `/profile`
10. `/profile/:userId`
11. `/profile/xp-history`
12. `/profile/skills`
13. `/profile/scoring`
14. `/profile/scoring-history`
15. `/leaderboard`
16. `/leaderboard/skills/:skill`
17. `/projects`
18. `/projects/new`
19. `/projects/:projectId`
20. `/projects/:projectId/edit`
21. `/projects/:projectId/members`
22. `/events`
23. `/events/create`
24. `/events/pending`
25. `/events/:eventId`
26. `/events/:eventId/participants`
27. `/events/:eventId/tasks`
28. `/events/tasks/:taskId`
29. `/communities/explore`
30. `/communities/create`
31. `/communities/:communityId`
32. `/communities/:communityId/tasks`
33. `/personnel/dashboard`
34. `/personnel/students`
35. `/personnel/whitelist`
36. `/personnel/profile`
37. `/personnel/college/email-config`
38. `/admin/users/:userId`
39. `/admin/users/:userId/rewards`
40. `/admin/users/:userId/moderation`
41. `/admin/rewards/bulk`

---

## Implementation Status (This pass)

Planned in this implementation pass:

- add shared composition infrastructure (context + form + shell)
- keep existing pages operational (no page migration yet)
- prepare for page-by-page rollout when requested

Not included in this pass:

- creating/migrating route pages listed above
- changing backend route registration/prefix behavior
