# Folder Audit (Living Document)

## Audit Protocol
- Status: In progress (multi-session).
- Rule: Only evidence-backed findings are recorded; probable risks are clearly labeled.
- Scope depth: Recursive.
- Severity scale: Critical / High / Medium / Low.

---

## Post-Remediation Status (2026-02-20)

The following workstreams from `docs/folder_audit_fix_plan.md` were applied on 2026-02-20:

| Workstream | Description | Status |
|------------|-------------|--------|
| A | SPA API boundary — all /api/* routes JSON-only, SSR moved to /legacy/* | ✅ Done |
| B | Auth 401 interceptor — no redirect on auth endpoint 401s | ✅ Done |
| C | Whitelist multi-tenancy — check/mark functions scoped to college_id | ✅ Done |
| D | Event dual identity — created_by_user_id + created_by_personnel_id FKs, nullable created_by | ✅ Done |
| E | Event state machine — can_transition() helper, replaced hardcoded checks | ✅ Done |
| F | Constants/schema — LEVEL_FORMULA_DIVISOR in models, bool rejection, min_items=1 | ✅ Done |
| G | Frontend test handlers — MSW validate-email returns correct {valid, is_registered, ...} shape | ✅ Done |
| H | Test coverage — personnel token fix, community paths, auth assertions, test_events.py added | ✅ Done |
| I | Migration — Path I-B taken (DB pre-populated); migration 0797b04af0db added for D1 FKs | ✅ Done (partial — test conftest still uses create_all) |

**DB State (as of 2026-02-20):**
- All tables exist in dev DB (created historically via db.create_all() + manual stamp)
- Alembic version stamped at db67220b1b6b (initial_migration) when dev DB was first populated
- New head: 0797b04af0db (add_event_dual_identity_fks), chained from db67220b1b6b
- For a fresh install: `flask db stamp db67220b1b6b && flask db upgrade`
- The legacy broken revision chain (65e2fad77c17 duplicate tables etc.) remains but is bypassed by the stamp approach

---

## Folder: `backend/app/models` (Audit Pass 1)
- Audit date: 2026-02-20
- Folder status: Partially complete (cross-folder context still open)
- Syntax/diagnostics: No immediate errors from editor diagnostics on models folder.

### 1) Severity-Categorized Findings

#### High
- Concrete violation: route layer directly accesses models instead of delegating to services, contrary to stated contract.
  - Re-audit (2026-02-20): ❌ Still open.
  - [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py#L6-L8)
  - [backend/app/routes/dashboard_routes.py](backend/app/routes/dashboard_routes.py#L4-L6)
  - [backend/app/routes/profile_routes.py](backend/app/routes/profile_routes.py#L10-L14)
  - [backend/app/routes/admin_routes.py](backend/app/routes/admin_routes.py#L10-L11)
  - [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py#L46)

#### Medium
- Concrete defect: `join_community` does not call eligibility guard (`can_user_join`), so college restriction/full/archived checks are bypassable in current flow.
  - Re-audit (2026-02-20): ✅ Fixed. `join_community` now calls `can_user_join` before insert.
  - Join flow: [backend/app/services/community_service.py](backend/app/services/community_service.py#L434-L470)
  - Guard logic: [backend/app/services/community_service.py](backend/app/services/community_service.py#L505-L534)
- Probable risk: mutable JSON list updates (`completed_actions`) may not always dirty-track without mutable helpers.
  - Re-audit (2026-02-20): ✅ Improved/Fix in practice. Updates now reassign list values (non in-place mutation), which reliably marks dirty state.
  - Mutation path: [backend/app/models/task_completion.py](backend/app/models/task_completion.py#L27-L107)

#### Low
- Probable risk: denormalized membership counter (`current_member_count`) can drift under concurrent joins/leaves.
  - Re-audit (2026-02-20): ❌ Still open (counter remains denormalized).
  - Counter model logic: [backend/app/models/community.py](backend/app/models/community.py#L32-L86)
  - Increment call: [backend/app/services/community_service.py](backend/app/services/community_service.py#L464)
- Probable risk: mixed timestamp strategy (`server_default=now()` in `College` vs UTC-aware Python timestamps elsewhere).
  - Re-audit (2026-02-20): ✅ Fixed. `College.created_at` now uses UTC-aware Python timestamp lambda.
  - [backend/app/models/college.py](backend/app/models/college.py#L24)
  - [backend/app/models/user.py](backend/app/models/user.py#L71-L76)

### 2) Connectivity Map (Model file → referenced in)

> Mapping is based on direct import statements (`from app.models.<file> ...`) across backend Python files.

#### Core identity
- `college.py` → setup scripts, app init, auth/admin/dashboard routes, auth/personnel/email/whitelist services, tests.
- `college_personnel.py` → setup scripts, app init, personnel/email/unified-auth services, tests.
- `user.py` → app init, many routes (admin/dashboard/leaderboard/personnel/profile/scoring), most core services, tests/scripts.
- `whitelisted_email.py` → setup scripts, app init, personnel route, email/whitelist services, tests.

#### Community domain
- `community.py` → app init, community route/service, gamification helper, tests.
- `community_member.py` → app init, community route/service, tests.
- `community_message.py` → app init, community route/service, tests.
- `community_task.py` → app init, community route/service, examples, tests.
- `community_moderator.py` → app init, community service, gamification helper.
- `community_poll.py` → app init, tests/factories.
- `community_file.py` → app init.
- `task_completion.py` → app init, community service.

#### Project domain
- `project.py` → app init, project route/service, tests.
- `project_member.py` → app init, project route/service.
- `project_language.py` → app init, project service.
- `language.py` → project/event/language services, tests/factories.
- `user_language.py` → app init, event/language services, tests/factories.

#### Scoring/Gamification
- `scoring.py` → app init, dashboard/scoring routes, project/scoring services, tests.
- `scoring_history.py` → app init, scoring route/service, tests.
- `user_skill.py` → app init, leaderboard route, skill service, gamification helper, tests.
- `xp_transaction.py` → app init, admin/profile routes, xp service, tests.

#### Events
- `event_models.py` → app init, event service.

### 3) High-signal cross-file notes for later folder audits
- `backend/app/routes` likely needs a refactor pass to re-align with the stated route→service dependency contract.
- `backend/app/services/community_service.py` should be revisited in its own folder audit for concurrency-safe joins and eligibility enforcement.
- Event and community tasks share a "JSON actions" pattern; verify consistency in validation and persistence when `services/event_service.py` and related routes are audited.

### 4) Next expected updates to this doc
- Add per-model references from non-import usage paths (query-only/class attribute access where relevant).
- Link discrepancies to specific migration definitions (`backend/migrations/versions`) when schema drift is suspected.
- Append remediation guidance only when requested in a follow-up session.

---

## Folder: `backend/app/routes` (Audit Pass 1)
- Audit date: 2026-02-20
- Folder status: Partially complete (cross-folder context still open)
- Syntax/diagnostics: No immediate editor diagnostics.

### 1) Severity-Categorized Findings

#### Critical
- Concrete runtime defect: participant serialization uses a non-existent attribute (`participant.participant_id`), while model field is `id`; this can fail event participant responses.
  - Re-audit (2026-02-20): ✅ Fixed. Serializer now uses `participant.id`.
  - Route serializer: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L594)
  - Model field: [backend/app/models/event_models.py](backend/app/models/event_models.py#L123)

#### High
- Concrete authorization bug: personnel id is passed where service expects college id for event authority checks, causing incorrect authorization outcomes.
  - Re-audit (2026-02-20): ✅ Fixed. Routes now pass `personnel.college_id` to authority methods.
  - Route pass-through: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L132), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L170), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L199), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L235)
  - Service contract expects `authority_college_id`: [backend/app/services/event_service.py](backend/app/services/event_service.py#L207-L214), [backend/app/services/event_service.py](backend/app/services/event_service.py#L253-L260), [backend/app/services/event_service.py](backend/app/services/event_service.py#L301-L321), [backend/app/services/event_service.py](backend/app/services/event_service.py#L357-L377)
- Concrete architectural violation: many route modules execute direct model/DB queries instead of thin route → service delegation.
  - Re-audit (2026-02-20): ❌ Still open in multiple modules.
  - Examples: [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py#L66-L73), [backend/app/routes/dashboard_routes.py](backend/app/routes/dashboard_routes.py#L23-L27), [backend/app/routes/profile_routes.py](backend/app/routes/profile_routes.py#L33), [backend/app/routes/admin_routes.py](backend/app/routes/admin_routes.py#L77), [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py#L333-L345)

#### Medium
- Concrete robustness issue: unguarded integer parsing on profile query params can raise `ValueError` and return 500 for invalid `limit` values.
  - Re-audit (2026-02-20): ✅ Fixed. `request.args.get(..., type=int)` is now used with bounds.
  - [backend/app/routes/profile_routes.py](backend/app/routes/profile_routes.py#L124)
  - [backend/app/routes/profile_routes.py](backend/app/routes/profile_routes.py#L234)
- Concrete consistency issue: legacy auth/college routes create JWTs but discard them (not returned/stored), while app is configured for header tokens; logout clears JWT cookies despite header-token mode.
  - Re-audit (2026-02-20): ✅ Fixed. Legacy routes no longer mint/discard JWTs and no longer clear JWT cookies in header-token mode.
  - Header token config: [backend/app/__init__.py](backend/app/__init__.py#L23)
  - Token created then dropped: [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L46), [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L138), [backend/app/routes/college_auth_routes.py](backend/app/routes/college_auth_routes.py#L22), [backend/app/routes/college_auth_routes.py](backend/app/routes/college_auth_routes.py#L102)
  - Cookie-clearing in header mode: [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L155), [backend/app/routes/college_auth_routes.py](backend/app/routes/college_auth_routes.py#L76), [backend/app/routes/college_auth_routes.py](backend/app/routes/college_auth_routes.py#L176)

#### Low
- API-surface inconsistency: multiple `/api/*` routes still render templates/flash/redirect (HTML flow), while other routes return JSON API contracts.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). community_routes, scoring_routes, personnel_dashboard_routes converted to JSON. auth_routes and college_auth_routes moved to /legacy/ prefix.
  - [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py#L2), [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py#L54), [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py#L351)
  - [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py#L19-L24), [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py#L82-L84)
  - [backend/app/routes/personnel_dashboard_routes.py](backend/app/routes/personnel_dashboard_routes.py#L67), [backend/app/routes/personnel_dashboard_routes.py](backend/app/routes/personnel_dashboard_routes.py#L80)

### 2) Connectivity Map (Route file → connected to)

#### Registration (application wiring)
- All route blueprints are registered in [backend/app/__init__.py](backend/app/__init__.py#L114-L126).

#### Route module dependencies (services/models)
- `event_routes.py` → `EventService`, JWT helpers (`get_user_id_or_error`, `get_personnel_id_or_error`).
- `project_routes.py` → `ProjectService`, project enums/models, direct `db.session.get(Project, ...)`.
- `scoring_routes.py` → `ScoringService`, direct `UserScoring/ScoringHistory/User` model operations.
- `profile_routes.py` → `XPService`, `SkillService`, `StreakService`, `User`, `XPTransaction`.
- `leaderboard_routes.py` → `XPService`, `SkillService`, `StreakService`, `User`, `UserSkill`.
- `community_routes.py` → `CommunityService` + direct `Community/CommunityMember/CommunityMessage` queries.
- `dashboard_routes.py` → direct `User/College/UserScoring` queries.
- `admin_routes.py` → `XPService`, `SkillService`, direct `User/College/XPTransaction` usage.
- `auth_routes.py` / `college_auth_routes.py` / `personnel_dashboard_routes.py` → mixed service+template routes.

#### External references (consumers)
- Frontend usage currently found for unified auth endpoints through `api` client in [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx#L26-L53).
- Frontend mock handlers also reference unified auth endpoints in [frontend/src/test/handlers.js](frontend/src/test/handlers.js#L4-L21).
- Backend route coverage references are concentrated in tests such as [backend/tests/test_projects.py](backend/tests/test_projects.py), [backend/tests/test_auth.py](backend/tests/test_auth.py), [backend/tests/test_leaderboard.py](backend/tests/test_leaderboard.py), [backend/tests/test_questionnaire.py](backend/tests/test_questionnaire.py).

### 3) High-signal cross-file notes for later folder audits
- `backend/app/services/event_service.py` should be audited next for authority-id handling and event participant serialization consumers.
- `backend/app/utils/jwt_helpers.py` should be audited for identity normalization consistency across HTML and JSON helpers.
- `frontend/src/context/AuthContext.jsx` and related API layers should be audited against actual route contracts because frontend currently references only a subset of route surface.

---

## Folder: `backend/app/services` (Audit Pass 1)
- Audit date: 2026-02-20
- Folder status: Partially complete (cross-folder context still open)
- Syntax/diagnostics: No immediate editor diagnostics.

### 1) Severity-Categorized Findings

#### High
- Concrete data-integrity bug (multi-tenant scope mismatch): whitelist lookups/mutations use `email` only, while schema uniqueness is `(email, college_id)`.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). check_if_whitelisted now takes email, college_id. mark_email_registered now takes email, college_id, user_id. unified_auth_service uses email_validation['college_id'] as validated_college_id. Legacy auth_routes.py call updated to pass college_id.
  - Service queries by email only: [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py#L221), [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py#L239)
  - Schema allows same email across colleges: [backend/app/models/whitelisted_email.py](backend/app/models/whitelisted_email.py#L44)
  - Call path that triggers this behavior: [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py#L304)
- Concrete eligibility-enforcement bug (service layer): `join_community` path does not invoke `can_user_join`, so full/inactive/archived/college-specific checks are bypassed.
  - Re-audit (2026-02-20): ✅ Fixed. Guard is now invoked in `join_community`.
  - Join method: [backend/app/services/community_service.py](backend/app/services/community_service.py#L434)
  - Eligibility guard exists separately: [backend/app/services/community_service.py](backend/app/services/community_service.py#L510)

#### Medium
- Probable repository hygiene risk: backup implementation file exists in active service directory (`scoring_service.py.bak`), increasing accidental divergence/confusion risk during edits/reviews.
  - Re-audit (2026-02-20): ❌ Still open (`backend/app/services/scoring_service.py.bak` still present).
  - File present in services listing: [backend/app/services](backend/app/services)
- Probable operational fragility: scoring service hard-fails when `GEMINI_API_KEY` is missing, making questionnaire scoring unavailable at runtime unless env is correctly provisioned.
  - Re-audit (2026-02-20): ❌ Still open.
  - Key requirement and client init: [backend/app/services/scoring_service.py](backend/app/services/scoring_service.py#L65-L75)

#### Low
- Probable timezone-window drift risk: daily cap/streak logic mixes `date.today()` and DB `func.date(...)`, which may diverge near day boundaries depending on DB/session timezone.
  - Re-audit (2026-02-20): ❌ Still open.
  - Streak date boundaries: [backend/app/services/streak_service.py](backend/app/services/streak_service.py#L42), [backend/app/services/streak_service.py](backend/app/services/streak_service.py#L273)
  - XP cap/date filters: [backend/app/services/xp_service.py](backend/app/services/xp_service.py#L294-L299), [backend/app/services/xp_service.py](backend/app/services/xp_service.py#L334-L339)

### 2) Connectivity Map (Service file → connected to)

#### Auth and identity services
- `auth_services.py` → used by auth/community routes and unified auth service.
- `college_auth_services.py` → used by college auth routes.
- `college_personnel_services.py` → used by setup script, personnel/college routes, unified auth service, personnel tests.
- `email_validation_service.py` → used by auth, college auth, unified auth routes, and unified auth service.
- `unified_auth_service.py` → used by unified auth routes.

#### Community/project/event services
- `community_service.py` → used by community routes and community tests.
- `event_service.py` → used by event routes.
- `project_service.py` → used by project routes.
- `language_proficiency_service.py` → used by project service.

#### Scoring/gamification services
- `scoring_service.py` → used by scoring routes and scoring service tests.
- `xp_service.py` → used by admin/auth/leaderboard/profile routes and community/event/project/streak/unified-auth services.
- `skill_service.py` → used by admin/leaderboard/profile routes and gamification tests.
- `streak_service.py` → used by auth/leaderboard/profile routes and unified-auth service.
- `whitelist_service.py` → used by setup/auth/personnel flows and unified-auth service.

### 3) High-signal cross-file notes for later folder audits
- `backend/app/routes/event_routes.py` and `backend/app/services/event_service.py` should be reviewed together for personnel identity vs college authority mapping.
- `backend/app/services/whitelist_service.py` and `backend/app/models/whitelisted_email.py` should be treated as a single correction unit due to `(email, college_id)` semantics.
- `backend/app/services/scoring_service.py` and deployment/environment docs should be audited together to ensure Gemini key requirements are explicit and enforced.

---

## Folder: `backend/app/utils` (Audit Pass 1)
- Audit date: 2026-02-20
- Folder status: Partially complete (cross-folder context still open)
- Syntax/diagnostics: No immediate editor diagnostics.

### 1) Severity-Categorized Findings

#### High
- Concrete contract mismatch in helper semantics: `get_college_id_or_redirect()` currently validates `personnel_` identity and returns personnel id, not college id, despite the function name and redirect text indicating college semantics.
  - Re-audit (2026-02-20): ✅ Fixed. Helper was removed/refactored; event/personnel callers now use explicit personnel helpers.
  - Implementation: [backend/app/utils/jwt_helpers.py](backend/app/utils/jwt_helpers.py#L29-L45)
  - Caller-facing error text: [backend/app/utils/jwt_helpers.py](backend/app/utils/jwt_helpers.py#L35)

#### Medium
- Concrete maintainability issue: duplicate imports in `jwt_helpers.py` (`flash`, `redirect`, `url_for` imported twice from Flask).
  - Re-audit (2026-02-20): ✅ Fixed.
  - [backend/app/utils/jwt_helpers.py](backend/app/utils/jwt_helpers.py#L1-L5)
- Concrete dead-code signal: `login_required` decorator utility currently has no imports/usages in backend code paths.
  - Re-audit (2026-02-20): ❌ Still open (no consumers found).
  - Definition: [backend/app/utils/decorators.py](backend/app/utils/decorators.py#L10)
  - Usage search result: no `from app.utils.decorators import ...` consumers found.

#### Low
- Probable standards/coverage drift: `gamification_helpers.py` contains usage examples referencing `admin_required` import from the same module, but that decorator is explicitly removed in this file.
  - Re-audit (2026-02-20): ✅ Fixed/improved. Stale in-file example reference is removed.
  - Removal note: [backend/app/utils/gamification_helpers.py](backend/app/utils/gamification_helpers.py#L13-L18)
  - Example reference: [backend/app/utils/gamification_helpers.py](backend/app/utils/gamification_helpers.py#L351)
- Probable validation strictness risk: `is_valid_email` regex rejects multiple RFC-valid address patterns (e.g., `+` in local part), potentially causing false negatives for legitimate users.
  - Re-audit (2026-02-20): ❌ Still open.
  - Regex implementation: [backend/app/utils/validators.py](backend/app/utils/validators.py#L8-L13)

### 2) Connectivity Map (Utils file → connected to)

#### `jwt_helpers.py`
- Imported by route modules:
  - [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py#L9)
  - [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py#L14)
  - [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L37)
- Key helper call sites include multiple student/personnel identity gates in event routes (e.g., [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L66-L71), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L232-L239)).

#### `validators.py`
- Imported/used by auth routes:
  - [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L3)
  - Field checks: [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L21), [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L80), [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L84)

#### `decorators.py`
- No current backend consumers found for `login_required`; module appears present but not integrated with active route decorators.

#### `gamification_helpers.py`
- No active backend imports found outside the module itself; references are mostly internal helper definitions and in-file usage examples.

### 3) High-signal cross-file notes for later folder audits
- `backend/app/routes/event_routes.py` and `backend/app/utils/jwt_helpers.py` should be audited together for identity naming and authority mapping consistency.
- `backend/app/routes/auth_routes.py` and `backend/app/utils/validators.py` should be reviewed together to confirm email validation policy (strict vs permissive) aligns with product requirements.
- If `decorators.py` is intentionally deprecated, consider repository cleanup/archival policy in a separate maintenance session.

---

## Folder: `backend/migrations/versions` (Audit Pass 1)
- Audit date: 2026-02-20
- Folder status: Complete for current revision set (schema/runtime validation against live DB still pending)
- Syntax/diagnostics: No immediate editor diagnostics.

### 1) Severity-Categorized Findings

#### Critical
- Concrete migration-chain break: `65e2fad77c17` re-creates `communities` and `community_members` that were already created earlier in chain by `605332d6dad9`; running upgrades on a normal linear DB state will fail with duplicate relation errors.
  - Re-audit (2026-02-20): ⚠️ Still exists in archive. Dev DB bypassed this via db.create_all() + stamp. New installs must use: flask db stamp head; flask db upgrade. Forward migration 0797b04af0db added for D1 schema.
  - First creation: [backend/migrations/versions/605332d6dad9_add_community_tables.py](backend/migrations/versions/605332d6dad9_add_community_tables.py#L21), [backend/migrations/versions/605332d6dad9_add_community_tables.py](backend/migrations/versions/605332d6dad9_add_community_tables.py#L32)
  - Duplicate creation later in chain: [backend/migrations/versions/65e2fad77c17_remove_flask_login_add_relationships.py](backend/migrations/versions/65e2fad77c17_remove_flask_login_add_relationships.py#L21), [backend/migrations/versions/65e2fad77c17_remove_flask_login_add_relationships.py](backend/migrations/versions/65e2fad77c17_remove_flask_login_add_relationships.py#L32)
- Concrete base-schema defect: initial revision defines FK from `user_interests.interest_id` to `interests.id`, but no `interests` table is created in this migration set.
  - Re-audit (2026-02-20): ⚠️ Still exists. Bypassed in dev via db.create_all(). user_interests table not present in live DB.
  - FK reference: [backend/migrations/versions/57edbf52e693_initial_schema.py](backend/migrations/versions/57edbf52e693_initial_schema.py#L45)
  - Table declaration using that FK: [backend/migrations/versions/57edbf52e693_initial_schema.py](backend/migrations/versions/57edbf52e693_initial_schema.py#L42)
- Concrete head-revision break: latest revision `01368659de48` is authored as a full schema bootstrap while still chained to prior revisions (`down_revision = 1a0df92c997d`), so it attempts to create already-existing core tables (`colleges`, `users`, `communities`, etc.) and is not safely incremental.
  - Re-audit (2026-02-20): ⚠️ Still exists. Bypassed in dev. New incremental migration 0797b04af0db is now the actual head (chained from db67220b1b6b).
  - Example duplicate creates in head revision: [backend/migrations/versions/01368659de48_events_module_v1.py](backend/migrations/versions/01368659de48_events_module_v1.py#L21), [backend/migrations/versions/01368659de48_events_module_v1.py](backend/migrations/versions/01368659de48_events_module_v1.py#L66), [backend/migrations/versions/01368659de48_events_module_v1.py](backend/migrations/versions/01368659de48_events_module_v1.py#L91)

#### High
- Concrete schema drift (auth/whitelist): migrations enforce global unique email in `whitelisted_emails`, while model contract is per-college unique `(email, college_id)`.
  - Re-audit (2026-02-20): ❌ Still open.
  - Migration uniqueness: [backend/migrations/versions/9b69ae95562e_enhanced_auth_system.py](backend/migrations/versions/9b69ae95562e_enhanced_auth_system.py#L59)
  - Model uniqueness contract: [backend/app/models/whitelisted_email.py](backend/app/models/whitelisted_email.py#L44)
- Concrete enum-shape drift risk in project domain: `1a0df92c997d` uses mixed/title/lower-case enum values for `project_*` types, while head revision uses uppercase variants for same enum names; this is incompatible if both are treated as sequential schema evolution.
  - Re-audit (2026-02-20): ❌ Still open.
  - Earlier enum values: [backend/migrations/versions/1a0df92c997d_add_project_tables.py](backend/migrations/versions/1a0df92c997d_add_project_tables.py#L35), [backend/migrations/versions/1a0df92c997d_add_project_tables.py](backend/migrations/versions/1a0df92c997d_add_project_tables.py#L39), [backend/migrations/versions/1a0df92c997d_add_project_tables.py](backend/migrations/versions/1a0df92c997d_add_project_tables.py#L43)
  - Head enum values: [backend/migrations/versions/01368659de48_events_module_v1.py](backend/migrations/versions/01368659de48_events_module_v1.py#L145), [backend/migrations/versions/01368659de48_events_module_v1.py](backend/migrations/versions/01368659de48_events_module_v1.py#L146), [backend/migrations/versions/01368659de48_events_module_v1.py](backend/migrations/versions/01368659de48_events_module_v1.py#L147)

#### Medium
- Probable portability risk: head revision uses `op.drop_column(..., if_exists=True)`; this keyword support is version/backend dependent and can fail on some Alembic stacks.
  - Re-audit (2026-02-20): ❌ Still open.
  - [backend/migrations/versions/01368659de48_events_module_v1.py](backend/migrations/versions/01368659de48_events_module_v1.py#L415)

#### Low
- Concrete metadata inconsistency: `c1f2b3d4e5f6` docstring `Revises:` value conflicts with actual `down_revision`, which increases audit confusion even if runtime chain still follows `down_revision`.
  - Re-audit (2026-02-20): ❌ Still open.
  - Docstring `Revises`: [backend/migrations/versions/c1f2b3d4e5f6_add_is_admin_field_to_users.py](backend/migrations/versions/c1f2b3d4e5f6_add_is_admin_field_to_users.py#L4)
  - Actual chain field: [backend/migrations/versions/c1f2b3d4e5f6_add_is_admin_field_to_users.py](backend/migrations/versions/c1f2b3d4e5f6_add_is_admin_field_to_users.py#L14)

### 2) Connectivity Map (Revision chain + domain touchpoints)

#### Linear revision chain discovered
- `57edbf52e693` → `9dddde00badc` → `605332d6dad9` → `176c545bc015` → `586fc7775ccb` → `65e2fad77c17` → `3c69ec1dc0e9` → `b1080a66c1e3` → `7e1ed7123058` → `9b69ae95562e` → `c1f2b3d4e5f6` → `1fa9e77999fa` → `b64ed5c64904` → `1a0df92c997d` → `01368659de48`

#### Domain coupling verified during migration audit
- Community domain tables evolve across `605332d6dad9`, `65e2fad77c17`, `3c69ec1dc0e9`, `b1080a66c1e3`, and are then re-bootstraped in `01368659de48`.
- Events/gamification tables originate in `b1080a66c1e3` and `7e1ed7123058`, then are recreated in `01368659de48`.
- Auth/whitelist schema originates in `9b69ae95562e` and conflicts with model-level uniqueness contract used by current service layer.

### 3) High-signal cross-file notes for later folder audits
- Event identity/authority chain audit should proceed next: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py), [backend/app/utils/jwt_helpers.py](backend/app/utils/jwt_helpers.py), [backend/app/services/event_service.py](backend/app/services/event_service.py).
- Whitelist chain audit should proceed after event chain: [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py), [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py), [backend/app/models/whitelisted_email.py](backend/app/models/whitelisted_email.py).

---

## Focused Chain: `event` identity/authority flow (Pass 1)
- Audit date: 2026-02-20
- Scope: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py), [backend/app/utils/jwt_helpers.py](backend/app/utils/jwt_helpers.py), [backend/app/services/event_service.py](backend/app/services/event_service.py), [backend/app/models/event_models.py](backend/app/models/event_models.py)
- Status: Partially complete (schema fix not applied; runtime behavior still at risk for personnel-created events)

### 1) Severity-Categorized Findings

#### Critical
- Concrete identity-model mismatch: personnel path passes `personnel_id` as `creator_id`, but service persists that value into `Event.created_by`, which is a FK to `users.id`. This is structurally incompatible unless ids coincidentally overlap across tables.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). Added created_by_user_id and created_by_personnel_id FKs to Event model. create_event service now populates correct field based on creator type. created_by made nullable.
  - Personnel caller id assignment: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L71)
  - Service persistence: [backend/app/services/event_service.py](backend/app/services/event_service.py#L131)
  - Model FK target: [backend/app/models/event_models.py](backend/app/models/event_models.py#L46)
- Concrete dead-path for college-created events: personnel can create events, but submit route is student-only (`get_user_id_or_error`), so personnel creators cannot execute the submit/publish flow that transitions their draft events.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). Submit route now accepts both user and personnel callers via dual-caller pattern.
  - Create route accepts personnel branch: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L66-L72)
  - Submit route requires student identity helper: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L104)

#### High
- Concrete contract drift between route docs and service behavior: route comment says creator type is forced for personnel, but service accepts `creator_type` from payload and does not enforce personnel-specific coercion.
  - Re-audit (2026-02-20): ❌ Still open.
  - Route expectation comment: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L56-L58)
  - Service reads payload creator type directly: [backend/app/services/event_service.py](backend/app/services/event_service.py#L82)

#### Medium
- Concrete implementation/style mismatch in helper naming: `get_personnel_id_or_redirect` returns JSON tuple responses (not redirects), making helper intent ambiguous for future callers.
  - Re-audit (2026-02-20): ❌ Still open.
  - Function name + behavior mismatch: [backend/app/utils/jwt_helpers.py](backend/app/utils/jwt_helpers.py#L28-L47)

#### Low
- Verified improvement versus prior audit state: authority calls now pass `personnel.college_id` to service methods (`approve/reject/cancel/complete/pending`), matching service contract (`authority_college_id`).
  - Re-audit (2026-02-20): ✅ Still valid improvement.
  - Route pass-through examples: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L138), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L180), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L213), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L252), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L564)
  - Service contract examples: [backend/app/services/event_service.py](backend/app/services/event_service.py#L207), [backend/app/services/event_service.py](backend/app/services/event_service.py#L253), [backend/app/services/event_service.py](backend/app/services/event_service.py#L301), [backend/app/services/event_service.py](backend/app/services/event_service.py#L357), [backend/app/services/event_service.py](backend/app/services/event_service.py#L1047)

### 2) Connectivity Map (identity resolution → service authority gate)
- JWT identity parsing helpers:
  - Student: [backend/app/utils/jwt_helpers.py](backend/app/utils/jwt_helpers.py#L50-L69)
  - Personnel: [backend/app/utils/jwt_helpers.py](backend/app/utils/jwt_helpers.py#L72-L93)
- Route-level identity branching:
  - Dual caller split: [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L64-L76), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L202-L219), [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py#L241-L258)
- Service-level authority enforcement:
  - College authority checks against `event.college_id`: [backend/app/services/event_service.py](backend/app/services/event_service.py#L231), [backend/app/services/event_service.py](backend/app/services/event_service.py#L277), [backend/app/services/event_service.py](backend/app/services/event_service.py#L341), [backend/app/services/event_service.py](backend/app/services/event_service.py#L390)

### 3) High-signal cross-file notes for next chain
- Whitelist chain remains next likely source of auth onboarding inconsistencies due prior-confirmed uniqueness scope drift and mixed lookup keys.

---

## Focused Chain: `whitelist` onboarding flow (Pass 1)
- Audit date: 2026-02-20
- Scope: [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py), [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py), [backend/app/services/email_validation_service.py](backend/app/services/email_validation_service.py), [backend/app/models/whitelisted_email.py](backend/app/models/whitelisted_email.py), [backend/app/routes/unified_auth_routes.py](backend/app/routes/unified_auth_routes.py)
- Status: Partially complete (logic risks identified; no corrective patch applied)

### 1) Severity-Categorized Findings

#### High
- Concrete college-binding integrity gap: student signup validates email/whitelist against detected college, but account creation uses client-supplied `college_id` instead of validated `email_validation['college_id']`. This can create users in a different college than the whitelist-college context.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). unified_auth_service now uses email_validation['college_id'] as validated_college_id.
  - Validation call: [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py#L271)
  - User creation with client `college_id`: [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py#L287-L293)
  - Validation returns scoped college id from whitelist check: [backend/app/services/email_validation_service.py](backend/app/services/email_validation_service.py#L110-L135)
- Concrete scope mismatch in registration marking: whitelist registration update is keyed by `email` only (no `college_id`), conflicting with per-college uniqueness contract and potentially updating wrong row in multi-college duplicates.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). mark_email_registered now takes email, college_id, user_id.
  - Call site: [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py#L304)
  - Email-only mutation query: [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py#L239)
  - Model uniqueness contract: [backend/app/models/whitelisted_email.py](backend/app/models/whitelisted_email.py#L44)

#### Medium
- Concrete scope mismatch in lookup helper: `check_if_whitelisted` uses `email` only; in multi-tenant schema this helper cannot disambiguate rows by college.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). check_if_whitelisted now takes email, college_id.
  - [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py#L221)
- Probable flow inconsistency between unified and legacy auth paths: legacy auth signup also marks whitelist registration by email only, carrying same ambiguity as unified flow.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). Legacy auth_routes.py call updated to pass college_id.
  - Legacy call site: [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L124)

#### Low
- Concrete positive alignment: add/bulk-add operations now check duplicates by `(email, college_id)`, which matches model contract for insertion paths.
  - Re-audit (2026-02-20): ✅ Still valid alignment.
  - Single add duplicate scope: [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py#L41)
  - Bulk add duplicate scope: [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py#L114)

### 2) Connectivity Map (validate → signup → whitelist mutation)
- Realtime email validation route: [backend/app/routes/unified_auth_routes.py](backend/app/routes/unified_auth_routes.py#L14-L30)
- User type detection + whitelist validation chain:
  - [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py#L44-L63)
  - [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py#L110)
  - [backend/app/services/email_validation_service.py](backend/app/services/email_validation_service.py#L110-L135)
- Student signup mutation path:
  - [backend/app/services/unified_auth_service.py](backend/app/services/unified_auth_service.py#L271-L304)
  - [backend/app/services/whitelist_service.py](backend/app/services/whitelist_service.py#L228-L251)

### 3) High-signal cross-file notes for next folders in list
- `backend/app/constants` and `backend/app/schemas` should be audited next to confirm enum/value contracts used by auth/event services are centralized and consistent.

---

## Folder: `backend/app/constants` + `backend/app/schemas` (Audit Pass 1)
- Audit date: 2026-02-20
- Scope: [backend/app/constants/event_constants.py](backend/app/constants/event_constants.py), [backend/app/constants/gamification.py](backend/app/constants/gamification.py), [backend/app/schemas/questionnaire_schema.py](backend/app/schemas/questionnaire_schema.py)
- Status: Complete for current files

### 1) Severity-Categorized Findings

#### Medium
- Concrete contract drift in event state machine usage: service claims transitions are enforced via `VALID_EVENT_TRANSITIONS`, but event lifecycle methods still use direct status equality checks and do not consume `VALID_EVENT_TRANSITIONS` as the source of truth.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). can_transition() helper added to EventService. Submit, approve, reject, cancel, complete methods now use can_transition() instead of hardcoded equality checks.
  - Service claim/import: [backend/app/services/event_service.py](backend/app/services/event_service.py#L12-L13), [backend/app/services/event_service.py](backend/app/services/event_service.py#L33)
  - Hardcoded event checks: [backend/app/services/event_service.py](backend/app/services/event_service.py#L179), [backend/app/services/event_service.py](backend/app/services/event_service.py#L228), [backend/app/services/event_service.py](backend/app/services/event_service.py#L274), [backend/app/services/event_service.py](backend/app/services/event_service.py#L383)
- Concrete central-constant bypass risk: `LEVEL_FORMULA_DIVISOR` is defined centrally, but level formulas in user and skill models hardcode `/100`; changing constant would not propagate.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). user.py and user_skill.py now import and use LEVEL_FORMULA_DIVISOR.
  - Constant definition: [backend/app/constants/gamification.py](backend/app/constants/gamification.py#L75)
  - Hardcoded formulas: [backend/app/models/user.py](backend/app/models/user.py#L133), [backend/app/models/user_skill.py](backend/app/models/user_skill.py#L100)
- Concrete schema validation edge case: integer validation uses `isinstance(value, int)`, which accepts booleans in Python (`True`/`False`), allowing non-numeric intent values into questionnaire numeric fields.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). questionnaire_schema.py now rejects booleans before the int isinstance check.
  - [backend/app/schemas/questionnaire_schema.py](backend/app/schemas/questionnaire_schema.py#L188)

#### Low
- Probable validation looseness: `q2_team_roles` is required and has `max_items=2` but no `min_items`, so an empty list can pass presence/type checks.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). min_items=1 added to q2_team_roles schema definition.
  - Field rules: [backend/app/schemas/questionnaire_schema.py](backend/app/schemas/questionnaire_schema.py#L17-L21)
  - List length enforcement logic: [backend/app/schemas/questionnaire_schema.py](backend/app/schemas/questionnaire_schema.py#L200-L204)

### 2) Connectivity Map (constants/schemas → active consumers)
- Event constants consumer:
  - [backend/app/services/event_service.py](backend/app/services/event_service.py#L28-L36)
- Gamification constants consumers:
  - [backend/app/services/xp_service.py](backend/app/services/xp_service.py#L10-L17)
  - [backend/app/services/streak_service.py](backend/app/services/streak_service.py#L8)
  - [backend/app/services/skill_service.py](backend/app/services/skill_service.py#L9-L14)
  - [backend/app/services/project_service.py](backend/app/services/project_service.py#L23)
  - [backend/app/routes/leaderboard_routes.py](backend/app/routes/leaderboard_routes.py#L13)
- Questionnaire schema consumers:
  - [backend/app/services/scoring_service.py](backend/app/services/scoring_service.py#L19)
  - Validation call path: [backend/app/services/scoring_service.py](backend/app/services/scoring_service.py#L134)

### 3) High-signal cross-file notes for next list item
- Frontend API consumer audit should now compare endpoint contracts used in [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx) and [frontend/src/utils/api.js](frontend/src/utils/api.js) against current backend route responses for event/auth flows.

---

## Folder: `frontend/src` API consumer parity (Audit Pass 1)
- Audit date: 2026-02-20
- Scope: [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx), [frontend/src/pages/Auth.jsx](frontend/src/pages/Auth.jsx), [frontend/src/utils/api.js](frontend/src/utils/api.js), [frontend/src/test/handlers.js](frontend/src/test/handlers.js)
- Status: Complete for current frontend auth consumer surface

### 1) Severity-Categorized Findings

#### High
- Concrete UX/control-flow issue: global Axios response interceptor redirects to `/auth` on any `401`, including expected invalid-credential responses from `/auth/login`. This can interrupt local form-level error handling and cause forced navigation loops.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). Interceptor now skips redirect for auth endpoint 401s (/api/auth/login, /api/auth/signup, /api/auth/validate-email).
  - Interceptor redirect: [frontend/src/utils/api.js](frontend/src/utils/api.js#L28-L31)
  - Login path expects to handle `401` in place: [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx#L47)

#### Medium
- Concrete test contract drift: MSW `validate-email` handler returns `{ success: true, ... }`, while app flow expects backend-style `valid` field (`result.valid`) to decide signup step. This can produce misleading test outcomes.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). handlers.js now returns { valid: true, is_registered: false, user_type: 'student', college_id: 1 }.
  - Consumer decision uses `result.valid`: [frontend/src/pages/Auth.jsx](frontend/src/pages/Auth.jsx#L31-L35)
  - Context pass-through expects backend payload shape: [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx#L27)
  - MSW mock shape mismatch: [frontend/src/test/handlers.js](frontend/src/test/handlers.js#L10)

#### Low
- Scope gap: no active frontend consumer for `/api/events` routes was found, so backend event-route defects currently have low immediate UI blast radius but remain backend/API risks.
  - Re-audit (2026-02-20): ✅ Still valid.
  - Search over `frontend/src/**/*.{js,jsx}` found no `/events` API usage.

### 2) Connectivity Map (frontend auth flow)
- Email step:
  - UI submit: [frontend/src/pages/Auth.jsx](frontend/src/pages/Auth.jsx#L25-L37)
  - API call wrapper: [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx#L24-L35)
- Login/signup step:
  - UI submit: [frontend/src/pages/Auth.jsx](frontend/src/pages/Auth.jsx#L40-L74)
  - API wrappers: [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx#L38-L61)
- Transport/interceptors:
  - [frontend/src/utils/api.js](frontend/src/utils/api.js#L3-L34)

### 3) High-signal cross-file notes for next list item
- Final priority item is backend tests alignment (`backend/tests` + `e2e`) to confirm which of the above defects are already covered vs currently untested.

---

## Folder: `backend/tests` + `e2e` coverage alignment (Audit Pass 1)
- Audit date: 2026-02-20
- Scope: [backend/tests](backend/tests), [backend/tests/conftest.py](backend/tests/conftest.py), [backend/tests/test_auth.py](backend/tests/test_auth.py), [backend/tests/test_community.py](backend/tests/test_community.py), [backend/tests/test_personnel.py](backend/tests/test_personnel.py), [backend/tests/test_questionnaire.py](backend/tests/test_questionnaire.py), [e2e/auth.spec.ts](e2e/auth.spec.ts)
- Status: Complete for current test files

### 1) Severity-Categorized Findings

#### High
- Concrete migration-risk blind spot: test DB lifecycle uses `_db.create_all()` / `_db.drop_all()` instead of running Alembic revisions, so migration chain defects (including current critical chain breaks) are not exercised by tests.
  - Re-audit (2026-02-20): ❌ Still open.
  - [backend/tests/conftest.py](backend/tests/conftest.py#L20-L22)
- Concrete personnel-auth coverage mismatch: `personnel_auth_headers` mints tokens as plain numeric identity rather than `personnel_<id>`, so tests using this fixture do not validate actual production personnel identity parsing.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). conftest.py now uses identity=f”personnel_{personnel_user['id']}”.
  - [backend/tests/conftest.py](backend/tests/conftest.py#L191)
- Coverage gap: no dedicated backend event test module detected under [backend/tests](backend/tests), despite high-risk issues in event identity/authority chain.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). backend/tests/test_events.py added with coverage for dual-identity creation, submit route, state machine transitions, and whitelist multi-tenancy.

#### Medium
- Concrete stale-route tolerance in community tests: auth-check tests target duplicated path segments (`/api/communities/communities/...`) and treat `404` as pass, which can hide regressions in real endpoint wiring.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). test_community.py corrected to /api/communities/create etc., assert exactly 401.
  - [backend/tests/test_community.py](backend/tests/test_community.py#L18-L35)
- Concrete assertion looseness in auth tests: some cases assert broad status sets or only “not 5xx,” reducing signal for contract regressions.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). test_auth.py tightened to exact expected status codes (400 for missing fields, 401 for wrong password).
  - [backend/tests/test_auth.py](backend/tests/test_auth.py#L35)
  - [backend/tests/test_auth.py](backend/tests/test_auth.py#L44)

#### Low
- Probable e2e fragility: auth Playwright scenarios rely on seeded accounts/domains by convention comments, not deterministic test fixtures/setup in-file.
  - Re-audit (2026-02-20): ❌ Still open.
  - [e2e/auth.spec.ts](e2e/auth.spec.ts#L12-L25)

### 2) Connectivity Map (tests → audited risk areas)
- Whitelist path gets direct service coverage in [backend/tests/test_personnel.py](backend/tests/test_personnel.py), but mostly single-college scenarios.
- Questionnaire schema and scoring validation have solid direct coverage in [backend/tests/test_questionnaire.py](backend/tests/test_questionnaire.py) and [backend/tests/test_scoring_service.py](backend/tests/test_scoring_service.py).
- Event identity/authority and migration-chain integrity currently have weak or absent direct test coverage.

### 3) High-signal follow-up recommendation
- Highest-value next action (when you switch from audit to fixes): add migration smoke test using Alembic upgrade path and add event-route auth tests with real `personnel_<id>` token semantics.

---

## Focused Track: Jinja2 → React SPA API boundary (Re-audit Pass 2)
- Audit date: 2026-02-20
- Scope: [backend/app/routes/main_routes.py](backend/app/routes/main_routes.py), [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py), [backend/app/routes/college_auth_routes.py](backend/app/routes/college_auth_routes.py), [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py), [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py), [backend/app/routes/personnel_dashboard_routes.py](backend/app/routes/personnel_dashboard_routes.py), [backend/app/__init__.py](backend/app/__init__.py), [frontend/src/App.jsx](frontend/src/App.jsx), [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx), [frontend/src/utils/api.js](frontend/src/utils/api.js), [frontend/src/test/handlers.js](frontend/src/test/handlers.js)
- Status: Partially complete (unified auth + several JSON routes are aligned, but `/api/*` still mixes API and server-rendered behavior)

### 1) Severity-Categorized Findings

#### Critical
- Concrete SPA-boundary violation: `/api/*` namespace still serves Jinja2/template redirect/flash flows in multiple modules, which conflicts with an API-only backend contract for React SPA migration.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). community_routes, scoring_routes, personnel_dashboard_routes converted to JSON. auth_routes and college_auth_routes moved to /legacy/ prefix.
  - [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py#L19-L49), [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py#L53-L97)
  - [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py#L35-L54)
  - [backend/app/routes/personnel_dashboard_routes.py](backend/app/routes/personnel_dashboard_routes.py#L63-L110)
  - [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L13-L61), [backend/app/routes/college_auth_routes.py](backend/app/routes/college_auth_routes.py#L8-L31)
- Concrete response-contract split: same endpoint path in scoring uses dual behavior (JSON for API callers, redirect/flash for form callers), increasing client ambiguity and regression risk during SPA rollout.
  - Mixed branch on request type: [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py#L56-L185)

#### High
- Concrete auth endpoint surface inconsistency during migration: legacy routes remain mounted under `/api/auth` but expose nested paths (`/api/check-username`, `/api/detect-college`), producing effective endpoints `/api/auth/api/*` while unified flow uses `/api/auth/*`.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). auth_routes moved to /legacy/auth, college_auth_routes to /legacy/college-auth. Nested /api/api/* routes removed.
  - Legacy nested paths: [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L159), [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py#L174)
  - Unified paths: [backend/app/routes/unified_auth_routes.py](backend/app/routes/unified_auth_routes.py#L12-L30), [backend/app/routes/unified_auth_routes.py](backend/app/routes/unified_auth_routes.py#L91-L109)
  - Shared mount context: [backend/app/__init__.py](backend/app/__init__.py#L114-L119)
- Concrete migration coverage gap: React router surface is currently limited (`/`, `/auth`, `/dashboard`), with no active frontend consumers for communities/events/profile/leaderboard/project API domains.
  - SPA routes: [frontend/src/App.jsx](frontend/src/App.jsx#L11-L16)
  - Current API usage concentrated in auth context: [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx#L24-L58)

#### Medium
- Concrete SPA UX risk: Axios global interceptor hard-redirects to `/auth` on any `401`, including expected auth failures that should be handled in-page.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). Interceptor now skips redirect for auth endpoint 401s (/api/auth/login, /api/auth/signup, /api/auth/validate-email).
  - [frontend/src/utils/api.js](frontend/src/utils/api.js#L24-L31)
- Concrete frontend test contract mismatch: MSW `validate-email` mock returns `success/exists` while app logic expects backend `valid/is_registered` semantics for step transitions.
  - Re-audit (2026-02-20): ✅ Fixed (2026-02-20). handlers.js now returns { valid: true, is_registered: false, user_type: 'student', college_id: 1 }.
  - Consumer expectations: [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx#L24-L35), [frontend/src/pages/Auth.jsx](frontend/src/pages/Auth.jsx#L29-L36)
  - Mock shape: [frontend/src/test/handlers.js](frontend/src/test/handlers.js#L4-L10)

### 2) Connectivity Map (SPA migration lanes)
- Lane A — Auth (closest to SPA-ready):
  - Backend: [backend/app/routes/unified_auth_routes.py](backend/app/routes/unified_auth_routes.py)
  - Frontend: [frontend/src/context/AuthContext.jsx](frontend/src/context/AuthContext.jsx), [frontend/src/pages/Auth.jsx](frontend/src/pages/Auth.jsx)
- Lane B — Legacy HTML flows still in API namespace:
  - [backend/app/routes/community_routes.py](backend/app/routes/community_routes.py), [backend/app/routes/scoring_routes.py](backend/app/routes/scoring_routes.py), [backend/app/routes/personnel_dashboard_routes.py](backend/app/routes/personnel_dashboard_routes.py), [backend/app/routes/auth_routes.py](backend/app/routes/auth_routes.py), [backend/app/routes/college_auth_routes.py](backend/app/routes/college_auth_routes.py)
- Lane C — JSON-first domains available but not yet consumed by SPA:
  - [backend/app/routes/event_routes.py](backend/app/routes/event_routes.py), [backend/app/routes/project_routes.py](backend/app/routes/project_routes.py), [backend/app/routes/profile_routes.py](backend/app/routes/profile_routes.py), [backend/app/routes/leaderboard_routes.py](backend/app/routes/leaderboard_routes.py)

### 3) High-signal migration recommendation
- For Jinja2→SPA transition safety, enforce a strict boundary: all `/api/*` routes return JSON only; move remaining template flows to non-API namespace (or retire), and keep React as the only UI renderer.
