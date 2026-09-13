# AIVOA — AI-Powered Pharmaceutical Complaint Management System

An end-to-end, locally runnable **AI-powered Customer Complaint Management System for the pharmaceutical industry**. Built for GMP/QMS customer complaint intake, document extraction, ICH Q9 quality risk triage, conversational AI investigation copilot, and PostgreSQL persistence.

---

## 1. System Architecture

```text
                                 +---------------------------------------+
                                 |         React + Vite Frontend         |
                                 |      (Redux Toolkit + Tailwind)       |
                                 +---------------------------------------+
                                                     │
                                        Axios REST   │   (CORS enabled)
                                                     ▼
                                 +---------------------------------------+
                                 |            FastAPI Backend            |
                                 |             (Python 3.12)             |
                                 +---------------------------------------+
                                      │                             │
                        Multipart File│                             │ Synchronous
                        Validation    ▼                             ▼ SQLAlchemy 2.0
                         +-----------------------+      +-----------------------+
                         | Document Text Parsers |      |      PostgreSQL       |
                         |  (pypdf, docx, eml)   |      |     (complaint_db)    |
                         +-----------------------+      +-----------------------+
                                      │
                                      ▼
             +───────────────────────────────────────────────────+
             |            LangGraph Processing Pipeline          |
             |           (In-Memory MemorySaver Checkpoint)      |
             +───────────────────────────────────────────────────+
                                      │
               1. Field Extraction (Groq openai/gpt-oss-120b verified)
                                      ▼
              2. Completeness Evaluation (GMP mandatory checks)
                                      ▼
              3. Severity Classification (Critical / Major / Minor)
                                      ▼
              4. ICH Q9 Quality Risk Assessment
                                      ▼
              5. Finalize Structured Result & AI Summary
                                      │
                                      ▼
             +───────────────────────────────────────────────────+
             |         AI Copilot Conversational Chat            |
             |       (Contextually Scoped by thread_id)          |
             +───────────────────────────────────────────────────+
```

---

## 2. Technology Stack

* **Frontend**: React 19, Vite, Redux Toolkit, Tailwind CSS, Google Inter Font, Axios, Lucide React Icons.
* **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (Synchronous `psycopg2-binary`, strictly NO async SQLAlchemy).
* **AI Orchestration**: LangGraph `StateGraph`, `MemorySaver` (in-memory checkpointing, strictly NO PostgreSQL checkpointer), `langchain-groq`.
* **Primary LLM**: Groq high-performance inference engine (`openai/gpt-oss-120b` — verified active model; `gemma2-9b-it` is decommissioned as of 2026, `qwen/qwen3.8-27b` is prohibited per assignment spec).
* **Document Parsing**: `pypdf`, `python-docx`, Python built-in `email` module (Strictly NO OCR).
* **Database**: PostgreSQL 18 local instance (`complaint_db`).

---

## 3. Project Directory Structure

