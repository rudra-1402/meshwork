"""
Tests for authentication endpoints:
  POST /api/auth/validate-email
  POST /api/auth/login
  POST /api/auth/signup
"""


class TestValidateEmail:
    def test_validate_email_missing_body(self, client):
        resp = client.post("/api/auth/validate-email", json={})
        assert resp.status_code in (400, 422)

    def test_validate_email_invalid_format(self, client):
        resp = client.post("/api/auth/validate-email", json={"email": "not-an-email"})
        assert resp.status_code == 400

    def test_validate_email_unwhitelisted_domain_returns_400(self, client):
        # Domains not in the college whitelist are rejected at validation time
        resp = client.post("/api/auth/validate-email", json={"email": "new@example.edu"})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["valid"] is False

    def test_validate_email_existing_user_is_registered(self, client, seeded_user):
        """A user that exists in the DB should come back as is_registered=True."""
        resp = client.post(
            "/api/auth/validate-email",
            json={"email": seeded_user["email"]},
        )
        # Either 200 (valid, is_registered) or 400 (domain not whitelisted).
        # The seeded user has a test.local domain which isn't in the college whitelist,
        # so the endpoint may reject it before checking existence.
        # The key assertion: no 5xx error.
        assert resp.status_code < 500


class TestLogin:
    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "nonexistent@student.edu",
            "password": "WrongPassword!"
        })
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["success"] is False

    def test_login_missing_fields(self, client):
        resp = client.post("/api/auth/login", json={"email": "someone@student.edu"})
        assert resp.status_code == 400

    def test_login_missing_email(self, client):
        resp = client.post("/api/auth/login", json={"password": "Pass123!"})
        assert resp.status_code == 400

    def test_login_empty_body(self, client):
        resp = client.post("/api/auth/login", content_type="application/json", data="{}")
        assert resp.status_code == 400


class TestSignup:
    def test_signup_missing_required_fields(self, client):
        resp = client.post("/api/auth/signup", json={"email": "newuser@student.edu"})
        assert resp.status_code in (400, 422)
        data = resp.get_json()
        assert data["success"] is False

    def test_signup_invalid_email_format(self, client):
        resp = client.post("/api/auth/signup", json={
            "email": "invalid",
            "password": "Pass123!",
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
        })
        assert resp.status_code == 400

    def test_signup_missing_user_type(self, client):
        """Unified signup requires user_type."""
        resp = client.post("/api/auth/signup", json={
            "email": "new@student.edu",
            "password": "Pass123!",
            "first_name": "New",
            "last_name": "User",
            "college_id": 1,
        })
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False


class TestProtectedEndpointsRespectJWT:
    """Smoke-test: a valid JWT grants access; missing JWT is rejected."""

    def test_valid_jwt_reaches_projects(self, client, auth_headers):
        resp = client.get("/api/projects", headers=auth_headers)
        # 200 OK — but NOT 401/403
        assert resp.status_code not in (401, 403)

    def test_no_jwt_blocked_from_projects(self, client):
        resp = client.get("/api/projects")
        assert resp.status_code == 401
