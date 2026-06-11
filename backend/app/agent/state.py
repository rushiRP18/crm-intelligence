"""
LangGraph Agent State Definition.

The AgentState TypedDict is the shared state that flows through
every node of the LangGraph workflow.
"""
from typing import TypedDict, Any


class AgentState(TypedDict):
    # --- Input ---
    email_id: int
    message_id: str
    sender: str
    subject: str
    body: str
    thread_id_str: str       # the string thread_id from original JSON

    # --- Built up during workflow ---
    thread_history: list[dict]        # all prior emails in thread
    rag_context: list[dict]           # top-3 retrieved chunks with scores
    web_intel: dict | None            # scraped G2/Trustpilot data
    heuristic_flags: dict             # flags from pre-filter

    # --- Classification output ---
    classification: dict              # matches ClassificationOutput schema

    # --- Reasoning trace (Thought→Action→Observation entries) ---
    reasoning_trace: list[str]

    # --- Agent execution control ---
    tool_calls_count: int             # max 6 enforced
    tool_calls_log: list[dict]        # {tool_name, input, output, duration_ms}
    max_tool_calls: int

    # --- Decision & output ---
    decision: str                     # draft_reply|escalate|flag_legal|flag_security|create_ticket|human_review
    draft: str | None                 # generated reply text
    escalation_brief: dict | None     # pre-filled brief for human reviewer
    final_action: str                 # what was actually done

    # --- Mode ---
    dry_run: bool                     # if True, plan but don't persist

    # --- Error handling ---
    error: str | None
