from flask_jwt_extended import create_access_token


def test_scoring_questionnaire_rejects_personnel_identity(client, personnel_auth_headers):
    resp = client.get('/api/scoring/questionnaire', headers=personnel_auth_headers)
    assert resp.status_code == 403


def test_scoring_submit_rejects_personnel_identity(client, personnel_auth_headers):
    resp = client.post('/api/scoring/submit', headers=personnel_auth_headers, json={'responses': {'q': 'a'}})
    assert resp.status_code == 403


def test_scoring_questionnaire_rejects_college_identity(client, app, seeded_user):
    with app.app_context():
        token = create_access_token(identity=f"college_{seeded_user['college_id']}")

    headers = {'Authorization': f'Bearer {token}'}
    resp = client.get('/api/scoring/questionnaire', headers=headers)
    assert resp.status_code == 401


def test_scoring_submit_rejects_college_identity(client, app, seeded_user):
    with app.app_context():
        token = create_access_token(identity=f"college_{seeded_user['college_id']}")

    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/scoring/submit', headers=headers, json={'responses': {'q': 'a'}})
    assert resp.status_code == 401
