import uuid
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from groq import RateLimitError, AuthenticationError, APIError

from app.utils.file_parser import extract_text_from_upload
from app.ai.graph import run_complaint_analysis, chat_with_copilot
from app.schemas.schemas import AIAnalyzeResponse, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Processing"])


@router.post("/analyze", response_model=AIAnalyzeResponse)
async def analyze_document(
    file: UploadFile = File(...),
    thread_id: Optional[str] = Form(None)
):
    """
    Accepts uploaded complaint document (PDF, DOCX, TXT, EML), validates size and format,
    parses text, initiates or resets a LangGraph session for the given or generated thread_id,
    and returns structured QA results.
    """
    # 1. Parse text with strict validation
    raw_text = await extract_text_from_upload(file)

    # 2. Retain provided thread_id or mint new UUID
    session_thread_id = thread_id.strip() if (thread_id and thread_id.strip()) else str(uuid.uuid4())
    logger.info("Starting AI complaint analysis pipeline for thread_id=%s, file=%s", session_thread_id, file.filename)

    # 3. Execute LangGraph pipeline
    try:
        final_state = run_complaint_analysis(raw_text=raw_text, thread_id=session_thread_id)
    except AuthenticationError as e:
        logger.error("Groq Authentication Error during analysis: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed with AI provider. Please verify GROQ_API_KEY configuration."
        )
    except RateLimitError as e:
        logger.error("Groq Rate Limit 429 Error during analysis: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI inference rate limit reached. Please wait a moment before re-submitting."
        )
    except Exception as e:
        logger.error("LangGraph processing pipeline failure: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI complaint analysis pipeline encountered an internal processing error."
        )

    # Preview of raw text
    text_preview = (raw_text[:400] + "...") if len(raw_text) > 400 else raw_text

    return AIAnalyzeResponse(
        thread_id=session_thread_id,
        extracted_fields=final_state.get("extracted_fields", {}),
        completeness=final_state.get("completeness", {
            "completeness_status": "Unknown",
            "missing_fields": [],
            "explanation": "No completeness check result available."
        }),
        severity=final_state.get("severity", {
            "initial_severity": "Major",
            "priority": "Medium",
            "triage_notes": "Preliminary default assigned."
        }),
        risk_assessment=final_state.get("risk_assessment", {
            "risk_level": "Medium",
            "key_risk_factors": [],
            "rationale": "",
            "extracted_evidence": []
        }),
        ai_summary=final_state.get("ai_summary", "Summary unavailable."),
        raw_text_preview=text_preview
    )


@router.post("/chat", response_model=ChatResponse)
def copilot_chat(payload: ChatRequest):
    """
    AI Copilot conversation endpoint utilizing the thread_id.
    Supports both text-only sessions and document-assisted complaint analysis.
    """
    thread_id = payload.thread_id.strip()
    message = payload.message.strip()

    if not thread_id:
        raise HTTPException(status_code=400, detail="Missing required 'thread_id' parameter.")
    if not message:
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    try:
        result = chat_with_copilot(
            thread_id=thread_id,
            user_message=message,
            current_form_data=payload.form_data
        )
        if isinstance(result, dict):
            severity_val = result.get("severity")
            if not severity_val or not bool(severity_val):
                severity_val = None

            completeness_val = result.get("completeness")
            if not completeness_val or not bool(completeness_val):
                completeness_val = None

            risk_val = result.get("risk_assessment")
            if not risk_val or not bool(risk_val):
                risk_val = None

            return ChatResponse(
                reply=result.get("reply", ""),
                thread_id=thread_id,
                action=result.get("action", "conversation"),
                form_updates=result.get("form_updates", {}),
                extracted_fields=result.get("extracted_fields", {}),
                severity=severity_val,
                completeness=completeness_val,
                risk_assessment=risk_val
            )
        return ChatResponse(reply=str(result), thread_id=thread_id)


    except AuthenticationError as e:
        logger.error("Groq Authentication Failure in chat: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed with AI provider. Please verify GROQ_API_KEY configuration."
        )
    except RateLimitError as e:
        logger.error("Groq Rate Limit 429 in chat: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI Copilot rate limit reached. Please wait a moment before trying again."
        )
    except Exception as e:
        logger.error("Error in AI Copilot chat: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI Copilot chat service encountered an error."
        )
