import os
import pexpect
import uuid
from flask import Flask, request, jsonify

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
                "message": child.before.strip() 
            })
            
        else:
            # Command finished cleanly without asking anything further
            output = child.before.strip()
            # Clean up session as it's now finished
            if session_id in active_sessions:
                del active_sessions[session_id]
            
            # Clean up the image file on the host to save disk space
            if host_image_path and os.path.exists(host_image_path):
                try:
                    os.remove(host_image_path)
                except Exception as e:
                    print(f"Error removing file {host_image_path}: {e}")
                    
            return jsonify({"status": "success", "response": output})
            
    except pexpect.TIMEOUT:
        if session_id in active_sessions:
            del active_sessions[session_id]
        if host_image_path and os.path.exists(host_image_path):
            try:
                os.remove(host_image_path)
            except Exception as e:
                print(f"Error removing file {host_image_path}: {e}")
        return jsonify({"status": "error", "message": "CLI process timed out."}), 504
    except Exception as e:
        if session_id in active_sessions:
            del active_sessions[session_id]
        if host_image_path and os.path.exists(host_image_path):
            try:
                os.remove(host_image_path)
            except Exception as e:
                print(f"Error removing file {host_image_path}: {e}")
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
    for container_prefix in ["/usr/src/app/temp/", "temp/"]:
        if container_prefix in prompt_for_cli:
            prompt_for_cli = prompt_for_cli.replace(container_prefix, os.path.join(host_temp_dir, ""))

    # Spawn the Antigravity CLI command directly on the host OS
    child = pexpect.spawn(f'/root/.local/bin/agy -p "{prompt_for_cli}" --dangerously-skip-permissions', encoding='utf-8', timeout=300)
    
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
        if host_image_path and os.path.exists(host_image_path):
            try:
                os.remove(host_image_path)
            except Exception as e:
                print(f"Error removing file {host_image_path}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Configuration via environment variables
    # Default to 172.17.0.1 for Docker gateway access, or 0.0.0.0 for general container use
    host = os.environ.get("FLASK_HOST", "172.17.0.1")
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    app.run(host=host, port=port, debug=debug)
