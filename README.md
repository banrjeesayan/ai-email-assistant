# AI Executive Email Assistant

A full-stack email analysis assistant that turns an incoming email into structured insight, action items, deadline detection, risk flags, and a ready-to-edit draft reply.

The application uses a FastAPI backend, a React/Vite frontend, and Google Gemini for AI-powered analysis. It is designed for executive-style inbox workflows where speed, accuracy, and clear follow-up matter.

## Features

- Analyze pasted emails and extract the main request, intent, urgency, and sentiment.
- Generate professional draft replies with `[CONFIRM: ...]` placeholders for missing information.
- Identify action items, owners, deadlines, and ambiguity.
- Resolve relative deadlines against the email received timestamp.
- Flag risks such as phishing, escalation, missing information, legal/financial concerns, and sensitive personal matters.
- Validate AI output against a strict Pydantic schema.
- Rotate through multiple Gemini API keys when quota limits are reached.
- Browse built-in sample emails for quick testing.
- View formatted analysis results or raw JSON output.

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, lucide-react |
| Backend | Python, FastAPI, Pydantic |
| AI Provider | Google Gemini through `google-genai` |
| Configuration | `.env`, `python-dotenv` |

## Project Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- analyzer.py       # Gemini prompt, key rotation, validation, normalization
|   |   |-- evaluator.py      # Benchmark evaluation helpers
|   |   |-- main.py           # FastAPI application and API routes
|   |   |-- sample_data.py    # Sample email dataset
|   |   `-- schemas.py        # Request and response models
|   |-- requirements.txt
|   `-- run.py
|-- frontend/
|   |-- src/
|   |   |-- components/       # UI components
|   |   |-- api.js            # API client helpers
|   |   |-- App.jsx
|   |   `-- main.jsx
|   `-- package.json
|-- start.sh                  # Starts backend and frontend together
`-- README.md
```

## Requirements

- Python 3.10+
- Node.js 18+
- npm
- At least one Gemini API key

## Environment Setup

Create `backend/.env` and add at least one Gemini API key:

```env
GEMINI_API_KEY_1=your_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

You can configure up to 11 keys:

```env
GEMINI_API_KEY_1=your_first_key
GEMINI_API_KEY_2=your_second_key
...
GEMINI_API_KEY_11=your_eleventh_key
```

The backend tries keys in order and rotates to the next key when Gemini returns a quota-related error.

## Run Locally

### Option 1: Start Everything

```bash
chmod +x start.sh
./start.sh
```

This starts:

- Backend API: `http://localhost:8000`
- Frontend app: `http://localhost:3000`

### Option 2: Start Services Manually

Start the backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Start the frontend in another terminal:

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

Open the app at:

```text
http://localhost:3000
```

Default demo login:

```text
Username: admin
Password: admin
```

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/health` | Returns service status and version. |
| `GET` | `/api/samples` | Returns the built-in sample email dataset. |
| `POST` | `/api/analyze` | Analyzes one email and returns structured AI output. |

### Analyze Request

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
  "body": "Hi Alex, can you review the proposal and send feedback by Friday?"
}
```

### Analyze Response

```json
{
  "success": true,
  "execution_source": "Gemini (gemini-3.1-flash-lite) - key #1",
  "data": {
    "summary": "...",
    "intent": {
      "primary": "request_action",
      "secondary": [],
      "explanation": "..."
    },
    "action_items": [],
    "deadlines": [],
    "sentiment": {
      "label": "neutral",
      "reason": "..."
    },
    "urgency": {
      "level": "medium",
      "reason": "..."
    },
    "flags": [],
    "reply_needed": true,
    "suggested_response": {
      "subject": null,
      "body": "...",
      "reason_if_none": null
    },
    "needs_user_input": [],
    "confidence": 0.9
  }
}
```

## Analysis Pipeline

1. The frontend sends the email content and user context to `/api/analyze`.
2. The backend builds a structured prompt with the user profile, received timestamp, sender, recipients, subject, and body.
3. Gemini returns JSON using a low-temperature configuration.
4. The backend cleans and normalizes the response.
5. Pydantic validates the result against the email analysis schema.
6. If validation fails, the backend retries once with the validation error included.
7. The API returns structured analysis and a draft response to the frontend.

## Response Schema

The model returns these main fields:

| Field | Purpose |
| --- | --- |
| `summary` | Short explanation of who wants what and why it matters. |
| `intent` | Primary intent, secondary intents, and explanation. |
| `action_items` | Tasks, owners, deadlines, and whether each item is explicit. |
| `deadlines` | Original date text, resolved date, deadline type, and ambiguity notes. |
| `sentiment` | Sentiment label and reasoning. |
| `urgency` | Urgency level and reasoning. |
| `flags` | Risk and workflow flags. |
| `reply_needed` | Whether a reply should be drafted. |
| `suggested_response` | Draft subject/body or reason no response is needed. |
| `needs_user_input` | Decisions or missing facts the user must provide. |
| `confidence` | Confidence score from 0.0 to 1.0. |

## Frontend Screens

- `LoginPage.jsx`: Demo login screen.
- `EmailAnalyzer.jsx`: Email input and analysis trigger.
- `SampleSelector.jsx`: Built-in sample email browser.
- `AnalysisView.jsx`: Formatted result view and raw JSON view.
- `BenchmarkView.jsx`: Benchmark UI placeholder that expects a backend benchmark route.
- `PromptDocView.jsx`: Prompt design documentation.

## Current Limitations

- Demo login is handled in the browser only and should not be used as production authentication.
- CORS is currently open to all origins.
- The frontend includes a benchmark view, but the backend does not currently expose `/api/benchmark`.
- Backend exceptions are wrapped by the API route, so some original HTTP status codes may be returned as `500`.
- API keys are rotated through a global index and are not protected by a lock.

## Production Recommendations

- Add server-side authentication and authorization.
- Restrict CORS to trusted frontend origins.
- Store API keys in a managed secrets service.
- Add request logging, rate limiting, and monitoring.
- Add automated tests for the API contract and schema normalization.
- Implement `/api/benchmark` or remove the benchmark UI until the route is available.

## License

No license file is currently included. Add a license before publishing or distributing this project.
