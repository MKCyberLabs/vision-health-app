# Gemini CLI Flask API

This is a lightweight Flask-based API wrapper for the `gemini` CLI tool. It enables remote systems (like automation platforms) to interact with the AI assistant, handling interactive prompts (y/n) through a session-based approach.

## Setup

1. Ensure the `gemini` CLI is installed and in your `PATH`.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application can be configured using environment variables:

- `FLASK_HOST`: The IP to bind the server to (default: `172.17.0.1`).
- `FLASK_PORT`: The port to listen on (default: `5000`).
- `FLASK_DEBUG`: Set to `true` to enable debug mode.
- `GEMINI_PATH`: Absolute path to the `gemini` executable if it's not in the PATH.

## Usage

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
