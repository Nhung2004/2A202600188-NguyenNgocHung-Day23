"""Node skeletons for the LangGraph workflow.

Each function should be small, testable, and return a partial state update. Avoid mutating the
input state in place.
"""

from __future__ import annotations

from .state import AgentState, ApprovalDecision, Route, make_event


def intake_node(state: AgentState) -> dict:
    """Normalize raw query into state fields."""
    query = state.get("query", "").strip()
    # Simple normalization: trim and lowercase for internal processing if needed
    # but keep the original query for the messages
    return {
        "query": query,
        "messages": [f"User query: {query}"],
        "events": [make_event("intake", "completed", "query normalized")],
    }


def classify_node(state: AgentState) -> dict:
    """Classify the query into a route using keyword-based heuristics."""
    query = state.get("query", "").lower()
    words = query.split()
    clean_words = [w.strip("?!.,;:") for w in words]
    
    # Priority-based keyword matching
    risky_keywords = {"refund", "delete", "send", "cancel", "remove", "revoke"}
    tool_keywords = {"status", "order", "lookup", "check", "track", "find", "search"}
    error_keywords = {"timeout", "fail", "error", "crash", "unavailable"}
    
    route = Route.SIMPLE
    risk_level = "low"
    
    # Check risky first (highest priority)
    if any(k in query for k in risky_keywords):
        route = Route.RISKY
        risk_level = "high"
    # Then tool
    elif any(k in query for k in tool_keywords):
        route = Route.TOOL
    # Then missing info (heuristic: very short and contains 'it')
    elif len(clean_words) < 5 and "it" in clean_words:
        route = Route.MISSING_INFO
    # Then error
    elif any(k in query for k in error_keywords):
        route = Route.ERROR
        
    return {
        "route": route.value,
        "risk_level": risk_level,
        "events": [make_event("classify", "completed", f"route={route.value}")],
    }


def ask_clarification_node(state: AgentState) -> dict:
    """Ask for missing information instead of hallucinating."""
    query = state.get("query", "")
    question = f"I'm not sure what you mean by '{query}'. Could you please provide more details or specify an order ID?"
    return {
        "pending_question": question,
        "final_answer": question,
        "events": [make_event("clarify", "completed", "missing information requested")],
    }


def tool_node(state: AgentState) -> dict:
    """Call a mock tool."""
    attempt = int(state.get("attempt", 0))
    scenario_id = state.get("scenario_id", "unknown")
    
    # Simulate transient failures for error-route scenarios or specifically for S05/S07
    # The prompt says S07 sets max_attempts=1, and S05 should retry.
    if state.get("route") == Route.ERROR.value and attempt < state.get("max_attempts", 3) - 1:
        result = f"ERROR: transient failure at attempt {attempt} for scenario {scenario_id}"
    else:
        result = f"Successfully processed request for scenario {scenario_id}. Details: {state.get('query')}"
        
    return {
        "tool_results": [result],
        "events": [make_event("tool", "completed", f"tool executed attempt={attempt}")],
    }


def risky_action_node(state: AgentState) -> dict:
    """Prepare a risky action for approval."""
    query = state.get("query", "").lower()
    
    # Heuristic to identify action type
    if "refund" in query:
        action_type = "REFUND"
        justification = "Customer requested a refund for a transaction."
    elif "delete" in query or "remove" in query:
        action_type = "DELETE_ACCOUNT"
        justification = "Account deletion request requires verification."
    else:
        action_type = "EXTERNAL_ACTION"
        justification = "Action involves sensitive operations or external systems."
        
    proposed_action = {
        "action_type": action_type,
        "justification": justification,
        "risk_level": state.get("risk_level", "high"),
        "evidence": [f"Query contains sensitive keywords: {query}"]
    }
    
    import json
    return {
        "proposed_action": json.dumps(proposed_action),
        "events": [make_event("risky_action", "pending_approval", f"Action '{action_type}' prepared for approval")],
    }


