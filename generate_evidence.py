import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "evidence"
OUT.mkdir(exist_ok=True)

sys.path.insert(0, str(ROOT / "system-1-agentic-loop"))
sys.path.insert(0, str(ROOT / "system-2-context-strategy"))
sys.path.insert(0, str(ROOT / "system-4-orchestrator"))

from agent_loop import Turn, run_agent
from context_strategy import select_context
from orchestrator import run_pipeline

# 1. Actual stop_reason-driven loop trace
turns = iter([
    Turn(stop_reason="tool_use", tool_name="lookup_claim",
         tool_input={"claim_id": "CL-1001"}),
    Turn(stop_reason="end_turn", content="Claim lookup completed."),
])
trace = []

def next_turn(messages, tool_results):
    turn = next(turns)
    trace.append({
        "stop_reason": turn.stop_reason,
        "tool_name": turn.tool_name,
        "tool_input": turn.tool_input,
        "content": turn.content
    })
    return turn

result = run_agent(
    next_turn,
    {"lookup_claim": lambda data: {"claim_id": data["claim_id"], "found": True}},
    max_turns=8
)
(OUT / "stop_reason_trace.json").write_text(
    json.dumps({"trace": trace, "result": str(result)}, indent=2),
    encoding="utf-8"
)

# 2. Actual context selection and budget accounting
items = [
    {"id": "claim-summary", "text": "Claim CL-1001: submitted; documents received.", "priority": 10},
    {"id": "policy-rule", "text": "Verify policy eligibility before approval.", "priority": 9},
    {"id": "old-note", "text": "Previous follow-up note with low relevance.", "priority": 1},
]
context_result = select_context(items, budget=100)
(OUT / "budget.json").write_text(
    json.dumps(context_result, indent=2, default=str),
    encoding="utf-8"
)

# 3. Actual orchestrator execution with a deliberate failure
def intake(task):
    return {"task": task, "claim_id": "CL-1001"}

def validate(state):
    return {"validated": True, "claim_id": state["results"]["intake"]["claim_id"]}

def summarize(state):
    raise RuntimeError("Demonstration failure: summary service unavailable")

pipeline_result = run_pipeline(
    "Process claim CL-1001",
    [("intake", intake), ("validate", validate), ("summarize", summarize)]
)
# Save a minimal JSON-safe report without recursive stage result objects.
pipeline_state = pipeline_result.get("state", {})
safe_pipeline_result = {
    "status": pipeline_result.get("status"),
    "failed_stage": pipeline_result.get("failed_stage"),
    "completed": list(pipeline_state.get("completed", [])),
    "checkpoint": pipeline_state.get("checkpoint", 0),
    "result_stage_names": list(pipeline_state.get("results", {}).keys()),
    "events": [
        {
            "event": event.get("event"),
            "stage": event.get("stage"),
            "index": event.get("index"),
            "error_type": event.get("error_type"),
        }
        for event in pipeline_result.get("events", [])
    ],
}
(OUT / "orchestration_run.json").write_text(
    json.dumps(safe_pipeline_result, indent=2),
    encoding="utf-8"
)

# 4. Record the test result file's actual summary
test_file = OUT / "test-results.txt"
test_text = test_file.read_text(encoding="utf-8") if test_file.exists() else ""
summary = {
    "test_results_file_present": test_file.exists(),
    "unittest_reports_31_tests": "Ran 31 tests" in test_text,
    "unittest_reports_ok": "\nOK" in test_text,
    "note": "Summary is derived from the saved unittest output."
}
(OUT / "evidence_summary.json").write_text(
    json.dumps(summary, indent=2), encoding="utf-8"
)

print("Evidence generation completed.")
print("Files:")
for path in sorted(OUT.iterdir()):
    if path.is_file():
        print(f" - {path.name} ({path.stat().st_size} bytes)")
