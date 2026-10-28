import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "system-1-agentic-loop"))
sys.path.insert(0, str(ROOT / "system-2-context-strategy"))
sys.path.insert(0, str(ROOT / "system-3-harness-config"))
sys.path.insert(0, str(ROOT / "system-4-orchestrator"))

from agent_loop import Turn, run_agent, validate_claim
from context_strategy import select_context, compress_text
from config_validator import validate_config
from orchestrator import run_pipeline


class AgentLoopTests(unittest.TestCase):
    def test_completes_on_end_turn(self):
        result = run_agent(lambda m, s: Turn("end_turn", "done"), {})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["answer"], "done")

    def test_executes_tool_then_finishes(self):
        turns = iter([Turn("tool_use", tool_name="lookup", tool_input={"id": 7}),
                      Turn("end_turn", "found")])
        result = run_agent(lambda m, s: next(turns), {"lookup": lambda x: str(x["id"])})
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["trace"][0]["stop_reason"], "tool_use")

    def test_unknown_tool_fails_safely(self):
        result = run_agent(lambda m, s: Turn("tool_use", tool_name="missing"), {})
        self.assertEqual(result["error"], "unknown_tool")

    def test_max_tokens_is_incomplete(self):
        result = run_agent(lambda m, s: Turn("max_tokens"), {})
        self.assertEqual(result["status"], "incomplete")

    def test_unknown_stop_reason_is_error(self):
        result = run_agent(lambda m, s: Turn("other"), {})
        self.assertEqual(result["status"], "error")

    def test_turn_limit(self):
        result = run_agent(lambda m, s: Turn("tool_use", tool_name="t"), {"t": lambda x: "ok"}, 2)
        self.assertEqual(result["status"], "limit_reached")
        self.assertEqual(len(result["trace"]), 2)

    def test_valid_claim(self):
        self.assertTrue(validate_claim({"claim_id": "C1", "claim_type": "auto", "description": "damage"})["valid"])

    def test_missing_claim_fields(self):
        result = validate_claim({"claim_id": "C1"})
        self.assertFalse(result["valid"])
        self.assertIn("description", result["missing_fields"])


class ContextTests(unittest.TestCase):
    def test_priority_order(self):
        r = select_context([{"id": "b", "priority": 1, "text": "B"},
                            {"id": "a", "priority": 9, "text": "A"}], 5)
        self.assertEqual(r["selected"][0]["id"], "a")

    def test_budget_is_respected(self):
        r = select_context([{"id": "a", "priority": 1, "text": "12345"}], 4)
        self.assertEqual(r["used"], 0)
        self.assertLessEqual(r["used"], r["budget"])

    def test_remaining_budget(self):
        r = select_context([{"id": "a", "priority": 1, "text": "abc"}], 5)
        self.assertEqual(r["remaining"], 2)

    def test_negative_budget_rejected(self):
        with self.assertRaises(ValueError):
            select_context([], -1)

    def test_compress_short_text(self):
        self.assertEqual(compress_text("abc", 5), "abc")

    def test_compress_long_text(self):
        self.assertEqual(compress_text("abcdefgh", 5), "ab...")

    def test_compress_zero(self):
        self.assertEqual(compress_text("abc", 0), "")

    def test_tie_breaks_by_id(self):
        r = select_context([{"id": "z", "priority": 1, "text": "z"},
                            {"id": "a", "priority": 1, "text": "a"}], 2)
        self.assertEqual([x["id"] for x in r["selected"]], ["a", "z"])


class ConfigTests(unittest.TestCase):
    def test_defaults_are_valid(self):
        self.assertTrue(validate_config({})["valid"])

    def test_custom_valid_config(self):
        self.assertTrue(validate_config({"max_turns": 4, "context_budget": 200})["valid"])

    def test_zero_turns_rejected(self):
        self.assertFalse(validate_config({"max_turns": 0})["valid"])

    def test_too_many_turns_rejected(self):
        self.assertFalse(validate_config({"max_turns": 101})["valid"])

    def test_negative_budget_rejected(self):
        self.assertFalse(validate_config({"context_budget": -1})["valid"])

    def test_non_boolean_network_rejected(self):
        self.assertFalse(validate_config({"allow_network": "yes"})["valid"])

    def test_bad_tools_rejected(self):
        self.assertFalse(validate_config({"allowed_tools": "lookup"})["valid"])

    def test_empty_tool_name_rejected(self):
        self.assertFalse(validate_config({"allowed_tools": [""]})["valid"])


