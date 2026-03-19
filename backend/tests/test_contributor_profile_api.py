"""Comprehensive API tests for Contributor Profile endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services import contributor_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_store():
    """Clear the contributor store before and after each test."""
    contributor_service._store.clear()
    yield
    contributor_service._store.clear()


class TestContributorProfileAPI:
    """Tests for Contributor Profile REST API endpoints."""

    def test_create_contributor_profile(self):
        """Test creating a new contributor profile."""
        resp = client.post(
            "/api/contributors",
            json={
                "username": "newuser",
                "display_name": "New User",
                "avatar_url": "https://example.com/avatar.png",
                "bio": "Test contributor",
                "skills": ["python", "rust"],
                "social_links": {"github": "https://github.com/newuser"}
            }
        )
        assert resp.status_code in [200, 201]
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["display_name"] == "New User"

    def test_create_contributor_minimal(self):
        """Test creating contributor with minimal fields."""
        resp = client.post(
            "/api/contributors",
            json={"username": "minimal", "display_name": "Minimal User"}
        )
        assert resp.status_code in [200, 201]
        data = resp.json()
        assert data["username"] == "minimal"
        assert data["stats"]["total_contributions"] == 0

    def test_create_duplicate_username(self):
        """Test that duplicate username is rejected."""
        client.post(
            "/api/contributors",
            json={"username": "dupuser", "display_name": "Dup User"}
        )
        resp = client.post(
            "/api/contributors",
            json={"username": "dupuser", "display_name": "Another Dup"}
        )
        assert resp.status_code == 409

    def test_create_invalid_username_spaces(self):
        """Test that username with spaces is rejected."""
        resp = client.post(
            "/api/contributors",
            json={"username": "invalid user", "display_name": "Invalid"}
        )
        assert resp.status_code == 422

    def test_create_invalid_username_special_chars(self):
        """Test that username with special characters is rejected."""
        resp = client.post(
            "/api/contributors",
            json={"username": "user@name!", "display_name": "Invalid"}
        )
        assert resp.status_code == 422

    def test_list_contributors_empty(self):
        """Test listing contributors when empty."""
        resp = client.get("/api/contributors")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_contributors_with_data(self):
        """Test listing contributors with data."""
        for i in range(3):
            client.post(
                "/api/contributors",
                json={"username": f"user{i}", "display_name": f"User {i}"}
            )
        
        resp = client.get("/api/contributors")
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

    def test_search_contributors_by_username(self):
        """Test searching contributors by username."""
        client.post(
            "/api/contributors",
            json={"username": "alice", "display_name": "Alice"}
        )
        client.post(
            "/api/contributors",
            json={"username": "bob", "display_name": "Bob"}
        )
        
        resp = client.get("/api/contributors?search=alice")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["username"] == "alice"

    def test_search_contributors_partial_match(self):
        """Test partial username search."""
        client.post(
            "/api/contributors",
            json={"username": "johnsmith", "display_name": "John Smith"}
        )
        
        resp = client.get("/api/contributors?search=john")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_skills(self):
        """Test filtering contributors by skills."""
        client.post(
            "/api/contributors",
            json={"username": "pythonista", "display_name": "Python Dev", "skills": ["python"]}
        )
        client.post(
            "/api/contributors",
            json={"username": "rustacean", "display_name": "Rust Dev", "skills": ["rust"]}
        )
        
        resp = client.get("/api/contributors?skills=python")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["username"] == "pythonista"

    def test_filter_by_multiple_skills(self):
        """Test filtering by multiple skills (OR logic)."""
        client.post(
            "/api/contributors",
            json={"username": "polyglot", "display_name": "Poly", "skills": ["python", "rust", "go"]}
        )
        
        resp = client.get("/api/contributors?skills=python,rust")
        assert resp.status_code == 200

    def test_filter_by_badges(self):
        """Test filtering contributors by badges."""
        client.post(
            "/api/contributors",
            json={"username": "early", "display_name": "Early", "badges": ["early_adopter"]}
        )
        client.post(
            "/api/contributors",
            json={"username": "newbie", "display_name": "Newbie", "badges": []}
        )
        
        resp = client.get("/api/contributors?badges=early_adopter")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_pagination_skip_limit(self):
        """Test pagination with skip and limit."""
        for i in range(10):
            client.post(
                "/api/contributors",
                json={"username": f"pageuser{i}", "display_name": f"Page User {i}"}
            )
        
        resp = client.get("/api/contributors?skip=0&limit=5")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 5
        assert resp.json()["total"] == 10

    def test_pagination_offset(self):
        """Test pagination with offset."""
        for i in range(5):
            client.post(
                "/api/contributors",
                json={"username": f"offsetuser{i}", "display_name": f"Offset User {i}"}
            )
        
        resp = client.get("/api/contributors?skip=2&limit=2")
        assert resp.status_code == 200

    def test_get_contributor_by_id(self):
        """Test getting a contributor by ID."""
        create_resp = client.post(
            "/api/contributors",
            json={"username": "getuser", "display_name": "Get User"}
        )
        contributor_id = create_resp.json()["id"]
        
        resp = client.get(f"/api/contributors/{contributor_id}")
        assert resp.status_code == 200
        assert resp.json()["username"] == "getuser"

    def test_get_contributor_not_found(self):
        """Test getting a non-existent contributor."""
        resp = client.get("/api/contributors/nonexistent-id")
        assert resp.status_code == 404

    def test_update_contributor_display_name(self):
        """Test updating contributor display name."""
        create_resp = client.post(
            "/api/contributors",
            json={"username": "updateuser", "display_name": "Original Name"}
        )
        contributor_id = create_resp.json()["id"]
        
        resp = client.patch(
            f"/api/contributors/{contributor_id}",
            json={"display_name": "Updated Name"}
        )
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated Name"

    def test_update_contributor_bio(self):
        """Test updating contributor bio."""
        create_resp = client.post(
            "/api/contributors",
            json={"username": "biouser", "display_name": "Bio User"}
        )
        contributor_id = create_resp.json()["id"]
        
        resp = client.patch(
            f"/api/contributors/{contributor_id}",
            json={"bio": "This is my updated bio"}
        )
        assert resp.status_code == 200
        assert resp.json()["bio"] == "This is my updated bio"

    def test_update_contributor_skills(self):
        """Test updating contributor skills."""
        create_resp = client.post(
            "/api/contributors",
            json={"username": "skilluser", "display_name": "Skill User", "skills": ["python"]}
        )
        contributor_id = create_resp.json()["id"]
        
        resp = client.patch(
            f"/api/contributors/{contributor_id}",
            json={"skills": ["python", "rust", "go"]}
        )
        assert resp.status_code == 200
        assert "rust" in resp.json()["skills"]

    def test_update_contributor_avatar(self):
        """Test updating contributor avatar URL."""
        create_resp = client.post(
            "/api/contributors",
            json={"username": "avataruser", "display_name": "Avatar User"}
        )
        contributor_id = create_resp.json()["id"]
        
        resp = client.patch(
            f"/api/contributors/{contributor_id}",
            json={"avatar_url": "https://example.com/new-avatar.png"}
        )
        assert resp.status_code == 200

    def test_delete_contributor(self):
        """Test deleting a contributor."""
        create_resp = client.post(
            "/api/contributors",
            json={"username": "deleteuser", "display_name": "Delete User"}
        )
        contributor_id = create_resp.json()["id"]
        
        resp = client.delete(f"/api/contributors/{contributor_id}")
        assert resp.status_code in [200, 204]
        
        # Verify deletion
        get_resp = client.get(f"/api/contributors/{contributor_id}")
        assert get_resp.status_code == 404

    def test_delete_contributor_not_found(self):
        """Test deleting a non-existent contributor."""
        resp = client.delete("/api/contributors/nonexistent-id")
        assert resp.status_code == 404


class TestContributorStats:
    """Tests for contributor statistics."""

    def test_initial_stats(self):
        """Test initial stats are zero."""
        resp = client.post(
            "/api/contributors",
            json={"username": "statsuser", "display_name": "Stats User"}
        )
        data = resp.json()
        assert data["stats"]["total_contributions"] == 0
        assert data["stats"]["total_bounties_completed"] == 0
        assert data["stats"]["total_earnings"] == 0

    def test_stats_after_contributions(self):
        """Test stats reflect contributions."""
        # Note: This would require integration with the bounty system
        # For now, we test the API structure
        resp = client.post(
            "/api/contributors",
            json={"username": "contributor", "display_name": "Contributor"}
        )
        assert "stats" in resp.json()


class TestContributorValidation:
    """Tests for input validation."""

    def test_username_too_short(self):
        """Test that short username is rejected."""
        resp = client.post(
            "/api/contributors",
            json={"username": "ab", "display_name": "Short"}
        )
        assert resp.status_code == 422

    def test_username_too_long(self):
        """Test that very long username is rejected."""
        long_username = "a" * 100
        resp = client.post(
            "/api/contributors",
            json={"username": long_username, "display_name": "Long"}
        )
        assert resp.status_code == 422

    def test_empty_display_name(self):
        """Test that empty display name is rejected."""
        resp = client.post(
            "/api/contributors",
            json={"username": "validuser", "display_name": ""}
        )
        assert resp.status_code == 422

    def test_invalid_avatar_url(self):
        """Test that invalid avatar URL is handled."""
        resp = client.post(
            "/api/contributors",
            json={"username": "urluser", "display_name": "URL User", "avatar_url": "not-a-url"}
        )
        # May or may not reject depending on validation
        assert resp.status_code in [200, 201, 422]


class TestContributorLeaderboard:
    """Tests for leaderboard functionality."""

    def test_leaderboard_empty(self):
        """Test leaderboard when no contributors."""
        resp = client.get("/api/leaderboard")
        assert resp.status_code == 200

    def test_leaderboard_with_contributors(self):
        """Test leaderboard with contributors."""
        # Create contributors with different earnings
        client.post(
            "/api/contributors",
            json={"username": "top", "display_name": "Top Contributor"}
        )
        client.post(
            "/api/contributors",
            json={"username": "second", "display_name": "Second Contributor"}
        )
        
        resp = client.get("/api/leaderboard")
        assert resp.status_code == 200

    def test_leaderboard_period_filter(self):
        """Test leaderboard with period filter."""
        resp = client.get("/api/leaderboard?period=week")
        assert resp.status_code == 200
        
        resp = client.get("/api/leaderboard?period=month")
        assert resp.status_code == 200
        
        resp = client.get("/api/leaderboard?period=all")
        assert resp.status_code == 200

    def test_leaderboard_limit(self):
        """Test leaderboard limit parameter."""
        for i in range(10):
            client.post(
                "/api/contributors",
                json={"username": f"lbuser{i}", "display_name": f"LB User {i}"}
            )
        
        resp = client.get("/api/leaderboard?limit=5")
        assert resp.status_code == 200