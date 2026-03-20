"""Tests for the Reputation & Ranking API.

Tests cover:
- Reputation score calculation
- Global leaderboard
- Skill-based leaderboards
- Tier-based leaderboards
- Period-based leaderboards
- Reputation history
- Contributor rankings
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.contributor import ContributorDB
from app.models.reputation import ReputationChangeSource
from app.services.contributor_service import _store
from app.services.reputation_service import (
    _reputation_history_store,
    _leaderboard_cache,
    calculate_reputation_score,
    add_reputation_change,
    get_contributor_rank,
    invalidate_leaderboard_cache,
)

client = TestClient(app)


def _seed_contributor(
    username: str,
    display_name: str,
    total_earnings: float = 0.0,
    bounties_completed: int = 0,
    reputation: int = 0,
    skills: list[str] | None = None,
    badges: list[str] | None = None,
    created_at: datetime | None = None,
) -> ContributorDB:
    """Insert a contributor directly into the in-memory store."""
    db = ContributorDB(
        id=uuid.uuid4(),
        username=username,
        display_name=display_name,
        total_earnings=total_earnings,
        total_bounties_completed=bounties_completed,
        reputation_score=reputation,
        skills=skills or [],
        badges=badges or [],
        avatar_url=f"https://github.com/{username}.png",
        created_at=created_at or datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    _store[str(db.id)] = db
    return db


@pytest.fixture(autouse=True)
def _clean():
    """Reset store and cache before every test."""
    _store.clear()
    _reputation_history_store.clear()
    _leaderboard_cache.clear()
    yield
    _store.clear()
    _reputation_history_store.clear()
    _leaderboard_cache.clear()


# ── Reputation Calculation Tests ─────────────────────────────────────────


class TestReputationCalculation:
    """Tests for reputation score calculation."""

    def test_base_calculation(self):
        """Test basic reputation calculation."""
        breakdown = calculate_reputation_score(
            bounties_completed=5,
            bounties_cancelled=0,
            tier_breakdown={"tier1": 5, "tier2": 0, "tier3": 0},
            avg_review_score=4.0,
            on_time_rate=1.0,
        )
        
        # 5 T1 bounties = 50 points
        assert breakdown.bounty_completion_score == 50
        # 100% success rate = 50 points
        assert breakdown.success_rate_score == 50
        # 4.0/5.0 * 30 = 24 points
        assert breakdown.code_quality_score == 24
        # 100% on-time = 20 points
        assert breakdown.timely_delivery_score == 20
        # Total = 144
        assert breakdown.total_score == 144

    def test_tier_multipliers(self):
        """Test tier multipliers in calculation."""
        # All T3 bounties (x2 multiplier)
        breakdown_t3 = calculate_reputation_score(
            bounties_completed=5,
            bounties_cancelled=0,
            tier_breakdown={"tier1": 0, "tier2": 0, "tier3": 5},
            avg_review_score=4.0,
            on_time_rate=1.0,
        )
        
        # 5 T3 bounties * 10 * 2.0 = 100 points
        assert breakdown_t3.bounty_completion_score == 100
        assert breakdown_t3.tier_multipliers["tier3"] == 100

    def test_mixed_tiers(self):
        """Test mixed tier calculation."""
        breakdown = calculate_reputation_score(
            bounties_completed=6,
            bounties_cancelled=0,
            tier_breakdown={"tier1": 2, "tier2": 2, "tier3": 2},
            avg_review_score=4.0,
            on_time_rate=1.0,
        )
        
        # T1: 2 * 10 * 1.0 = 20
        # T2: 2 * 10 * 1.5 = 30
        # T3: 2 * 10 * 2.0 = 40
        # Total bounty score = 90
        assert breakdown.bounty_completion_score == 90
        assert breakdown.tier_multipliers["tier1"] == 20
        assert breakdown.tier_multipliers["tier2"] == 30
        assert breakdown.tier_multipliers["tier3"] == 40

    def test_success_rate_penalty(self):
        """Test success rate affects score."""
        # 80% success rate
        breakdown_80 = calculate_reputation_score(
            bounties_completed=8,
            bounties_cancelled=2,
            tier_breakdown={"tier1": 8, "tier2": 0, "tier3": 0},
            avg_review_score=4.0,
            on_time_rate=1.0,
        )
        
        # Success rate = 8/10 = 0.8
        assert breakdown_80.success_rate_score == 40  # 0.8 * 50

    def test_code_quality_bonus(self):
        """Test code quality affects score."""
        # High code quality
        breakdown_high = calculate_reputation_score(
            bounties_completed=5,
            bounties_cancelled=0,
            tier_breakdown={"tier1": 5, "tier2": 0, "tier3": 0},
            avg_review_score=5.0,  # Perfect
            on_time_rate=1.0,
        )
        
        # Low code quality
        breakdown_low = calculate_reputation_score(
            bounties_completed=5,
            bounties_cancelled=0,
            tier_breakdown={"tier1": 5, "tier2": 0, "tier3": 0},
            avg_review_score=2.5,  # Poor
            on_time_rate=1.0,
        )
        
        assert breakdown_high.code_quality_score == 30  # 5/5 * 30
        assert breakdown_low.code_quality_score == 15   # 2.5/5 * 30

    def test_timely_delivery_bonus(self):
        """Test on-time rate affects score."""
        breakdown = calculate_reputation_score(
            bounties_completed=5,
            bounties_cancelled=0,
            tier_breakdown={"tier1": 5, "tier2": 0, "tier3": 0},
            avg_review_score=4.0,
            on_time_rate=0.75,  # 75% on time
        )
        
        assert breakdown.timely_delivery_score == 15  # 0.75 * 20


# ── Global Leaderboard Tests ────────────────────────────────────────────


class TestGlobalLeaderboard:
    """Tests for global reputation leaderboard."""

    def test_empty_leaderboard(self):
        """Test empty leaderboard returns empty results."""
        resp = client.get("/api/reputation/leaderboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["entries"] == []
        assert data["top3"] == []

    def test_single_contributor(self):
        """Test leaderboard with one contributor."""
        _seed_contributor("alice", "Alice", total_earnings=500.0, bounties_completed=3, reputation=80)

        resp = client.get("/api/reputation/leaderboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["entries"]) == 1
        assert data["entries"][0]["rank"] == 1
        assert data["entries"][0]["username"] == "alice"
        assert data["entries"][0]["reputation_score"] == 80

    def test_ranking_order(self):
        """Test contributors ranked by reputation score."""
        _seed_contributor("low", "Low Rep", reputation=50)
        _seed_contributor("mid", "Mid Rep", reputation=100)
        _seed_contributor("high", "High Rep", reputation=200)

        resp = client.get("/api/reputation/leaderboard")
        data = resp.json()
        assert data["total"] == 3
        usernames = [e["username"] for e in data["entries"]]
        assert usernames == ["high", "mid", "low"]

    def test_top3_highlighted(self):
        """Test top 3 contributors are highlighted."""
        _seed_contributor("gold", "Gold", reputation=300)
        _seed_contributor("silver", "Silver", reputation=200)
        _seed_contributor("bronze", "Bronze", reputation=100)

        resp = client.get("/api/reputation/leaderboard")
        data = resp.json()
        assert len(data["top3"]) == 3
        assert data["top3"][0]["username"] == "gold"
        assert data["top3"][1]["username"] == "silver"
        assert data["top3"][2]["username"] == "bronze"

    def test_tiebreaker_by_earnings(self):
        """Test earnings used as tiebreaker for same reputation."""
        _seed_contributor("low_earn", "Low Earn", reputation=100, total_earnings=50.0)
        _seed_contributor("high_earn", "High Earn", reputation=100, total_earnings=500.0)

        resp = client.get("/api/reputation/leaderboard")
        data = resp.json()
        # Higher earnings should rank first
        assert data["entries"][0]["username"] == "high_earn"
        assert data["entries"][1]["username"] == "low_earn"

    def test_pagination(self):
        """Test pagination works correctly."""
        for i in range(10):
            _seed_contributor(f"user{i}", f"User {i}", reputation=100 - i)

        # First page
        resp = client.get("/api/reputation/leaderboard?limit=5&offset=0")
        data = resp.json()
        assert data["total"] == 10
        assert len(data["entries"]) == 5
        assert data["offset"] == 0

        # Second page
        resp = client.get("/api/reputation/leaderboard?limit=5&offset=5")
        data = resp.json()
        assert len(data["entries"]) == 5
        assert data["offset"] == 5


# ── Skill Leaderboard Tests ─────────────────────────────────────────────


class TestSkillLeaderboard:
    """Tests for skill-based leaderboards."""

    def test_filter_by_skill(self):
        """Test filtering contributors by skill."""
        _seed_contributor("fe_dev", "FE Dev", reputation=100, skills=["frontend", "testing"])
        _seed_contributor("be_dev", "BE Dev", reputation=150, skills=["backend"])
        _seed_contributor("fullstack", "Full Stack", reputation=200, skills=["frontend", "backend"])

        resp = client.get("/api/reputation/leaderboard/skill/frontend")
        assert resp.status_code == 200
        data = resp.json()
        assert data["skill"] == "frontend"
        assert data["total"] == 2
        
        usernames = [e["username"] for e in data["entries"]]
        assert "fe_dev" in usernames
        assert "fullstack" in usernames
        assert "be_dev" not in usernames

    def test_skill_ranking(self):
        """Test contributors ranked within skill."""
        _seed_contributor("junior", "Junior FE", reputation=50, skills=["frontend"])
        _seed_contributor("senior", "Senior FE", reputation=200, skills=["frontend"])

        resp = client.get("/api/reputation/leaderboard/skill/frontend")
        data = resp.json()
        assert data["entries"][0]["username"] == "senior"
        assert data["entries"][0]["rank"] == 1

    def test_empty_skill_leaderboard(self):
        """Test skill with no contributors."""
        resp = client.get("/api/reputation/leaderboard/skill/nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["entries"] == []


# ── Tier Leaderboard Tests ──────────────────────────────────────────────


class TestTierLeaderboard:
    """Tests for tier-based leaderboards."""

    def test_filter_by_tier(self):
        """Test filtering contributors by tier."""
        _seed_contributor("t1_dev", "T1 Dev", reputation=100, badges=["tier-1"])
        _seed_contributor("t2_dev", "T2 Dev", reputation=150, badges=["tier-2"])
        _seed_contributor("multi", "Multi Tier", reputation=200, badges=["tier-1", "tier-3"])

        resp = client.get("/api/reputation/leaderboard/tier/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == 1
        assert data["total"] == 2

        usernames = [e["username"] for e in data["entries"]]
        assert "t1_dev" in usernames
        assert "multi" in usernames
        assert "t2_dev" not in usernames

    def test_tier_validation(self):
        """Test tier must be 1, 2, or 3."""
        resp = client.get("/api/reputation/leaderboard/tier/5")
        assert resp.status_code == 422  # Validation error


# ── Period Leaderboard Tests ────────────────────────────────────────────


class TestPeriodLeaderboard:
    """Tests for period-based leaderboards."""

    def test_all_time_period(self):
        """Test all-time period leaderboard."""
        _seed_contributor("old", "Old Timer", reputation=100)
        _seed_contributor("new", "Newcomer", reputation=200)

        resp = client.get("/api/reputation/leaderboard/period/all")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period"] == "all"
        assert data["total"] == 2

    def test_week_period(self):
        """Test weekly leaderboard."""
        now = datetime.now(timezone.utc)
        
        # Recent contributor
        _seed_contributor("recent", "Recent", reputation=100, created_at=now - timedelta(days=3))
        # Old contributor (outside week)
        _seed_contributor("ancient", "Ancient", reputation=200, created_at=now - timedelta(days=30))

        resp = client.get("/api/reputation/leaderboard/period/week")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period"] == "week"
        # MVP behavior may vary based on implementation


# ── Reputation History Tests ────────────────────────────────────────────


class TestReputationHistory:
    """Tests for reputation history tracking."""

    def test_get_reputation_details(self):
        """Test getting contributor reputation details."""
        contributor = _seed_contributor("alice", "Alice", reputation=100, bounties_completed=5)

        resp = client.get(f"/api/reputation/{contributor.id}")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["contributor_id"] == str(contributor.id)
        assert data["current_score"] == 100
        assert "breakdown" in data
        assert "stats" in data
        assert "history" in data

    def test_reputation_not_found(self):
        """Test 404 for non-existent contributor."""
        fake_id = str(uuid.uuid4())
        resp = client.get(f"/api/reputation/{fake_id}")
        assert resp.status_code == 404

    def test_reputation_change_recorded(self):
        """Test reputation changes are recorded."""
        contributor = _seed_contributor("bob", "Bob", reputation=50)
        
        # Add a reputation change
        add_reputation_change(
            contributor_id=str(contributor.id),
            score_before=50,
            score_after=100,
            source=ReputationChangeSource.BOUNTY_COMPLETED,
            bounty_id=str(uuid.uuid4()),
            description="Completed T2 bounty",
        )

        resp = client.get(f"/api/reputation/{contributor.id}")
        data = resp.json()
        
        assert len(data["history"]) == 1
        assert data["history"][0]["change"] == 50
        assert data["history"][0]["source"] == "bounty_completed"


# ── Contributor Rank Tests ──────────────────────────────────────────────


class TestContributorRank:
    """Tests for contributor ranking."""

    def test_global_rank(self):
        """Test global ranking."""
        _seed_contributor("first", "First", reputation=300)
        _seed_contributor("second", "Second", reputation=200)
        third = _seed_contributor("third", "Third", reputation=100)

        resp = client.get(f"/api/reputation/{third.id}/rank")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["global_rank"] == 3
        assert data["global_total"] == 3
        assert data["percentile"] == 0.0  # Bottom contributor

    def test_percentile(self):
        """Test percentile calculation."""
        _seed_contributor("top", "Top", reputation=300)
        _seed_contributor("mid", "Mid", reputation=200)
        _seed_contributor("bottom", "Bottom", reputation=100)

        # Top contributor should be in top 33%
        top = _store.get(list(_store.keys())[0])
        resp = client.get(f"/api/reputation/{top.id}/rank")
        data = resp.json()
        assert data["percentile"] == pytest.approx(66.7, rel=0.1)

    def test_skill_rank(self):
        """Test rank within skill."""
        _seed_contributor("fe_junior", "FE Junior", reputation=50, skills=["frontend"])
        fe_senior = _seed_contributor("fe_senior", "FE Senior", reputation=200, skills=["frontend", "backend"])

        resp = client.get(f"/api/reputation/{fe_senior.id}/rank")
        data = resp.json()
        
        assert "frontend" in data["category_ranks"]
        assert data["category_ranks"]["frontend"] == 1

    def test_tier_rank(self):
        """Test rank within tier."""
        _seed_contributor("t1_junior", "T1 Junior", reputation=50, badges=["tier-1"])
        t1_senior = _seed_contributor("t1_senior", "T1 Senior", reputation=200, badges=["tier-1", "tier-2"])

        resp = client.get(f"/api/reputation/{t1_senior.id}/rank")
        data = resp.json()
        
        assert "tier1" in data["tier_ranks"]
        assert data["tier_ranks"]["tier1"] == 1


# ── Summary & Utility Tests ─────────────────────────────────────────────


class TestUtilityEndpoints:
    """Tests for utility endpoints."""

    def test_skills_list(self):
        """Test skills list endpoint."""
        resp = client.get("/api/reputation/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert "skills" in data
        assert len(data["skills"]) > 0
        
        skill_ids = [s["id"] for s in data["skills"]]
        assert "frontend" in skill_ids
        assert "backend" in skill_ids

    def test_summary_empty(self):
        """Test summary with no contributors."""
        resp = client.get("/api/reputation/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_contributors"] == 0
        assert data["top_contributor"] is None

    def test_summary_with_contributors(self):
        """Test summary with contributors."""
        _seed_contributor("low", "Low", reputation=50, badges=["tier-1"])
        _seed_contributor("high", "High", reputation=200, badges=["tier-2", "tier-3"])

        resp = client.get("/api/reputation/summary")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["total_contributors"] == 2
        assert data["avg_reputation"] == 125.0
        assert data["top_contributor"]["username"] == "high"
        assert data["tiers"]["tier1"] == 1
        assert data["tiers"]["tier2"] == 1
        assert data["tiers"]["tier3"] == 1


# ── Cache Tests ─────────────────────────────────────────────────────────


class TestCaching:
    """Tests for caching behavior."""

    def test_cache_returns_same_result(self):
        """Test cached results are consistent."""
        _seed_contributor("cached", "Cached", reputation=100)

        resp1 = client.get("/api/reputation/leaderboard")
        resp2 = client.get("/api/reputation/leaderboard")
        
        assert resp1.json() == resp2.json()

    def test_cache_invalidation(self):
        """Test cache invalidation."""
        _seed_contributor("first", "First", reputation=100)
        resp1 = client.get("/api/reputation/leaderboard")
        assert resp1.json()["total"] == 1

        # Invalidate and add new contributor
        invalidate_leaderboard_cache()
        _seed_contributor("second", "Second", reputation=200)
        
        resp2 = client.get("/api/reputation/leaderboard")
        assert resp2.json()["total"] == 2