class OrchestratorTests(unittest.TestCase):
    def test_pipeline_completes(self):
        r = run_pipeline({"id": "1"}, [("a", lambda s: 2), ("b", lambda s: 3)])
        self.assertEqual(r["status"], "completed")
        self.assertEqual(r["state"]["checkpoint"], 2)

    def test_results_are_recorded(self):
        r = run_pipeline({}, [("count", lambda s: 7)])
        self.assertEqual(r["state"]["results"]["count"], 7)

    def test_failure_is_captured(self):
        def fail(state):
            raise RuntimeError("intentional test failure")
        r = run_pipeline({}, [("bad", fail)])
        self.assertEqual(r["status"], "failed")
        self.assertEqual(r["failed_stage"], "bad")

    def test_prior_checkpoint_survives_failure(self):
        def fail(state):
            raise ValueError("failure")
        r = run_pipeline({}, [("first", lambda s: "ok"), ("second", fail)])
        self.assertEqual(r["state"]["checkpoint"], 1)
        self.assertEqual(r["state"]["completed"], ["first"])

    def test_events_include_checkpoint(self):
        r = run_pipeline({}, [("first", lambda s: "ok")])
        self.assertEqual(r["events"][-1]["event"], "checkpoint_saved")

    def test_empty_pipeline_completes(self):
        r = run_pipeline({}, [])
        self.assertEqual(r["status"], "completed")
        self.assertEqual(r["state"]["checkpoint"], 0)

    def test_task_is_preserved(self):
        task = {"claim": "X"}
        r = run_pipeline(task, [])
        self.assertEqual(r["state"]["task"], task)


if __name__ == "__main__":
    unittest.main()


class OrchestratorEnhancementTests(__import__("unittest").TestCase):
    def test_sql_filter_returns_only_matching_defects(self):
        from pathlib import Path
        import importlib.util

        path = Path(__file__).resolve().parents[1] / "system-4-orchestrator" / "orchestrator.py"
        spec = importlib.util.spec_from_file_location("enhanced_orchestrator", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        defects = [
            {"id": "D2", "status": "open", "severity": "high"},
            {"id": "D1", "status": "closed", "severity": "high"},
            {"id": "D3", "status": "open", "severity": "low"},
        ]
        result = module.filter_defects_sql(defects)
        self.assertEqual([item["id"] for item in result], ["D2"])

    def test_hot_state_stays_within_byte_budget(self):
        from pathlib import Path
        import importlib.util

        path = Path(__file__).resolve().parents[1] / "system-4-orchestrator" / "orchestrator.py"
        spec = importlib.util.spec_from_file_location("enhanced_orchestrator", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = module.create_hot_state({
            "task": "quality review",
            "completed": ["intake", "validate"],
            "checkpoint": 2,
            "results": {"large": "x" * 10000},
        }, max_bytes=5000)
        self.assertLessEqual(result["bytes"], 5000)

    def test_stale_checkpoint_requires_fresh_run(self):
        from pathlib import Path
        import importlib.util

        path = Path(__file__).resolve().parents[1] / "system-4-orchestrator" / "orchestrator.py"
        spec = importlib.util.spec_from_file_location("enhanced_orchestrator", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertTrue(module.should_resume(30, 60))
        self.assertFalse(module.should_resume(90, 60))

    def test_forked_state_is_isolated(self):
        from pathlib import Path
        import importlib.util

        path = Path(__file__).resolve().parents[1] / "system-4-orchestrator" / "orchestrator.py"
        spec = importlib.util.spec_from_file_location("enhanced_orchestrator", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        original = {"results": {"count": 1}}
        branch = module.fork_state(original)
        branch["results"]["count"] = 99
        self.assertEqual(original["results"]["count"], 1)
