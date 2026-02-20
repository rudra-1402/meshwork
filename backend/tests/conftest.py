"""
Pytest fixtures for MeshWork backend tests.
"""
import uuid
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app import create_app
from app.extensions import db as _db


def _ensure_test_database_exists(test_db_uri: str):
    """Create the test database if it doesn't exist."""
    url = make_url(test_db_uri)
    test_db_name = url.database
    admin_url = url.set(database="postgres")

    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": test_db_name},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{test_db_name}"'))
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def app():
    test_db_uri = "postgresql://postgres:Rudra#9936@localhost:5432/meshwork_test"
    _ensure_test_database_exists(test_db_uri)

    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": test_db_uri,
        "JWT_SECRET_KEY": "test-secret-key-not-for-production",
        "WTF_CSRF_ENABLED": False,
    })

    with app.app_context():
        engine_url = str(_db.engine.url)
        if "meshwork_test" not in engine_url:
            raise RuntimeError(
                f"Refusing to run tests against non-test database: {engine_url}"
            )

        _db.drop_all()
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def db_rollback(app):
    """Roll back any uncommitted changes after each test."""
    with app.app_context():
        yield
        _db.session.rollback()


# =============================================================================
# SHARED USER FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def seeded_user(app):
    """
    One user committed for the entire test session.
    No explicit teardown — db.drop_all() at session end cleans everything.
    """
    with app.app_context():
        from app.models.user import User
        from app.models.college import College
        
        # Create college first
        college = College(
            name="Test College Session",
            email="testcollege@session.edu",
            domain="session.edu",
        )
        college.set_password("CollegePass123!")
        _db.session.add(college)
        _db.session.commit()
        college_id = college.id
        
        # Create user with college
        u = User(
            username="sessuser",
            first_name="Session",
            last_name="User",
            email="sessuser@test.local",
            college_id=college_id,
        )
        u.set_password("TestPass123!")
        _db.session.add(u)
        _db.session.commit()
        yield {"id": u.id, "email": "sessuser@test.local", "password": "TestPass123!", "college_id": college_id}


@pytest.fixture(scope="session")
def auth_headers(app, seeded_user):
    """Bearer token for seeded_user, valid for the full test session."""
    with app.app_context():
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=str(seeded_user["id"]))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def xp_user(app):
    """
    Fresh isolated user for XP tests.
    Fully cleaned up after each test (transactions → projects → user).
    """
    uid = uuid.uuid4().hex[:8]
    with app.app_context():
        from app.models.user import User
        u = User(
            username=f"xpuser_{uid}",
            first_name="XP",
            last_name="Tester",
            email=f"xp_{uid}@test.local",
        )
        u.set_password("TestPass123!")
        _db.session.add(u)
        _db.session.commit()
        user_id = u.id

    yield user_id

    # Teardown in dependency order (no ORM cascade on these FKs)
    with app.app_context():
        from app.models.xp_transaction import XPTransaction
        from app.models.project import Project
        from app.models.user import User
        from app.models.scoring import UserScoring
        from app.models.scoring_history import ScoringHistory

        XPTransaction.query.filter_by(user_id=user_id).delete()
        ScoringHistory.query.filter_by(user_id=user_id).delete()
        UserScoring.query.filter_by(user_id=user_id).delete()
        for p in Project.query.filter_by(creator_id=user_id).all():
            _db.session.delete(p)   # ORM delete cascades to members + languages
        _db.session.commit()

        u = _db.session.get(User, user_id)
        if u:
            _db.session.delete(u)
            _db.session.commit()


# =============================================================================
# PERSONNEL USER FIXTURES
# =============================================================================

