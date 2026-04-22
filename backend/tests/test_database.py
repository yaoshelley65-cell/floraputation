"""
Floraputation Backend — Database Connection Tests

Verifies that the Supabase client can connect to the database
and perform basic operations against the `varieties` table.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.database import get_supabase_client, verify_connection


class TestSupabaseConfig:
    """Verify that Supabase configuration is loaded correctly."""

    def test_supabase_url_is_set(self):
        settings = get_settings()
        assert settings.supabase_url, "SUPABASE_URL must not be empty"
        assert settings.supabase_url.startswith("https://"), "SUPABASE_URL must use HTTPS"

    def test_supabase_key_is_set(self):
        settings = get_settings()
        assert settings.supabase_anon_key, "SUPABASE_ANON_KEY must not be empty"
        assert len(settings.supabase_anon_key) > 50, "SUPABASE_ANON_KEY looks too short"


class TestSupabaseConnection:
    """Verify live connectivity to the Supabase database."""

    def test_client_initialises(self):
        """The Supabase client should initialise without errors."""
        client = get_supabase_client()
        assert client is not None

    def test_query_varieties_table(self):
        """A simple SELECT on the varieties table should return data."""
        client = get_supabase_client()
        response = (
            client.table("varieties")
            .select("id, variety, crop, score")
            .limit(3)
            .execute()
        )
        assert response.data is not None
        assert len(response.data) > 0, "Expected at least one row"
        # Verify expected columns are present
        first_row = response.data[0]
        assert "id" in first_row
        assert "variety" in first_row
        assert "crop" in first_row

    def test_total_row_count(self):
        """The varieties table should contain a substantial number of records."""
        client = get_supabase_client()
        response = (
            client.table("varieties")
            .select("id", count="exact")
            .limit(0)
            .execute()
        )
        assert response.count is not None
        assert response.count >= 3000, (
            f"Expected 3000+ rows, got {response.count}"
        )
        print(f"\n  ✓ Total varieties in database: {response.count}")

    def test_table_schema_columns(self):
        """Verify that all expected columns exist in the varieties table."""
        expected_columns = {
            "id", "variety", "crop", "series", "company", "source_url",
            "score", "consumer", "grower", "retailer", "trend",
            "positive", "neutral", "negative", "confidence",
            "mentions", "mentions_raw", "cg_gap", "decision",
            "opportunity", "tags", "created_at",
            "original_series", "original_variety",
        }
        client = get_supabase_client()
        response = (
            client.table("varieties")
            .select("*")
            .limit(1)
            .execute()
        )
        assert response.data, "Expected at least one row for schema check"
        actual_columns = set(response.data[0].keys())
        missing = expected_columns - actual_columns
        assert not missing, f"Missing columns in varieties table: {missing}"
        print(f"\n  ✓ All {len(expected_columns)} expected columns present")
        print(f"  ✓ Actual columns ({len(actual_columns)}): {sorted(actual_columns)}")

    def test_sample_data_integrity(self):
        """Verify that sample data has reasonable values."""
        client = get_supabase_client()
        response = (
            client.table("varieties")
            .select("*")
            .limit(5)
            .execute()
        )
        for row in response.data:
            assert row.get("variety"), "variety name should not be empty"
            assert row.get("crop"), "crop should not be empty"
            if row.get("score") is not None:
                assert 0 <= row["score"] <= 100, (
                    f"Score {row['score']} out of expected range [0, 100]"
                )
        print(f"\n  ✓ Sample data integrity check passed for {len(response.data)} rows")

    def test_search_query(self):
        """Verify that ilike search works on the varieties table."""
        client = get_supabase_client()
        response = (
            client.table("varieties")
            .select("id, variety, crop, score")
            .ilike("crop", "%Rose%")
            .limit(5)
            .execute()
        )
        assert response.data is not None
        for row in response.data:
            assert "rose" in row["crop"].lower(), (
                f"Expected 'rose' in crop, got '{row['crop']}'"
            )
        print(f"\n  ✓ Search query returned {len(response.data)} Rose varieties")

    def test_order_and_pagination(self):
        """Verify that ordering and range-based pagination work."""
        client = get_supabase_client()
        response = (
            client.table("varieties")
            .select("id, variety, score")
            .order("score", desc=True)
            .range(0, 4)
            .execute()
        )
        assert len(response.data) == 5
        scores = [r["score"] for r in response.data if r["score"] is not None]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by score DESC"
        print(f"\n  ✓ Pagination & ordering work correctly. Top score: {scores[0]}")


@pytest.mark.asyncio
class TestVerifyConnection:
    """Test the verify_connection helper function."""

    async def test_verify_connection_returns_connected(self):
        result = await verify_connection()
        assert result["status"] == "connected", f"Connection failed: {result}"
        assert result["total_rows"] >= 3000
        assert len(result["sample_data"]) > 0
        print(f"\n  ✓ verify_connection(): {result['total_rows']} total rows")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
