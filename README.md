# AI Executive Email Assistant — Backend API

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.8-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2.10.6-E92063.svg)](https://docs.pydantic.dev/)
[![Google Gemini](https://img.shields.io/badge/Gemini-3.1_Flash_Lite-orange.svg)](https://ai.google.dev/)

The backend service for the **AI Executive Email Assistant**. Built with **FastAPI**, **Pydantic v2**, and the **Google GenAI SDK (`google-genai`)**, this service exposes high-performance REST endpoints to analyze incoming executive emails, extract actionable intelligence, resolve deadlines, assess risks, and generate context-aware draft replies.

> **Related Repository:** [Frontend Client (React + Vite)](https://github.com/banrjeesayan/ai-email-assistant-frontend)

---

## Architecture & End-to-End Pipeline

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React / Vite)"]
        Req["HTTP POST /api/analyze"]
    end

    subgraph Backend["FastAPI Backend Service"]
        Main["FastAPI Router (main.py)"]
        CORS["CORS Middleware"]
        SchemaIn["Pydantic Validation (schemas.py)"]
        Analyzer["Analysis Pipeline (analyzer.py)"]
        KeyPool["11-Key Gemini Rotation Manager"]
        Cleaner["JSON Cleaner & Normalizer"]
        SchemaOut["Pydantic Result Validator (schemas.py)"]
        Evaluator["Benchmark Engine (evaluator.py)"]
    end

    subgraph AI["AI Layer (Google Gemini)"]
        Gemini["Gemini 3.1 Flash Lite (google-genai SDK)"]
    end

    Req --> Main
    Main --> CORS
    CORS --> SchemaIn
    SchemaIn --> Analyzer
    Analyzer --> KeyPool
    KeyPool -->|Low Temp 0.1, JSON Mode| Gemini
    Gemini -->|JSON / Text| Cleaner
    Cleaner --> SchemaOut
    SchemaOut -- "Validation Fails" -->|Self-Correction Retry| Gemini
    SchemaOut -- "Validated Result" --> Main
    Main -->|Structured JSON Response| Client
```

---

## Backend Workflow Stages

The backend processes every incoming email through 5 internal stages:

1. **Request Ingestion & Schema Verification (`main.py` & `schemas.py`)**
   - Receives incoming JSON via `POST /api/analyze`.
   - Validates user context (`user_name`, `user_role`, `tone`, `signoff`) and email fields (`sender`, `recipients`, `subject`, `body`, `received_at`) against `AnalyzeEmailRequest`.
2. **Prompt Engineering & Injection Defense (`analyzer.py`)**
   - Assembles an immutable system prompt with strict executive analysis guidelines.
   - **Prompt Injection Defense:** Strictly treats email text as untrusted **DATA** rather than instructions, preventing prompt injection attacks.
   - **Temporal Grounding:** Uses `received_at` timestamp and timezone to resolve relative time phrases (e.g., *"tomorrow morning"*, *"EOD Friday"*) into ISO/calendar dates.
   - **Hallucination Prevention:** Directs the model to output `[CONFIRM: ...]` placeholder tags for any unstated facts rather than inventing details.
3. **LLM Inference with Automated Key Pool Rotation (`analyzer.py`)**
   - Connects to Google Gemini (`gemini-3.1-flash-lite`) using the official `google-genai` SDK with deterministic temperature (`0.1`) and `response_mime_type="application/json"`.
   - **Multi-Key Failover:** Maintains a pool of up to 11 Gemini API keys loaded from `.env`. When Google raises a rate-limit error (`429`, `RESOURCE_EXHAUSTED`, or quota exceeded), the backend dynamically rotates to the next available key and retries seamlessly.
4. **JSON Sanitization, Schema Normalization & Self-Correction**
   - `clean_json()` removes any markdown enclosures (` ```json ... ``` `).
   - `normalize()` canonicalizes schema discrepancies (fuzzy key mapping, repairing combined sentiment/urgency blocks, and standardizing list structures).
   - Validates data against the strict `EmailAnalysisResult` Pydantic model.
   - **Self-Correction Retry Loop:** If parsing or validation encounters a `ValidationError`, the error is fed back to Gemini in an automated self-healing prompt to regenerate valid JSON.
   - `_ensure_body()` guarantees that a fallback draft reply is generated if `reply_needed` is `true`.
5. **Evaluation Benchmark Suite (`evaluator.py`)**
   - Includes a built-in benchmarking system evaluating 28 sample emails across 5 weighted dimensions:
     - **Intent match (25%)**
     - **Urgency match (20%)**
     - **Deadline accuracy (20%)**
     - **Action items precision & recall (15%)**
     - **Reply quality & safety flags (20%)**

---

## Technologies, Libraries & Tools

| Library / Tool | Version | Role & Specific Responsibility |
|---|---|---|
| **Python** | `3.10+` | Core programming language for the backend runtime. |
| **FastAPI** | `0.115.8` | Asynchronous REST API framework, path routing, and OpenAPI documentation. |
| **Uvicorn** | `0.34.0` | High-performance ASGI server hosting the FastAPI application. |
| **Pydantic** | `2.10.6` | Data validation, type enforcement, schema definitions, and custom validators. |
| **google-genai** | `1.5.0` | Official Google GenAI SDK used to interface with Gemini models in JSON mode. |
| **Gemini 3.1 Flash Lite** | `gemini-3.1-flash-lite` | LLM model performing intent extraction, sentiment scoring, deadline resolution, and drafting. |
| **python-dotenv** | `1.0.1` | Loads configuration and the 11-key API pool from `.env`. |
| **requests** | `2.32.3` | Synchronous HTTP utility library. |

---

## Directory Structure

```text
backend/
|-- app/
|   |-- analyzer.py       # Prompt engineering, key rotation, normalization & Gemini client
|   |-- evaluator.py      # Benchmark suite scoring 28 test cases across 5 metrics
|   |-- main.py           # FastAPI routes, CORS middleware, and application entry
|   |-- sample_data.py    # Ground-truth dataset containing 28 standard & edge-case emails
|   `-- schemas.py        # Pydantic models for incoming requests and structured outputs
|-- requirements.txt      # Pinned Python package dependencies
|-- run.py                # Convenience script to launch Uvicorn
`-- README.md             # Backend technical documentation
```

---

## Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# Gemini Model Selection
GEMINI_MODEL=gemini-3.1-flash-lite

# Gemini API Key Pool (configure 1 to 11 keys for automatic failover)
GEMINI_API_KEY_1=your_first_key_here
GEMINI_API_KEY_2=your_second_key_here
GEMINI_API_KEY_3=your_third_key_here
```

---

## Installation & Running Locally

### 1. Setup Virtual Environment
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Server
```bash
python run.py
```
Or with Uvicorn directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Base:** `http://localhost:8000`
- **Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## API Endpoints

### 1. Health Check
- **Endpoint:** `GET /api/health`
- **Response:**
  ```json
  {
    "status": "ok",
    "service": "AI Email Assistant API",
    "version": "1.0.0"
  }
  ```

### 2. Get Sample Emails
- **Endpoint:** `GET /api/samples`
- **Description:** Returns the 28 benchmark emails with metadata and categories.

### 3. Analyze Email
- **Endpoint:** `POST /api/analyze`
- **Request Body (`AnalyzeEmailRequest`):**
  ```json
  {
    "user_name": "Alex Morgan",
    "user_role": "Executive Director",
    "tone": "professional but warm",
    "signoff": "Best regards,\nAlex",
    "received_at": "2026-09-29 10:15 IST",
    "sender": "Taylor Lee <taylor@example.com>",
    "recipients": "Alex Morgan <alex@company.com>",
    "subject": "Follow-up on proposal",
    "body": "Hi Alex, can you review the attached proposal and send feedback by Friday?"
  }
  ```
- **Response Body (`EmailAnalysisResult`):**
  ```json
  {
    "success": true,
    "execution_source": "Gemini (gemini-3.1-flash-lite) — key #1",
    "data": {
      "summary": "Taylor Lee requests a review of the proposal by Friday.",
      "intent": {
        "primary": "request_action",
        "secondary": [],
        "explanation": "Sender asks for review and feedback on a proposal."
      },
      "action_items": [
        {
          "task": "Review proposal and send feedback",
          "owner": "user",
          "deadline": "2026-10-02",
          "explicit": true
        }
      ],
      "deadlines": [
        {
          "original_text": "by Friday",
          "resolved_date": "2026-10-02",
          "type": "hard",
          "ambiguity_note": null
        }
      ],
      "sentiment": {
        "label": "neutral",
        "reason": "Direct business request without strong emotional polarity."
      },
      "urgency": {
        "level": "medium",
        "reason": "Specific deadline requested within a few days."
      },
      "flags": [],
      "reply_needed": true,
      "suggested_response": {
        "subject": null,
        "body": "Hi Taylor,\n\nThanks for sending this over. I will review the proposal and share my feedback by Friday.\n\n[CONFIRM: any specific comments or approval]\n\nBest regards,\nAlex",
        "reason_if_none": null
      },
      "needs_user_input": [
        "Confirm review feedback points"
      ],
      "confidence": 0.95
    }
  }
  ```

---

## Running the Benchmark Evaluation Suite

To evaluate model accuracy across the 28 sample emails:

```bash
python3 -c "
from app.evaluator import run_benchmark_suite
import json
results = run_benchmark_suite()
print(json.dumps(results['summary'], indent=2))
"
```
