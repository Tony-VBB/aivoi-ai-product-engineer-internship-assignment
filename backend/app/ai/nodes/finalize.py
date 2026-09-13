import logging
from typing import Dict, Any
from app.ai.state import ComplaintState

logger = logging.getLogger(__name__)


def finalize_node(state: ComplaintState) -> Dict[str, Any]:
    """
    LangGraph node: Assembles unified structured output and concise executive summary.
    """
    extracted = state.get("extracted_fields", {})
    completeness = state.get("completeness", {})
    severity = state.get("severity", {})
    risk = state.get("risk_assessment", {})

    product = extracted.get("product_name") or "Pharmaceutical Product"
    strength = extracted.get("product_strength") or ""
    batch = extracted.get("batch_number") or "Unknown Lot"
    customer = extracted.get("customer_name") or "Reporter"
    desc = extracted.get("complaint_description") or "Complaint logged"
    sev = severity.get("initial_severity") or "Unclassified"
    risk_level = risk.get("risk_level") or "Unassessed"

    # Construct executive summary
    summary_parts = [
        f"Complaint filed for {product} {strength} (Batch: {batch}) by {customer}.",
        f"Issue Description: {desc}",
        f"Initial Quality Triage: {sev} Severity / {risk_level} Risk Level.",
        f"Data Completeness: {completeness.get('completeness_status', 'Unknown')}."
    ]

    missing = completeness.get("missing_fields", [])
    if missing:
        summary_parts.append(f"Pending Information Required: {', '.join(missing[:3])}.")

    # Prioritize suggested next action if classified, otherwise construct summary
    suggested_action = severity.get("suggested_action")
    if suggested_action and suggested_action.strip():
        ai_summary = suggested_action.strip()
    else:
        ai_summary = " ".join(summary_parts)

    return {
        "ai_summary": ai_summary
    }
