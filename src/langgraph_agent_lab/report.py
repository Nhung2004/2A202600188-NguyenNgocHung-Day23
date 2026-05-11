"""Report generation helper."""

from __future__ import annotations

from pathlib import Path

from .metrics import MetricsReport


def render_report_stub(metrics: MetricsReport) -> str:
    """Return a detailed report using the lab template."""
    scenario_rows = ""
    for m in metrics.scenario_metrics:
        row = f"| {m.scenario_id} | {m.expected_route} | {m.actual_route} | {m.success} | {m.retry_count} | {m.interrupt_count} |\n"
        scenario_rows += row

    return f"""# Day 08 Lab Report — LangGraph Agentic Orchestration

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

- **Total scenarios**: {metrics.total_scenarios}
- **Success rate**: {metrics.success_rate:.2%}
- **Average nodes visited**: {metrics.avg_nodes_visited:.2f}
- **Total retries**: {metrics.total_retries}
- **Total interrupts**: {metrics.total_interrupts}

| Scenario | Expected route | Actual route | Success | Retries | Interrupts |
|---|---|---|---:|---:|---:|
{scenario_rows}

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
"""


def write_report(metrics: MetricsReport, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_report_stub(metrics), encoding="utf-8")
