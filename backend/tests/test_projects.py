"""
Tests for project endpoints:
  GET    /api/projects              — discover_projects
  POST   /api/projects              — create_project
  GET    /api/projects/<id>         — get_project
  PATCH  /api/projects/<id>         — update_project
  POST   /api/projects/<id>/fork
  POST   /api/projects/<id>/members
  PATCH  /api/projects/<id>/members/<uid>
  DELETE /api/projects/<id>/members/<uid>
  DELETE /api/projects/<id>
"""


class TestProjectsRequireAuth:
    """All project routes must reject requests without a valid JWT."""

    def test_discover_no_token(self, client):
        assert client.get("/api/projects").status_code == 401

    def test_create_no_token(self, client):
        assert client.post("/api/projects", json={"title": "Test"}).status_code == 401

    def test_get_project_no_token(self, client):
        assert client.get("/api/projects/1").status_code == 401

    def test_fork_no_token(self, client):
        assert client.post("/api/projects/1/fork").status_code == 401

    def test_delete_no_token(self, client):
        assert client.delete("/api/projects/1").status_code == 401


class TestCreateProject:
    def test_create_missing_title(self, client, auth_headers):
        resp = client.post("/api/projects", json={"description": "No title"}, headers=auth_headers)
        assert resp.status_code == 400
        assert resp.get_json()["success"] is False

    def test_create_invalid_status(self, client, auth_headers):
        resp = client.post("/api/projects", json={"title": "T", "status": "Flying"}, headers=auth_headers)
        assert resp.status_code == 400
        assert "Invalid status" in resp.get_json()["message"]

    def test_create_invalid_visibility(self, client, auth_headers):
        resp = client.post("/api/projects", json={"title": "T", "visibility": "secret"}, headers=auth_headers)
        assert resp.status_code == 400

    def test_create_invalid_membership_policy(self, client, auth_headers):
        resp = client.post("/api/projects", json={"title": "T", "membership_policy": "whatever"}, headers=auth_headers)
        assert resp.status_code == 400

    def test_create_success(self, client, auth_headers, project_factory):
        """Happy path: create a project and verify the response shape."""
        project = project_factory(
            title="Happy Path Project",
            description="A well-formed project",
            visibility="public",
        )
        assert project["title"] == "Happy Path Project"
        assert project["description"] == "A well-formed project"
        assert project["id"] is not None
        assert project["status"] == "Draft"           # Default
        assert project["visibility"] == "public"

    def test_create_sets_creator_as_owner(self, client, auth_headers, project_factory, seeded_user):
        """The creator should appear in members with role 'owner'."""
        project = project_factory(title="Owner Check")
        members = project["members"]
        owner_ids = [m["user_id"] for m in members if m["role"] == "owner"]
        assert seeded_user["id"] in owner_ids

    def test_create_title_max_length(self, client, auth_headers):
        """Title over 200 characters is rejected."""
        resp = client.post(
            "/api/projects",
            json={"title": "x" * 201},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestGetProject:
    def test_get_nonexistent_project(self, client, auth_headers):
        resp = client.get("/api/projects/999999", headers=auth_headers)
        assert resp.status_code == 404
        assert resp.get_json()["success"] is False

    def test_get_own_project(self, client, auth_headers, project_factory):
        """Creator can retrieve their own project by ID."""
        created = project_factory(title="Get Me")
        resp = client.get(f"/api/projects/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["id"] == created["id"]
        assert data["data"]["title"] == "Get Me"

    def test_get_returns_members_and_languages(self, client, auth_headers, project_factory):
        """Response must include members and languages arrays."""
        created = project_factory(title="Structure Check")
        resp = client.get(f"/api/projects/{created['id']}", headers=auth_headers)
        body = resp.get_json()["data"]
        assert "members" in body
        assert "languages" in body
        assert isinstance(body["members"], list)
        assert isinstance(body["languages"], list)


class TestUpdateProject:
    def test_update_title(self, client, auth_headers, project_factory):
        created = project_factory(title="Original Title")
        resp = client.patch(
            f"/api/projects/{created['id']}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["title"] == "Updated Title"

    def test_update_invalid_status_transition(self, client, auth_headers, project_factory):
        """DRAFT → IN_PROGRESS is not a valid transition (must go DRAFT → OPEN first)."""
        created = project_factory(title="State Machine Check")
        resp = client.patch(
            f"/api/projects/{created['id']}",
            json={"status": "In Progress"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_update_valid_status_transition(self, client, auth_headers, project_factory):
        """DRAFT → OPEN is a valid transition."""
        created = project_factory(title="Open Me")
        resp = client.patch(
            f"/api/projects/{created['id']}",
            json={"status": "Open"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.get_json()["data"]["status"] == "Open"

    def test_update_nonexistent_project(self, client, auth_headers):
        resp = client.patch("/api/projects/999999", json={"title": "Ghost"}, headers=auth_headers)
        assert resp.status_code == 404


class TestDeleteProject:
    def test_cancel_own_project(self, client, auth_headers, project_factory):
        """DELETE soft-cancels a project. State machine: DRAFT→OPEN first, then OPEN→CANCELLED."""
        created = project_factory(title="Cancel Me", status="Open")
        resp = client.delete(f"/api/projects/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.get_json()["success"] is True

    def test_cancel_nonexistent_project(self, client, auth_headers):
        resp = client.delete("/api/projects/999999", headers=auth_headers)
        assert resp.status_code == 404


class TestDiscoverProjects:
    def test_discover_returns_list(self, client, auth_headers):
        resp = client.get("/api/projects", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_discover_limit_param(self, client, auth_headers):
        """limit query param is accepted and capped at 100."""
        resp = client.get("/api/projects?limit=5", headers=auth_headers)
        assert resp.status_code == 200

    def test_discover_limit_hard_cap(self, client, auth_headers):
        """Requesting limit=500 should still return at most 100 results."""
        resp = client.get("/api/projects?limit=500", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] <= 100
