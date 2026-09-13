from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.db.session import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Complaint Identification & Core Lifecycle
    complaint_id = Column(String(64), unique=True, index=True, nullable=False)
    complaint_date = Column(String(32), nullable=True)
    received_date = Column(String(32), nullable=True)
    status = Column(String(32), default="Under Review", nullable=False)

    # Product Information
    product_name = Column(String(255), nullable=True)
    product_strength = Column(String(128), nullable=True)
    product_type = Column(String(128), nullable=True)
    batch_number = Column(String(128), index=True, nullable=True)
    manufacturing_site = Column(String(255), nullable=True)
    manufacturing_date = Column(String(32), nullable=True)
    expiry_date = Column(String(32), nullable=True)
    quantity_affected = Column(String(128), nullable=True)

    # Customer & Reporter Information
    customer_name = Column(String(255), nullable=True)
    customer_contact = Column(String(255), nullable=True)
    reported_by = Column(String(255), nullable=True)

    # Complaint Incident Information
    event_date = Column(String(32), nullable=True)
    complaint_description = Column(Text, nullable=True)
    complaint_category = Column(String(128), nullable=True)

    # AI Quality & Risk Triage
    initial_severity = Column(String(32), nullable=True)  # Critical, Major, Minor
    priority = Column(String(32), nullable=True)          # High, Medium, Low
    completeness_status = Column(String(32), nullable=True) # Complete, Partially Complete, Incomplete
    missing_information = Column(JSON, nullable=True)     # List of missing fields/reasons
    ai_summary = Column(Text, nullable=True)
    ai_risk_assessment = Column(JSON, nullable=True)      # Detailed breakdown

    # System Audit Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "complaint_date": self.complaint_date,
            "received_date": self.received_date,
            "status": self.status,
            "product_name": self.product_name,
            "product_strength": self.product_strength,
            "product_type": self.product_type,
            "batch_number": self.batch_number,
            "manufacturing_site": self.manufacturing_site,
            "manufacturing_date": self.manufacturing_date,
            "expiry_date": self.expiry_date,
            "quantity_affected": self.quantity_affected,
            "customer_name": self.customer_name,
            "customer_contact": self.customer_contact,
            "reported_by": self.reported_by,
            "event_date": self.event_date,
            "complaint_description": self.complaint_description,
            "complaint_category": self.complaint_category,
            "initial_severity": self.initial_severity,
            "priority": self.priority,
            "completeness_status": self.completeness_status,
            "missing_information": self.missing_information or [],
            "ai_summary": self.ai_summary,
            "ai_risk_assessment": self.ai_risk_assessment or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