def approval_node(state: AgentState) -> dict:
    """Human approval step with optional LangGraph interrupt()."""
    import os
    import json

    proposed_action_str = state.get("proposed_action") or "{}"
    try:
        proposed_action = json.loads(proposed_action_str)
    except Exception:
        proposed_action = {"action": proposed_action_str}

    if os.getenv("LANGGRAPH_INTERRUPT", "").lower() == "true":
        from langgraph.types import interrupt

        value = interrupt({
            "proposed_action": proposed_action,
            "risk_level": state.get("risk_level"),
        })
        if isinstance(value, dict):
            decision = ApprovalDecision(**value)
        else:
            decision = ApprovalDecision(approved=bool(value))
    else:
        # Improved mock decision
        is_approved = True
        comment = f"Automatically approved {proposed_action.get('action_type', 'action')} based on system policy."
        decision = ApprovalDecision(approved=is_approved, comment=comment)

    return {
        "approval": decision.model_dump(),
        "events": [make_event("approval", "completed", f"approved={decision.approved}, comment={decision.comment}")],
    }


def retry_or_fallback_node(state: AgentState) -> dict:
    """Record a retry attempt or fallback decision."""
    attempt = int(state.get("attempt", 0)) + 1
    max_attempts = int(state.get("max_attempts", 3))
    
    error_msg = f"Retry attempt {attempt}/{max_attempts}"
    
    # Simulated exponential backoff metadata
    backoff_ms = 100 * (2 ** (attempt - 1))
    
    return {
        "attempt": attempt,
        "errors": [error_msg],
        "events": [make_event("retry", "completed", error_msg, attempt=attempt, next_backoff_ms=backoff_ms)],
    }


def answer_node(state: AgentState) -> dict:
    """Produce a final response grounded in tool results."""
    tool_results = state.get("tool_results", [])
    approval = state.get("approval")
    
    if tool_results:
        latest_result = tool_results[-1]
        answer = f"I have processed your request. Result: {latest_result}"
        if approval and approval.get("approved"):
            answer += " (Action was approved by support team)"
    else:
        answer = f"I have handled your request: '{state.get('query')}'"
        
    return {
        "final_answer": answer,
        "events": [make_event("answer", "completed", "answer generated")],
    }


def evaluate_node(state: AgentState) -> dict:
    """Evaluate tool results — the 'done?' check that enables retry loops."""
    tool_results = state.get("tool_results", [])
    if not tool_results:
        return {
            "evaluation_result": "needs_retry",
            "events": [make_event("evaluate", "completed", "no tool results, retry needed")],
        }
        
    latest = tool_results[-1]
    
    # Stricter error detection
    is_error = any(msg in latest.upper() for msg in ["ERROR", "TIMEOUT", "FAILURE", "FAILED"])
    
    if is_error:
        return {
            "evaluation_result": "needs_retry",
            "events": [make_event("evaluate", "completed", f"tool result indicates failure: {latest}")],
        }
        
    return {
        "evaluation_result": "success",
        "events": [make_event("evaluate", "completed", "tool result satisfactory")],
    }


def dead_letter_node(state: AgentState) -> dict:
    """Log unresolvable failures for manual review."""
    attempt = state.get("attempt", 0)
    msg = f"CRITICAL: Request failed after {attempt} attempts. Manual intervention required."
    
    # In a real app, we might write to a database or call an external alerting service here.
    import logging
    logging.error(f"Dead Letter Queue Entry: {state.get('scenario_id')} - {state.get('query')}")
    
    return {
        "final_answer": msg,
        "events": [make_event("dead_letter", "completed", "max retries exceeded, escalated to manual review")],
    }


def finalize_node(state: AgentState) -> dict:
    """Finalize the run and emit a final audit event."""
    return {"events": [make_event("finalize", "completed", "workflow finished")]}