@pytest.fixture()
def personnel_user(app):
    """
    Fresh isolated personnel user for personnel tests.
    Cleaned up after each test.
    """
    uid = uuid.uuid4().hex[:8]
    with app.app_context():
        from app.models.college import College
        from app.models.college_personnel import CollegePersonnel
        
        # Create college first
        college = College(
            name=f"Test College {uid}",
            email=f"college_{uid}@edu",
            domain=f"college{uid}.edu",
        )
        college.set_password("CollegePass123!")
        _db.session.add(college)
        _db.session.commit()
        college_id = college.id
        
        # Create personnel
        personnel = CollegePersonnel(
            first_name="Personnel",
            last_name="User",
            email=f"personnel_{uid}@college{uid}.edu",
            role="faculty",
            college_id=college_id,
        )
        personnel.set_password("TestPass123!")
        _db.session.add(personnel)
        _db.session.commit()
        personnel_id = personnel.id

    yield {"id": personnel_id, "college_id": college_id, "email": personnel.email}

    # Cleanup
    with app.app_context():
        from app.models.college import College
        from app.models.college_personnel import CollegePersonnel
        
        personnel = _db.session.get(CollegePersonnel, personnel_id)
        if personnel:
            _db.session.delete(personnel)
        _db.session.commit()
        
        college = _db.session.get(College, college_id)
        if college:
            _db.session.delete(college)
        _db.session.commit()


@pytest.fixture()
def personnel_auth_headers(app, personnel_user):
    """Bearer token for personnel_user (prefixed identity format)."""
    with app.app_context():
        from flask_jwt_extended import create_access_token
        token = create_access_token(identity=f"personnel_{personnel_user['id']}")
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# COLLABORATION FIXTURES
# =============================================================================

@pytest.fixture()
def two_users(app):
    """
    Creates two users for collaboration/integration tests.
    Returns a list of user IDs.
    """
    uid = uuid.uuid4().hex[:8]
    user_ids = []
    
    with app.app_context():
        from app.models.user import User
        from app.models.college import College
        
        # Create shared college
        college = College(
            name=f"Collab College {uid}",
            email=f"collabcollege_{uid}@edu",
            domain=f"collab{uid}.edu",
        )
        college.set_password("CollegePass123!")
        _db.session.add(college)
        _db.session.commit()
        college_id = college.id
        
        for i in range(2):
            u = User(
                username=f"collab_{uid}_{i}",
                first_name=f"User{i}",
                last_name="Collab",
                email=f"collab_{uid}_{i}@student.edu",
                college_id=college_id,
            )
            u.set_password("TestPass123!")
            _db.session.add(u)
        _db.session.commit()
        
        user_ids = [u.id for u in User.query.filter(
            User.username.like(f"collab_{uid}_%")
        ).all()]

    yield user_ids

    # Cleanup
    with app.app_context():
        from app.models.user import User
        from app.models.college import College
        from app.models.xp_transaction import XPTransaction
        from app.models.project import Project
        from app.models.community_member import CommunityMember
        
        college_id = None
        for user_id in user_ids:
            # Delete related records first
            XPTransaction.query.filter_by(user_id=user_id).delete()
            CommunityMember.query.filter_by(user_id=user_id).delete()
            
            # Delete projects created by user
            for p in Project.query.filter_by(creator_id=user_id).all():
                _db.session.delete(p)
            
            # Delete user
            u = _db.session.get(User, user_id)
            if u:
                college_id = u.college_id
                _db.session.delete(u)
        
        _db.session.commit()
        
        # Delete college
        if college_id:
            college = _db.session.get(College, college_id)
            if college:
                _db.session.delete(college)
                _db.session.commit()


@pytest.fixture()
def users_with_xp(app):
    """
    Creates 10 users with different XP levels for leaderboard tests.
    Returns a list of user IDs sorted by XP (descending).
    """
    uid = uuid.uuid4().hex[:8]
    user_ids = []
    
    with app.app_context():
        from app.models.user import User
        
        xp_values = [5000, 3000, 2000, 1500, 1000, 500, 200, 100, 50, 0]
        for i, xp in enumerate(xp_values):
            u = User(
                username=f"lbuser_{uid}_{i}",
                first_name=f"Leader{i}",
                last_name="Board",
                email=f"lb_{uid}_{i}@student.edu",
                xp=xp,  # Changed from total_xp to xp
            )
            u.set_password("TestPass123!")
            _db.session.add(u)
        _db.session.commit()
        
        user_ids = [u.id for u in User.query.filter(
            User.username.like(f"lbuser_{uid}_%")
        ).order_by(User.xp.desc()).all()]  # Changed total_xp to xp

    yield user_ids

    # Cleanup
    with app.app_context():
        from app.models.user import User
        User.query.filter(User.username.like(f"lbuser_{uid}_%")).delete()
        _db.session.commit()


