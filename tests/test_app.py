import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the activities dict to its original state after each test."""
    snapshot = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(snapshot)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200(client):
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_returns_all_nine(client):
    response = client.get("/activities")
    data = response.json()
    assert len(data) == 9


def test_get_activities_shape(client):
    response = client.get("/activities")
    data = response.json()
    for activity in data.values():
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


# ---------------------------------------------------------------------------
# GET / (redirect)
# ---------------------------------------------------------------------------

def test_redirect_root(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert "/static/index.html" in response.headers["location"]


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success(client):
    response = client.post("/activities/Soccer Team/signup?email=new@mergington.edu")
    assert response.status_code == 200
    assert "new@mergington.edu" in activities["Soccer Team"]["participants"]


def test_signup_success_message(client):
    response = client.post("/activities/Soccer Team/signup?email=new@mergington.edu")
    assert "message" in response.json()


def test_signup_duplicate_returns_400(client):
    # michael@mergington.edu is already in Chess Club
    response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert response.status_code == 400


def test_signup_unknown_activity_returns_404(client):
    response = client.post("/activities/Unknown Activity/signup?email=test@mergington.edu")
    assert response.status_code == 404


def test_signup_full_activity_returns_400(client):
    # Fill Soccer Team (max 22) to capacity
    for i in range(22):
        activities["Soccer Team"]["participants"].append(f"student{i}@mergington.edu")
    response = client.post("/activities/Soccer Team/signup?email=overflow@mergington.edu")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success(client):
    response = client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert response.status_code == 200
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]


def test_unregister_success_message(client):
    response = client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
    assert "message" in response.json()


def test_unregister_not_registered_returns_400(client):
    response = client.delete("/activities/Soccer Team/signup?email=nobody@mergington.edu")
    assert response.status_code == 400


def test_unregister_unknown_activity_returns_404(client):
    response = client.delete("/activities/Unknown Activity/signup?email=test@mergington.edu")
    assert response.status_code == 404
