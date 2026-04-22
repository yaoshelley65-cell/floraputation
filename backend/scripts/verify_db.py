#!/usr/bin/env python3
"""
Floraputation Backend — Database Verification Script

Standalone script to verify Supabase connectivity, inspect the
`varieties` table schema, and print sample data.

Usage:
    python scripts/verify_db.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.core.database import get_supabase_client


SEPARATOR = "=" * 60


def main() -> None:
    settings = get_settings()

    print(SEPARATOR)
    print("  Floraputation — Supabase Database Verification")
    print(SEPARATOR)
    print(f"  Supabase URL : {settings.supabase_url}")
    print(f"  Anon Key     : {settings.supabase_anon_key[:20]}...{settings.supabase_anon_key[-10:]}")
    print(SEPARATOR)

    # 1. Initialise client
    print("\n[1/5] Initialising Supabase client...")
    client = get_supabase_client()
    print("  ✓ Client initialised successfully.\n")

    # 2. Count total rows
    print("[2/5] Counting rows in `varieties` table...")
    count_resp = (
        client.table("varieties")
        .select("id", count="exact")
        .limit(0)
        .execute()
    )
    total = count_resp.count
    print(f"  ✓ Total rows: {total}\n")

    # 3. Inspect schema (column names & sample types)
    print("[3/5] Inspecting table schema...")
    schema_resp = (
        client.table("varieties")
        .select("*")
        .limit(1)
        .execute()
    )
    if schema_resp.data:
        row = schema_resp.data[0]
        print(f"  ✓ Columns ({len(row)}):")
        for col, val in row.items():
            print(f"      {col:<16}  {type(val).__name__:<8}  sample={repr(val)[:60]}")
    print()

    # 4. Fetch sample data
    print("[4/5] Fetching 5 sample rows (ordered by score DESC)...")
    sample_resp = (
        client.table("varieties")
        .select("id, variety, crop, series, company, score, decision")
        .order("score", desc=True)
        .limit(5)
        .execute()
    )
    for i, row in enumerate(sample_resp.data, 1):
        print(f"  [{i}] {json.dumps(row, ensure_ascii=False)}")
    print()

    # 5. Quick aggregation: unique crops & companies
    print("[5/5] Counting unique crops and companies...")
    crops_resp = client.table("varieties").select("crop").execute()
    companies_resp = client.table("varieties").select("company").execute()
    unique_crops = {r["crop"] for r in crops_resp.data if r.get("crop")}
    unique_companies = {r["company"] for r in companies_resp.data if r.get("company")}
    print(f"  ✓ Unique crops    : {len(unique_crops)}")
    print(f"  ✓ Unique companies: {len(unique_companies)}")
    print(f"  Sample crops      : {sorted(unique_crops)[:10]}")
    print(f"  Sample companies  : {sorted(unique_companies)[:10]}")

    print(f"\n{SEPARATOR}")
    print("  All checks passed. Database connection is healthy.")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
