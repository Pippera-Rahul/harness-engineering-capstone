# Harness Engineering Capstone — Reflection

## 1. Overview

This capstone brings together four distinct harness-engineering systems: a stop-reason-driven claims agent, a context selection and compression strategy, a Claude Code configuration harness, and a multi-shift quality-monitoring orchestrator. Each system addresses a different reliability problem. The official course repositories were tested independently, and the resulting logs and run artifacts are preserved under `evidence/`.

The submission also contains custom implementations under `system-1-agentic-loop/`, `system-2-context-strategy/`, `system-3-harness-config/`, and `system-4-orchestrator/`. These custom demonstrations should be distinguished from the official reference implementations and their recorded runs. Official results below refer to the preserved course-system evidence, not to an assumption that every custom demonstration behaves identically.

## 2. System 1 — Stop-Reason-Driven Agent Loop

The claims-intake agent uses the model's stop reason to distinguish a tool-use response from a normal end of turn. Python code handles the resulting control flow, executes supported tool calls, and enforces a terminal-action backstop. This is more reliable than relying on prompt instructions alone to guarantee that every claim reaches a terminal outcome.

The official test suite recorded 30 passed tests with exit code 0. The official run processed eight claims and recorded four routed outcomes and four escalations. The estimated run cost was $0.1334. The claim-level results and supporting run files are preserved under `evidence/official-runs/system-1/`, with a trace excerpt at `evidence/stop_reason_trace.jsonl` and a summary of outcomes at `evidence/routing-results.json`.

The run also exposed a meaningful failure mode: four claims were escalated because the model ended its turn without calling a terminal tool. Three of those escalations were claims expected to route. The deterministic backstop prevented these cases from being silently treated as successful routing, but it did not make the model's routing decisions correct. This distinction matters: safe failure handling is valuable, yet it is not a substitute for evaluating task accuracy and improving model behavior.

## 3. System 2 — Long-Conversation Context Strategy

The context strategy assembles a smaller working context from retained case facts, resolved information, and active conversation details. The official run measured a baseline of 38,708 tokens and an assembled context of 17,039 tokens, a reduction of approximately 55.98%. These figures are recorded in the official run artifacts under `evidence/official-runs/system-2/`.

The official evaluation passed all six question-answering checks. They covered a refund amount, a subscription cancellation reason, a payment failure code, a card's last four digits, a subscription proration refund, and an exact status token. The control evaluation without the retained case facts showed one regression among two control questions. That result supports the value of retaining relevant facts, while also showing that context reduction must be evaluated alongside answer quality.

The official context-strategy suite initially recorded 28 passed and two skipped tests because run artifacts were not yet present. After generating the official run artifacts, the suite was rerun and recorded 30 passed tests with exit code 0. The final evidence should therefore use `system-2-context-strategy-after-run.txt` rather than treating the earlier skipped run as the final result. The custom context-budget demonstration is separate and should not be described as having measured the official model-token reduction.

## 4. System 3 — Claude Code Harness Configuration

The Claude Code configuration harness organizes project-wide guidance, scoped rules, reusable commands, and skill instructions. The copied configuration includes `system-3-harness-config/CLAUDE.md`, `.claude/rules/`, `.claude/commands/review.md`, `.claude/skills/deploy-check/SKILL.md`, and supporting standards files.

The official configuration test suite recorded 35 passed tests with exit code 0. In addition, the copied configuration was checked with the official validator; it returned `OK` and `VALIDATOR_EXIT_CODE=0`. The recorded result is in `evidence/config-validation-copied.txt`.

This system illustrates the difference between behavioral guidance and enforceable constraints. `CLAUDE.md`, scoped rules, command instructions, and skill instructions communicate expectations to Claude Code. A validator can deterministically reject invalid configuration, but written guidance alone cannot guarantee that every action will comply. Both mechanisms are useful and serve different purposes.

## 5. System 4 — Multi-Shift Quality Monitoring and Recovery

