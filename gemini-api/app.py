import os
import pexpect
import uuid
from flask import Flask, request, jsonify
import shutil
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

app = Flask(__name__)

# ⚡ Bolt Optimization: Cache paths at module level to avoid repeated os.stat/I/O per request
HOST_TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'temp'))
AGY_PATH = "/root/.local/bin/agy"
if not os.path.exists(AGY_PATH):
    AGY_PATH = shutil.which("agy") or shutil.which("agy.exe") or "agy"

from werkzeug.exceptions import HTTPException

# Dictionary to hold live CLI processes and metadata in RAM
active_sessions = {}

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
                "image_path": host_image_path
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
            if session_id in active_sessions:
                del active_sessions[session_id]
                child.close(force=True)
            
            # Image remains on the host for the frontend to serve

            return jsonify({"status": "success", "response": output})
            
    except pexpect.TIMEOUT:
        if child and child.isalive():
            child.close(force=True)
        if session_id in active_sessions:
            del active_sessions[session_id]
        if host_image_path and os.path.exists(host_image_path):
            try:
                os.remove(host_image_path)
            except Exception:
                pass
        child.close(force=True)
        return jsonify({"status": "error", "message": "CLI process timed out."}), 504
    except Exception as e:
        app.logger.exception("Error during handle_cli_interaction: %s", e)
        if child and child.isalive():
            child.close(force=True)
        if session_id in active_sessions:
            del active_sessions[session_id]
        if host_image_path and os.path.exists(host_image_path):
            try:
                os.remove(host_image_path)
            except Exception:
                pass
        if 'child' in locals() and child:
            child.close(force=True)
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
    text_model = os.environ.get("GEMINI_TEXT_MODEL", "gpt-4o")
    image_model = os.environ.get("GEMINI_IMAGE_MODEL", "claude-3-5-sonnet-20240620")
    
    if requested_model:
        model = requested_model
    else:
        model = image_model if host_image_path else text_model

    # Determine the path to agy (either installed or the local mock for tests)
    agy_path = os.environ.get("AGY_PATH", "/root/.local/bin/agy")
    if not os.path.exists(agy_path):
        # Fallback to local mock if absolute path not found
        agy_path = os.path.join(os.path.dirname(__file__), 'bin', 'agy')

    # Spawn the Antigravity CLI command directly on the host OS
    # Use a list for arguments to prevent argument injection vulnerabilities
    spawn_env = os.environ.copy()
    if 'ALL_PROXY' not in spawn_env:
        spawn_env['ALL_PROXY'] = 'socks5://127.0.0.1:1080'
    child = pexpect.spawn(agy_path, ['-p', prompt_for_cli, '--model', model, '--dangerously-skip-permissions'], env=spawn_env, encoding='utf-8', timeout=300)
    
    return handle_cli_interaction(child, session_id, host_image_path)

@app.route('/reply', methods=['POST'])
def reply_gemini():
    data = request.json
    if not isinstance(data, dict):
        data = {}
    session_id = data.get("session_id")
    answer = data.get("answer") # Expecting 'y' or 'n'
    
    if not isinstance(answer, str) or answer.lower() not in ['y', 'n']:
        return jsonify({"status": "error", "message": "Invalid answer format. Must be 'y' or 'n'."}), 400

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
        app.logger.exception("Error during reply_gemini: %s", e)
        if 'child' in locals() and child and child.isalive():
            child.close(force=True)
        if session_id in active_sessions:
            del active_sessions[session_id]
        if host_image_path and os.path.exists(host_image_path):
            try:
                os.remove(host_image_path)
            except Exception:
                pass
        if 'child' in locals() and child:
            child.close(force=True)
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500


