# MeshWork Test Patterns Documentation

**Purpose:** This document extracts patterns from existing test files (`test_auth.py`, `test_projects.py`, `test_scoring.py`, `conftest.py`, `factories.py`) to guide creation of 6 new test modules in future sessions.

---

## Table of Contents
1. [Testing Stack & Philosophy](#testing-stack--philosophy)
2. [Test File Structure](#test-file-structure)
3. [Fixture Patterns (conftest.py)](#fixture-patterns-conftestpy)
4. [Factory Patterns (factories.py)](#factory-patterns-factoriespy)
5. [Test Organization Patterns](#test-organization-patterns)
6. [Assertion Patterns](#assertion-patterns)
7. [Templates for 6 New Test Modules](#templates-for-6-new-test-modules)
8. [Coverage Targets](#coverage-targets)

---

## Testing Stack & Philosophy

### Technology Stack
- **pytest 8.3.2** → Test runner with fixture injection
- **pytest-cov** → Coverage measurement
- **factory-boy** → Test data generation (declarative, repeatable)
- **flask.testing.FlaskClient** → HTTP test client with context management
- **SQLAlchemy 2.0** → ORM with session management for test isolation

### Testing Philosophy (Derived from Existing Tests)
1. **Transaction Isolation:** Every test gets a clean DB state via `db_rollback` autouse fixture
2. **Two Fixture Scopes:**
   - **Session-scoped:** Shared across all tests (app, seeded_user)
   - **Function-scoped:** Isolated per test (xp_user with manual cleanup)
3. **Unit vs Integration Split:**
   - **Pure Unit Tests:** No DB, test static methods/pure functions (see `TestLevelCalculation`)
   - **Integration Tests:** Use DB fixtures, test service + DB interaction (see `TestAwardXP`)
4. **API-Driven Testing:** Use Flask test client to call routes (not direct service calls) where possible
5. **Minimal Happy Path Coverage:** Existing tests focus on error cases and edge detection

---

## Test File Structure

### Standard Import Block
```python
"""Brief module description."""
import pytest
from datetime import datetime, timezone

# Import app context models/services here (inside test functions to avoid circular imports)
# OR import at module level if safe

# Fixtures imported automatically from conftest.py via pytest
```

### Class-Based Test Organization
```python
class TestFeatureName:
    """Tests for <specific feature/endpoint>."""
    
    def test_happy_path(self, client, auth_headers):
        """Describe expected behavior in docstring."""
        # Arrange
        # Act
        # Assert
        
    def test_error_case(self, client, auth_headers):
        """Describe error condition."""
        # Focus on status codes + error messages
```

**Why Classes?**
- Groups related tests logically (easier navigation in pytest output)
- Can share setup via class-level fixtures if needed (not used currently)
- Mirror's feature structure (TestCreateProject, TestDeleteProject, etc.)

---

## Fixture Patterns (conftest.py)

### 1. Session-Scoped Application Fixture
```python
@pytest.fixture(scope="session")
def app():
    """Creates Flask app once for entire test session with test config."""
    from app import create_app
    from app.extensions import db as _db
    
    test_app = create_app()
    test_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "postgresql://postgres:...@localhost:5432/meshwork_test",
        "JWT_SECRET_KEY": "test-secret-do-not-use-in-prod",
        "WTF_CSRF_ENABLED": False,
    })
    
    with test_app.app_context():
        _db.create_all()  # Create all tables
        yield test_app
        _db.drop_all()    # Teardown after session
```

**Key Points:**
- `scope="session"` → created once, shared across all tests
- Test database is separate from dev/prod (`meshwork_test`)
- `create_all()` before tests, `drop_all()` after
- Disable CSRF for test client requests

### 2. Test Client Fixture
```python
@pytest.fixture(scope="session")
def client(app):
    """Provides Flask test client for HTTP requests."""
    return app.test_client()
```

**Usage:**
```python
def test_example(client):
    resp = client.get('/api/endpoint')
    assert resp.status_code == 200
```

### 3. Auto-Rollback Fixture (Transaction Isolation)
```python
@pytest.fixture(autouse=True)
def db_rollback():
    """Rolls back DB changes after each test → isolated state."""
    yield
    _db.session.rollback()
```

**Why `autouse=True`?**
- Runs automatically for every test (no need to request it)
- Ensures no test pollutes DB state for subsequent tests
- **Exception:** Session-scoped fixtures like `seeded_user` persist across tests

### 4. Session-Scoped User Fixture (Persistent)
```python
@pytest.fixture(scope="session")
def seeded_user(app):
    """Creates a user once, persists for entire session. Use for read-only auth tests."""
    with app.app_context():
        from app.models.user import User
        u = User(username="testuser", email="test@student.edu")
        u.set_password("TestPass123!")
        _db.session.add(u)
        _db.session.commit()
        return u.id  # Return ID, not ORM object
```

**When to Use:**
- Tests that only need authenticated requests (don't modify user state)
- Avoids creating duplicate users for every test

### 5. Function-Scoped User Fixture with Cleanup (Isolated)
```python
@pytest.fixture()
def xp_user(app):
    """Creates fresh user per test with XP=0. Cleanup removes user + cascaded data."""
    user_id = None
    with app.app_context():
        from app.models.user import User
        u = User(username="xp_testuser", email="xp@student.edu", total_xp=0)
        u.set_password("TestPass123!")
        _db.session.add(u)
        _db.session.commit()
        user_id = u.id
    
    yield user_id  # Test runs here
    
    # Cleanup phase
    with app.app_context():
        from app.models.xp_transaction import XPTransaction
        from app.models.project import Project
        
        # Delete cascaded relationships first
        XPTransaction.query.filter_by(user_id=user_id).delete()
        for p in Project.query.filter_by(creator_id=user_id).all():
            _db.session.delete(p)  # Cascade to members + languages
        _db.session.commit()
        
        # Delete user last
        u = _db.session.get(User, user_id)
        if u:
            _db.session.delete(u)
            _db.session.commit()
```

**When to Use:**
- Tests that modify user state (XP, skills, streaks)
- Need guaranteed clean state before/after test
- **Why Manual Cleanup?** Prevents FK constraint errors from orphaned records

### 6. Auth Headers Fixture
```python
@pytest.fixture()
def auth_headers(app, seeded_user):
    """Returns Authorization header dict with valid JWT token."""
    with app.app_context():
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=seeded_user)
    return {"Authorization": f"Bearer {token}"}
```

**Usage:**
```python
def test_protected_endpoint(client, auth_headers):
    resp = client.get('/api/dashboard', headers=auth_headers)
    assert resp.status_code == 200
```

### 7. Factory-Based Fixture (project_factory)
```python
@pytest.fixture()
def project_factory(app, client, auth_headers):
    """Creates projects via API, tracks IDs, cleans up after test."""
    created_ids = []
    
    def _make(title="Test Project", **extra):
        resp = client.post(
            "/api/projects",
            json={"title": title, **extra},
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.get_json()
        pid = resp.get_json()["data"]["id"]
        created_ids.append(pid)
        return resp.get_json()["data"]  # Return project dict
    
    yield _make  # Callable factory
    
    # Cleanup all created projects
    with app.app_context():
        from app.models.project import Project
        for pid in created_ids:
            p = _db.session.get(Project, pid)
            if p:
                _db.session.delete(p)
        _db.session.commit()
```

**Usage:**
```python
def test_example(project_factory):
    proj = project_factory(title="My Project", status="Open")
    assert proj["title"] == "My Project"
    # Cleanup happens automatically after test
```

**Pattern:**
- Returns a callable that creates resources
- Tracks created IDs in closure
- Cleanup iterates tracked IDs and deletes

---

## Factory Patterns (factories.py)

### 1. Base Factory Configuration
```python
import factory
from factory.alchemy import SQLAlchemyModelFactory
from app.extensions import db

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"  # Auto-commit after create
```

**Key Settings:**
- `sqlalchemy_session` → Use app's DB session
- `sqlalchemy_session_persistence = "commit"` → Persist to DB immediately

### 2. Auto-Generated Sequences
```python
username = factory.Sequence(lambda n: f"user_{n}")
email = factory.Sequence(lambda n: f"user_{n}@student.edu")
```

**Result:**
- `user_0@student.edu`, `user_1@student.edu`, etc. (unique per factory call)

### 3. Fake Data with Faker
```python
first_name = factory.Faker("first_name")  # "John", "Emily", etc.
last_name = factory.Faker("last_name")
description = factory.Faker("paragraph")
```

### 4. Custom Creation Logic (_create Override)
```python
@classmethod
def _create(cls, model_class, *args, **kwargs):
    """Override to hash password before saving."""
    obj = model_class(*args, **kwargs)
    obj.set_password("TestPass123!")  # Hash password before commit
    db.session.add(obj)
    db.session.commit()
    return obj
```

**When to Use:**
- Model requires method calls before save (password hashing, email verification)
- Need to trigger side effects (send email, create related records)

### 5. SubFactory (Foreign Key Relationships)
```python
class ProjectFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Project
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"
    
    title = factory.Sequence(lambda n: f"Project {n}")
    creator = factory.SubFactory(UserFactory)  # Auto-creates User if not provided
    status = ProjectStatus.OPEN
```

**Behavior:**
- If `creator` not provided → creates User via UserFactory
- If `creator=user_obj` passed → uses existing user

**Usage:**
```python
# Auto-create user
project = ProjectFactory()

# Use existing user
project = ProjectFactory(creator=existing_user)
```

---

## Test Organization Patterns

### 1. Group by Feature/Endpoint
```python
class TestValidateEmail:
    """All tests for /api/auth/validate-email."""
    # test_detects_student_domain
    # test_detects_personnel_domain
    # test_invalid_email_format

class TestLogin:
    """All tests for /api/auth/login."""
    # test_successful_login
    # test_invalid_password
```

### 2. Group by User Flow
```python
class TestProjectsRequireAuth:
    """Ensures all project endpoints reject unauthenticated requests."""
    # test_discover_no_token
    # test_create_no_token
    # test_get_project_no_token
```

### 3. Separate Unit vs Integration Tests
```python
class TestLevelCalculation:
    """Pure unit tests - no DB fixtures, test static methods."""
    
    def test_zero_xp_is_level_1(self):
        """No fixtures needed - pure function test."""
        assert User.calculate_level_from_xp(0) == 1

class TestAwardXP:
    """Integration tests - requires DB and user fixture."""
    
    def test_award_positive_xp(self, app, xp_user):
        """Needs app context + DB user."""
        with app.app_context():
            # ...
```

---

## Assertion Patterns

### 1. Status Code Assertions
```python
# Exact match
resp = client.post('/api/login', json={...})
assert resp.status_code == 200

# Range match (flexible for different error conditions)
assert resp.status_code in {400, 401, 422}  # Client error family
assert 200 <= resp.status_code < 300       # Success family
```

**Why Ranges?**
- Backend may change 400 → 422 without breaking test intent
- Focus on "client error vs server error vs success"

### 2. JSON Response Structure
```python
data = resp.get_json()
assert data["success"] is True  # Boolean check
assert "data" in data           # Key existence
assert isinstance(data["data"], list)  # Type check
```

### 3. Counting Assertions (Audit Trails)
```python
before_count = XPTransaction.query.filter_by(user_id=user_id).count()
# ... perform action ...
after_count = XPTransaction.query.filter_by(user_id=user_id).count()
assert after_count == before_count + 1  # Exactly one record created
```

### 4. State Change Assertions
```python
# Before
user = db.session.get(User, user_id)
initial_xp = user.total_xp

# Action
XPService.award_xp(user, 50, source="task")

# After - refresh from DB
db.session.expire(user)
user = db.session.get(User, user_id)
assert user.total_xp == initial_xp + 50
```

**Pattern:**
- Capture state before
- Perform action
- Refresh from DB (`db.session.expire` + re-fetch)
- Assert delta

### 5. Error Message Validation
```python
resp = client.post('/api/auth/login', json={"email": "bad", "password": "x"})
data = resp.get_json()
assert data["success"] is False
assert "error" in data  # Error key present
assert "Invalid credentials" in data["error"]  # Specific message
```

---

## Templates for 6 New Test Modules

### Module 1: test_community.py

**Coverage Target:** `community_routes.py` (0%), `community_service.py` (0%)

**Required Fixtures:**
- `community_factory` (create via API, cleanup after test)
- `community_member_factory` (add members to community)
- `auth_headers` (existing)

**New Factories Needed in factories.py:**
```python
class CommunityFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Community
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"
    
    name = factory.Sequence(lambda n: f"Community {n}")
    description = factory.Faker("paragraph")
    creator = factory.SubFactory(UserFactory)
    is_private = False
    member_count = 0
```

**Test Classes:**
```python
class TestCommunityAuth:
    """Verify JWT required for all community endpoints."""
    # test_list_communities_no_token
    # test_create_community_no_token
    # test_join_community_no_token

class TestCreateCommunity:
    # test_create_with_valid_data
    # test_create_missing_name → 400
    # test_create_duplicate_name → 409 (if enforced)

class TestJoinCommunity:
    # test_join_public_community → success
    # test_join_private_community → 403 or pending invite
    # test_join_already_member → 400

class TestCommunityMessages:
    # test_post_message_as_member
    # test_post_message_as_non_member → 403
    # test_message_audit_trail → verify CommunityMessage created

class TestCommunityPolls:
    # test_create_poll
    # test_vote_on_poll
    # test_vote_twice_same_poll → 400

class TestCommunityTasks:
    # test_create_task
    # test_complete_task → XP awarded (if applicable)
    # test_task_completion_audit
```

**Estimated Coverage Impact:** 0% → 65%

---

### Module 2: test_personnel.py

**Coverage Target:** `personnel_dashboard_routes.py` (0%), `college_personnel_services.py` (12%)

**Required Fixtures:**
- `personnel_user` (function-scoped, email domain = `@college.edu`, cleanup)
- `personnel_auth_headers`

**New Factories Needed:**
```python
class PersonnelFactory(SQLAlchemyModelFactory):
    class Meta:
        model = CollegePersonnel
        # Note: Personnel may inherit from User or be separate model
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"
    
    username = factory.Sequence(lambda n: f"prof_{n}")
    email = factory.Sequence(lambda n: f"prof_{n}@college.edu")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    department = factory.Faker("job")
```

**Test Classes:**
```python
class TestPersonnelAuth:
    # test_personnel_login_with_college_email
    # test_personnel_cannot_use_student_endpoints → 403
    # test_student_cannot_use_personnel_endpoints → 403

class TestPersonnelDashboard:
    # test_get_dashboard_data → success + data shape
    # test_dashboard_shows_supervised_students
    # test_dashboard_shows_department_stats

class TestPersonnelModeration:
    # test_approve_student_project
    # test_reject_student_project
    # test_view_flagged_content

class TestPersonnelAnalytics:
    # test_get_department_leaderboard
    # test_get_skill_distribution
    # test_export_student_progress → CSV/JSON download
```

**Estimated Coverage Impact:** 12% → 70%

---

### Module 3: test_questionnaire.py

**Coverage Target:** `questionnaire_schema.py` (9%), skill/language proficiency endpoints

**Required Fixtures:**
- `auth_headers` (existing)
- `skill_factory`, `language_factory`

**New Factories Needed:**
```python
class SkillFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UserSkill  # Or Skill base model
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"
    
    user = factory.SubFactory(UserFactory)
    skill_name = factory.Faker("job")
    proficiency_level = 3  # 1-5 scale
```

**Test Classes:**
```python
class TestOnboardingQuestionnaire:
    # test_submit_skills → UserSkill records created
    # test_submit_languages → UserLanguage records created
    # test_submit_invalid_proficiency → 400

class TestUpdateSkills:
    # test_add_new_skill
    # test_update_existing_skill_proficiency
    # test_delete_skill

class TestSkillQueries:
    # test_get_user_skills
    # test_filter_users_by_skill
    # test_skill_autocomplete
```

**Estimated Coverage Impact:** 9% → 80%

---

### Module 4: test_leaderboard.py

**Coverage Target:** `leaderboard_routes.py` (0%), leaderboard logic in scoring/xp services

**Required Fixtures:**
- `multiple_users_with_xp` (create 10 users with varying XP, cleanup after)

**New Fixtures in conftest.py:**
```python
@pytest.fixture()
def users_with_xp(app):
    """Creates 10 users with different XP levels for leaderboard tests."""
    user_ids = []
    with app.app_context():
        from app.models.user import User
        xp_values = [0, 50, 100, 200, 500, 1000, 1500, 2000, 3000, 5000]
        for i, xp in enumerate(xp_values):
            u = User(username=f"lbuser_{i}", email=f"lb{i}@student.edu", total_xp=xp)
            u.set_password("TestPass123!")
            _db.session.add(u)
        _db.session.commit()
        user_ids = [u.id for u in User.query.filter(User.username.like("lbuser_%")).all()]
    
    yield user_ids
    
    # Cleanup
    with app.app_context():
        User.query.filter(User.username.like("lbuser_%")).delete()
        _db.session.commit()
```

**Test Classes:**
```python
class TestGlobalLeaderboard:
    # test_top_10_users_by_xp
    # test_pagination → limit/offset params
    # test_exclude_inactive_users

class TestDepartmentLeaderboard:
    # test_filter_by_department
    # test_cross_department_comparison

class TestLeaderboardRanking:
    # test_user_sees_own_rank
    # test_tied_scores_handled_correctly
    # test_rank_updates_after_xp_change
```

**Estimated Coverage Impact:** 0% → 75%

---

### Module 5: test_gamification.py

**Coverage Target:** `streak_service.py` (18%), `skill_service.py`, gamification helpers

**Required Fixtures:**
- `xp_user` (existing)
- `streak_user` (similar to xp_user but tracks login streaks)

**New Fixtures:**
```python
@pytest.fixture()
def streak_user(app):
    """User for testing streak service - tracks daily login."""
    # Similar to xp_user, but include cleanup for DailyStreak records
    pass
```

**Test Classes:**
```python
class TestStreakTracking:
    # test_first_login_creates_streak
    # test_consecutive_login_increments_streak
    # test_missed_day_resets_streak
    # test_streak_xp_bonus_awarded

class TestSkillLeveling:
    # test_xp_in_skill_increases_proficiency
    # test_skill_level_cap_at_5
    # test_skill_progress_percentage

class TestAchievements:
    # test_award_achievement
    # test_duplicate_achievement_ignored
    # test_achievement_unlocked_event

class TestDailyRewards:
    # test_daily_login_bonus
    # test_bonus_only_once_per_day
    # test_consecutive_days_multiplier
```

**Estimated Coverage Impact:** Streak service 18% → 80%, Skill service 20% → 75%

---

### Module 6: test_integration.py

**Coverage Target:** Cross-service workflows (e.g., "create project → join → complete task → earn XP")

**Required Fixtures:**
- All existing fixtures
- `two_users` fixture (creator + collaborator scenarios)

**New Fixtures:**
```python
@pytest.fixture()
def two_users(app):
    """Creates two users for collaboration tests."""
    user_ids = []
    with app.app_context():
        from app.models.user import User
        for i in range(2):
            u = User(username=f"collab_{i}", email=f"collab{i}@student.edu")
            u.set_password("TestPass123!")
            _db.session.add(u)
        _db.session.commit()
        user_ids = [u.id for u in User.query.filter(User.username.like("collab_%")).all()]
    
    yield user_ids
    
    # Cleanup (projects, memberships, XP transactions)
    with app.app_context():
        from app.models.user import User
        User.query.filter(User.username.like("collab_%")).delete()
        _db.session.commit()
```

**Test Classes:**
```python
class TestProjectCollaborationWorkflow:
    # test_full_workflow:
    #   1. User A creates project
    #   2. User B requests join
    #   3. User A approves request
    #   4. User B completes task in project
    #   5. User B earns XP
    #   6. User A earns XP (project creator bonus)
    #   7. Project status changes to IN_PROGRESS

class TestCommunityEngagementWorkflow:
    # test_community_lifecycle:
    #   1. User creates community
    #   2. Multiple users join
    #   3. Post messages → engagement score increases
    #   4. Create poll → members vote
    #   5. Leaderboard reflects community XP

class TestStreakXPIntegration:
    # test_daily_login_awards_xp_and_increments_streak
    # test_streak_broken_after_24h_no_login
    # test_xp_cap_not_bypassed_by_streak_bonus

class TestSkillXPProgression:
    # test_complete_python_task_increases_python_skill
    # test_skill_level_up_awards_bonus_xp
```

**Estimated Coverage Impact:** Overall 41% → 60% (integration tests fill gaps between services)

---

## Coverage Targets

### Before New Tests (Current)
| File/Service                  | Coverage |
|-------------------------------|----------|
| Overall                       | 41%      |
| community_routes.py           | 0%       |
| community_service.py          | 0%       |
| personnel_dashboard_routes.py | 0%       |
| leaderboard_routes.py         | 0%       |
| questionnaire_schema.py       | 9%       |
| college_personnel_services.py | 12%      |
| scoring_service.py            | 15%      |
| streak_service.py             | 18%      |
| auth_routes.py                | 19%      |
| language_proficiency_service.py | 20%    |

### After New Tests (Projected)
| Module                  | Target Coverage |
|-------------------------|-----------------|
| test_community.py       | 65%             |
| test_personnel.py       | 70%             |
| test_questionnaire.py   | 80%             |
| test_leaderboard.py     | 75%             |
| test_gamification.py    | 75-80%          |
| test_integration.py     | 60%             |
| **Overall**             | **~65%**        |

---

## Checklist for Creating Each Test Module

### 1. Analyze Routes/Services First
```bash
# Read route file to understand endpoints
code backend/app/routes/<module>_routes.py

# Read service file to understand business logic
code backend/app/services/<module>_service.py

# Note all endpoints, required params, expected responses
```

### 2. Create Required Factories (factories.py)
- Add `<Model>Factory` for each model tested
- Use `SubFactory` for relationships
- Override `_create` if model methods needed

### 3. Create Required Fixtures (conftest.py)
- Add `<resource>_factory` fixture if API-driven creation
- Add specialized user fixtures if different from `seeded_user`
- Include cleanup logic in `yield` teardown

### 4. Write Tests (test_<module>.py)
- Start with `TestAuth` class (ensure JWT protection)
- Add `TestCreate<Resource>` (happy path + validation)
- Add edge cases (duplicates, not found, forbidden)
- Add audit trail tests (XP transactions, history records)

### 5. Run Tests and Check Coverage
```bash
# Run only new module
pytest backend/tests/test_<module>.py -v

# Check coverage for specific file
pytest backend/tests/test_<module>.py --cov=backend/app/routes/<module>_routes --cov-report=term-missing
```

### 6. Iterate
- Add missing test cases based on coverage report
- Focus on uncovered branches (if/else, try/except)
- Aim for 70%+ coverage before moving to next module

---

## Common Pitfalls to Avoid

1. **Forgetting app.app_context()**
   ```python
   # WRONG - will fail outside request context
   user = db.session.get(User, user_id)
   
   # CORRECT
   with app.app_context():
       user = db.session.get(User, user_id)
   ```

2. **Not Refreshing ORM Objects After Changes**
   ```python
   # WRONG - may see stale cached data
   assert user.total_xp == expected_xp
   
   # CORRECT
   db.session.expire(user)
   user = db.session.get(User, user_id)
   assert user.total_xp == expected_xp
   ```

3. **Incomplete Cleanup in Fixtures**
   - Must delete child records before parent (FK constraints)
   - Use `query.filter_by(...).delete()` for bulk deletes
   - Commit after deletions

4. **Using Session-Scoped Fixtures for Mutable Tests**
   - `seeded_user` is OK for read-only auth tests
   - Use `xp_user` (function-scoped) for tests that modify user

5. **Hardcoding IDs**
   ```python
   # WRONG - ID may differ between test runs
   resp = client.get('/api/users/1')
   
   # CORRECT - use fixture-returned IDs
   resp = client.get(f'/api/users/{seeded_user}')
   ```

---

## Example: Full Test File Template

```python
"""
Tests for <feature> endpoints and services.
Coverage targets: <route_file> (0% → 70%), <service_file> (0% → 80%)
"""
import pytest
from datetime import datetime, timezone


# =============================================================================
# AUTH CHECKS
# =============================================================================

class TestRequireAuth:
    """Verify all <feature> endpoints reject unauthenticated requests."""
    
    def test_list_no_token(self, client):
        resp = client.get('/api/<feature>')
        assert resp.status_code == 401
    
    def test_create_no_token(self, client):
        resp = client.post('/api/<feature>', json={})
        assert resp.status_code == 401


# =============================================================================
# CREATE
# =============================================================================

class TestCreate:
    """Test <feature> creation endpoint."""
    
    def test_create_with_valid_data(self, client, auth_headers):
        resp = client.post(
            '/api/<feature>',
            json={"name": "Test", "description": "Test desc"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test"
    
    def test_create_missing_required_field(self, client, auth_headers):
        resp = client.post(
            '/api/<feature>',
            json={"description": "Missing name"},
            headers=auth_headers,
        )
        assert resp.status_code in {400, 422}
        data = resp.get_json()
        assert data["success"] is False


# =============================================================================
# READ
# =============================================================================

class TestGet:
    """Test retrieving <feature> resources."""
    
    def test_get_existing_resource(self, client, auth_headers, <feature>_factory):
        resource = <feature>_factory(name="Test Item")
        resp = client.get(f'/api/<feature>/{resource["id"]}', headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["data"]["name"] == "Test Item"
    
    def test_get_nonexistent_resource(self, client, auth_headers):
        resp = client.get('/api/<feature>/999999', headers=auth_headers)
        assert resp.status_code == 404


# =============================================================================
# UPDATE
# =============================================================================

class TestUpdate:
    """Test updating <feature> resources."""
    
    def test_update_own_resource(self, client, auth_headers, <feature>_factory):
        resource = <feature>_factory(name="Original")
        resp = client.patch(
            f'/api/<feature>/{resource["id"]}',
            json={"name": "Updated"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["name"] == "Updated"


# =============================================================================
# DELETE
# =============================================================================

class TestDelete:
    """Test deleting <feature> resources."""
    
    def test_delete_own_resource(self, client, auth_headers, <feature>_factory):
        resource = <feature>_factory()
        resp = client.delete(f'/api/<feature>/{resource["id"]}', headers=auth_headers)
        assert resp.status_code == 200
        
        # Verify deletion
        get_resp = client.get(f'/api/<feature>/{resource["id"]}', headers=auth_headers)
        assert get_resp.status_code == 404

```

---

**End of Documentation**

This document should provide sufficient context to create all 6 test modules in a future session. Focus on:
1. Copying fixture patterns from conftest.py
2. Creating factories following UserFactory/ProjectFactory examples
3. Organizing tests by feature/endpoint
4. Using consistent assertion patterns
5. Including cleanup logic in all fixtures that create DB resources
