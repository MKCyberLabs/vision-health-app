import os
import pexpect
import uuid
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

app = Flask(__name__)

# Dictionary to hold live CLI processes and metadata in RAM
active_sessions = {}

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
            
            # Clean up the image file on the host to save disk space
            pass
                    
            return jsonify({"status": "success", "response": output})
            
    except pexpect.TIMEOUT:
        if session_id in active_sessions:
            del active_sessions[session_id]
        pass
        return jsonify({"status": "error", "message": "CLI process timed out."}), 504
    except Exception as e:
        if session_id in active_sessions:
            del active_sessions[session_id]
        pass
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_gemini():
    data = request.json
    prompt = data.get("message", "")
    image_path = data.get("image_path", "")
    
    if not prompt:
        return jsonify({"status": "error", "message": "No prompt provided."}), 400

    session_id = str(uuid.uuid4())
    
    # Resolve the host's absolute temp directory path (parent of gemini-api folder)
    host_temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'temp'))
    
    # Resolve the specific image path on the host
    host_image_path = None
    if image_path:
        host_image_path = os.path.join(host_temp_dir, os.path.basename(image_path))
        
    # Translate container-style temp paths in the prompt to host-level temp paths
    prompt_for_cli = prompt
    if "/usr/src/app/temp/" in prompt_for_cli:
        prompt_for_cli = prompt_for_cli.replace("/usr/src/app/temp/", os.path.join(host_temp_dir, ""))
    elif "temp/" in prompt_for_cli:
        prompt_for_cli = prompt_for_cli.replace("temp/", os.path.join(host_temp_dir, ""))

    # Resolve the agy executable path
    agy_path = "/root/.local/bin/agy"
    if not os.path.exists(agy_path):
        import shutil
        agy_path = shutil.which("agy") or shutil.which("agy.exe") or "agy"

    # Determine which model to use based on environment variables
    text_model = os.environ.get("GEMINI_TEXT_MODEL", "gpt-4o")
    image_model = os.environ.get("GEMINI_IMAGE_MODEL", "claude-3-5-sonnet-20240620")
    model = image_model if host_image_path else text_model

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
    session_id = data.get("session_id")
    answer = data.get("answer") # Expecting 'y' or 'n'
    
    if not session_id or session_id not in active_sessions:
        return jsonify({"error": "Session expired or invalid. Try again."}), 404
        
    session_data = active_sessions[session_id]
    child = session_data["child"]
    host_image_path = session_data["image_path"]
    
    try:
        # Send the "y" or "n" keystroke to the waiting CLI
        child.sendline(answer)
        
        # Re-enter interaction loop
        return handle_cli_interaction(child, session_id, host_image_path)
        
    except Exception as e:
        if session_id in active_sessions:
            del active_sessions[session_id]
        pass
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/health-matrix', methods=['POST'])
def health_matrix():
    data = request.json
    meal_description = data.get('mealDescription', '')
    image_path = data.get('imagePath', '')
    meal_time = data.get('mealTime', '')
    weight = data.get('weight', '')
    
    if not meal_description and not image_path:
        return jsonify({'error': 'Payload Validation Failed: Either mealDescription or imagePath is required.'}), 400

    session_id = str(uuid.uuid4())
    host_temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'temp'))
    
    host_image_path = None
    if image_path:
        host_image_path = os.path.join(host_temp_dir, os.path.basename(image_path))

    prompt = f"Analyze this meal eaten at {meal_time}. Description: {meal_description}. "
    if weight:
        prompt += f"CRITICAL: The user has explicitly specified the weight of the food is {weight} grams. You MUST calculate all nutritional values based strictly on this {weight}g weight! Do not use default portion sizes. "
    if host_image_path:
        prompt += f"Image: {host_image_path} "
        
    prompt += """Return ONLY a valid JSON object matching exactly this schema (do not wrap in markdown tags).
CRITICAL: You MUST break down the meal into individual components in the "foodItems" array. For EVERY item in the array, you MUST provide its individual nutritional breakdown using ALL the exact keys below: "name", "grams", "calories", "protein", "carbs", "fat", "fiber", "saturatedFat", and "sugar". Do NOT use "weight", use "grams".
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
      "sugar": number
    }
  ]
}"""

    agy_path = "/root/.local/bin/agy"
    if not os.path.exists(agy_path):
        import shutil
        agy_path = shutil.which("agy") or shutil.which("agy.exe") or "agy"

    # Determine which model to use based on environment variables
    text_model = os.environ.get("GEMINI_TEXT_MODEL", "gpt-4o")
    image_model = os.environ.get("GEMINI_IMAGE_MODEL", "claude-3-5-sonnet-20240620")
    model = image_model if host_image_path else text_model
    
    spawn_env = os.environ.copy()
    if 'ALL_PROXY' not in spawn_env:
        spawn_env['ALL_PROXY'] = 'socks5://127.0.0.1:1080'
    child = pexpect.spawn(agy_path, ['-p', prompt, '--model', model, '--dangerously-skip-permissions'], env=spawn_env, encoding='utf-8', timeout=300)
    
    return handle_cli_interaction(child, session_id, host_image_path)

if __name__ == '__main__':
    # Configuration via environment variables
    # Default to 172.17.0.1 for Docker gateway access, or 0.0.0.0 for general container use
    host = os.environ.get("FLASK_HOST", "172.17.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    app.run(host=host, port=port, debug=debug)
