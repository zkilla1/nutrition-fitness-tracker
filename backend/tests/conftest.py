import pytest

from app import create_app


@pytest.fixture
def app():
    return create_app({"SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:", "TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth(client):
    def make(email="zach@example.com", password="password123"):
        resp = client.post("/api/auth/register", json={"email": email, "password": password})
        assert resp.status_code == 201, resp.json
        return {"Authorization": f"Bearer {resp.json['token']}"}

    return make
