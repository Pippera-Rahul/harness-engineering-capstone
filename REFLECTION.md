# Harness Engineering Capstone — Reflection

## 1. System 1: Stop-Reason-Driven Agent Loop

The agent loop in `system-1-agentic-loop/agent_loop.py` handles tool-use responses, end-turn responses, incomplete responses, unknown stop reasons, unknown tools, and turn limits. The stop reason determines whether the loop should execute a tool, terminate normally, or report an incomplete or unsupported response.

The implementation makes control-flow decisions in deterministic Python code instead of relying only on instructions to the model. The saved `evidence/stop_reason_trace.json` demonstrates a tool-use step followed by end-turn termination.

## 2. System 2: Context Selection and Compression

The context strategy in `system-2-context-strategy/context_strategy.py` selects context items according to priority and a configured budget. It also provides text compression through `compress_text`.

The current budget is based on text length, not actual model-token counts. Therefore, the budget output demonstrates the selection algorithm but does not establish a model-token reduction percentage. A comparison against a raw baseline and an evaluation of question-answering quality would be needed to measure the strategy's effectiveness more fully.

The saved `evidence/budget.json` records the current selection and budget calculation.

## 3. System 3: Harness Configuration

The configuration validator in `system-3-harness-config/config_validator.py` checks settings such as maximum turns, context budget, network permission, and allowed tool names. This keeps configuration constraints explicit and testable.

The current configuration is stored in `harness_config.json`, and `evidence/config-validation.txt` records a validation result. The combined test suite covers invalid values and valid configurations. The separate course-specific configuration artifacts and rubric test requirements still need independent verification.

## 4. System 4: Multi-Stage Orchestration

The orchestrator in `system-4-orchestrator/orchestrator.py` runs stages, records results and checkpoints, and captures failures while preserving the state available at the time of failure.

The successful demonstration in `system-4-orchestrator/run_demo.py` runs four stages: intake, validation, analysis, and summary. Its generated evidence shows all four stages completed at checkpoint 4. SQL filtering selects open, high-severity defects, returning two matching records from the simulated dataset.

Additional helpers demonstrate compact state creation, checkpoint-age policy checks, and isolated state copies. The generated hot-state is measured in serialized UTF-8 bytes and is below the configured 5,000-byte limit. The resume helper checks checkpoint age; it does not itself restore or restart a pipeline. The workflow uses simulated data and is not connected to a production monitoring system.

System 4 evidence includes:
- `evidence/orchestration_run.json`
- `evidence/defect_slice.json`
- `evidence/hot_state.json`
- `evidence/checkpoint_policy.json`

## 5. Cross-System Comparison

Deterministic code enforcement is useful when a requirement must be checked consistently, such as configuration validation, tool allowlists, budget limits, or checkpoint decisions. Prompt-based guidance can communicate desired behavior, but it is not a substitute for programmatic validation when strict enforcement is required.

Context handling and orchestration solve different problems. System 2 decides which information to retain within a selection budget. System 4 tracks workflow progress, results, and checkpoints across stages. The current System 2 budget measures characters, while System 4's hot-state helper measures serialized UTF-8 bytes; neither measurement should be described as actual model-token usage.

## 6. Verification Evidence

The combined test suite currently reports 35 passing tests when run with:

    python3 -m unittest discover -s tests -v

Relevant evidence files include:
- `evidence/stop_reason_trace.json` — example agent-loop trace.
- `evidence/budget.json` — context selection and character-budget calculation.
- `evidence/config-validation.txt` — configuration validation result.
- `evidence/orchestration_run.json` — latest successful orchestration run.
- `evidence/defect_slice.json` — SQL-filtered defect results.
- `evidence/hot_state.json` — compact state and byte measurement.
- `evidence/checkpoint_policy.json` — checkpoint-age policy results.
- `evidence/test-results.txt` — recorded test output, which should be regenerated when the test suite changes.

## 7. Limitations and Remaining Work

The 35 passing tests belong to the current combined test suite. They do not prove that the separate rubric-specific test counts or all course deliverables have been satisfied.

The demonstration uses simulated data. The context budget is character-based rather than token-based, and no question-answering evaluation or raw-baseline reduction has been established here. The checkpoint helper evaluates freshness but does not implement pipeline restoration. Separate system-specific test suites, required Claude Code configuration artifacts, and any remaining course evaluation requirements must be checked against the original rubric before claiming full completion.
