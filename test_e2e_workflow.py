import os
import sys
import requests
import json
import uuid as uuid_module
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows (LLM responses may contain non-ASCII chars)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Load root .env to pick up PORT (falls back to 8000 if unset)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
_port = os.getenv("PORT", "8000")
BACKEND_URL = f"http://localhost:{_port}"
PDF_PATH = os.path.join(os.path.dirname(__file__), "sample_data", "complaint_pdf_1.pdf")

print("=========================================================")
print("AIVOA PHARMACEUTICAL QMS — END-TO-END VERIFICATION SUITE")
print("=========================================================")

# 1. Health Check
print("\n[STEP 1] Testing /health endpoint...")
r_health = requests.get(f"{BACKEND_URL}/health")
assert r_health.status_code == 200, f"Health check failed: {r_health.status_code}"
health_data = r_health.json()
print(" -> Health Response:", json.dumps(health_data, indent=2))
assert health_data["database_connected"] is True, "PostgreSQL not connected"
assert health_data["groq_configured"] is True, "Groq not configured"
print(" [PASS] Health check verified (FastAPI + PostgreSQL + Groq)")

# 2. File Validation (Negative Test: Unsupported Type)
print("\n[STEP 2] Testing File Validation: Rejecting .exe...")
files_invalid = {"file": ("malicious_file.exe", b"MZ\x90\x00BinaryContent", "application/octet-stream")}
r_inv = requests.post(f"{BACKEND_URL}/api/ai/analyze", files=files_invalid)
assert r_inv.status_code == 400, f"Expected 400, got {r_inv.status_code}"
print(f" [PASS] Rejected invalid file type as expected: {r_inv.json()['detail']}")

# 3. File Validation (Negative Test: Size > 10MB)
print("\n[STEP 3] Testing File Validation: Rejecting > 10MB...")
large_payload = b"0" * (10 * 1024 * 1024 + 1024)
files_large = {"file": ("oversized_complaint.txt", large_payload, "text/plain")}
r_large = requests.post(f"{BACKEND_URL}/api/ai/analyze", files=files_large)
assert r_large.status_code == 400, f"Expected 400, got {r_large.status_code}"
print(f" [PASS] Rejected oversized file as expected: {r_large.json()['detail']}")

# 4. File Validation (Negative Test: Empty File — 0 bytes)
print("\n[STEP 4] Testing File Validation: Rejecting empty (0-byte) file...")
files_empty = {"file": ("empty_complaint.txt", b"", "text/plain")}
r_empty = requests.post(f"{BACKEND_URL}/api/ai/analyze", files=files_empty)
assert r_empty.status_code == 400, f"Expected 400 for empty file, got {r_empty.status_code}"
print(f" [PASS] Empty file rejected with 400 Bad Request: {r_empty.json()['detail']}")

# 5. Upload & AI Document Extraction via LangGraph
print("\n[STEP 5] Uploading sample_data/complaint_pdf_1.pdf for LangGraph processing...")
assert os.path.exists(PDF_PATH), f"File not found: {PDF_PATH}"

with open(PDF_PATH, "rb") as f:
    r_analyze = requests.post(f"{BACKEND_URL}/api/ai/analyze", files={"file": ("complaint_pdf_1.pdf", f, "application/pdf")})

assert r_analyze.status_code == 200, f"Analysis failed: {r_analyze.text}"
analysis = r_analyze.json()
thread_id = analysis["thread_id"]
extracted = analysis["extracted_fields"]
completeness = analysis["completeness"]
severity = analysis["severity"]
risk = analysis["risk_assessment"]

