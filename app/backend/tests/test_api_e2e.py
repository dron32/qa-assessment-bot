from starlette.testclient import TestClient

from app.backend.src.main import create_app


def client():
    app = create_app()
    return TestClient(app)


def test_start_self_review():
    c = client()
    r = c.post("/api/reviews/self/start", headers={"X-User-Id": "10", "X-User-Role": "user"})
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "self"
    assert data["author_id"] == 10


def test_admin_rbac_forbidden():
    c = client()
    r = c.post("/api/admin/competencies", headers={"X-User-Role": "user"}, params={"key": "k1", "title": "t1"})
    assert r.status_code == 403


def test_admin_ok():
    c = client()
    r = c.post("/api/admin/competencies", headers={"X-User-Role": "admin"}, params={"key": "k1", "title": "t1"})
    assert r.status_code == 200
    assert r.json()["key"] == "k1"


