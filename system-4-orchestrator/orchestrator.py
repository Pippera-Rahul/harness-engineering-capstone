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
