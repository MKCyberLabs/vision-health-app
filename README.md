# Vision Health App (Frontend)

The **AI Health Matrix** frontend is a Node.js web application that provides a user interface for analyzing food images and obtaining health/nutritional breakdowns. It proxies requests to the Python Gemini API backend.

## Architecture
- **Frontend/API:** Node.js, Express, TailwindCSS
- **Backend API:** Python, Flask (runs natively on port 5000)
- **Deployment:** Docker & Docker Compose

## Setup & Running Locally

> **Note on Podman/Docker Daemon:** If you get an error like `Cannot connect to the Docker daemon`, your container service might be down (e.g., after a reboot). You can restart it by running:
> ```bash
> sudo systemctl start podman.socket # Or 'sudo systemctl start docker' depending on your system
> ```

Because the production application relies on a Traefik reverse proxy network (`proxy`), running this locally requires you to spin up the local replica first.

### 1. Boot the Traefik Proxy Network
This step sets up the required Docker network and Traefik dashboard so the frontend container can successfully start without "network not found" errors.
```bash
docker-compose -f docker-compose.traefik.yml up -d
```
*(You can view the Traefik dashboard at `http://localhost:8080`)*

### 2. Boot the Frontend Application
Once the proxy network is up, start the main Node.js application:
```bash
docker-compose up -d
```
The frontend is now running and accessible at **[http://localhost:3000](http://localhost:3000)**.

### 3. Boot the Native Python Backend
The frontend relies on the backend API running on your host machine to process images. 
By default, for security, the API binds strictly to `172.17.0.1` (the internal Docker bridge) so it is only accessible to your containers (via `host.docker.internal`) and not exposed to the public internet.

Navigate to the `gemini-api` directory and start it natively:
```bash
cd gemini-api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Environment Variables
If running the frontend natively (without Docker), you can specify the backend URL:
- `GEMINI_API_URL`: The URL of the Python backend (defaults to `http://localhost:5000` or `http://host.docker.internal:5000` inside Docker).
- `PORT`: The port the Node server listens on (defaults to `3000`).

## Testing

To easily verify that the frontend and backend are communicating properly without needing to use the browser interface, you can run a quick `curl` test from your terminal.

This command simulates an image upload by sending your local `package.json` file to the Node frontend, which proxies it to the Python backend:

```bash
curl -X POST -F "image=@package.json" http://localhost:3000/analyze
```

If everything is working properly, you will receive a successful JSON response with a "health matrix" (where the AI playfully points out that `package.json` is not edible!).
