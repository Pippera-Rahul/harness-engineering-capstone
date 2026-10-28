"""A deterministic stop-reason-driven claims intake loop."""
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Turn:
    stop_reason: str
    content: str = ""
    tool_name: str = ""
    tool_input: dict = field(default_factory=dict)


def run_agent(
    next_turn: Callable[[list, dict], Turn],
    tools: dict[str, Callable[[dict], str]],
    max_turns: int = 8,
) -> dict:
    """Continue on tool_use, finish on end_turn, and fail safely on limits."""
    messages = []
    trace = []
    for index in range(max_turns):
        turn = next_turn(messages, {})
        trace.append({"turn": index + 1, "stop_reason": turn.stop_reason})
        if turn.stop_reason == "end_turn":
            return {"status": "completed", "answer": turn.content, "trace": trace}
        if turn.stop_reason == "tool_use":
            if turn.tool_name not in tools:
                return {"status": "error", "error": "unknown_tool", "trace": trace}
            result = tools[turn.tool_name](turn.tool_input)
            messages.append({"tool": turn.tool_name, "result": result})
            continue
        if turn.stop_reason == "max_tokens":
            return {"status": "incomplete", "error": "max_tokens", "trace": trace}
        return {"status": "error", "error": "unsupported_stop_reason", "trace": trace}
    return {"status": "limit_reached", "trace": trace}


def validate_claim(claim: dict) -> dict:
    required = ("claim_id", "claim_type", "description")
    missing = [key for key in required if not str(claim.get(key, "")).strip()]
    return {"valid": not missing, "missing_fields": missing}