The orchestration system manages workflow state and decides whether an interrupted run can resume. The official recovery implementation uses a 30-minute freshness threshold. It chooses a fresh run if the manifest has no steps, the manifest is already complete, or the latest step is older than the threshold. An incomplete run whose latest step is within the threshold can resume.

The official orchestration test suite recorded 33 passed tests with exit code 0. The run and state evidence are preserved in `evidence/official-runs/`, including the copied `hot_state.json` and `shift_scratchpad.jsonl` artifacts.

An important limitation appeared during the recorded-response demonstration: the command reported `new=0`, meaning it detected no new defects for that run. The supplied recorded response described historical findings from 30 April 2026, including repeated high- and medium-severity capacitor-bank findings and a low-severity vent-squeal finding. Those historical findings must not be represented as newly detected defects on the run date. The recorded response supports analysis of the historical scenario, while the run's zero-new-defect result must remain explicit.

## 6. Deterministic Enforcement Versus Prompt Guidance

Deterministic enforcement is appropriate when a requirement must be checked consistently. Examples in these systems include branching on the model stop reason, requiring a terminal claim action or escalating, validating the Claude Code configuration, checking context evaluation answers, and applying the orchestration recovery threshold.

Prompt and configuration guidance remains useful for explaining roles, expected behavior, code conventions, and review procedures. However, instructions such as those in `CLAUDE.md` or a skill file are not equivalent to executable checks. A robust harness combines clear guidance with tests, validators, bounded control flow, observable outcomes, and explicit recovery behavior.

## 7. Context Efficiency and State Management

The official System 2 run reduced the measured context from 38,708 tokens to 17,039 tokens while passing all six evaluation questions. This provides evidence of context efficiency for that scenario, although it does not establish that the same reduction or answer quality will hold for every conversation.

System 4's saved hot-state file is measured in serialized bytes, whereas System 2's context figures are measured in tokens. These measurements describe different resources and should not be compared as if they were equivalent. Compact persisted workflow state supports recovery and continuity; compact model context supports efficient inference. Both require measurements appropriate to their purpose.

## 8. Verification Results

The final official suite results are:

| System | Passed | Skipped | Exit code |
|---|---:|---:|---:|
| System 1 — Agent loop | 30 | 0 | 0 |
| System 2 — Context strategy, after run | 30 | 0 | 0 |
| System 3 — Claude Code configuration | 35 | 0 | 0 |
| System 4 — Orchestration | 33 | 0 | 0 |
| **Total across separate suites** | **128** | **0** | **0** |

These are results from four separate official test suites, not a single combined test suite. The earlier System 2 log had two skipped tests; the post-run suite is the final result used in this table.

Key evidence files include:

- `evidence/official-tests/system-1-agentic-loop.txt`
- `evidence/official-tests/system-2-context-strategy-after-run.txt`
- `evidence/official-tests/system-3-claude-code-config.txt`
- `evidence/official-tests/system-4-orchestration.txt`
- `evidence/stop_reason_trace.jsonl`
- `evidence/routing-results.json`
- `evidence/official-runs/system-2/budget.json`
- `evidence/official-runs/system-2/eval.jsonl`
- `evidence/official-runs/system-2/eval_control.jsonl`
- `evidence/config-validation-copied.txt`

## 9. Limitations and Lessons Learned

Passing tests establish that the tested behaviors satisfy the checks in the recorded suites; they do not prove that every real-world input will be handled correctly. System 1's unexpected escalations demonstrate why successful execution and task accuracy must be evaluated separately. System 2's control evaluation demonstrates why token savings must be assessed alongside factual retention and answer quality. System 4's historical recorded-response run demonstrates why timestamps and the distinction between historical evidence and newly detected events matter.

The main lesson is that reliable agent systems require more than good prompts. They need explicit control flow, measurable context policies, validated configuration, observable state, recovery rules, regression tests, and evidence that makes failures visible. Future improvements should focus on reducing unexpected claim escalations, broadening context-evaluation coverage, and testing orchestration against both recent and stale interrupted runs.
