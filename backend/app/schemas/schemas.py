from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExtractedComplaintFields(BaseModel):
    complaint_id: Optional[str] = Field(None, description="Complaint identifier, e.g. CMP-2026-001 or null if none")
    complaint_date: Optional[str] = Field(None, description="Date complaint was filed (YYYY-MM-DD or as found)")
    received_date: Optional[str] = Field(None, description="Date received by quality unit")
    product_name: Optional[str] = Field(None, description="Commercial name of pharmaceutical product")
    product_strength: Optional[str] = Field(None, description="Dosage strength, e.g., 500mg, 1g/vial")
    product_type: Optional[str] = Field(None, description="Dosage form, e.g., Tablet, Injectable, Vial, Suspension")
    batch_number: Optional[str] = Field(None, description="Batch/Lot number")
    manufacturing_site: Optional[str] = Field(None, description="Manufacturing facility or site name")
    manufacturing_date: Optional[str] = Field(None, description="Date of manufacture")
    expiry_date: Optional[str] = Field(None, description="Expiration date")
    quantity_affected: Optional[str] = Field(None, description="Number of units or vials affected")
    customer_name: Optional[str] = Field(None, description="Name of reporting customer or facility")
    customer_contact: Optional[str] = Field(None, description="Contact details: phone, email, or address")
    reported_by: Optional[str] = Field(None, description="Complaint source type: e.g. Pharmacy, Hospital, Patient, Doctor, Distributor")
    event_date: Optional[str] = Field(None, description="Date defect or adverse event occurred")
    complaint_description: Optional[str] = Field(None, description="Detailed statement of the issue")
    complaint_category: Optional[str] = Field(None, description="Quality category, e.g., Physical Defect - Discoloration, Contamination, Packaging Defect")


class CompletenessCheckResult(BaseModel):
    completeness_status: str = Field(..., description="'Complete', 'Partially Complete', or 'Incomplete'")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing required or recommended fields")
    explanation: str = Field(..., description="Brief QA rationale on what is missing and impact on investigation")


class SeverityClassificationResult(BaseModel):
    initial_severity: str = Field(..., description="'Critical', 'Major', or 'Minor'")
    priority: str = Field(..., description="'High', 'Medium', or 'Low'")
    triage_notes: str = Field(..., description="Preliminary triage rationale based strictly on complaint facts")
    suggested_action: Optional[str] = Field(None, description="Suggested next QA action, e.g. Route to QA Investigation & Issue Replacement")


class RiskAssessmentResult(BaseModel):
    risk_level: str = Field(..., description="'High', 'Medium', or 'Low'")
    key_risk_factors: List[str] = Field(default_factory=list, description="Key quality and patient safety hazard points")
    rationale: str = Field(..., description="Risk assessment rationale")
    extracted_evidence: List[str] = Field(default_factory=list, description="Verbatim citations from the complaint source")


class AIAnalyzeResponse(BaseModel):
    thread_id: str
    extracted_fields: ExtractedComplaintFields
    completeness: CompletenessCheckResult
    severity: SeverityClassificationResult
    risk_assessment: RiskAssessmentResult
    ai_summary: str
    raw_text_preview: Optional[str] = None


class ChatRequest(BaseModel):
    thread_id: str
    message: str
    form_data: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    action: Optional[str] = "conversation"  # "fill_form" | "conversation"
    form_updates: Optional[Dict[str, Any]] = Field(default_factory=dict)
    extracted_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)
    severity: Optional[Dict[str, Any]] = None
    completeness: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None




class ComplaintCreate(BaseModel):
    complaint_id: Optional[str] = None
    complaint_date: Optional[str] = None
    received_date: Optional[str] = None
    status: Optional[str] = "Under Review"
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    product_type: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_site: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    reported_by: Optional[str] = None
    event_date: Optional[str] = None
    complaint_description: Optional[str] = None
    complaint_category: Optional[str] = None
    initial_severity: Optional[str] = None
    priority: Optional[str] = None
    completeness_status: Optional[str] = None
    missing_information: Optional[List[str]] = Field(default_factory=list)
    ai_summary: Optional[str] = None
    ai_risk_assessment: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ComplaintResponse(ComplaintCreate):
    id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database_connected: bool
    groq_configured: bool
