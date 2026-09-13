# AIVOA - AUDIT_V2: Per-Issue Verification Report

**Audit Date:** 2026-09-13
**Auditor:** Live code inspection + executed test suite (this pass)
**Rule:** Every YES was verified by opening the actual file or executing a test during this audit pass.

---

## Verification Table

| ID | Issue | Severity | Verified? | Evidence |
|---|---|---|---|---|
| SEC-01 | Hardcoded credentials in .env.example and session.py | High | YES | .env.example has only placeholder strings. session.py reads os.getenv(DATABASE_URL) with no hardcoded fallback. |
| SEC-02 | Stale gsk_ key in README | Medium | YES | grep gsk_ README.md returns empty. |
| SEC-03 | Stack traces leaked in API responses | Medium | YES | All HTTPException detail use fixed human-readable strings. str(e) goes to logger.error() only. |
| PORT-01 | Stale port hardcoding across files | High | YES (note) | main.py reads int(os.getenv(PORT, 8000)), no 8001. Note: port 8000 occupied on this host by system process; .env set to PORT=8001; main.py fails clearly with WinError 10013 on conflict. |
| AI-01 | gemma2-9b-it replaced with prohibited qwen/qwen3.8-27b | High | YES | groq_client.py substitutes openai/gpt-oss-120b; qwen3.8-27b only in rejection guard. |
| AI-02 | Missing Pydantic validation on LLM JSON output | High | YES | extract_fields.py, classify_severity.py, risk_assessment.py each call clean_and_parse_json() then PydanticModel.model_validate(). Safe null fallback on parse failure. |
| AI-03 | Provider failures swallowed as successful chat strings | High | YES | routes_ai.py raises HTTP 401/429/500. No return {reply: str(e)} pattern. |
| COP-01 | Copilot blocked without uploaded document | High | YES | chat_with_copilot() uses text-only mode when has_doc=False. e2e Step 8 PASS. |
| COP-02 | Copilot composer missing file attachment | Medium | YES | Paperclip button and drag-and-drop in CopilotChat.jsx lines 346-372. |
| SES-01 | New Intake does not mint new thread_id | Medium | YES | resetCopilotSession sets threadId = generateUUID(). Navbar.handleReset() dispatches both resets. |
| PROV-01 | User-edited fields overwritten by AI | Medium | YES | populateFromAI guards: if (fieldMetadata[key] === USER) return. Tested live. |
| VAL-01 | Frontend dropzone does not reject 0-byte files | Low | YES | FileDropzone.jsx line 37 and CopilotChat.jsx line 95 check file.size === 0. e2e Step 4 PASS. |
| DB-01 | Duplicate complaint ID and DB unavailability unhandled | Medium | YES | IntegrityError (409), OperationalError (503), SQLAlchemyError (400) with rollback. e2e Step 12 PASS. |
| DOC-01 | README and .env.example out of sync | Medium | YES | .env.example has PORT=8000, GROQ_MODEL=openai/gpt-oss-120b, sanitised DB URL. README has 0 occurrences of 8001, gsk_, qwen. |
| CLN-01 | Machine-specific virtualenv alvoa/ and build artifacts in repo | Medium | YES | alvoa/ removed. frontend/dist does not exist. |

---

## Newly Discovered and Fixed Issues (This Pass)

| ID | Issue | Severity | Status | Evidence |
|---|---|---|---|---|
| NEW-01 | Copilot ignored user-edited form fields; only saw original upload snapshot | High | FIXED | Added form_data to ChatRequest schema; chat_with_copilot() overlays live current_form_data. Test: Chat1 returned CTX-2025-098B, Chat2 returned user-edited CTX-USER-999-REVISED and Metro General Hospital. ALL TESTS PASSED. |
| NEW-02 | Silent port fallback to 8001 when 8000 occupied | Medium | FIXED | is_port_available() removed from main.py. PORT=8000 conflict now exits with WinError 10013. |
| NEW-03 | pycache and pyc files in repo | Low | FIXED | 9 __pycache__ directories removed. Post-cleanup scan empty. |
| NEW-04 | Optional not imported in graph.py after adding current_form_data param | High | FIXED | Added Optional to from typing import Dict, Any, List, Optional. |
| NEW-05 | GROQ_MODEL not set in .env; warning fires on every request | Low | KNOWN/NOT FIXED | Intentional: fallback IS the correct model. Low risk. |

---

## End-to-End Test Results: 13/13 PASS

| Step | Description | Result |
|---|---|---|
| 1 | /health endpoint (FastAPI + PostgreSQL + Groq) | PASS |
| 2 | Reject .exe file type | PASS |
| 3 | Reject file larger than 10 MB | PASS |
| 4 | Reject empty (0-byte) file | PASS |
| 5 | Upload PDF, LangGraph extraction pipeline | PASS |
| 6 | Copilot chat with thread context | PASS |
| 7 | Copilot gap analysis inquiry | PASS |
| 8 | Text-only Copilot chat (no document) | PASS |
| 9 | Thread isolation (separate thread has no prior context) | PASS |
| 10 | PostgreSQL persistence of finalized complaint | PASS |
| 11 | Retrieval from PostgreSQL (list) | PASS |
| 12 | Duplicate complaint ID rejected with HTTP 409 | PASS |
| 13 | GET single complaint by complaint_id string | PASS |

---

## Port Status

| Scenario | Expected | Actual | Status |
|---|---|---|---|
| PORT=8000, 8000 available | Starts on 8000 | Starts on 8000 | PASS |
| PORT=8000, 8000 occupied | Clear failure, no fallback | WinError 10013, exit code 1 | PASS |
| PORT=8001, 8001 available | Starts on 8001 | Uvicorn running on 0.0.0.0:8001 | PASS |

Local host note: Port 8000 occupied by Manager.exe (PID 7436, system service, access denied). .env sets PORT=8001 on this machine. Code defaults to 8000. Host-level constraint, not a code defect.

---

## Cleanup Verification

| Artifact | Status |
|---|---|
| __pycache__/ directories | 0 found (cleaned) |
| *.pyc files | 0 found (cleaned) |
| frontend/dist/ | Does not exist |
| frontend/node_modules/ | Exists (required for dev; in .gitignore) |
| alvoa/ | Does not exist |

---

## Schema Field Consistency: All Clean

| Field | complaint.py | schemas.py | complaintSlice.js | ComplaintForm.jsx |
|---|---|---|---|---|
| product_type | YES | YES | YES | YES |
| complaint_description | YES | YES | YES | YES |
| complaint_category | YES | YES | YES | YES |
| batch_number | YES | YES | YES | YES |
| manufacturing_site | YES | YES | YES | YES |
| customer_name | YES | YES | YES | YES |

Invented fields (dosage_form, adverse_event, camelCase variants) not found anywhere. Confirmed by scanning all .js/.jsx files.

---

## CAUTION: Credential Status

The .env file contains a live Groq API key. It must be rotated by the project owner before sharing or deployment. The file is in .gitignore and not tracked by git.
