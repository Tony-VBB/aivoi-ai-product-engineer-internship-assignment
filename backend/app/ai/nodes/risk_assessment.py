import logging
from typing import Dict, Any
from app.ai.state import ComplaintState
from app.ai.groq_client import get_groq_client, execute_with_backoff
from app.ai.nodes.extract_fields import clean_and_parse_json
from app.schemas.schemas import RiskAssessmentResult

logger = logging.getLogger(__name__)

RISK_PROMPT = """You are a senior pharmaceutical Quality Risk Management (QRM) specialist operating under ICH Q9 principles.
Perform an AI Risk Assessment based strictly on the complaint data provided below.

Rules:
1. Clearly distinguish verified facts found in the complaint from your AI-generated analytical rationale.
2. Cite direct evidence phrases under "extracted_evidence".
3. Return ONLY a valid JSON object matching the schema below.

Complaint Data:
Product: {product_name} ({product_strength}, {product_type})
Batch: {batch_number}
Description: {complaint_description}
Initial Severity: {initial_severity}
Quantity: {quantity_affected}

JSON Schema:
{{
  "risk_level": "High" | "Medium" | "Low",
  "key_risk_factors": ["string describing hazard 1", "string describing hazard 2", "..."],
  "rationale": "Comprehensive 2-3 sentence QA explanation of patient hazard, potential lot-wide scope, and regulatory risk.",
  "extracted_evidence": ["quoted verbatim phrase 1 from complaint", "quoted verbatim phrase 2 from complaint"]
}}
"""


def risk_assessment_node(state: ComplaintState) -> Dict[str, Any]:
    """LangGraph node: Computes ICH Q9-aligned pharmaceutical risk assessment."""
    extracted = state.get("extracted_fields", {})
    severity = state.get("severity", {})
    errors = list(state.get("errors", []))

    llm = get_groq_client(temperature=0.0)
    prompt = RISK_PROMPT.format(
        product_name=extracted.get("product_name") or "Unknown Product",
        product_strength=extracted.get("product_strength") or "Unknown Strength",
        product_type=extracted.get("product_type") or "Unknown Type",
        batch_number=extracted.get("batch_number") or "Unknown Batch",
        complaint_description=extracted.get("complaint_description") or "No description provided",
        initial_severity=severity.get("initial_severity") or "Major",
        quantity_affected=extracted.get("quantity_affected") or "Unspecified"
    )

    try:
        response = execute_with_backoff(lambda: llm.invoke(prompt))
        raw_result = clean_and_parse_json(response.content)

        risk_lvl = raw_result.get("risk_level", "").strip().capitalize()
        if risk_lvl not in {"High", "Medium", "Low"}:
            risk_lvl = "Medium"
        raw_result["risk_level"] = risk_lvl

        if not isinstance(raw_result.get("key_risk_factors"), list):
            val = raw_result.get("key_risk_factors")
            raw_result["key_risk_factors"] = [str(val)] if val else []
        if not isinstance(raw_result.get("extracted_evidence"), list):
            val = raw_result.get("extracted_evidence")
            raw_result["extracted_evidence"] = [str(val)] if val else []

        validated = RiskAssessmentResult.model_validate(raw_result)
        result = validated.model_dump()
    except Exception as e:
        logger.error("Error during risk assessment or validation: %s", str(e))
        errors.append(f"Risk assessment fallback triggered: {str(e)}")
        # Safe fallback (never invent data)
        desc = extracted.get("complaint_description") or "Complaint reported"
        sev = severity.get("initial_severity", "Major")
        fallback_model = RiskAssessmentResult(
            risk_level="High" if sev == "Critical" else ("Medium" if sev == "Major" else "Low"),
            key_risk_factors=[
                f"Defect reported for batch {extracted.get('batch_number') or 'unidentified'}",
                "Potential patient health or treatment interruption risk"
            ],
            rationale=f"Initial assessment assigned due to reported {sev.lower()} defect. Investigation required to verify batch containment.",
            extracted_evidence=[desc[:120]]
        )
        result = fallback_model.model_dump()

    return {
        "risk_assessment": result,
        "errors": errors
    }
