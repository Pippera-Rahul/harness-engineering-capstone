"""Validate harness settings without requiring API credentials."""


DEFAULTS = {
    "max_turns": 8,
    "context_budget": 4000,
    "allow_network": False,
    "allowed_tools": ["lookup_claim", "check_policy"],
}


def validate_config(config: dict) -> dict:
    errors = []
    merged = {**DEFAULTS, **config}
    if not isinstance(merged["max_turns"], int) or not 1 <= merged["max_turns"] <= 100:
        errors.append("max_turns must be an integer from 1 to 100")
    if not isinstance(merged["context_budget"], int) or merged["context_budget"] < 1:
        errors.append("context_budget must be a positive integer")
    if not isinstance(merged["allow_network"], bool):
        errors.append("allow_network must be boolean")
    if not isinstance(merged["allowed_tools"], list) or not all(
        isinstance(x, str) and x.strip() for x in merged["allowed_tools"]
    ):
        errors.append("allowed_tools must be a list of non-empty strings")
    return {"valid": not errors, "errors": errors, "effective_config": merged}
