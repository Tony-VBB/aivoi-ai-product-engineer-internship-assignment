import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from app.db.session import get_db
from app.models.complaint import Complaint
from app.schemas.schemas import ComplaintCreate, ComplaintResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    """
    Persists user-reviewed and finalized pharmaceutical complaint into PostgreSQL.
    Safely handles duplicate IDs (409 Conflict) and database connection errors (503).
    """
    cid = payload.complaint_id
    if not cid or cid.strip() == "":
        cid = f"CMP-2026-{uuid.uuid4().hex[:6].upper()}"

    complaint = Complaint(
        complaint_id=cid,
        complaint_date=payload.complaint_date,
        received_date=payload.received_date,
        status=payload.status or "Under Review",
        product_name=payload.product_name,
        product_strength=payload.product_strength,
        product_type=payload.product_type,
        batch_number=payload.batch_number,
        manufacturing_site=payload.manufacturing_site,
        manufacturing_date=payload.manufacturing_date,
        expiry_date=payload.expiry_date,
        quantity_affected=payload.quantity_affected,
        customer_name=payload.customer_name,
        customer_contact=payload.customer_contact,
        reported_by=payload.reported_by,
        event_date=payload.event_date,
        complaint_description=payload.complaint_description,
        complaint_category=payload.complaint_category,
        initial_severity=payload.initial_severity,
        priority=payload.priority,
        completeness_status=payload.completeness_status,
        missing_information=payload.missing_information,
        ai_summary=payload.ai_summary,
        ai_risk_assessment=payload.ai_risk_assessment,
    )

    try:
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        logger.info("Successfully persisted complaint ID %s (db id: %d)", complaint.complaint_id, complaint.id)
        return complaint.to_dict()

    except IntegrityError as e:
        db.rollback()
        logger.warning("Duplicate complaint ID encountered: %s", cid)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Complaint with ID '{cid}' already exists."
        )
    except OperationalError as e:
        db.rollback()
        logger.error("Database connection failure while saving complaint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL database connection failed. Please ensure PostgreSQL is running and accessible."
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("SQLAlchemy database error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to persist complaint due to a database validation error."
        )
    except Exception as e:
        db.rollback()
        logger.error("Unexpected error saving complaint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while persisting the complaint."
        )


@router.get("", response_model=List[ComplaintResponse])
def list_complaints(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    Returns list of saved pharmaceutical complaints.
    """
    try:
        complaints = db.query(Complaint).order_by(Complaint.id.desc()).offset(skip).limit(limit).all()
        return [c.to_dict() for c in complaints]
    except OperationalError as e:
        logger.error("Database connection failure on list_complaints: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL database connection unavailable."
        )
    except Exception as e:
        logger.error("Error retrieving complaints: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving complaint records."
        )


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a single complaint by database integer ID or complaint_id string.
    """
    try:
        complaint = None
        if complaint_id.isdigit():
            complaint = db.query(Complaint).filter(Complaint.id == int(complaint_id)).first()
        if not complaint:
            complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()

        if not complaint:
            raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found.")

        return complaint.to_dict()
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error("Database connection failure on get_complaint: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL database connection unavailable."
        )
    except Exception as e:
        logger.error("Error retrieving complaint '%s': %s", complaint_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the complaint record."
        )
