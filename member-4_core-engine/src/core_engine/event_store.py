"""
SQLite Event Store for Tesseract Core Engine.
Append-only persistence for raw and structured events, sessions, episodes,
and historical friction records with auto-purge retention policies.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .models import Episode, FrictionScore, Session, TesseractEvent, utc_now_iso

logger = logging.getLogger("tesseract.core_engine.event_store")


class EventStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema if not exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    payload_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
                CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);

                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    events_count INTEGER NOT NULL DEFAULT 0,
                    sources_json TEXT NOT NULL DEFAULT '[]',
                    primary_intent TEXT NOT NULL DEFAULT 'working',
                    topics_json TEXT NOT NULL DEFAULT '[]'
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);
                CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active);

                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    session_ids_json TEXT NOT NULL DEFAULT '[]',
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    topic TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    events_count INTEGER NOT NULL DEFAULT 0,
                    friction_score REAL NOT NULL DEFAULT 0.0,
                    signals_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_episodes_start_time ON episodes(start_time);
                CREATE INDEX IF NOT EXISTS idx_episodes_topic ON episodes(topic);
                CREATE INDEX IF NOT EXISTS idx_episodes_outcome ON episodes(outcome);

                CREATE TABLE IF NOT EXISTS friction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    score REAL NOT NULL,
                    level TEXT NOT NULL,
                    signals_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_friction_timestamp ON friction_history(timestamp);
                """)
        logger.info("EventStore initialized at %s", self.db_path)

    # --- Events ---

    def insert_event(self, event: TesseractEvent) -> None:
        """Insert a single event into SQLite."""
        session_id = event.metadata.session_id if isinstance(event.metadata, object) else None
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO events
                (event_id, source, event_type, timestamp, session_id,
                 payload_json, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.source,
                    event.event_type,
                    event.timestamp,
                    session_id,
                    json.dumps(event.payload),
                    json.dumps(
                        event.metadata.to_dict()
                        if hasattr(event.metadata, "to_dict")
                        else event.metadata
                    ),
                    utc_now_iso(),
                ),
            )

    def get_recent_events(
        self,
        limit: int = 50,
        source: str | None = None,
        event_type: str | None = None,
        since_iso: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query recent events with optional filters."""
        query = "SELECT * FROM events WHERE 1=1"
        params: list[Any] = []

        if source:
            query += " AND source = ?"
            params.append(source)
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        if since_iso:
            query += " AND timestamp >= ?"
            params.append(since_iso)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            events = []
            for row in rows:
                events.append(
                    {
                        "event_id": row["event_id"],
                        "source": row["source"],
                        "event_type": row["event_type"],
                        "timestamp": row["timestamp"],
                        "payload": json.loads(row["payload_json"]),
                        "metadata": json.loads(row["metadata_json"]),
                    }
                )
            return events

    def get_event_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM events")
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    # --- Sessions ---

    def insert_or_update_session(self, session: Session) -> None:
        """Insert or update session."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions
                (session_id, start_time, end_time, is_active, events_count,
                 sources_json, primary_intent, topics_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    end_time=excluded.end_time,
                    is_active=excluded.is_active,
                    events_count=excluded.events_count,
                    sources_json=excluded.sources_json,
                    primary_intent=excluded.primary_intent,
                    topics_json=excluded.topics_json
                """,
                (
                    session.session_id,
                    session.start_time,
                    session.end_time,
                    1 if session.is_active else 0,
                    session.events_count,
                    json.dumps(session.sources),
                    session.primary_intent,
                    json.dumps(session.topics),
                ),
            )

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
            if not row:
                return None
            return {
                "session_id": row["session_id"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "is_active": bool(row["is_active"]),
                "events_count": row["events_count"],
                "sources": json.loads(row["sources_json"]),
                "primary_intent": row["primary_intent"],
                "topics": json.loads(row["topics_json"]),
            }

    def get_active_session(self) -> dict[str, Any] | None:
        """Get most recent active session."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE is_active = 1 ORDER BY start_time DESC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            return {
                "session_id": row["session_id"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "is_active": True,
                "events_count": row["events_count"],
                "sources": json.loads(row["sources_json"]),
                "primary_intent": row["primary_intent"],
                "topics": json.loads(row["topics_json"]),
            }

    # --- Episodes ---

    def insert_or_update_episode(self, episode: Episode) -> None:
        """Insert or update episode."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO episodes
                (episode_id, session_ids_json, start_time, end_time, topic,
                 intent, outcome, events_count, friction_score, signals_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(episode_id) DO UPDATE SET
                    session_ids_json=excluded.session_ids_json,
                    end_time=excluded.end_time,
                    topic=excluded.topic,
                    intent=excluded.intent,
                    outcome=excluded.outcome,
                    events_count=excluded.events_count,
                    friction_score=excluded.friction_score,
                    signals_json=excluded.signals_json
                """,
                (
                    episode.episode_id,
                    json.dumps(episode.session_ids),
                    episode.start_time,
                    episode.end_time,
                    episode.topic,
                    episode.intent,
                    episode.outcome,
                    episode.events_count,
                    episode.friction_score,
                    json.dumps(episode.signals),
                ),
            )

    def get_recent_episodes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent learning episodes."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM episodes ORDER BY start_time DESC LIMIT ?", (limit,)
            ).fetchall()
            episodes = []
            for row in rows:
                episodes.append(
                    {
                        "episode_id": row["episode_id"],
                        "session_ids": json.loads(row["session_ids_json"]),
                        "start_time": row["start_time"],
                        "end_time": row["end_time"],
                        "topic": row["topic"],
                        "intent": row["intent"],
                        "outcome": row["outcome"],
                        "events_count": row["events_count"],
                        "friction_score": row["friction_score"],
                        "signals": json.loads(row["signals_json"]),
                    }
                )
            return episodes

    # --- Friction History ---

    def record_friction_score(self, topic: str, friction: FrictionScore) -> None:
        """Record friction history entry."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO friction_history (timestamp, topic, score, level, signals_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    utc_now_iso(),
                    topic,
                    friction.score,
                    friction.level,
                    json.dumps(friction.signals),
                ),
            )

    # --- Retention Purge ---

    def purge_expired_data(self, raw_retention_days: int = 30) -> int:
        """Auto-purge events older than retention days."""
        cutoff_date = (datetime.now(UTC) - timedelta(days=raw_retention_days)).isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM events WHERE timestamp < ?", (cutoff_date,))
            deleted_count = cursor.rowcount
            logger.info("Purged %d expired events older than %s", deleted_count, cutoff_date)
            return deleted_count

    # --- Analytics ---

    def get_analytics_summary(self) -> dict[str, Any]:
        """Aggregate analytics summary."""
        with self._get_connection() as conn:
            total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            total_sessions = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            total_episodes = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            sources_breakdown = conn.execute(
                "SELECT source, COUNT(*) as cnt FROM events GROUP BY source"
            ).fetchall()
            intents_breakdown = conn.execute(
                "SELECT intent, COUNT(*) as cnt FROM episodes GROUP BY intent"
            ).fetchall()

            return {
                "total_events": total_events,
                "total_sessions": total_sessions,
                "total_episodes": total_episodes,
                "sources": {row["source"]: row["cnt"] for row in sources_breakdown},
                "intents": {row["intent"]: row["cnt"] for row in intents_breakdown},
                "generated_at": utc_now_iso(),
            }

    def clear_all_data(self) -> None:
        """Completely wipe all events, sessions, episodes, and friction history."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM events")
            conn.execute("DELETE FROM sessions")
            conn.execute("DELETE FROM episodes")
            conn.execute("DELETE FROM friction_history")
        logger.info("Cleared all data from EventStore at %s", self.db_path)

    def get_browser_activity_summary(self) -> dict[str, Any]:
        """Aggregate browser sensor telemetry for dashboard and intelligence layers."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE source = 'browser' ORDER BY timestamp DESC LIMIT 500"
            ).fetchall()

            searches = []
            youtube_videos = []
            domain_counts: dict[str, int] = {}
            total_watch_seconds = 0
            event_count = len(rows)

            for r in rows:
                etype = r["event_type"]
                try:
                    payload = json.loads(r["payload_json"])
                except Exception:
                    payload = {}

                # Domain aggregation from URLs
                url = payload.get("url") or payload.get("video_url") or payload.get("from_url") or ""
                if url:
                    from urllib.parse import urlparse
                    try:
                        parsed = urlparse(url)
                        domain = parsed.netloc or parsed.path
                        domain = domain.split(":")[0]
                        if domain.startswith("www."):
                            domain = domain[4:]
                        if domain:
                            domain_counts[domain] = domain_counts.get(domain, 0) + 1
                    except Exception:
                        pass

                if etype == "search_performed":
                    query = payload.get("query")
                    engine = payload.get("engine", "Google")
                    if query and not any(s["query"] == query for s in searches):
                        searches.append({
                            "query": query,
                            "engine": engine,
                            "timestamp": r["timestamp"]
                        })
                elif etype == "youtube_watching":
                    title = payload.get("video_title") or payload.get("title") or "YouTube Video"
                    v_url = payload.get("video_url") or payload.get("url") or ""
                    channel = payload.get("channel") or "YouTube"
                    watch_time = int(payload.get("watch_time_s") or payload.get("duration_s") or 60)
                    total_watch_seconds += watch_time
                    if v_url and not any(y["url"] == v_url for y in youtube_videos):
                        youtube_videos.append({
                            "title": title,
                            "url": v_url,
                            "channel": channel,
                            "duration_s": payload.get("duration_s"),
                            "watch_time_s": watch_time,
                            "timestamp": r["timestamp"]
                        })

            top_domains = sorted(
                [{"domain": k, "count": v} for k, v in domain_counts.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:10]

            return {
                "total_browser_events": event_count,
                "top_domains": top_domains,
                "recent_searches": searches[:15],
                "youtube_videos": youtube_videos[:15],
                "total_watch_minutes": round(total_watch_seconds / 60, 1),
                "generated_at": utc_now_iso(),
            }