@pytest.fixture()
def streak_user(app):
    """
    Fresh isolated user for streak tests.
    Cleanup includes streak-related records.
    """
    uid = uuid.uuid4().hex[:8]
    with app.app_context():
        from app.models.user import User
        
        u = User(
            username=f"streakuser_{uid}",
            first_name="Streak",
            last_name="Tester",
            email=f"streak_{uid}@test.local",
            current_streak=0,
            max_streak=0,  # Changed from longest_streak to max_streak
        )
        u.set_password("TestPass123!")
        _db.session.add(u)
        _db.session.commit()
        user_id = u.id

    yield user_id

    # Cleanup
    with app.app_context():
        from app.models.user import User
        from app.models.xp_transaction import XPTransaction
        
        # Delete XP transactions (including streak bonuses)
        XPTransaction.query.filter_by(user_id=user_id).delete()
        _db.session.commit()
        
        # Delete user
        u = _db.session.get(User, user_id)
        if u:
            _db.session.delete(u)
            _db.session.commit()


# =============================================================================
# PROJECT FIXTURE
# =============================================================================

@pytest.fixture()
def project_factory(app, client, auth_headers):
    """
    Creates projects via the API and deletes them after the test.
    Usage:  project = project_factory(title="My Project")
    """
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
        return resp.get_json()["data"]

    yield _make

    with app.app_context():
        from app.models.project import Project
        for pid in created_ids:
            p = _db.session.get(Project, pid)
            if p:
                _db.session.delete(p)
        _db.session.commit()


# =============================================================================
# COMMUNITY FIXTURE
# =============================================================================

@pytest.fixture()
def community_factory(app, client, auth_headers):
    """
    Creates communities via the API and deletes them after the test.
    Usage:  community = community_factory(name="Test Community")
    
    Note: If community routes don't exist yet, this will fail.
    In that case, use direct model creation via factories.py instead.
    """
    created_ids = []

    def _make(name="Test Community", **extra):
        # Try API creation first, fall back to direct model creation
        try:
            resp = client.post(
                "/api/communities",
                json={"community_name": name, **extra},
                headers=auth_headers,
            )
            if resp.status_code == 201:
                cid = resp.get_json()["data"]["community_id"]
                created_ids.append(cid)
                return resp.get_json()["data"]
        except:
            pass
        
        # Fallback: direct model creation
        with app.app_context():
            from app.models.community import Community
            from app.models.user import User
            
            # Get user from auth_headers
            user = User.query.filter_by(email="sessuser@test.local").first()
            
            community = Community(
                community_name=name,
                subject=extra.get("subject", "Test Subject"),
                description=extra.get("description", "Test Description"),
                created_by=user.id,
                college_id=user.college_id,
                **{k: v for k, v in extra.items() if k not in ["subject", "description"]}
            )
            _db.session.add(community)
            _db.session.commit()
            created_ids.append(community.community_id)
            return {
                "community_id": community.community_id,
                "community_name": community.community_name,
                "subject": community.subject,
            }

    yield _make

    # Cleanup
    with app.app_context():
        from app.models.community import Community
        from app.models.community_member import CommunityMember
        from app.models.community_message import CommunityMessage
        
        for cid in created_ids:
            # Delete members first
            CommunityMember.query.filter_by(community_id=cid).delete()
            CommunityMessage.query.filter_by(community_id=cid).delete()
            
            # Delete community
            c = _db.session.get(Community, cid)
            if c:
                _db.session.delete(c)
        
        _db.session.commit()
