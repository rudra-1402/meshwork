# Frontend Reachability Audit — 2026-02-21

## Scope
- Verify frontend pages are reachable through registered routes.
- Check for network-risk API usage patterns (hardcoded hosts, non-canonical calls).
- Catch dead-end links before adding more pages.

## Checks Run
1. Route registration audit in `frontend/src/App.jsx`.
2. API usage grep (`fetch`, `axios`, `api.get/post/...`) under `frontend/src`.
3. Hardcoded host grep (`localhost`, `127.0.0.1`) under `frontend/src`.
4. Path link grep (`to="/..."`, `href="/..."`) under `frontend/src`.
5. Lint + targeted regression tests (`PhaseCPages`).

## Findings
- API risk: no hardcoded backend host in page/context calls; shared API client is used.
- Route risk found and fixed:
  - `/projects/new` linked but not routed.
  - `/projects/:projectId` linked but not routed.
  - `/events/:eventId` linked but not routed.
  - `/communities/:communityId` linked but not routed.

## Fixes Applied
- Added pages:
  - `frontend/src/pages/ProjectsNew.jsx`
  - `frontend/src/pages/ProjectDetail.jsx`
  - `frontend/src/pages/EventDetail.jsx`
  - `frontend/src/pages/CommunityDetail.jsx`
- Added routes in `frontend/src/App.jsx`:
  - `/projects/new`
  - `/projects/:projectId`
  - `/events/:eventId`
  - `/communities/:communityId`

## Validation
- `npm run lint` passed.
- `npm run test -- src/__tests__/pages/PhaseCPages.test.jsx --run` passed (3/3).

## Remaining Notes
- `Navbar` currently uses `href` links (full navigation) rather than SPA `Link`; routes are reachable, but this can still cause full-page reload behavior.
- Unused `Landing_v1.jsx` exists in repository but is not routed.
