from typing import TypedDict, List, Dict, Any, Optional


class ComplaintState(TypedDict):
    thread_id: str
    raw_text: str
    extracted_fields: Dict[str, Any]
    completeness: Dict[str, Any]
    severity: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    ai_summary: str
    errors: List[str]
    messages: List[Dict[str, str]]
