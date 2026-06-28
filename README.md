# vision-health-app

This is the Docker Compose deployment for vision-health-app.

## Location
- Directory: `/opt/docker/containers/vision-health-app`

## Management
To start the container:
```bash
cd /opt/docker/containers/vision-health-app
docker compose up -d
```

To stop the container:
```bash
cd /opt/docker/containers/vision-health-app
docker compose down
```

## Details
Found docker-compose.yml:
```yaml
version: '3.8'

services:
  vision-app:
    build: .
    container_name: vision-health
    restart: unless-stopped
    ports:
      - "3000:3000"

    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.vision.rule=Host(`vision.mkcyberlabs.in`)"
      - "traefik.http.routers.vision.entrypoints=websecure"
      - "traefik.http.routers.vision.tls.certresolver=letsencrypt"
      - "traefik.http.services.vision.loadbalancer.server.port=3000"

    env_file:
      - .env
    environmen
...
```
