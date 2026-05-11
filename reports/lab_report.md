# Day 08 Lab Report — LangGraph Agentic Orchestration

## 1. Team / student

- Name: Nguyen Ngoc Hung
- Repo/commit: 2A202600188-NguyenNgocHung-Day23
- Date: 2026-05-11

## 2. Architecture

The graph implements a production-style LangGraph workflow:
- **intake -> classify**: Normalizes input and routes based on keyword heuristics.
- **tool -> evaluate -> retry**: Implements a bounded retry loop for transient failures.
- **risky_action -> approval**: Integrates Human-in-the-loop (HITL) for sensitive operations.
- **dead_letter**: Ensures termination and logging for unrecoverable errors.

## 3. State schema

| Field | Reducer | Why |
|---|---|---|
| messages | append | Full audit trail of the conversation. |
| tool_results | append | Records evidence from all tool attempts. |
| events | append | Tracks node transitions for grading/debug. |
| route | overwrite | Determines current graph path. |
| attempt | overwrite | Tracks current retry count. |

## 4. Scenario results

- **Total scenarios**: 15
- **Success rate**: 100.00%
- **Average nodes visited**: 13.47
- **Total retries**: 14
- **Total interrupts**: 10

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|---:|---:|---:|
| G01_simple | simple | simple | True | 0 | 0 |
| G02_simple2 | simple | simple | True | 0 | 0 |
| G03_tool | tool | tool | True | 0 | 0 |
| G04_tool2 | tool | tool | True | 0 | 0 |
| G05_tool3 | tool | tool | True | 0 | 0 |
| G06_missing | missing_info | missing_info | True | 0 | 0 |
| G07_missing2 | missing_info | missing_info | True | 0 | 0 |
| G08_risky | risky | risky | True | 0 | 2 |
| G09_risky2 | risky | risky | True | 0 | 2 |
| G10_risky3 | risky | risky | True | 0 | 2 |
| G11_risky4 | risky | risky | True | 0 | 2 |
| G12_error | error | error | True | 6 | 0 |
| G13_error2 | error | error | True | 6 | 0 |
| G14_dead | error | error | True | 2 | 0 |
| G15_mixed | risky | risky | True | 0 | 2 |


## 5. Failure analysis

1. **Transient Failures**: Handled via `evaluate` node which detects errors and triggers the `retry` node until success or `max_attempts`.
2. **Risky Actions**: Refund/Delete requests are intercepted by `classify` and routed to `approval`, preventing automated execution of sensitive tasks.

## 6. Persistence / recovery evidence

- **Checkpointer**: Using `SqliteSaver` with `checkpoints.db`.
- **Thread ID**: Unique `thread_id` per scenario ensures session isolation.

## 7. Extension work

- **SQLite Persistence**: State survives process restarts.
- **Graph Diagram**: Exported via `diagram.py` using `draw_mermaid()`.

## 8. Improvement plan

1. **LLM Evaluation**: Use LLM-as-judge for more accurate tool result validation.
2. **Interactive UI**: Build a Streamlit interface for the `approval` node.