@app.route('/health-matrix', methods=['POST'])
def health_matrix():
    data = request.json
    if not isinstance(data, dict):
        data = {}
    meal_description = data.get('mealDescription', '')
    image_path = data.get('imagePath', '')
    meal_time = data.get('mealTime', '')
    weight = data.get('weight', '')
    requested_model = data.get('model', '')
    
    if not meal_description and not image_path:
        return jsonify({'error': 'Payload Validation Failed: Either mealDescription or imagePath is required.'}), 400

    session_id = str(uuid.uuid4())
    
    host_image_path = None
    if image_path:
        host_image_path = os.path.join(HOST_TEMP_DIR, os.path.basename(image_path))

    prompt = f"Analyze this meal eaten at {meal_time}. Description: {meal_description}. "
    if weight:
        prompt += f"CRITICAL: The user has explicitly specified the weight of the food is {weight} grams. You MUST calculate all nutritional values based strictly on this {weight}g weight! Do not use default portion sizes. "
    if host_image_path:
        prompt += f"Image: {host_image_path} "
        prompt += "CRITICAL: First, verify if the image actually contains identifiable food or drinks. If the image does NOT contain food (e.g. it is a car, a face, a room, etc.), you MUST return exactly this JSON: {\"error\": \"NOT_FOOD\", \"aiNote\": \"Explanation of why this was rejected\"} and ignore the rest of the schema. NOTE: Exotic fruits (like dragon fruit), raw vegetables, snacks, salads, yogurt, and generally ANY ingredient or item commonly edible by humans ARE absolutely food and MUST be processed! If you are ever unsure, ALWAYS assume the image contains food. ONLY reject the image if you are 100% absolutely certain it is NOT food. "
        
    prompt += """Return ONLY a valid JSON object matching exactly this schema (do not wrap in markdown tags).
CRITICAL: The Description provided above is the User's Input Note. You MUST output your own insights/feedback exclusively into the "healthInsight" field so they do not conflict.
CRITICAL: You MUST break down the meal into individual components in the "foodItems" array. For EVERY item in the array, you MUST provide its individual nutritional breakdown using ALL the exact keys below: "name", "grams", "calories", "protein", "carbs", "fat", "fiber", "saturatedFat", and "sugar". Do NOT use "weight", use "grams".
CRITICAL: For EVERY item in the array, you MUST assign a health "rating" integer from 1 to 5 based strictly on purely nutritional quality (1 = ultra-processed/junk, 5 = whole foods, nutrient-dense, balanced macros).
CRITICAL: If an image is provided without a description, you MUST do your absolute best to visually identify the food and estimate the portion size. Do NOT ask the user for more information. Do NOT return text. You MUST return ONLY the JSON matrix based on your best visual estimation.
{
  "calories": number,
  "protein": number,
  "carbs": number,
  "fat": number,
  "fiber": number,
  "saturatedFat": number,
  "sugar": number,
  "healthInsight": "string description",
  "foodItems": [
    {
      "name": "string name",
      "grams": number,
      "calories": number,
      "protein": number,
      "carbs": number,
      "fat": number,
      "fiber": number,
      "saturatedFat": number,
      "sugar": number,
      "rating": number
    }
  ]
}"""

    # Determine which model to use based on environment variables or request param
    text_model = os.environ.get("GEMINI_TEXT_MODEL", "gpt-4o")
    image_model = os.environ.get("GEMINI_IMAGE_MODEL", "claude-3-5-sonnet-20240620")
    
    if requested_model:
        model = requested_model
    else:
        model = image_model if host_image_path else text_model
    
    spawn_env = os.environ.copy()
    if 'ALL_PROXY' not in spawn_env:
        spawn_env['ALL_PROXY'] = 'socks5://127.0.0.1:1080'
    child = pexpect.spawn(AGY_PATH, ['-p', prompt, '--model', model, '--dangerously-skip-permissions'], env=spawn_env, encoding='utf-8', timeout=300)
    
    return handle_cli_interaction(child, session_id, host_image_path)