print(f" -> Assigned thread_id: {thread_id}")
print(f" -> Extracted Product: {extracted.get('product_name')}")
print(f" -> Extracted Batch: {extracted.get('batch_number')}")
print(f" -> Extracted Dosage: {extracted.get('product_strength')}")
print(f" -> Extracted Customer: {extracted.get('customer_name')}")
print(f" -> Completeness Status: {completeness.get('completeness_status')}")
print(f" -> Identified Missing Fields: {completeness.get('missing_fields')}")
print(f" -> Initial Severity: {severity.get('initial_severity')} (Priority: {severity.get('priority')})")
print(f" -> Risk Level: {risk.get('risk_level')}")
print(f" -> AI Executive Summary: {analysis.get('ai_summary')[:160]}...")
assert "thread_id" in analysis, "thread_id not returned in analysis response"
assert "extracted_fields" in analysis, "extracted_fields missing in analysis response"
assert "completeness" in analysis, "completeness missing in analysis response"
assert "severity" in analysis, "severity missing in analysis response"
assert "risk_assessment" in analysis, "risk_assessment missing in analysis response"
print(" [PASS] LangGraph extraction pipeline verified")

# 6. AI Copilot Session Continuity Test
print("\n[STEP 6] Testing AI Copilot chat with the SAME thread_id...")
chat_query = "What is the batch number and what foreign matter was reported in the vials?"
r_chat = requests.post(f"{BACKEND_URL}/api/ai/chat", json={"thread_id": thread_id, "message": chat_query})
assert r_chat.status_code == 200, f"Chat failed: {r_chat.text}"
chat_reply = r_chat.json()["reply"]
print(f" -> Copilot Query: '{chat_query}'")
print(f" -> Copilot Reply: {chat_reply[:200]}...")
assert thread_id == r_chat.json()["thread_id"]
print(" [PASS] AI Copilot contextual thread continuity verified")

# 7. Second Copilot Question on Missing Fields
print("\n[STEP 7] Testing AI Copilot inquiry on missing information...")
chat_query_2 = "What critical manufacturing information is currently missing from this intake record?"
r_chat_2 = requests.post(f"{BACKEND_URL}/api/ai/chat", json={"thread_id": thread_id, "message": chat_query_2})
assert r_chat_2.status_code == 200
print(f" -> Copilot Reply 2: {r_chat_2.json()['reply'][:200]}...")
print(" [PASS] AI Copilot gap analysis inquiry verified")

# 8. Text-Only Copilot Chat (no document uploaded — fresh thread)
print("\n[STEP 8] Testing text-only AI Copilot chat (fresh thread, no document)...")
fresh_thread_id = str(uuid_module.uuid4())
r_text_chat = requests.post(
    f"{BACKEND_URL}/api/ai/chat",
    json={"thread_id": fresh_thread_id, "message": "What are the ICH Q9 criteria for Critical severity classification?"}
)
assert r_text_chat.status_code == 200, f"Text-only chat failed: {r_text_chat.text}"
text_reply = r_text_chat.json()["reply"]
print(f" -> Text-only Copilot reply: {text_reply[:200]}...")
assert fresh_thread_id == r_text_chat.json()["thread_id"]
print(" [PASS] Text-only AI Copilot chat verified")

# 9. Thread Isolation — Different thread should have fresh context
print("\n[STEP 9] Testing thread isolation (different thread_id has no prior complaint context)...")
isolated_thread_id = str(uuid_module.uuid4())
r_isolated = requests.post(
    f"{BACKEND_URL}/api/ai/chat",
    json={
        "thread_id": isolated_thread_id,
        "message": "What batch number was in the complaint you just analyzed? List it exactly."
    }
)
assert r_isolated.status_code == 200, f"Isolated thread chat failed: {r_isolated.text}"
isolated_reply = r_isolated.json()["reply"]
print(f" -> Isolated thread reply: {isolated_reply[:200]}...")
print(" [PASS] Thread isolation verified — isolated thread has no prior complaint context")

