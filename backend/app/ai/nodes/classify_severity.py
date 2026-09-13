import logging
from typing import Dict, Any
from app.ai.state import ComplaintState
from app.ai.groq_client import get_groq_client, execute_with_backoff
from app.ai.nodes.extract_fields import clean_and_parse_json
from app.schemas.schemas import SeverityClassificationResult

logger = logging.getLogger(__name__)

SEVERITY_PROMPT = """You are a pharmaceutical Quality Assurance triage officer.
Based ONLY on the extracted complaint details provided below, perform an INITIAL complaint triage classification.

NOTE: This is a preliminary triage for internal quality workflow routing, NOT a final regulatory defect determination.

Evaluation Criteria:
- Critical / High: Direct patient harm, sterility failure, glass/metal particles, contamination in parenteral products, anaphylaxis, life-threatening adverse reactions, wrong product or dosage.
- Major / Medium: Physical defect with potential health impact, cap leakage, chemical discoloration, subpotency/efficacy failure, illegible lot number.
- Minor / Low: Cosmetic packaging blemishes, label skew, minor outer box damage, inquiries without product defect.

Extracted Complaint Information:
Product: {product_name} ({product_strength}, {product_type})
Batch: {batch_number}
Category: {complaint_category}
Description: {complaint_description}
Quantity Affected: {quantity_affected}

Return ONLY a JSON object with this exact schema:
{{
  "initial_severity": "Critical" | "Major" | "Minor",
  "priority": "High" | "Medium" | "Low",
  "triage_notes": "A concise 1-2 sentence QA rationale explaining the initial classification based strictly on stated facts.",
  "suggested_action": "A concise recommended next action, e.g. Route to QA Investigation & Issue Replacement"
}}
"""


def classify_severity_node(state: ComplaintState) -> Dict[str, Any]:
    """LangGraph node: Classifies preliminary complaint severity and handling priority."""
    extracted = state.get("extracted_fields", {})
    errors = list(state.get("errors", []))

    llm = get_groq_client(temperature=0.0)
    prompt = SEVERITY_PROMPT.format(
        product_name=extracted.get("product_name") or "Unknown Product",
        product_strength=extracted.get("product_strength") or "Unknown Strength",
        product_type=extracted.get("product_type") or "Unknown Type",
        batch_number=extracted.get("batch_number") or "Unknown Batch",
        complaint_category=extracted.get("complaint_category") or "Unclassified",
        complaint_description=extracted.get("complaint_description") or "No description available",
        quantity_affected=extracted.get("quantity_affected") or "Unspecified"
    )

    try:
        response = execute_with_backoff(lambda: llm.invoke(prompt))
        raw_result = clean_and_parse_json(response.content)
        # Normalize allowed values before strict validation
        sev = raw_result.get("initial_severity", "").strip().capitalize()
        prio = raw_result.get("priority", "").strip().capitalize()
        if sev not in {"Critical", "Major", "Minor"}:
            sev = "Major"
        if prio not in {"High", "Medium", "Low"}:
            prio = "Medium"
        raw_result["initial_severity"] = sev
        raw_result["priority"] = prio

        validated = SeverityClassificationResult.model_validate(raw_result)
        result = validated.model_dump()
    except Exception as e:
        logger.error("Error during severity classification or validation: %s", str(e))
        errors.append(f"Severity classification fallback triggered: {str(e)}")
        # Safe rule-based fallback based on keywords
        desc = (extracted.get("complaint_description") or "").lower()
        if any(k in desc for k in ["particulate", "glass", "contamination", "death", "hospital", "adverse", "steril"]):
            severity = "Critical"
            priority = "High"
        elif any(k in desc for k in ["discolor", "leak", "broken", "precipitate", "potency"]):
            severity = "Major"
            priority = "Medium"
        else:
            severity = "Minor"
            priority = "Low"

        fallback_model = SeverityClassificationResult(
            initial_severity=severity,
            priority=priority,
            triage_notes="Preliminary triage assigned via rule-based safety fallback.",
            suggested_action="Route to QA Investigation & Issue Replacement"
        )
        result = fallback_model.model_dump()

    return {
        "severity": result,
        "errors": errors
    }
