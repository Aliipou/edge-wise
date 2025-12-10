"""
Tests for API gamification endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from smallworld.api.app import app, user_scores, simulation_history


@pytest.fixture
def client():
    """Create test client."""
    # Clear state before each test
    user_scores.clear()
    simulation_history.clear()
    return TestClient(app)


class TestLeaderboard:
    """Tests for leaderboard endpoint."""

    def test_empty_leaderboard(self, client):
        """Test leaderboard when empty."""
        response = client.get("/leaderboard")
        assert response.status_code == 200
        assert response.json() == []

    def test_leaderboard_with_users(self, client):
        """Test leaderboard with users."""
        # Add some users
        user_scores["user1"] = type("UserScore", (), {
            "user_id": "user1",
            "username": "alice",
            "score": 100,
            "optimizations": 5,
            "streak": 3,
            "achievements": [],
            "last_active": "2024-01-01",
        })()
        user_scores["user2"] = type("UserScore", (), {
            "user_id": "user2",
            "username": "bob",
            "score": 200,
            "optimizations": 10,
            "streak": 7,
            "achievements": [],
            "last_active": "2024-01-01",
        })()

        response = client.get("/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Should be sorted by score descending
        assert data[0]["username"] == "bob"
        assert data[0]["rank"] == 1
        assert data[1]["username"] == "alice"
        assert data[1]["rank"] == 2

    def test_leaderboard_limit(self, client):
        """Test leaderboard with limit parameter."""
        for i in range(20):
            user_scores[f"user{i}"] = type("UserScore", (), {
                "user_id": f"user{i}",
                "username": f"user_{i}",
                "score": i * 10,
                "optimizations": i,
                "streak": 0,
                "achievements": [],
                "last_active": "2024-01-01",
            })()

        response = client.get("/leaderboard?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


class TestUserScore:
    """Tests for user score endpoints."""

    def test_get_new_user_score(self, client):
        """Test getting score for new user creates user."""
        response = client.get("/users/newuser123/score")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "newuser123"
        assert data["score"] == 0
        assert data["optimizations"] == 0

    def test_get_existing_user_score(self, client):
        """Test getting score for existing user."""
        # Create user first
        client.get("/users/existinguser/score")
        # Modify the score
        user_scores["existinguser"].score = 500

        response = client.get("/users/existinguser/score")
        assert response.status_code == 200
        assert response.json()["score"] == 500

    def test_update_user_score(self, client):
        """Test updating user score."""
        # Create user
        client.get("/users/testuser/score")

        # Update score
        response = client.post("/users/testuser/score?points=100")
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 100

    def test_update_score_with_optimization(self, client):
        """Test updating score with optimization completed."""
        client.get("/users/optimizer/score")

        response = client.post(
            "/users/optimizer/score?points=50&optimization_completed=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["optimizations"] == 1
        # Should also get first_optimization achievement (+10 bonus)
        assert "first_optimization" in data["achievements"]
        assert data["score"] == 60  # 50 + 10 bonus


class TestAchievements:
    """Tests for achievements endpoint."""

    def test_get_achievements(self, client):
        """Test getting all achievements."""
        response = client.get("/achievements")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 5
        # Check structure
        for achievement in data:
            assert "id" in achievement
            assert "name" in achievement
            assert "description" in achievement
            assert "rarity" in achievement
            assert "points" in achievement


class TestSimulations:
    """Tests for simulation endpoints."""

    def test_record_simulation(self, client):
        """Test recording a simulation result."""
        response = client.post(
            "/simulations?user_id=simuser&original_path_length=3.0"
            "&optimized_path_length=2.5&shortcuts_applied=2"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "simuser"
        assert data["original_path_length"] == 3.0
        assert data["optimized_path_length"] == 2.5
        assert data["improvement_percent"] > 0
        assert data["points_earned"] > 0

    def test_simulation_with_high_improvement(self, client):
        """Test simulation with 50%+ improvement for achievement."""
        response = client.post(
            "/simulations?user_id=perfectuser&original_path_length=4.0"
            "&optimized_path_length=1.5&shortcuts_applied=3"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["improvement_percent"] >= 50

        # Check user got the perfect_score achievement
        user_response = client.get("/users/perfectuser/score")
        user_data = user_response.json()
        assert "perfect_score" in user_data["achievements"]

    def test_get_simulation_history(self, client):
        """Test getting simulation history."""
        # Record some simulations
        client.post(
            "/simulations?user_id=histuser&original_path_length=3.0"
            "&optimized_path_length=2.5&shortcuts_applied=1"
        )
        client.post(
            "/simulations?user_id=histuser&original_path_length=3.0"
            "&optimized_path_length=2.0&shortcuts_applied=2"
        )

        response = client.get("/simulations?user_id=histuser")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_all_simulations(self, client):
        """Test getting all simulations without user filter."""
        client.post(
            "/simulations?user_id=user1&original_path_length=3.0"
            "&optimized_path_length=2.5&shortcuts_applied=1"
        )
        client.post(
            "/simulations?user_id=user2&original_path_length=3.0"
            "&optimized_path_length=2.0&shortcuts_applied=2"
        )

        response = client.get("/simulations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_simulation_history_limit(self, client):
        """Test simulation history with limit."""
        for i in range(10):
            client.post(
                f"/simulations?user_id=limituser&original_path_length={3.0 + i * 0.1}"
                f"&optimized_path_length={2.5 + i * 0.1}&shortcuts_applied=1"
            )

        response = client.get("/simulations?user_id=limituser&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


class TestExport:
    """Tests for export endpoint."""

    def test_export_json(self, client):
        """Test exporting data as JSON."""
        # Add some data first
        client.post(
            "/simulations?user_id=exportuser&original_path_length=3.0"
            "&optimized_path_length=2.5&shortcuts_applied=1"
        )

        response = client.get("/export/json")
        assert response.status_code == 200
        data = response.json()
        assert "export_date" in data
        assert "total_simulations" in data
        assert "simulations" in data
        assert data["total_simulations"] >= 1

    def test_export_csv(self, client):
        """Test exporting data as CSV."""
        client.post(
            "/simulations?user_id=csvuser&original_path_length=3.0"
            "&optimized_path_length=2.5&shortcuts_applied=1"
        )

        response = client.get("/export/csv")
        assert response.status_code == 200
        data = response.json()
        assert "csv" in data
        assert "id,user_id" in data["csv"]

    def test_export_user_filter(self, client):
        """Test export with user filter."""
        client.post(
            "/simulations?user_id=userA&original_path_length=3.0"
            "&optimized_path_length=2.5&shortcuts_applied=1"
        )
        client.post(
            "/simulations?user_id=userB&original_path_length=3.0"
            "&optimized_path_length=2.0&shortcuts_applied=2"
        )

        response = client.get("/export/json?user_id=userA")
        assert response.status_code == 200
        data = response.json()
        assert data["total_simulations"] == 1

    def test_export_invalid_format(self, client):
        """Test export with invalid format."""
        response = client.get("/export/xml")
        assert response.status_code == 400
        assert "Unsupported format" in response.json()["error"]
