import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.ai.state import ComplaintState
from app.ai.nodes.extract_fields import extract_fields_node, clean_and_parse_json

from app.ai.nodes.completeness_check import completeness_check_node
from app.ai.nodes.classify_severity import classify_severity_node
from app.ai.nodes.risk_assessment import risk_assessment_node
from app.ai.nodes.finalize import finalize_node
from app.ai.groq_client import get_groq_client, execute_with_backoff

logger = logging.getLogger(__name__)

# Compile LangGraph workflow with MemorySaver (strictly in-memory, NOT PostgreSQL)
checkpointer = MemorySaver()

workflow = StateGraph(ComplaintState)

workflow.add_node("extract_fields", extract_fields_node)
workflow.add_node("completeness_check", completeness_check_node)
workflow.add_node("classify_severity", classify_severity_node)
workflow.add_node("risk_assessment", risk_assessment_node)
workflow.add_node("finalize", finalize_node)

workflow.set_entry_point("extract_fields")
workflow.add_edge("extract_fields", "completeness_check")
workflow.add_edge("completeness_check", "classify_severity")
workflow.add_edge("classify_severity", "risk_assessment")
workflow.add_edge("risk_assessment", "finalize")
workflow.add_edge("finalize", END)

complaint_app = workflow.compile(checkpointer=checkpointer)


def run_complaint_analysis(raw_text: str, thread_id: str) -> Dict[str, Any]:
    """
    Executes the LangGraph analysis pipeline for a document, scoped by unique thread_id.
    When attached to an existing session, retains thread_id and initializes a clean complaint context.
    """
    initial_state: ComplaintState = {
        "thread_id": thread_id,
        "raw_text": raw_text,
        "extracted_fields": {},
        "completeness": {},
        "severity": {},
        "risk_assessment": {},
        "ai_summary": "",
        "errors": [],
        "messages": []
    }

    config = {"configurable": {"thread_id": thread_id}}
    final_state = complaint_app.invoke(initial_state, config=config)
    return final_state


