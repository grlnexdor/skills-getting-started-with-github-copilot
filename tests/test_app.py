import pytest
import copy
from fastapi.testclient import TestClient

from src.app import app, activities

# Initial activities data for reset
INITIAL_ACTIVITIES = copy.deepcopy(activities)

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    global activities
    activities.clear()
    activities.update(copy.deepcopy(INITIAL_ACTIVITIES))

def test_root_redirect():
    """Test that root path redirects to static index"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert "/static/index.html" in response.headers.get("location", "")

def test_get_activities():
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    # Check structure
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess
    assert isinstance(chess["participants"], list)

def test_signup_successful():
    """Test successful signup"""
    response = client.post("/activities/Chess%20Club/signup?email=test@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "test@example.com" in data["message"]
    assert "Chess Club" in data["message"]
    # Verify added to participants
    get_response = client.get("/activities")
    activities_data = get_response.json()
    assert "test@example.com" in activities_data["Chess Club"]["participants"]

def test_signup_activity_not_found():
    """Test signup for non-existent activity"""
    response = client.post("/activities/NonExistent/signup?email=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]

def test_signup_already_signed_up():
    """Test signup when already signed up"""
    # First signup
    client.post("/activities/Chess%20Club/signup?email=test@example.com")
    # Second signup
    response = client.post("/activities/Chess%20Club/signup?email=test@example.com")
    assert response.status_code == 400
    data = response.json()
    assert "Student is already signed up" in data["detail"]

def test_unregister_successful():
    """Test successful unregister"""
    # First signup
    client.post("/activities/Chess%20Club/signup?email=test@example.com")
    # Then unregister
    response = client.delete("/activities/Chess%20Club/unregister?email=test@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "test@example.com" in data["message"]
    assert "Chess Club" in data["message"]
    # Verify removed
    get_response = client.get("/activities")
    activities_data = get_response.json()
    assert "test@example.com" not in activities_data["Chess Club"]["participants"]

def test_unregister_activity_not_found():
    """Test unregister from non-existent activity"""
    response = client.delete("/activities/NonExistent/unregister?email=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]

def test_unregister_not_signed_up():
    """Test unregister when not signed up"""
    response = client.delete("/activities/Chess%20Club/unregister?email=test@example.com")
    assert response.status_code == 400
    data = response.json()
    assert "Student is not signed up for this activity" in data["detail"]

def test_signup_special_characters():
    """Test signup with special characters in activity name"""
    # Assuming no activity with special chars, but test encoding
    response = client.post("/activities/Art%20Studio/signup?email=test@example.com")
    assert response.status_code == 200  # Art Studio exists

def test_multiple_signups():
    """Test multiple different signups"""
    client.post("/activities/Chess%20Club/signup?email=user1@example.com")
    client.post("/activities/Programming%20Class/signup?email=user2@example.com")
    get_response = client.get("/activities")
    data = get_response.json()
    assert "user1@example.com" in data["Chess Club"]["participants"]
    assert "user2@example.com" in data["Programming Class"]["participants"]