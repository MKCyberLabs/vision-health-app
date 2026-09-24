import os
import json
import pexpect
import uuid
import time
import threading
from flask import Flask, request, jsonify
import shutil
from dotenv import load_dotenv

from analysis_contract import (
    AnalysisContractError,
    meal_analysis_schema,
    validate_meal_analysis,
)
from prompts import build_health_prompt, build_telegram_prompt
from providers import (
    AgyProvider,
    GoogleProvider,
    OpenRouterProvider,
    ProviderError,
    ProviderRouter,
)

# Load environment variables from .env if present
load_dotenv()

app = Flask(__name__)

# ⚡ Bolt Optimization: Cache paths at module level to avoid repeated os.stat/I/O per request
HOST_TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'temp'))

def get_agy_path():
    # 1. Check environment variable override
    env_path = os.environ.get("AGY_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
        
    # 2. Check system PATH
    system_path = shutil.which("agy") or shutil.which("agy.exe")
    if system_path:
        return system_path
        
    # 3. Check common hardcoded locations
    common_paths = [
        os.path.expanduser("~/.local/bin/agy"),
        "/root/.local/bin/agy",
        "/usr/local/bin/agy",
        "/usr/bin/agy"
    ]
    
    # 4. If running as root, dynamically check all user home directories
    if os.path.exists("/home"):
        for user_dir in os.listdir("/home"):
            common_paths.append(f"/home/{user_dir}/.local/bin/agy")
            
    for path in common_paths:
        if os.path.exists(path):
            return path
            
    # Fallback
    return "agy"

AGY_PATH = get_agy_path()
PROVIDER_ROUTER = ProviderRouter({
    "agy": AgyProvider(AGY_PATH),
    "openrouter": OpenRouterProvider(),
    "google": GoogleProvider(),
})

from werkzeug.exceptions import HTTPException

# Dictionary to hold live CLI processes and metadata in RAM
active_sessions = {}

def safe_close_child(child):
    if child and child.isalive():
        try:
            child.close(force=True)
        except Exception:
            pass

def cleanup_stale_sessions():
    while True:
        try:
            current_time = time.time()
            for sid, data in list(active_sessions.items()):
                if current_time - data.get("timestamp", 0) > 300: # 5 minutes TTL
                    app.logger.warning(f"Cleaning up stale session: {sid}")
                    child = data.get("child")
                    safe_close_child(child)
                    host_image_path = data.get("image_path")
                    if host_image_path and os.path.exists(host_image_path):
                        try:
                            os.remove(host_image_path)
                        except Exception:
                            pass
                    active_sessions.pop(sid, None)
        except Exception as e:
            app.logger.error(f"Error in background cleanup loop: {e}")
        time.sleep(60)

# Start background cleanup thread
cleanup_thread = threading.Thread(target=cleanup_stale_sessions, daemon=True)
cleanup_thread.start()

@app.errorhandler(Exception)
def handle_exception(e):
    # Pass through HTTP errors to standard handlers if they are configured
    if isinstance(e, HTTPException):
        return jsonify({"status": "error", "message": e.description}), e.code
    # Log the full exception but return a safe generic message
    app.logger.exception("Unhandled Exception: %s", e)
    return jsonify({"status": "error", "message": "An internal error occurred."}), 500

@app.errorhandler(400)
def handle_400(e):
    return jsonify({"status": "error", "message": "Bad Request."}), 400

@app.errorhandler(404)
def handle_404(e):
    return jsonify({"status": "error", "message": "Not Found."}), 404

@app.errorhandler(405)
def handle_405(e):
    return jsonify({"status": "error", "message": "Method Not Allowed."}), 405

@app.errorhandler(415)
def handle_415(e):
    return jsonify({"status": "error", "message": "Unsupported Media Type."}), 415

# Prompt regexes for the gemini CLI
PROMPT_REGEXES = [r'(?i)proceed\? \[y/n\]', r'(?i)yes/no']

def handle_cli_interaction(child, session_id, host_image_path):
    """
    Common logic to handle interaction with a pexpect child.
    Returns a Flask response based on the CLI's state.
    """
    try:
        # Listen for prompts or process completion
        index = child.expect(PROMPT_REGEXES + [pexpect.EOF], timeout=300)
        
        if index < len(PROMPT_REGEXES):
            # The CLI is paused and asking a question. Save the live session.
            active_sessions[session_id] = {
                "child": child,
                "image_path": host_image_path,
                "timestamp": time.time()
            }
            return jsonify({
                "status": "needs_approval", 
                "session_id": session_id,
                "message": (child.before or "").strip() 
            })
            
        else:
            # Command finished cleanly without asking anything further
            output = (child.before or "").strip()
            # Clean up session as it's now finished
            active_sessions.pop(session_id, None)
            safe_close_child(child)
            
            # 🛡️ Sentinel: Clean up the image now that interaction is complete to prevent disk exhaustion DoS
            if host_image_path and os.path.exists(host_image_path):
                try:
                    os.remove(host_image_path)
                except Exception as e:
                    app.logger.warning("Failed to remove image on success: %s", e)

            return jsonify({"status": "success", "response": output})
            
    except pexpect.TIMEOUT:
        safe_close_child(child)
        active_sessions.pop(session_id, None)
        if host_image_path and os.path.exists(host_image_path):
            try:
                os.remove(host_image_path)
            except Exception:
                pass
        safe_close_child(child)
        return jsonify({"status": "error", "message": "CLI process timed out."}), 504
    except Exception as e:
        safe_close_child(child)
        app.logger.exception("Error during handle_cli_interaction: %s", e)
        safe_close_child(child)
        active_sessions.pop(session_id, None)
        if host_image_path and os.path.exists(host_image_path):
            try:
                os.remove(host_image_path)
            except Exception:
                pass
        safe_close_child(child)
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

@app.route('/ask', methods=['POST'])
def ask_gemini():
    data = request.json
    if not isinstance(data, dict):
        data = {}
    prompt = data.get("message", "")
    image_path = data.get("image_path", "")
    requested_model = data.get("model", "")
    
    if not prompt:
        return jsonify({"status": "error", "message": "No prompt provided."}), 400

    session_id = str(uuid.uuid4())
    
    # Resolve the specific image path on the host
    host_image_path = None
    if image_path:
        host_image_path = os.path.join(HOST_TEMP_DIR, os.path.basename(image_path))
        
    # Translate container-style temp paths in the prompt to host-level temp paths
    prompt_for_cli = prompt
    for container_prefix in ["/usr/src/app/temp/", "temp/"]:
        if container_prefix in prompt_for_cli:
            prompt_for_cli = prompt_for_cli.replace(container_prefix, os.path.join(HOST_TEMP_DIR, ""))

    # Determine which model to use based on environment variables or request param
    text_model = os.environ.get("AGY_TEXT_MODEL") or os.environ.get("GEMINI_TEXT_MODEL", "gemini-3.8-flash-low")
    image_model = os.environ.get("AGY_IMAGE_MODEL") or os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.8-flash-low")
    
    if requested_model:
        model = requested_model
    else:
        model = image_model if host_image_path else text_model

    # Spawn the Antigravity CLI command directly on the host OS
    # Use a list for arguments to prevent argument injection vulnerabilities
    spawn_env = os.environ.copy()
    if 'ALL_PROXY' not in spawn_env:
        spawn_env['ALL_PROXY'] = 'socks5://127.0.0.1:1080'
    child = pexpect.spawn(AGY_PATH, ['-p', prompt_for_cli, '--model', model, '--dangerously-skip-permissions'], env=spawn_env, encoding='utf-8', timeout=300)
    
    return handle_cli_interaction(child, session_id, host_image_path)

@app.route('/reply', methods=['POST'])
def reply_gemini():
    child = None
    data = request.json
    if not isinstance(data, dict):
        data = {}
    session_id = data.get("session_id")
    answer = data.get("answer") # Expecting 'y' or 'n'
    
    # 🛡️ Sentinel: Prevent Interactive CLI Injection by strictly allowlisting the input
    if answer not in ['y', 'n', 'yes', 'no', 'Y', 'N', 'Yes', 'No']:
        return jsonify({"status": "error", "message": "Invalid answer format."}), 400

    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Session expired or invalid. Try again."}), 404
        
    # Strict allowlist validation for pexpect interactive input to prevent CLI injection
    valid_answers = ['y', 'n', 'yes', 'no']
    if not isinstance(answer, str) or answer.lower().strip() not in valid_answers:
        return jsonify({"error": "Invalid answer format. Expected 'y' or 'n'."}), 400

    session_data = active_sessions[session_id]
    child = session_data["child"]
    host_image_path = session_data["image_path"]
    
    try:
        # Send the "y" or "n" keystroke to the waiting CLI
        child.sendline(answer)
        
        # Re-enter interaction loop
        return handle_cli_interaction(child, session_id, host_image_path)
        
    except Exception as e:
        safe_close_child(child)
        app.logger.exception("Error during reply_gemini: %s", e)
        if 'child' in locals():
            safe_close_child(child)
        active_sessions.pop(session_id, None)
        if 'host_image_path' in locals() and host_image_path and os.path.exists(host_image_path):
            try:
                os.remove(host_image_path)
            except Exception:
                pass
        safe_close_child(child)
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500


def resolve_host_image_path(image_path):
    if not image_path:
        return None
    target_path = os.path.join(HOST_TEMP_DIR, os.path.basename(image_path))
    if not os.path.isfile(target_path):
        raise ValueError("Image file was not found in the shared upload directory.")
    return target_path


def run_meal_analysis(data, prompt, host_image_path, telegram=False):
    request_id = str(uuid.uuid4())
    started_at = time.monotonic()
    try:
        provider_response = PROVIDER_ROUTER.generate(
            prompt,
            host_image_path,
            meal_analysis_schema(telegram),
            requested_provider=data.get("provider") or None,
            requested_model=data.get("model") or None,
        )
        result = validate_meal_analysis(provider_response.text, telegram=telegram)
        elapsed_ms = round((time.monotonic() - started_at) * 1000)
        app.logger.info(
            "Meal analysis completed request_id=%s provider=%s model=%s fallback=%s latency_ms=%s",
            request_id,
            provider_response.provider,
            provider_response.model,
            provider_response.fallback_used,
            elapsed_ms,
        )
        # Keep response for old NutriSnap images while exposing parsed result to new images.
        return jsonify({
            "status": "success",
            "response": json.dumps(result, separators=(",", ":")),
            "result": result,
            "meta": {
                "requestId": request_id,
                "provider": provider_response.provider,
                "model": provider_response.model,
                "fallbackUsed": provider_response.fallback_used,
                "latencyMs": elapsed_ms,
            },
        })
    except AnalysisContractError as exc:
        app.logger.error("Invalid provider output request_id=%s error=%s", request_id, exc)
        return jsonify({
            "status": "error",
            "code": "invalid_provider_output",
            "message": "The analysis provider returned an invalid meal result.",
            "requestId": request_id,
        }), 502
    except ProviderError as exc:
        app.logger.error(
            "Provider failure request_id=%s provider=%s code=%s error=%s",
            request_id,
            exc.provider,
            exc.code,
            exc,
        )
        status_code = 504 if exc.code == "timeout" else 503 if exc.code in {
            "configuration_error", "unknown_provider"
        } else 502
        return jsonify({
            "status": "error",
            "code": exc.code,
            "message": "The configured analysis provider is unavailable.",
            "requestId": request_id,
        }), status_code


@app.get('/health')
def health():
    return jsonify({"status": "ok"})


@app.get('/ready')
def ready():
    readiness = PROVIDER_ROUTER.readiness()
    return jsonify({
        "status": "ready" if readiness["ready"] else "not_ready",
        **readiness,
    }), 200 if readiness["ready"] else 503


@app.route('/health-matrix', methods=['POST'])
def health_matrix():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    meal_description = data.get('mealDescription', '')
    image_path = data.get('imagePath', '')
    if not meal_description and not image_path:
        return jsonify({'error': 'Payload Validation Failed: Either mealDescription or imagePath is required.'}), 400
    try:
        host_image_path = resolve_host_image_path(image_path)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    prompt = build_health_prompt(
        meal_description,
        data.get('mealTime', ''),
        data.get('weight', ''),
        host_image_path,
    )
    return run_meal_analysis(data, prompt, host_image_path)


@app.route('/health-matrix-telegram', methods=['POST'])
def health_matrix_telegram():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    meal_description = data.get('mealDescription', '')
    image_path = data.get('imagePath', '')
    if not meal_description and not image_path:
        return jsonify({'error': 'Payload Validation Failed: Either mealDescription or imagePath is required.'}), 400
    try:
        host_image_path = resolve_host_image_path(image_path)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    prompt = build_telegram_prompt(
        meal_description,
        data.get('telegramTimestamp', ''),
        data.get('userLocalTime', ''),
        data.get('weight', ''),
        host_image_path,
    )
    return run_meal_analysis(data, prompt, host_image_path, telegram=True)

if __name__ == '__main__':
    # Configuration via environment variables
    # Default to 172.17.0.1 for Docker gateway access, or 0.0.0.0 for general container use
    host = os.environ.get("FLASK_HOST", "172.17.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    app.run(host=host, port=port, debug=debug)