def chat_with_copilot(
    thread_id: str,
    user_message: str,
    current_form_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    AI Copilot chat handler with live form context, zero-hallucination guardrails,
    structured JSON output, and interactive form filling tool capability.
    Supports live user form updates, text-only sessions, and document-assisted complaint analysis.
    """
    config = {"configurable": {"thread_id": thread_id}}
    current_snapshot = complaint_app.get_state(config)

    has_doc = False
    history: List[Dict[str, str]] = []

    if current_snapshot and current_snapshot.values:
        state_values = current_snapshot.values
        extracted = dict(state_values.get("extracted_fields", {}) or {})
        has_doc = bool(extracted or state_values.get("raw_text"))
        completeness = dict(state_values.get("completeness", {}) or {})
        severity = dict(state_values.get("severity", {}) or {})
        risk = dict(state_values.get("risk_assessment", {}) or {})
        ai_summary = state_values.get("ai_summary", "")
        history = list(state_values.get("messages", []))
    else:
        extracted = {}
        completeness = {}
        severity = {}
        risk = {}
        ai_summary = "No complaint document uploaded. Operating in text-only QMS consultation mode."
        history = []

    # Live Form-State Context: Overlay live user-edited form fields onto extracted record
    if current_form_data and isinstance(current_form_data, dict):
        for k, v in current_form_data.items():
            if v is not None and str(v).strip() != "":
                extracted[k] = v
        if any(extracted.values()):
            has_doc = True

    if has_doc:
        context_summary = f"""
Current Pharmaceutical Complaint Record (thread: {thread_id}):
- Summary: {ai_summary}
- Product: {extracted.get('product_name')} (Strength: {extracted.get('product_strength')}, Form: {extracted.get('product_type')})
- Batch Number: {extracted.get('batch_number')}
- Manufacturing Site: {extracted.get('manufacturing_site')}
- Expiry Date: {extracted.get('expiry_date')}
- Quantity Affected: {extracted.get('quantity_affected')}
- Customer: {extracted.get('customer_name')} ({extracted.get('customer_contact')}, Role: {extracted.get('reported_by')})
- Event Date: {extracted.get('event_date')}
- Description: {extracted.get('complaint_description')}
- Completeness Status: {completeness.get('completeness_status')}
- Missing Fields: {', '.join(completeness.get('missing_fields', []))}
- Initial Severity: {severity.get('initial_severity')} (Priority: {severity.get('priority')})
- Triage Notes: {severity.get('triage_notes')}
- Risk Level: {risk.get('risk_level')}
- Key Risk Factors: {', '.join(risk.get('key_risk_factors', []))}
- Risk Rationale: {risk.get('rationale')}
"""
    else:
        context_summary = f"""
Current Status: Text-only Pharmaceutical QMS consultation session (thread: {thread_id}).
No complaint document has been uploaded yet. The user may provide complaint details in chat to fill the intake form, or ask quality questions.
"""

    history_text = ""
    for msg in history[-6:]:
        history_text += f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}\n"

    system_prompt = f"""You are the AIVOA AI Quality Copilot, an expert assistant for pharmaceutical QMS complaint investigations, GMP compliance, and intake form triage.

CRITICAL RULES:
1. Zero Hallucination: Do not invent batch numbers, dates, or customer names that were never mentioned.
2. If a field is not provided or requested, leave it as null in form_updates.

FORM-FILLING & CONVERSATIONAL EDITING CAPABILITIES:
1. DIRECT COMPLAINT INGESTION:
When the user types raw narrative complaint details (e.g. "Apollo Pharmacy reported 12 discolored capsules in a sealed bottle. Product: Amoxicillin Capsules 500 mg, batch AMX240602..."):
- Set "action": "fill_form".
- Extract all provided details and infer quality triage fields:
  * "product_name": Commercial drug name (e.g. "Amoxicillin Capsules")
  * "product_strength": Dosage strength (e.g. "500 mg")
  * "product_type": Dosage form (e.g. "Capsules", "Tablets", "Vial")
  * "batch_number": Batch/lot number (e.g. "AMX240602")
  * "quantity_affected": Units affected (e.g. "12 capsules")
  * "manufacturing_date": Manufacturing date (e.g. "March 2026")
  * "expiry_date": Expiration date (e.g. "February 2028")
  * "customer_name": Facility or customer (e.g. "Apollo Pharmacy")
  * "reported_by": Complaint Source (e.g. "Pharmacy", "Hospital", "Patient", "Distributor", "Regulatory Agency")
  * "complaint_category": Standardized defect category (e.g. "Product Defect - Discoloration")
  * "complaint_description": Full complaint statement
  * "initial_severity": "Critical" | "Major" | "Minor"
  * "suggested_action": Recommended next QA action (e.g. "Route to QA Investigation & Issue Replacement")
  * "initial_risk_assessment": Concise ICH Q9 risk rationale (e.g. "Potential moisture ingress or primary packaging seal failure leading to capsule discoloration.")
- In "reply", provide a concise, professional confirmation of the ingested details.

2. CONVERSATIONAL FIELD EDITING & PATCHING:
When the user asks to modify, correct, or update specific field(s) (e.g. "Change the batch number to CT-99824" or "The affected quantity was actually 500 vials"):
- Set "action": "fill_form".
- Populate "form_updates" with ONLY the modified field(s).
- In "reply", confirm the exact change made.

3. GENERAL CONSULTATION:
When the user asks general quality/GMP/ICH questions without complaint details or patch requests:
- Set "action": "conversation".
- Set "form_updates": {{}}.

OUTPUT FORMAT REQUIREMENTS:
You MUST respond with a valid JSON object only. Do NOT include markdown fences outside the JSON:
{{
  "reply": "Your clear, professional response",
  "action": "fill_form" | "conversation",
  "form_updates": {{
    "product_name": string or null,
    "product_strength": string or null,
    "product_type": string or null,
    "batch_number": string or null,
    "manufacturing_site": string or null,
    "manufacturing_date": string or null,
    "expiry_date": string or null,
    "quantity_affected": string or null,
    "customer_name": string or null,
    "customer_contact": string or null,
    "reported_by": string or null,
    "event_date": string or null,
    "complaint_description": string or null,
    "complaint_category": string or null,
    "initial_severity": "Critical" | "Major" | "Minor" | null,
    "suggested_action": string or null,
    "initial_risk_assessment": string or null
  }}
}}

{context_summary}

Recent Conversation:
{history_text}

User Question: {user_message}
JSON Output:"""

    llm = get_groq_client(temperature=0.0)
    response = execute_with_backoff(lambda: llm.invoke(system_prompt))
    raw_content = response.content.strip()

    action = "conversation"
    form_updates = {}
    reply = raw_content

    try:
        parsed = clean_and_parse_json(raw_content)
        if isinstance(parsed, dict):
            reply = parsed.get("reply", raw_content)
            action = parsed.get("action", "conversation")
            raw_updates = parsed.get("form_updates", {})
            if isinstance(raw_updates, dict):
                # Filter out null / None / empty string updates
                form_updates = {
                    k: v for k, v in raw_updates.items()
                    if v is not None and str(v).strip() != ""
                }
    except Exception as e:
        logger.warning("Could not parse Copilot response as JSON, falling back to raw text: %s", str(e))

    # If form_updates contains fields, mark action as fill_form
    if form_updates and action != "fill_form":
        action = "fill_form"

    # Propagate triage updates into severity/risk state
    if "initial_severity" in form_updates:
        severity["initial_severity"] = form_updates["initial_severity"]
    if "suggested_action" in form_updates:
        severity["suggested_action"] = form_updates["suggested_action"]
        ai_summary = form_updates["suggested_action"]
    if "initial_risk_assessment" in form_updates:
        risk["rationale"] = form_updates["initial_risk_assessment"]

    # Merge non-null updates into extracted fields
    if form_updates:
        for k, v in form_updates.items():
            if k not in {"initial_severity", "suggested_action", "initial_risk_assessment"}:
                extracted[k] = v

    # Update conversation history in state
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})

    if not current_snapshot or not current_snapshot.values:
        initial_text_state: ComplaintState = {
            "thread_id": thread_id,
            "raw_text": "",
            "extracted_fields": extracted,
            "completeness": completeness,
            "severity": severity,
            "risk_assessment": risk,
            "ai_summary": ai_summary if has_doc else (
                f"Complaint details recorded for {extracted.get('product_name', 'product')}"
                if extracted else "Text-only session"
            ),
            "errors": [],
            "messages": history
        }
        config = {"configurable": {"thread_id": thread_id}}
        complaint_app.update_state(config, initial_text_state)
    else:
        complaint_app.update_state(config, {
            "messages": history,
            "extracted_fields": extracted
        })

    return {
        "reply": reply,
        "thread_id": thread_id,
        "action": action,
        "form_updates": form_updates,
        "extracted_fields": extracted,
        "completeness": completeness if isinstance(completeness, dict) else None,
        "severity": severity if isinstance(severity, dict) else None,
        "risk_assessment": risk if isinstance(risk, dict) else None
    }