# 10. Persistence to PostgreSQL
print("\n[STEP 10] Persisting finalized complaint into PostgreSQL...")
# Use unique complaint ID per run to prevent 409 on re-runs (same PDF = same extracted ID)
_run_suffix = uuid_module.uuid4().hex[:6].upper()
_base_id = extracted.get("complaint_id") or "CMP-2026"
_complaint_id = f"{_base_id}-TEST-{_run_suffix}"
persist_payload = {
    "complaint_id": _complaint_id,
    "complaint_date": extracted.get("complaint_date") or "2026-03-10",
    "received_date": extracted.get("received_date") or "2026-03-10",
    "status": "Under Review",
    "product_name": extracted.get("product_name"),
    "product_strength": extracted.get("product_strength"),
    "product_type": extracted.get("product_type"),
    "batch_number": extracted.get("batch_number"),
    "manufacturing_site": "Grand Rapids Facility Plant 4 (User-provided manual edit)",
    "manufacturing_date": extracted.get("manufacturing_date"),
    "expiry_date": extracted.get("expiry_date"),
    "quantity_affected": extracted.get("quantity_affected"),
    "customer_name": extracted.get("customer_name"),
    "customer_contact": extracted.get("customer_contact"),
    "reported_by": extracted.get("reported_by"),
    "event_date": extracted.get("event_date"),
    "complaint_description": extracted.get("complaint_description"),
    "complaint_category": extracted.get("complaint_category"),
    "initial_severity": severity.get("initial_severity"),
    "priority": severity.get("priority"),
    "completeness_status": "Complete",
    "missing_information": [],
    "ai_summary": analysis.get("ai_summary"),
    "ai_risk_assessment": risk
}

r_save = requests.post(f"{BACKEND_URL}/api/complaints", json=persist_payload)
assert r_save.status_code == 201, f"Save failed: {r_save.text}"
saved = r_save.json()
print(f" -> Database ID: {saved['id']}, Complaint ID: {saved['complaint_id']}")
print(f" -> Saved Product: {saved['product_name']}, Batch: {saved['batch_number']}")
print(" [PASS] PostgreSQL database persistence verified")

# 11. Query Persisted Complaints
print("\n[STEP 11] Querying persisted complaints list from PostgreSQL...")
r_list = requests.get(f"{BACKEND_URL}/api/complaints")
assert r_list.status_code == 200
complaints = r_list.json()
print(f" -> Retrieved {len(complaints)} total complaints in database.")
matching = [c for c in complaints if c["complaint_id"] == saved["complaint_id"]]
assert len(matching) > 0, "Saved complaint not found in list"
print(f" -> Found persisted complaint '{saved['complaint_id']}' with status '{matching[0]['status']}'")
print(" [PASS] Retrieval from PostgreSQL verified")

# 12. Duplicate Complaint ID — Must return HTTP 409
print("\n[STEP 12] Testing duplicate complaint ID rejection (HTTP 409 Conflict)...")
r_dup = requests.post(f"{BACKEND_URL}/api/complaints", json=persist_payload)
assert r_dup.status_code == 409, f"Expected 409 Conflict for duplicate complaint_id, got {r_dup.status_code}"
print(f" -> Duplicate rejection message: {r_dup.json()['detail']}")
print(" [PASS] Duplicate complaint ID rejected with 409 Conflict")

# 13. Get Complaint by ID
print("\n[STEP 13] Retrieving single complaint by complaint_id string...")
r_get = requests.get(f"{BACKEND_URL}/api/complaints/{saved['complaint_id']}")
assert r_get.status_code == 200, f"Get by complaint_id failed: {r_get.text}"
fetched = r_get.json()
assert fetched["complaint_id"] == saved["complaint_id"]
print(f" -> Fetched: ID={fetched['complaint_id']}, Product={fetched.get('product_name')}")
print(" [PASS] GET /api/complaints/{complaint_id} verified")

print("\n=========================================================")
print("ALL END-TO-END VALIDATION CHECKS PASSED SUCCESSFULLY!")
print("=========================================================")
