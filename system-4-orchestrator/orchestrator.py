"""Tiered orchestration with checkpoints and explicit failure recovery."""


def run_pipeline(task: dict, stages: list[tuple[str, callable]]) -> dict:
    state = {"task": task, "completed": [], "results": {}, "checkpoint": 0}
    events = []
    for index, (name, stage) in enumerate(stages, start=1):
        events.append({"event": "stage_started", "stage": name, "index": index})
        try:
            result = stage(state)
        except Exception as exc:
            events.append({
                "event": "stage_failed",
                "stage": name,
                "error_type": type(exc).__name__,
            })
            return {
                "status": "failed",
                "failed_stage": name,
                "state": state,
                "events": events,
            }
        state["results"][name] = result
        state["completed"].append(name)
        state["checkpoint"] = index
        events.append({"event": "checkpoint_saved", "stage": name, "index": index})
    return {"status": "completed", "state": state, "events": events}


def filter_defects_sql(defects: list[dict], status: str = "open",
                       severity: str = "high") -> list[dict]:
    """Use SQL to filter a defect slice instead of filtering in Python."""
    import sqlite3
    import json

    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("""
            CREATE TABLE defects (
                id TEXT, status TEXT, severity TEXT, payload TEXT
            )
        """)
        connection.executemany(
            "INSERT INTO defects VALUES (?, ?, ?, ?)",
            [
                (
                    str(item.get("id", "")),
                    str(item.get("status", "")),
                    str(item.get("severity", "")),
                    json.dumps(item),
                )
                for item in defects
            ],
        )
        rows = connection.execute(
            """
            SELECT payload FROM defects
            WHERE status = ? AND severity = ?
            ORDER BY id
            """,
            (status, severity),
        ).fetchall()
        return [json.loads(row[0]) for row in rows]
    finally:
        connection.close()


def create_hot_state(state: dict, max_bytes: int = 5_000) -> dict:
    """Create a compact JSON-safe state bounded by UTF-8 byte size."""
    import json

    if max_bytes < 2:
        raise ValueError("max_bytes must be at least 2")

    compact = {
        "task": state.get("task"),
        "completed": list(state.get("completed", [])),
        "checkpoint": state.get("checkpoint", 0),
        "results": state.get("results", {}),
    }

    encoded = json.dumps(
        compact, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")

    if len(encoded) <= max_bytes:
        return {"state": compact, "bytes": len(encoded), "truncated": False}

    # Retain essential checkpoint metadata; omit bulky results if necessary.
    compact["results"] = {}
    compact["truncated"] = True
    encoded = json.dumps(
        compact, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")

    if len(encoded) > max_bytes:
        compact = {
            "checkpoint": state.get("checkpoint", 0),
            "truncated": True,
        }
        encoded = json.dumps(compact, separators=(",", ":")).encode("utf-8")

    if len(encoded) > max_bytes:
        raise ValueError("max_bytes is too small for checkpoint metadata")

    return {"state": compact, "bytes": len(encoded), "truncated": True}


def should_resume(checkpoint_age_seconds: float,
                  staleness_threshold_seconds: float) -> bool:
    """Resume only when a checkpoint is fresh enough to trust."""
    if checkpoint_age_seconds < 0:
        raise ValueError("checkpoint age cannot be negative")
    if staleness_threshold_seconds < 0:
        raise ValueError("staleness threshold cannot be negative")
    return checkpoint_age_seconds <= staleness_threshold_seconds


def fork_state(state: dict) -> dict:
    """Give a branch an isolated copy of state; mutations won't leak."""
    import copy
    return copy.deepcopy(state)
