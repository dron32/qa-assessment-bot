from starlette.testclient import TestClient

from app.backend.src.main import create_app


def test_healthcheck_ok() -> None:
    app = create_app()
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}




