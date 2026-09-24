# NutriSnap Analysis Provider API

This Flask service is the AI boundary for NutriSnap. Meal analysis can run through the authenticated Antigravity CLI, OpenRouter, or the Google Gemini API while the HTTP contract consumed by NutriSnap stays stable. Antigravity remains the default.

## Setup

1. Ensure the `agy` CLI is installed, authenticated, and in your `PATH`.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Provider configuration

Copy `.env.example` to `.env`. The default configuration uses the existing Antigravity subscription:

```env
ANALYSIS_TEXT_PROVIDER=agy
ANALYSIS_IMAGE_PROVIDER=agy
AGY_TEXT_MODEL=gemini-3.8-flash-low
AGY_IMAGE_MODEL=gemini-3.8-flash-low
ANALYSIS_FALLBACK_PROVIDER=none
```

Use model IDs printed by `agy models`, rather than display labels. The old `GEMINI_TEXT_MODEL` and `GEMINI_IMAGE_MODEL` names remain supported as aliases. Removed Gemini 3.5 Flash names are automatically mapped to the matching Gemini 3.8 Flash effort level during an upgrade.

To use OpenRouter for text while leaving image analysis on Antigravity:

```env
ANALYSIS_TEXT_PROVIDER=openrouter
ANALYSIS_IMAGE_PROVIDER=agy
OPENROUTER_API_KEY=...
OPENROUTER_TEXT_MODEL=google/gemini-2.5-flash
```

To use the direct Google API, select `google` and configure `GOOGLE_API_KEY` (or the compatible `GEMINI_API_KEY`) plus `GOOGLE_TEXT_MODEL` and `GOOGLE_IMAGE_MODEL`.

Fallback is opt-in. For example, `ANALYSIS_FALLBACK_PROVIDER=openrouter` retries retriable Antigravity failures through OpenRouter. Invalid input and configuration errors do not trigger fallback.

Do not use `agy -c` for HTTP requests. It continues the most recent conversation and can mix context between users. The service intentionally invokes stateless `agy -p` requests.

## Running the Server

### Option A: Foreground (Development)
Start the Flask application natively (make sure your virtual environment is activated):
```bash
python app.py
```
*(By default, this runs on `0.0.0.0:5000` to allow the Dockerized frontend to communicate with it.)*

### Option B: Background (Production/Continuous)
To start the server so it continues running after you close your terminal:
```bash
nohup python app.py > backend.log 2>&1 &
```

### Stopping or Restarting a Background Server
If you change your `.env` models or need to restart a server running in the background:

1. **Find the Process ID (PID)**:
   ```bash
   ps aux | grep "[p]ython app.py"
   ```
   *Look for the number in the second column (e.g., `4382`).*
2. **Kill the Process**:
   ```bash
   kill <PID>
   ```
3. **Restart**:
   Run the `nohup` command from Option B again.

## Usage

Health checks are available at `GET /health` and `GET /ready`. The readiness response reports configuration booleans only and never returns API keys.

Meal endpoints return a structured `result` and retain the legacy JSON-string `response` during rolling deployments. The response metadata identifies the provider, model, request, fallback state, and latency.

### 1. Initiate a Request
Send a POST request to `/ask` with your prompt.

**Request:**
```bash
curl -X POST http://172.17.0.1:5000/ask \
     -H "Content-Type: application/json" \
     -d '{"message": "Add a license header to all files in src/"}'
```

**Response (Success):**
```json
{"status": "success", "response": "Completed successfully."}
```

**Response (Approval Needed):**
```json
{
  "status": "needs_approval",
  "session_id": "8432-...",
  "message": "I will modify 5 files. Proceed? [y/n]"
}
```

### 2. Provide Approval
If the response status is `needs_approval`, send the answer to `/reply`.

**Request:**
```bash
curl -X POST http://172.17.0.1:5000/reply \
     -H "Content-Type: application/json" \
     -d '{"session_id": "8432-...", "answer": "y"}'
```

The API will continue to return `needs_approval` if the CLI asks subsequent questions, or `success` when the command completes.

## Tests

Run the provider, contract, and Flask route tests from `gemini-api`:

```bash
./venv/bin/python -m unittest discover -s tests -v
```
