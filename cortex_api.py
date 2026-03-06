"""Cortex API — FastAPI routes for memory access.

Provides HTTP endpoints for reading and writing organism memories.
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/cortex", tags=["cortex"])

# The organism instance is wired at startup
_organism = None


def set_organism(org):
    global _organism
    _organism = org


class RememberRequest(BaseModel):
    content: str
    tags: list[str] = []
    importance: float = 0.5
    memory_type: str = "episodic"


@router.post("/remember")
def remember(req: RememberRequest):
    """Store a memory in the cortex."""
    from cortex import MemoryType
    mem = _organism.cortex.remember(
        content=req.content,
        memory_type=MemoryType(req.memory_type),
        tags=req.tags,
        importance=req.importance,
        source="api",
    )
    return {"id": mem.id, "content": mem.content, "tags": mem.tags}


@router.get("/recall")
def recall(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search cortex memories."""
    memories = _organism.cortex.recall(query, limit=limit)
    return [
        {
            "id": m.id,
            "type": m.type.value,
            "content": m.content,
            "tags": m.tags,
            "importance": round(m.importance, 3),
            "created_at": m.created_at,
        }
        for m in memories
    ]


@router.get("/recent")
def recent(hours: int = Query(24, ge=1, le=168), limit: int = Query(20, ge=1, le=100)):
    """Get recent memories."""
    memories = _organism.cortex.recall_recent(hours=hours, limit=limit)
    return [
        {
            "id": m.id,
            "type": m.type.value,
            "content": m.content,
            "tags": m.tags,
            "importance": round(m.importance, 3),
            "created_at": m.created_at,
        }
        for m in memories
    ]


@router.get("/stats")
def stats():
    """Cortex statistics."""
    return _organism.cortex.stats()