@app.route('/health-matrix-telegram', methods=['POST'])
def health_matrix_telegram():
    data = request.json
    if not isinstance(data, dict):
        data = {}
    meal_description = data.get('mealDescription', '')
    image_path = data.get('imagePath', '')
    telegram_timestamp = data.get('telegramTimestamp', '')
    user_local_time = data.get('userLocalTime', '')
    weight = data.get('weight', '')
    requested_model = data.get('model', '')
    
    if not meal_description and not image_path:
        return jsonify({'error': 'Payload Validation Failed: Either mealDescription or imagePath is required.'}), 400

    session_id = str(uuid.uuid4())
    
    host_image_path = None
    if image_path:
        host_image_path = os.path.join(HOST_TEMP_DIR, os.path.basename(image_path))

    prompt = f"The user sent this message exactly at the following anchor time: {telegram_timestamp} (User's Local Time: {user_local_time}). "
    prompt += f"Based on this description: '{meal_description}', calculate the actual ISO 8601 UTC time the meal was consumed. "
    prompt += "If no specific time is implied (e.g. they just said 'my meal' or didn't provide a description), assume it was consumed exactly at the anchor time. "
    prompt += "Based on the calculated meal time, or the context of the description, determine the appropriate category ('Breakfast', 'Lunch', 'Dinner', 'Snacks'). Make sure to classify according to typical local time meal hours (e.g. 1:30 PM is Lunch). "
    
    if weight:
        prompt += f"CRITICAL: The user explicitly specified the weight is {weight} grams. Calculate nutritional values based strictly on {weight}g. "
    if host_image_path:
        prompt += f"Image: {host_image_path} "
        prompt += "CRITICAL: First, verify if the image actually contains identifiable food or drinks. If the image does NOT contain food (e.g. it is a car, a face, a room, etc.), you MUST return exactly this JSON: {\"error\": \"NOT_FOOD\", \"aiNote\": \"Explanation of why this was rejected\"} and ignore the rest of the schema. NOTE: Exotic fruits (like dragon fruit), raw vegetables, snacks, salads, yogurt, and generally ANY ingredient or item commonly edible by humans ARE absolutely food and MUST be processed! If you are ever unsure, ALWAYS assume the image contains food. ONLY reject the image if you are 100% absolutely certain it is NOT food. "
        
    prompt += """Return ONLY a valid JSON object matching exactly this schema (do not wrap in markdown tags).
CRITICAL: The Description provided above is the User's Input Note. You MUST output your own insights/feedback exclusively into the "healthInsight" field so they do not conflict.
CRITICAL: You MUST break down the meal into individual components in the "foodItems" array.
CRITICAL: For EVERY item in the array, you MUST assign a health "rating" integer from 1 to 5 based strictly on purely nutritional quality (1 = ultra-processed/junk, 5 = whole foods, nutrient-dense, balanced macros).
CRITICAL: Include the exact "calculatedTime" (ISO 8601 UTC) and "calculatedCategory" string in the root.
{
  "calculatedTime": "string ISO 8601 UTC time",
  "calculatedCategory": "string",
  "calories": number,
  "protein": number,
  "carbs": number,
  "fat": number,
  "fiber": number,
  "saturatedFat": number,
  "sugar": number,
  "healthInsight": "string description",
  "foodItems": [
    {
      "name": "string name",
      "grams": number,
      "calories": number,
      "protein": number,
      "carbs": number,
      "fat": number,
      "fiber": number,
      "saturatedFat": number,
      "sugar": number,
      "rating": number
    }
  ]
}"""

    text_model = os.environ.get("GEMINI_TEXT_MODEL", "gpt-4o")
    image_model = os.environ.get("GEMINI_IMAGE_MODEL", "claude-3-5-sonnet-20240620")
    model = requested_model if requested_model else (image_model if host_image_path else text_model)
    
    spawn_env = os.environ.copy()
    if 'ALL_PROXY' not in spawn_env:
        spawn_env['ALL_PROXY'] = 'socks5://127.0.0.1:1080'
    child = pexpect.spawn(AGY_PATH, ['-p', prompt, '--model', model, '--dangerously-skip-permissions'], env=spawn_env, encoding='utf-8', timeout=300)
    
    return handle_cli_interaction(child, session_id, host_image_path)

if __name__ == '__main__':
    # Configuration via environment variables
    # Default to 172.17.0.1 for Docker gateway access, or 0.0.0.0 for general container use
    host = os.environ.get("FLASK_HOST", "172.17.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    app.run(host=host, port=port, debug=debug)
