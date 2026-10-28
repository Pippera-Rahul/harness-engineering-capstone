import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from orchestrator import (
    run_pipeline,
    filter_defects_sql,
    create_hot_state,
    should_resume,
    fork_state,
)

evidence = ROOT / "evidence"
evidence.mkdir(exist_ok=True)

def intake(state):
    return {
        "batch_id": "SHIFT-2026-10-28-A",
        "reported_defects": 5,
    }

def validate(state):
    return {"validation": "passed", "records_checked": 5}

def analyze(state):
    defects = [
        {"id": "D001", "status": "open", "severity": "high",
         "description": "Scanner intermittently fails"},
        {"id": "D002", "status": "open", "severity": "low",
         "description": "Label alignment issue"},
        {"id": "D003", "status": "closed", "severity": "high",
         "description": "Previously fixed conveyor fault"},
        {"id": "D004", "status": "open", "severity": "high",
         "description": "Repeated package misrouting"},
        {"id": "D005", "status": "open", "severity": "medium",
         "description": "Delayed dashboard refresh"},
    ]
    filtered = filter_defects_sql(defects, status="open", severity="high")
    return {
        "sql_filter": "status = 'open' AND severity = 'high'",
        "matching_count": len(filtered),
        "defects": filtered,
    }

def summarize(state):
    return {
        "summary": "High-severity open defects require follow-up.",
        "recommended_action": "Assign owners and investigate recurring failures.",
    }

stages = [
    ("intake", intake),
    ("validate", validate),
    ("analyze", analyze),
    ("summarize", summarize),
]

result = run_pipeline(
    {"workflow": "multi-shift quality monitoring", "shift": "A"},
    stages,
)

if result["status"] != "completed":
    raise SystemExit(f"Workflow failed: {result}")

state = result["state"]
hot = create_hot_state(state, max_bytes=5000)

# Demonstrate independent branch state.
branch = fork_state(state)
branch["results"]["branch_only"] = {"isolated": True}
assert "branch_only" not in state["results"]

# Demonstrate checkpoint freshness policy.
resume_checks = {
    "fresh_checkpoint_resumes": should_resume(30, 60),
    "stale_checkpoint_resumes": should_resume(90, 60),
}

(evidence / "orchestration_run.json").write_text(
    json.dumps(result, indent=2) + "\n",
    encoding="utf-8",
)
(evidence / "hot_state.json").write_text(
    json.dumps(hot, indent=2) + "\n",
    encoding="utf-8",
)
(evidence / "defect_slice.json").write_text(
    json.dumps(state["results"]["analyze"], indent=2) + "\n",
    encoding="utf-8",
)
(evidence / "checkpoint_policy.json").write_text(
    json.dumps(resume_checks, indent=2) + "\n",
    encoding="utf-8",
)

print("Workflow status:", result["status"])
print("Completed stages:", ", ".join(state["completed"]))
print("Checkpoint:", state["checkpoint"])
print("SQL-filtered defects:", state["results"]["analyze"]["matching_count"])
print("Hot-state bytes:", hot["bytes"])
print("Hot-state within 5000 bytes:", hot["bytes"] <= 5000)
print("Checkpoint policy:", resume_checks)
print("Evidence saved under:", evidence)
