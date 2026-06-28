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
