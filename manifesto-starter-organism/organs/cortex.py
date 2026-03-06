"""Cortex — Persistent Memory Engine.

A structured, persistent memory system backed by SQLite.
Gives the organism episodic, procedural, and semantic memory
that survives restarts.

Memory types:
  EPISODIC   — What happened (events, outcomes, timestamps)
  PROCEDURAL — How to do things (learned behaviors)
  SEMANTIC   — What things mean (distilled facts)
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import sqlite3
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger("organism.cortex")

MAX_DB_SIZE_MB = 100
MAX_MEMORY_COUNT = 500


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    SEMANTIC = "semantic"


@dataclass
class Memory:
    id: str
    type: MemoryType
    content: str
    tags: list[str]
    importance: float
    created_at: float
    last_accessed: float
    access_count: int
    source: str
    metadata: dict

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d


class CortexFullError(Exception):
    """Raised when cortex.db exceeds MAX_DB_SIZE_MB."""


class Cortex:
    """Persistent AI memory engine."""

    def __init__(self, db_path: str | Path = "cortex.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._init_schema()
        logger.info("🧠 Cortex initialized — %s", self.db_path)

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                importance REAL DEFAULT 0.5,
                created_at REAL NOT NULL,
                last_accessed REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                source TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(type);
            CREATE INDEX IF NOT EXISTS idx_mem_importance ON memories(importance DESC);
            CREATE INDEX IF NOT EXISTS idx_mem_created ON memories(created_at DESC);
        """)
        self._conn.commit()

    # ── Store ─────────────────────────────────────────────

    def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        tags: list[str] | None = None,
        importance: float = 0.5,
        source: str = "",
        metadata: dict | None = None,
    ) -> Memory:
        """Store a memory. Returns the created Memory object."""
        if self.db_size_mb > MAX_DB_SIZE_MB:
            raise CortexFullError(
                f"Cortex full: {self.db_size_mb:.1f}MB > {MAX_DB_SIZE_MB}MB"
            )

        now = time.time()
        mem_id = hashlib.sha256(
            f"{content}:{now}".encode()
        ).hexdigest()[:16]

        tags = tags or []
        metadata = metadata or {}

        mem = Memory(
            id=mem_id,
            type=memory_type,
            content=content,
            tags=tags,
            importance=max(0.0, min(1.0, importance)),
            created_at=now,
            last_accessed=now,
            access_count=0,
            source=source,
            metadata=metadata,
        )

        self._conn.execute(
            """INSERT OR REPLACE INTO memories
               (id, type, content, tags, importance, created_at,
                last_accessed, access_count, source, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                mem.id, mem.type.value, mem.content,
                json.dumps(mem.tags), mem.importance, mem.created_at,
                mem.last_accessed, mem.access_count, mem.source,
                json.dumps(mem.metadata),
            ),
        )
        self._conn.commit()

        # Auto-prune if over capacity
        count = self._count()
        if count > MAX_MEMORY_COUNT:
            self._prune(count - MAX_MEMORY_COUNT)

        logger.debug("Remembered: %s (%.2f)", mem_id, mem.importance)
        return mem

    # ── Recall ────────────────────────────────────────────

    def recall(
        self,
        query: str,
        limit: int = 10,
        memory_type: MemoryType | None = None,
    ) -> list[Memory]:
        """Search memories by keyword query. Updates access counts."""
        words = [w.strip() for w in query.split() if w.strip()]
        if not words:
            return []

        conditions = []
        params: list = []
        for word in words:
            conditions.append("content LIKE ?")
            params.append(f"%{word}%")

        where = " AND ".join(conditions)
        if memory_type:
            where += " AND type = ?"
            params.append(memory_type.value)

        params.append(limit)
        rows = self._conn.execute(
            f"""SELECT * FROM memories
                WHERE {where}
                ORDER BY importance DESC, last_accessed DESC
                LIMIT ?""",
            params,
        ).fetchall()

        memories = [self._row_to_memory(r) for r in rows]

        # Update access counts
        now = time.time()
        for mem in memories:
            self._conn.execute(
                "UPDATE memories SET access_count = access_count + 1, "
                "last_accessed = ? WHERE id = ?",
                (now, mem.id),
            )
        if memories:
            self._conn.commit()

        return memories

    def recall_recent(self, hours: int = 24, limit: int = 20) -> list[Memory]:
        """Get recent memories."""
        cutoff = time.time() - (hours * 3600)
        rows = self._conn.execute(
            """SELECT * FROM memories
               WHERE created_at > ?
               ORDER BY created_at DESC LIMIT ?""",
            (cutoff, limit),
        ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def recall_by_tags(self, tags: list[str], limit: int = 10) -> list[Memory]:
        """Find memories matching any of the given tags."""
        if not tags:
            return []
        conditions = ["tags LIKE ?" for _ in tags]
        params = [f'%"{t}"%' for t in tags]
        params.append(limit)
        rows = self._conn.execute(
            f"""SELECT * FROM memories
                WHERE {" OR ".join(conditions)}
                ORDER BY importance DESC LIMIT ?""",
            params,
        ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    # ── Consolidation ─────────────────────────────────────

    def consolidate(self, max_age_hours: int = 72) -> list[Memory]:
        """Consolidate old episodic memories into semantic knowledge.

        Like human sleep — compresses episodes into distilled facts.
        """
        cutoff = time.time() - (max_age_hours * 3600)
        rows = self._conn.execute(
            """SELECT * FROM memories
               WHERE type = 'episodic' AND created_at < ?
               ORDER BY importance DESC LIMIT 20""",
            (cutoff,),
        ).fetchall()

        if not rows:
            return []

        old = [self._row_to_memory(r) for r in rows]
        consolidated: list[Memory] = []

        # Group by first tag and compress
        groups: dict[str, list[Memory]] = {}
        for mem in old:
            key = mem.tags[0] if mem.tags else "general"
            groups.setdefault(key, []).append(mem)

        for tag, mems in groups.items():
            if len(mems) < 2:
                continue
            summary = f"Consolidated {len(mems)} episodes about '{tag}': "
            summary += "; ".join(m.content[:80] for m in mems[:5])
            new_mem = self.remember(
                content=summary,
                memory_type=MemoryType.SEMANTIC,
                tags=[tag, "consolidated"],
                importance=max(m.importance for m in mems),
                source="consolidation",
            )
            consolidated.append(new_mem)
            # Remove originals
            ids = [m.id for m in mems]
            placeholders = ",".join("?" for _ in ids)
            self._conn.execute(
                f"DELETE FROM memories WHERE id IN ({placeholders})", ids
            )

        if consolidated:
            self._conn.commit()
            logger.info("Consolidated %d memory groups", len(consolidated))

        return consolidated

    # ── Decay ─────────────────────────────────────────────

    def decay(self, factor: float = 0.98) -> int:
        """Apply Ebbinghaus decay — unused memories fade.

        Memories accessed recently decay slower. Memories below 0.05
        importance are deleted.
        """
        now = time.time()
        rows = self._conn.execute(
            "SELECT id, importance, last_accessed FROM memories"
        ).fetchall()

        decayed = 0
        to_delete: list[str] = []

        for mem_id, importance, last_accessed in rows:
            age_hours = (now - last_accessed) / 3600
            # Older = faster decay
            adjusted_factor = factor ** (1 + math.log1p(age_hours) * 0.1)
            new_importance = importance * adjusted_factor

            if new_importance < 0.05:
                to_delete.append(mem_id)
            else:
                self._conn.execute(
                    "UPDATE memories SET importance = ? WHERE id = ?",
                    (round(new_importance, 4), mem_id),
                )
            decayed += 1

        if to_delete:
            placeholders = ",".join("?" for _ in to_delete)
            self._conn.execute(
                f"DELETE FROM memories WHERE id IN ({placeholders})", to_delete
            )
            logger.info("Decay pruned %d faded memories", len(to_delete))

        self._conn.commit()
        return decayed

    # ── Stats ─────────────────────────────────────────────

    @property
    def db_size_mb(self) -> float:
        if self.db_path.exists():
            return self.db_path.stat().st_size / (1024 * 1024)
        return 0.0

    def stats(self) -> dict:
        """Memory statistics."""
        total = self._count()
        by_type = {}
        for row in self._conn.execute(
            "SELECT type, COUNT(*) FROM memories GROUP BY type"
        ).fetchall():
            by_type[row[0]] = row[1]
        return {
            "total_memories": total,
            "by_type": by_type,
            "db_size_mb": round(self.db_size_mb, 2),
            "max_db_size_mb": MAX_DB_SIZE_MB,
            "max_memory_count": MAX_MEMORY_COUNT,
        }

    # ── Internal ──────────────────────────────────────────

    def _count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]

    def _prune(self, n: int) -> None:
        """Delete the n least important memories."""
        self._conn.execute(
            "DELETE FROM memories WHERE id IN ("
            "  SELECT id FROM memories ORDER BY importance ASC LIMIT ?"
            ")", (n,),
        )
        self._conn.commit()
        logger.info("Pruned %d low-importance memories", n)

    def _row_to_memory(self, row: tuple) -> Memory:
        return Memory(
            id=row[0],
            type=MemoryType(row[1]),
            content=row[2],
            tags=json.loads(row[3]),
            importance=row[4],
            created_at=row[5],
            last_accessed=row[6],
            access_count=row[7],
            source=row[8],
            metadata=json.loads(row[9]),
        )

    def close(self) -> None:
        self._conn.close()
