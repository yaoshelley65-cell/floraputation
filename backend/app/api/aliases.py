"""
Variety Aliases API — Community-contributed multilingual names.

Users can contribute alternative names for plant varieties in different
languages. These aliases are used to expand search coverage during
scraping and analysis, making results more comprehensive.

Example: Variety "Suntaste" might also be known as "泡泡菊" in Chinese.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.database import get_supabase_admin_client
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/aliases", tags=["Aliases (Community)"])


# --- Models ---

class AliasCreate(BaseModel):
    """Request to contribute a new alias for a variety."""
    variety_id: int = Field(..., description="ID of the variety in the varieties table")
    alias_name: str = Field(
        ..., min_length=1, max_length=200,
        description="The alternative name, e.g. '泡泡菊', 'Margarita africana'",
    )
    language: str = Field(
        ..., min_length=2, max_length=20,
        description="Language code or name, e.g. 'zh', 'es', 'ja', 'de', 'English', '中文'",
    )
    region: str = Field(
        "", max_length=100,
        description="Optional region where this name is used, e.g. 'China', 'Japan', 'Latin America'",
    )
    source: str = Field(
        "", max_length=500,
        description="Where this name was found, e.g. 'Taobao listing', 'Japanese seed catalog', user note",
    )
    contributor: str = Field(
        "anonymous", max_length=100,
        description="Contributor name or identifier",
    )


class AliasBatchCreate(BaseModel):
    """Batch contribute multiple aliases at once."""
    aliases: List[AliasCreate] = Field(
        ..., min_length=1, max_length=50,
        description="List of aliases to contribute",
    )


class AliasUpdate(BaseModel):
    """Update an existing alias."""
    alias_name: Optional[str] = Field(None, min_length=1, max_length=200)
    language: Optional[str] = Field(None, min_length=2, max_length=20)
    region: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field(None, max_length=500)
    is_verified: Optional[bool] = None


# --- Endpoints ---

@router.post("/contribute")
async def contribute_alias(request: AliasCreate):
    """
    Contribute a new alternative name for a plant variety.

    Anyone can contribute names they know in different languages.
    Contributions are stored and used to expand search coverage.
    Duplicate names for the same variety are automatically skipped.
    """
    client = get_supabase_admin_client()

    try:
        # Verify the variety exists
        variety = (
            client.table("varieties")
            .select("id, variety, crop")
            .eq("id", request.variety_id)
            .execute()
        )
        if not variety.data:
            raise HTTPException(
                status_code=404,
                detail=f"Variety with id={request.variety_id} not found",
            )

        variety_info = variety.data[0]

        # Check for duplicate
        existing = (
            client.table("variety_aliases")
            .select("id")
            .eq("variety_id", request.variety_id)
            .ilike("alias_name", request.alias_name)
            .execute()
        )
        if existing.data:
            return {
                "status": "duplicate",
                "message": f"Alias '{request.alias_name}' already exists for this variety",
                "existing_id": existing.data[0]["id"],
            }

        # Insert the alias
        alias_data = {
            "variety_id": request.variety_id,
            "variety_name": variety_info["variety"],
            "crop_name": variety_info["crop"],
            "alias_name": request.alias_name.strip(),
            "language": request.language.strip(),
            "region": request.region.strip() if request.region else "",
            "source": request.source.strip() if request.source else "",
            "contributor": request.contributor.strip(),
            "is_verified": False,
            "use_count": 0,
        }

        result = client.table("variety_aliases").insert(alias_data).execute()

        logger.info(
            "New alias contributed: '%s' (%s) for variety '%s' by %s",
            request.alias_name, request.language,
            variety_info["variety"], request.contributor,
        )

        return {
            "status": "created",
            "message": f"Thank you! Alias '{request.alias_name}' added for {variety_info['variety']}",
            "alias": result.data[0] if result.data else alias_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error contributing alias: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/contribute/batch")
async def contribute_aliases_batch(request: AliasBatchCreate):
    """
    Contribute multiple aliases at once.
    Useful for importing names from catalogs or databases.
    """
    client = get_supabase_admin_client()
    results = {"created": 0, "duplicates": 0, "errors": 0, "details": []}

    for alias in request.aliases:
        try:
            # Verify variety exists
            variety = (
                client.table("varieties")
                .select("id, variety, crop")
                .eq("id", alias.variety_id)
                .execute()
            )
            if not variety.data:
                results["errors"] += 1
                results["details"].append({
                    "alias_name": alias.alias_name,
                    "status": "error",
                    "message": f"Variety id={alias.variety_id} not found",
                })
                continue

            variety_info = variety.data[0]

            # Check duplicate
            existing = (
                client.table("variety_aliases")
                .select("id")
                .eq("variety_id", alias.variety_id)
                .ilike("alias_name", alias.alias_name)
                .execute()
            )
            if existing.data:
                results["duplicates"] += 1
                continue

            # Insert
            alias_data = {
                "variety_id": alias.variety_id,
                "variety_name": variety_info["variety"],
                "crop_name": variety_info["crop"],
                "alias_name": alias.alias_name.strip(),
                "language": alias.language.strip(),
                "region": alias.region.strip() if alias.region else "",
                "source": alias.source.strip() if alias.source else "",
                "contributor": alias.contributor.strip(),
                "is_verified": False,
                "use_count": 0,
            }
            client.table("variety_aliases").insert(alias_data).execute()
            results["created"] += 1

        except Exception as e:
            results["errors"] += 1
            results["details"].append({
                "alias_name": alias.alias_name,
                "status": "error",
                "message": str(e),
            })

    return results


@router.get("/variety/{variety_id}")
async def get_aliases_for_variety(variety_id: int):
    """
    Get all known aliases/names for a specific variety.
    Returns names in all languages contributed by the community.
    """
    client = get_supabase_admin_client()

    try:
        # Get variety info
        variety = (
            client.table("varieties")
            .select("id, variety, crop, series")
            .eq("id", variety_id)
            .execute()
        )
        if not variety.data:
            raise HTTPException(status_code=404, detail="Variety not found")

        variety_info = variety.data[0]

        # Get all aliases
        aliases = (
            client.table("variety_aliases")
            .select("*")
            .eq("variety_id", variety_id)
            .order("use_count", desc=True)
            .execute()
        )

        # Group by language
        by_language = {}
        for a in aliases.data or []:
            lang = a.get("language", "unknown")
            if lang not in by_language:
                by_language[lang] = []
            by_language[lang].append(a)

        return {
            "variety": variety_info,
            "total_aliases": len(aliases.data or []),
            "languages": list(by_language.keys()),
            "by_language": by_language,
            "aliases": aliases.data or [],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_by_alias(
    name: str = Query(..., min_length=1, description="Name to search (any language)"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Search varieties by any known name in any language.

    This is the core lookup: given a name like '泡泡菊', find the
    matching variety and all its other known names.
    """
    client = get_supabase_admin_client()

    try:
        # Search in aliases
        alias_results = (
            client.table("variety_aliases")
            .select("*")
            .ilike("alias_name", f"%{name}%")
            .limit(limit)
            .execute()
        )

        # Also search in the main varieties table
        variety_results = (
            client.table("varieties")
            .select("id, variety, crop, series, score")
            .ilike("variety", f"%{name}%")
            .limit(limit)
            .execute()
        )

        # Combine results
        found_variety_ids = set()
        matches = []

        # From alias matches
        for a in alias_results.data or []:
            vid = a["variety_id"]
            if vid not in found_variety_ids:
                found_variety_ids.add(vid)
                matches.append({
                    "variety_id": vid,
                    "variety_name": a.get("variety_name", ""),
                    "crop_name": a.get("crop_name", ""),
                    "matched_alias": a["alias_name"],
                    "matched_language": a.get("language", ""),
                    "match_source": "alias",
                })

        # From direct variety name matches
        for v in variety_results.data or []:
            vid = v["id"]
            if vid not in found_variety_ids:
                found_variety_ids.add(vid)
                matches.append({
                    "variety_id": vid,
                    "variety_name": v["variety"],
                    "crop_name": v["crop"],
                    "matched_alias": v["variety"],
                    "matched_language": "en",
                    "match_source": "primary_name",
                })

        return {
            "query": name,
            "total_matches": len(matches),
            "matches": matches,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-names/{variety_id}")
async def get_all_searchable_names(variety_id: int):
    """
    Get ALL searchable names for a variety — primary name + all aliases.

    This is used by the scraping engine to expand search queries
    across multiple languages for comprehensive data collection.
    """
    client = get_supabase_admin_client()

    try:
        # Get primary name
        variety = (
            client.table("varieties")
            .select("id, variety, crop, series")
            .eq("id", variety_id)
            .execute()
        )
        if not variety.data:
            raise HTTPException(status_code=404, detail="Variety not found")

        v = variety.data[0]
        names = [{"name": v["variety"], "language": "en", "is_primary": True}]

        # Get aliases
        aliases = (
            client.table("variety_aliases")
            .select("alias_name, language, is_verified, use_count")
            .eq("variety_id", variety_id)
            .order("use_count", desc=True)
            .execute()
        )

        for a in aliases.data or []:
            names.append({
                "name": a["alias_name"],
                "language": a.get("language", ""),
                "is_primary": False,
                "is_verified": a.get("is_verified", False),
                "use_count": a.get("use_count", 0),
            })

        # Increment use_count for tracking popularity
        if aliases.data:
            for a in aliases.data:
                try:
                    client.table("variety_aliases").update({
                        "use_count": (a.get("use_count", 0) or 0) + 1,
                    }).eq("variety_id", variety_id).eq(
                        "alias_name", a["alias_name"]
                    ).execute()
                except Exception:
                    pass

        return {
            "variety_id": variety_id,
            "crop": v["crop"],
            "total_names": len(names),
            "names": names,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{alias_id}")
async def update_alias(alias_id: int, request: AliasUpdate):
    """Update an existing alias (e.g., mark as verified, fix typo)."""
    client = get_supabase_admin_client()

    try:
        update_data = {}
        if request.alias_name is not None:
            update_data["alias_name"] = request.alias_name.strip()
        if request.language is not None:
            update_data["language"] = request.language.strip()
        if request.region is not None:
            update_data["region"] = request.region.strip()
        if request.source is not None:
            update_data["source"] = request.source.strip()
        if request.is_verified is not None:
            update_data["is_verified"] = request.is_verified

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        result = (
            client.table("variety_aliases")
            .update(update_data)
            .eq("id", alias_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Alias not found")

        return {"status": "updated", "alias": result.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{alias_id}")
async def delete_alias(alias_id: int):
    """Delete an alias."""
    client = get_supabase_admin_client()

    try:
        result = (
            client.table("variety_aliases")
            .delete()
            .eq("id", alias_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Alias not found")

        return {
            "status": "deleted",
            "deleted_alias": result.data[0]["alias_name"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_alias_stats():
    """Get community contribution statistics."""
    client = get_supabase_admin_client()

    try:
        all_aliases = (
            client.table("variety_aliases")
            .select("language, is_verified, contributor")
            .execute()
        )

        data = all_aliases.data or []
        languages = {}
        contributors = set()
        verified = 0

        for a in data:
            lang = a.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1
            contributors.add(a.get("contributor", "anonymous"))
            if a.get("is_verified"):
                verified += 1

        return {
            "total_aliases": len(data),
            "total_languages": len(languages),
            "total_contributors": len(contributors),
            "verified_count": verified,
            "unverified_count": len(data) - verified,
            "by_language": languages,
            "top_contributors": list(contributors)[:20],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
