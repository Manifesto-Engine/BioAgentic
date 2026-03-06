"""Persistent Cortex — AI Memory Engine.

A structured, persistent memory system that gives AI agents episodic,
procedural, semantic, and relational memory across sessions.

Memory types:
  EPISODIC     — What happened (events, outcomes, timestamps)
  PROCEDURAL   — How to do things (skills, workflows)
  SEMANTIC     — What things mean (facts, concepts)
  RELATIONAL   — How things connect (links between memories)
"""
from __future__ import annotations

import sqlite3
import json
import time
import hashlib
import logging
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger("cortex")

DB_PATH = Path(__file__).parent / "cortex.db"
MAX_DB_SIZE_MB = 100
MAX_MEMORY_COUNT = 500


class MemoryType(str, Enum):
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    SEMANTIC = "semantic"
    RELATIONAL = "relational"


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
    linked_ids: list[str]
    metadata: dict


class CortexFullError(Exception):
    """Raised when cortex.db exceeds MAX_DB_SIZE_MB."""


class Cortex:
    """Persistent AI memory engine."""

    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._fts_available = False
        self._init_schema()
        self._init_fts()
        logger.info("Cortex initialized: %s", self.db_path)

    def _init_schema(self):
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
                linked_ids TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
            CREATE INDEX IF NOT EXISTS idx_memories_importance ON memories(importance);
            CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
        """)
        self._conn.commit()

    def _init_fts(self):
        """Initialize FTS5 virtual table. Returns True if available."""
        try:
            self._conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(content, tags, tokenize='porter')
            """)
            self._conn.commit()
            self._fts_available = True
            return True
        except Exception:
            logger.debug("FTS5 not available — using LIKE fallback")
            return False

    @property
    def db_size_mb(self) -> float:
        try:
            return self.db_path.stat().st_size / (1024 * 1024)
        except FileNotFoundError:
            return 0.0

    @property
    def is_full(self) -> bool:
        return self.db_size_mb >= MAX_DB_SIZE_MB

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
        if self.is_full:
            raise CortexFullError(f"Cortex at {self.db_size_mb:.1f}MB — refusing write")

        tags = tags or []
        metadata = metadata or {}
        now = time.time()
        mem_id = hashlib.sha256(
            f"{content}:{now}:{source}".encode()
        ).hexdigest()[:16]

        memory = Memory(
            id=mem_id,
            type=memory_type,
            content=content,
            tags=tags,
            importance=importance,
            created_at=now,
            last_accessed=now,
            access_count=0,
            source=source,
            linked_ids=[],
            metadata=metadata,
        )

        self._conn.execute(
            """INSERT OR REPLACE INTO memories
               (id, type, content, tags, importance, created_at,
                last_accessed, access_count, source, linked_ids, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                memory.id, memory.type.value, memory.content,
                json.dumps(memory.tags), memory.importance,
                memory.created_at, memory.last_accessed,
                memory.access_count, memory.source,
                json.dumps(memory.linked_ids), json.dumps(memory.metadata),
            ),
        )

        if self._fts_available:
            try:
                self._conn.execute(
                    "INSERT INTO memories_fts (rowid, content, tags) "
                    "VALUES ((SELECT rowid FROM memories WHERE id = ?), ?, ?)",
                    (memory.id, memory.content, json.dumps(memory.tags)),
                )
            except Exception:
                pass

        self._conn.commit()
        self._enforce_count_cap()
        return memory

    def recall(
        self,
        query: str,
        limit: int = 10,
        memory_type: MemoryType | None = None,
    ) -> list[Memory]:
        """Search memories by keyword query. Updates access counts."""
        if self._fts_available:
            try:
                return self._recall_fts(query, limit, memory_type)
            except Exception:
                pass
        return self._recall_like(query, limit, memory_type)

    def _recall_fts(
        self, query: str, limit: int, memory_type: MemoryType | None,
    ) -> list[Memory]:
        safe_query = " ".join(
            w for w in query.split() if w.isalnum()
        )
        if not safe_query:
            return []

        type_clause = ""
        params: list = [safe_query]
        if memory_type:
            type_clause = "AND m.type = ?"
            params.append(memory_type.value)
        params.append(limit)

        rows = self._conn.execute(
            f"""SELECT m.* FROM memories m
                JOIN memories_fts f ON f.rowid = m.rowid
                WHERE memories_fts MATCH ?
                {type_clause}
                ORDER BY m.importance DESC
                LIMIT ?""",
            params,
        ).fetchall()

        memories = [self._row_to_memory(r) for r in rows]
        self._touch(memories)
        return memories

    def _recall_like(
        self, query: str, limit: int, memory_type: MemoryType | None,
    ) -> list[Memory]:
        words = [w for w in query.split() if len(w) >= 2]
        if not words:
            return []

        clauses = " AND ".join(
            "(content LIKE ? OR tags LIKE ?)" for _ in words
        )
        params: list = []
        for w in words:
            p = f"%{w}%"
            params.extend([p, p])

        type_clause = ""
        if memory_type:
            type_clause = "AND type = ?"
            params.append(memory_type.value)

        params.append(limit)

        rows = self._conn.execute(
            f"""SELECT * FROM memories
                WHERE {clauses} {type_clause}
                ORDER BY importance DESC
                LIMIT ?""",
            params,
        ).fetchall()

        memories = [self._row_to_memory(r) for r in rows]
        self._touch(memories)
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
        clauses = " OR ".join("tags LIKE ?" for _ in tags)
        params = [f'%"{t}"%' for t in tags]
        params.append(limit)
        rows = self._conn.execute(
            f"""SELECT * FROM memories
                WHERE {clauses}
                ORDER BY importance DESC LIMIT ?""",
            params,
        ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def consolidate(self, max_age_hours: int = 72) -> list[Memory]:
        """Consolidate old episodic memories into semantic knowledge.

        Like human sleep — compresses episodes into distilled facts.
        """
        cutoff = time.time() - (max_age_hours * 3600)
        rows = self._conn.execute(
            """SELECT * FROM memories
               WHERE type = 'episodic' AND created_at < ?
               ORDER BY importance DESC LIMIT 10""",
            (cutoff,),
        ).fetchall()

        if len(rows) < 3:
            return []

        episodes = [self._row_to_memory(r) for r in rows]
        summary = "; ".join(e.content[:80] for e in episodes[:5])
        semantic = self.remember(
            content=f"Consolidated: {summary}",
            memory_type=MemoryType.SEMANTIC,
            tags=["consolidated", "auto"],
            importance=0.7,
            source="metabolism",
        )

        for ep in episodes:
            self._conn.execute(
                "UPDATE memories SET importance = importance * 0.5 WHERE id = ?",
                (ep.id,),
            )
        self._conn.commit()
        return [semantic]

    def decay(self, decay_rate: float = 0.995) -> int:
        """Apply Ebbinghaus decay to all memories.

        High-importance and recently-accessed memories decay slower.
        Returns count of memories decayed.
        """
        now = time.time()
        rows = self._conn.execute(
            "SELECT id, importance, last_accessed, tags FROM memories"
        ).fetchall()

        decayed = 0
        for row in rows:
            mem_id, importance, last_accessed, tags_json = row
            tags = json.loads(tags_json) if tags_json else []

            # Identity-tagged memories are immune to decay
            if "identity" in tags:
                continue

            age_hours = (now - last_accessed) / 3600
            effective_decay = decay_rate ** (1 + age_hours * 0.01)
            new_importance = importance * effective_decay

            if new_importance < 0.01:
                self._conn.execute("DELETE FROM memories WHERE id = ?", (mem_id,))
            else:
                self._conn.execute(
                    "UPDATE memories SET importance = ? WHERE id = ?",
                    (new_importance, mem_id),
                )
            decayed += 1

        self._conn.commit()
        return decayed

    def count(self) -> int:
        """Total memory count."""
        row = self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()
        return row[0] if row else 0

    def stats(self) -> dict:
        """Cortex statistics."""
        return {
            "total_memories": self.count(),
            "db_size_mb": round(self.db_size_mb, 2),
            "fts_available": self._fts_available,
            "max_size_mb": MAX_DB_SIZE_MB,
            "max_count": MAX_MEMORY_COUNT,
        }

    def close(self):
        """Close the database connection."""
        try:
            self._conn.close()
        except Exception:
            pass

    # ── Internal ──────────────────────────────────────────

    def _row_to_memory(self, row: tuple) -> Memory:
        return Memory(
            id=row[0],
            type=MemoryType(row[1]),
            content=row[2],
            tags=json.loads(row[3]) if row[3] else [],
            importance=row[4],
            created_at=row[5],
            last_accessed=row[6],
            access_count=row[7],
            source=row[8] or "",
            linked_ids=json.loads(row[9]) if row[9] else [],
            metadata=json.loads(row[10]) if row[10] else {},
        )

    def _touch(self, memories: list[Memory]):
        """Update access timestamp and count for retrieved memories."""
        now = time.time()
        for m in memories:
            self._conn.execute(
                "UPDATE memories SET last_accessed = ?, access_count = access_count + 1 WHERE id = ?",
                (now, m.id),
            )
        if memories:
            self._conn.commit()

    def _enforce_count_cap(self):
        """Prune lowest-importance memories when count exceeds cap."""
        count = self.count()
        if count <= MAX_MEMORY_COUNT:
            return
        excess = count - MAX_MEMORY_COUNT
        self._conn.execute(
            """DELETE FROM memories WHERE id IN (
                SELECT id FROM memories
                WHERE tags NOT LIKE '%"identity"%'
                ORDER BY importance ASC LIMIT ?
            )""",
            (excess,),
        )
        self._conn.commit()
