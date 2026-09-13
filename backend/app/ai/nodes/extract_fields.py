import re
import json
import logging
from typing import Dict, Any
from app.ai.state import ComplaintState
from app.ai.groq_client import get_groq_client, execute_with_backoff
from app.schemas.schemas import ExtractedComplaintFields

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are a senior pharmaceutical Quality Assurance (QA) data extraction specialist.
Analyze the following pharmaceutical customer complaint document text and extract the information into a strict JSON object.

CRITICAL RULES:
1. Return ONLY valid JSON, with NO surrounding explanation, NO markdown backticks, and NO conversational text.
2. NEVER hallucinate or invent information. If a field is not explicitly mentioned or is ambiguous in the text, you MUST return null for that field.
3. Distinguish between verified facts and missing data.

JSON Schema to output:
{
  "complaint_id": string or null (e.g. CMP-2026-..., reference code, or null if unassigned),
  "complaint_date": string or null (YYYY-MM-DD or formatted as stated),
  "received_date": string or null (YYYY-MM-DD or formatted as stated),
  "product_name": string or null (Commercial name of product),
  "product_strength": string or null (e.g. 500 mg, 1g/vial, 20mg/ml),
  "product_type": string or null (e.g. Vial, Tablet, Capsule, Injectable, Suspension),
  "batch_number": string or null (Lot or batch number),
  "manufacturing_site": string or null (Facility or site location),
  "manufacturing_date": string or null (Date of manufacture),
  "expiry_date": string or null (Expiration date),
  "quantity_affected": string or null (Quantity of units/vials/packs affected),
  "customer_name": string or null (Facility, hospital, pharmacy or person reporting),
  "customer_contact": string or null (Email, phone number, address),
  "reported_by": string or null (Complaint source type: Pharmacy, Hospital, Patient, Doctor, Distributor, Regulatory Agency, or role),
  "event_date": string or null (Date the incident or defect occurred),
  "complaint_description": string or null (Detailed factual description of the issue),
  "complaint_category": string or null (e.g. Physical Contamination, Packaging Defect, Labelling Error, Suspected Adverse Event, Subpotent)
}

Document Text:
\"\"\"{text}\"\"\"
"""


def clean_and_parse_json(text: str) -> Dict[str, Any]:
    """
    Robust JSON extraction and fallback normalization for LLM outputs.
    Handles markdown code blocks, preamble text, trailing commas, and formatting quirks.
    """
    cleaned = text.strip()
    # Strip markdown code fences if present
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Find first '{' and last '}'
    match = re.search(r"(\{[\s\S]*\})", cleaned)
    if match:
        candidate = match.group(1)
        # Attempt trailing comma cleanup
        candidate = re.sub(r",\s*([\]}])", r"\1", candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            logger.warning("Regex candidate JSON parsing failed: %s", str(e))

    raise ValueError("LLM response did not contain valid parseable JSON.")


def extract_fields_node(state: ComplaintState) -> Dict[str, Any]:
    """LangGraph node: extracts structured fields from raw complaint text."""
    raw_text = state.get("raw_text", "")
    errors = list(state.get("errors", []))

    if not raw_text.strip():
        return {
            "extracted_fields": {},
            "errors": errors + ["Input text is empty; extraction aborted."]
        }

    llm = get_groq_client(temperature=0.0)
    prompt = EXTRACTION_PROMPT.replace("{text}", raw_text)

    try:
        response = execute_with_backoff(lambda: llm.invoke(prompt))
        extracted_raw = clean_and_parse_json(response.content)
        # Pydantic schema validation
        validated_fields = ExtractedComplaintFields.model_validate(extracted_raw)
        extracted = validated_fields.model_dump()
    except Exception as e:
        logger.error("Error during field extraction or schema validation: %s", str(e))
        errors.append(f"Field extraction fallback triggered: {str(e)}")
        # Safe fallback structure with null values (never invent data)
        fallback_model = ExtractedComplaintFields(
            complaint_id=None,
            complaint_date=None,
            received_date=None,
            product_name=None,
            product_strength=None,
            product_type=None,
            batch_number=None,
            manufacturing_site=None,
            manufacturing_date=None,
            expiry_date=None,
            quantity_affected=None,
            customer_name=None,
            customer_contact=None,
            reported_by=None,
            event_date=None,
            complaint_description=raw_text[:500] if raw_text else None,
            complaint_category="Unclassified"
        )
        extracted = fallback_model.model_dump()

    return {
        "extracted_fields": extracted,
        "errors": errors
    }
