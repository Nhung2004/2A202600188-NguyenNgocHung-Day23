# Day 08 Lab Report — LangGraph Agentic Orchestration

## 1. Team / student

- Name: Nguyễn Ngọc Hưng
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

- **Total scenarios**: 7
- **Success rate**: 100.00%
- **Average nodes visited**: 19.71
- **Total retries**: 12
- **Total interrupts**: 6

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|---:|---:|---:|
| S01_simple | simple | simple | True | 0 | 0 |
| S02_tool | tool | tool | True | 0 | 0 |
| S03_missing | missing_info | missing_info | True | 0 | 0 |
| S04_risky | risky | risky | True | 0 | 3 |
| S05_error | error | error | True | 9 | 0 |
| S06_delete | risky | risky | True | 0 | 3 |
| S07_dead_letter | error | error | True | 3 | 0 |


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