```text
aivoa/
├── README.md                          # Comprehensive technical documentation
├── .env                               # Active local environment variables
├── .env.example                       # Reference environment variables
├── .gitignore                         # Git exclusion rules
├── requirements.txt                   # Root requirements pointer
├── sample_data/
│   ├── generate_sample_pdf.py         # ReportLab sample PDF generator
│   └── complaint_pdf_1.pdf            # Realistic pharmaceutical complaint PDF
├── test_e2e_workflow.py               # End-to-end integration test suite
├── backend/
│   ├── requirements.txt               # Backend Python dependencies
│   ├── main.py                        # FastAPI application entry point & CORS
│   └── app/
│       ├── api/
│       │   ├── routes_complaints.py   # Complaint CRUD & PostgreSQL persistence
│       │   └── routes_ai.py           # Document analysis & Copilot chat endpoints
│       ├── models/
│       │   └── complaint.py           # SQLAlchemy 2.0 Complaint table model
│       ├── schemas/
│       │   └── schemas.py             # Pydantic schemas for AI & persistence
│       ├── db/
│       │   └── session.py             # Synchronous SQLAlchemy 2.0 session engine
│       ├── utils/
│       │   └── file_parser.py         # PDF, DOCX, TXT, EML text extraction & size checks
│       └── ai/
│           ├── groq_client.py         # Centralized Groq client & 429 backoff
│           ├── graph.py               # LangGraph workflow & Copilot chat handler
│           ├── state.py               # ComplaintState TypedDict definition
│           └── nodes/
│               ├── extract_fields.py      # Field extraction + JSON fallback
│               ├── completeness_check.py  # GMP completeness verification
│               ├── classify_severity.py   # Severity & priority triage
│               ├── risk_assessment.py     # ICH Q9 risk assessment
│               └── finalize.py            # Result aggregation & AI summary
└── frontend/
    ├── package.json                   # React dependencies & scripts
    ├── vite.config.js                 # Vite build configuration
    ├── tailwind.config.js             # Tailwind CSS configuration
    ├── postcss.config.js              # PostCSS plugins
    ├── index.html                     # HTML5 template with Inter font
    └── src/
        ├── index.css                  # Custom styling & scrollbar
        ├── main.jsx                   # React root entry point
        ├── App.jsx                    # Root view orchestrator
        ├── store/
        │   ├── index.js               # Redux Toolkit store
        │   └── slices/
        │       ├── complaintSlice.js  # Form state, AI badges, & DB persistence
        │       └── aiCopilotSlice.js  # Upload progress, risk result, & chat
        ├── api/
        │   └── apiClient.js           # Axios API client
        ├── components/
        │   ├── Navbar.jsx             # Header with health & DB status pills
        │   ├── ComplaintForm/
        │   │   └── ComplaintForm.jsx  # Editable pharmaceutical complaint form
        │   └── AICopilot/
        │       ├── AICopilot.jsx          # Right pane container
        │       ├── FileDropzone.jsx       # Drag & drop upload with size checks
        │       ├── ExtractionProgress.jsx # Stepped extraction progress
        │       ├── RiskAssessmentCard.jsx # ICH Q9 risk badges & citations
        │       └── CopilotChat.jsx        # Conversational AI investigation chat
        └── pages/
            └── ComplaintDashboard.jsx # Dual-pane layout page
```

---

## 4. Prerequisites

