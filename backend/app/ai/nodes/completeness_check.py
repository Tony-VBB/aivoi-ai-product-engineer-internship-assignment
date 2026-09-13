import logging
from typing import Dict, Any, List
from app.ai.state import ComplaintState

logger = logging.getLogger(__name__)

# Essential pharmaceutical investigation requirements
MANDATORY_FIELDS = {
    "product_name": "Product Name",
    "batch_number": "Batch/Lot Number",
    "complaint_description": "Complaint Description",
}

RECOMMENDED_FIELDS = {
    "customer_name": "Customer / Reporter Name",
    "customer_contact": "Customer Contact Details",
    "event_date": "Incident / Event Date",
    "complaint_date": "Complaint Filing Date",
    "quantity_affected": "Quantity Affected",
    "expiry_date": "Expiration Date",
    "manufacturing_site": "Manufacturing Facility"
}


def completeness_check_node(state: ComplaintState) -> Dict[str, Any]:
    """
    Evaluates presence of mandatory and recommended pharmaceutical QMS complaint fields.
    Returns completeness_status, missing_fields, and explanation.
    """
    extracted = state.get("extracted_fields", {})
    missing_fields: List[str] = []
    missing_mandatory: List[str] = []

    # Check mandatory fields
    for key, label in MANDATORY_FIELDS.items():
        val = extracted.get(key)
        if not val or str(val).strip().lower() in {"null", "none", "n/a", ""}:
            missing_mandatory.append(label)
            missing_fields.append(label)

    # Check recommended fields
    for key, label in RECOMMENDED_FIELDS.items():
        val = extracted.get(key)
        if not val or str(val).strip().lower() in {"null", "none", "n/a", ""}:
            missing_fields.append(label)

    # Determine status & explanation
    if missing_mandatory:
        status = "Incomplete"
        explanation = (
            f"Critical investigation data missing: {', '.join(missing_mandatory)}. "
            "Under GMP guidelines, batch investigation and root-cause analysis cannot proceed without lot identification and issue details."
        )
    elif len(missing_fields) > 2:
        status = "Partially Complete"
        explanation = (
            f"Mandatory product identity verified, but secondary fields are missing: {', '.join(missing_fields[:3])}. "
            "Additional customer follow-up is recommended to complete the investigation record."
        )
    else:
        status = "Complete"
        explanation = "All core pharmaceutical complaint and traceability fields successfully verified for investigation."

    completeness_raw = {
        "completeness_status": status,
        "missing_fields": missing_fields,
        "explanation": explanation
    }

    try:
        from app.schemas.schemas import CompletenessCheckResult
        validated = CompletenessCheckResult.model_validate(completeness_raw)
        completeness_result = validated.model_dump()
    except Exception as e:
        logger.error("Error validating completeness result schema: %s", str(e))
        completeness_result = completeness_raw

    return {
        "completeness": completeness_result
    }