* **Python**: 3.11+ (verified with 3.12.4; use standard virtual environment `.venv`)
* **Node.js**: 18+ (verified with v22.14.0)
* **npm**: 9+ (verified with 11.1.0)
* **PostgreSQL**: 14+ (installed locally on port 5432, service `postgresql-x64-18`)
* **Groq API Key**: Active key from [Groq Console](https://console.groq.com)

---

## 5. Environment Configuration

Create or update `.env` in the root directory:

```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
DATABASE_URL=postgresql://user:password@localhost:5432/complaint_db
ALLOWED_ORIGINS=http://localhost:5173
PORT=8000
```

> **Note**: If your PostgreSQL password contains special characters like `:`, `/`, or `;`, ensure they are URL-encoded in `DATABASE_URL` (e.g. `urllib.parse.quote_plus`).

---

## 6. Local Setup & Startup Instructions

### 1. Database Setup
Ensure PostgreSQL is running locally on port 5432 and the `complaint_db` database exists:

```sql
CREATE DATABASE complaint_db;
```
*(The backend automatically creates all required tables on startup via SQLAlchemy `Base.metadata.create_all`)*.

### 2. Backend Installation & Startup
Using a standard virtual environment:

```bash
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate  # Windows (or source .venv/bin/activate on Linux/macOS)

# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI backend server
cd backend
python -u main.py
```
* The backend will be live at `http://127.0.0.1:8000`.
* Health check endpoint: `http://127.0.0.1:8000/health`.
* Interactive Swagger Docs: `http://127.0.0.1:8000/docs`.

### 3. Frontend Installation & Startup
In a separate terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start Vite React development server
npm run dev
```
* The application UI will be accessible at `http://localhost:5173`.

---

## 7. Sample Data Generation

A realistic pharmaceutical customer complaint PDF is included under `sample_data/`:

```bash
python sample_data/generate_sample_pdf.py
```
This produces `sample_data/complaint_pdf_1.pdf`:
* **Product**: Ceftriaxone Sodium for Injection USP (1g / vial).
* **Batch**: `CTX-2025-098B`.
* **Issue**: Reconstituted sterile vials showed dark particulate matter and discoloration.
* **Missing Field**: Manufacturing facility is intentionally left blank to demonstrate the AI completeness checker.

---

## 8. LangGraph Workflow & MemorySaver Thread Strategy

### State Graph Flow
1. **`extract_fields`**: Uses LLM to extract product name, dosage, batch, quantities, and incident descriptions. Equipped with regex and markdown stripping to safely parse JSON.
2. **`completeness_check`**: Evaluates mandatory GMP fields (`product_name`, `batch_number`, `complaint_description`). Identifies missing fields and explains investigation impact.
3. **`classify_severity`**: Classifies preliminary initial severity (`Critical`, `Major`, `Minor`) and priority (`High`, `Medium`, `Low`).
4. **`risk_assessment`**: Implements ICH Q9 Quality Risk Management assessment (identifies hazards, rationale, and verbatim complaint citations).
5. **`finalize`**: Formulates unified structured output and concise executive summary.

### Thread Strategy (`thread_id`)
* When a file is uploaded, a unique `UUID4` `thread_id` is minted.
* LangGraph uses an in-memory `MemorySaver()` checkpointer.
* All subsequent AI Copilot queries reference this exact same `thread_id`, preserving full context of the complaint record and conversation history without sharing state across unrelated complaints.
* Strictly satisfies the requirement: **No PostgreSQL checkpointer is used for LangGraph**.

---

## 9. Error Handling & Resilience

1. **Document Validation**:
   - Files are checked against the 10 MB limit both on the frontend and on the FastAPI route before parsing.
   - Only `.pdf`, `.docx`, `.txt`, and `.eml` extensions are permitted; unauthorized types return HTTP 400.
2. **LLM JSON Parsing Fallback**:
   - If the LLM wraps JSON in markdown fences (````json ... ````) or outputs preamble text, regex recovery extracts the innermost `{...}` object.
   - If malformed JSON occurs, a rule-based fallback populates default fields and flags the issue without crashing.
3. **Groq HTTP 429 Rate Limiting**:
   - `execute_with_backoff` applies exponential backoff with jitter across up to 3 retries.
   - If the quota persists, returns a controlled user-friendly HTTP 429 response.
4. **PostgreSQL Resilience**:
   - Database operations are wrapped in `try/except OperationalError` blocks with automatic transaction rollbacks.
   - If the database is offline, `/health` reports `degraded` and the frontend shows an actionable error banner rather than crashing.

---

## 10. Automated End-to-End Test Suite

Run the automated E2E test suite to verify the entire pipeline:

```bash
python test_e2e_workflow.py
```

### Verified Test Cases:
1. `GET /health`: Returns 200 with active PostgreSQL and Groq status.
2. Negative test: Uploading `.exe` is rejected with HTTP 400.
3. Negative test: Uploading file > 10MB is rejected with HTTP 400.
4. Analysis pipeline: `complaint_pdf_1.pdf` parsed and extracted with high fidelity.
5. Completeness check: Correctly flags missing `Manufacturing Facility`.
6. Triage: Classifies defect as `Critical` Severity / `High` Risk.
7. Copilot Continuity: Copilot accurately answers queries using the `thread_id` context.
8. Persistence: Final complaint saved to PostgreSQL table `complaints`.
9. Query: Saved complaint retrieved and verified.

---

## 11. Interview Readiness & Explanations

### Complete Data Flow
```text
User selects PDF in Dropzone
   ↓
Client validates file type and size <= 10MB
   ↓
Axios multipart upload to POST /api/ai/analyze
   ↓
FastAPI parses bytes using pypdf into clean text
   ↓
Mint unique thread_id (UUID4)
   ↓
LangGraph StateGraph executes with MemorySaver
   ↓
Groq LLM extracts fields, checks completeness, & evaluates ICH Q9 risk
   ↓
Structured response dispatched to Redux (complaintSlice & aiCopilotSlice)
   ↓
Left Pane automatically populates fields with "AI" badges
   ↓
User reviews, fills in missing fields, and clicks "Save Complaint"
   ↓
POST /api/complaints commits record to PostgreSQL via SQLAlchemy 2.0
   ↓
User chats with Copilot in Right Pane using thread_id for contextual recall
```

### Common Interview Questions & Answers
* **Q: Why use LangGraph instead of a simple chain?**
  * *A: LangGraph provides a cyclical, stateful graph architecture where each node focuses on a specific QMS responsibility (extraction, completeness, triage, risk). This separation of concerns enables granular fallback handling, deterministic state inspection, and in-memory checkpointing (`MemorySaver`) per `thread_id`.*
* **Q: Why use synchronous SQLAlchemy instead of async?**
  * *A: In standard CRUD services with thread-pooled ASGI servers (Uvicorn), synchronous SQLAlchemy 2.0 with connection pooling (`pool_pre_ping=True`) is significantly simpler to trace, debug, and maintain without risking async context leaks or subtle event loop conflicts.*
* **Q: How are missing values distinguished from hallucinations?**
  * *A: The LLM extraction prompt strictly penalizes invention, instructing null outputs for absent data. The Completeness Node compares the output against mandatory GMP fields and flags missing elements with explicit visual warnings in the UI.*
