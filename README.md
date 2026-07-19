# Stremio MovieBox

A lightweight and fast self hosted MovieBox addon for Stremio.

## Overview

This Stremio addon proxies and scrapes streams from MovieBox or ShowBox backend APIs and delivers them to your Stremio client. It is designed for simplicity, low overhead, and speed, making it suitable for self hosting in low resource environments.

## Features

* **Movies & Series:** Supports Stremio Cinemeta metadata.
* **Lightweight:** Minimal architecture with no unnecessary abstractions.
* **Fast Resolution:** Asynchronous scraping from backend providers.
* **Docker Ready:** Includes a multi stage Docker build for easy deployment.

## Project Structure

```text
server/
    app.py         # FastAPI application entrypoint
    routes.py      # Stremio API endpoints
    manifest.py    # Stremio Manifest configuration
moviebox/
    client.py      # HTTP Client handling proxying, signing, and tokens
    crypto.py      # Utilities for request signing and hashing
    parser.py      # Logic for parsing backend responses
    models.py      # Minimal data models for validation
streaming/
    provider.py    # Matches Cinemeta data to MovieBox entries
    metadata.py    # Fetches metadata from Cinemeta
config.py          # Centralized configuration
logger.py          # Standard structured logging
```

## Self Hosting with Docker

You can run the pre-built image from Docker Hub with a single command:

```bash
docker run -d --name stremio-moviebox -p 8000:8000 --restart unless-stopped mesamirh/stremio-moviebox:latest
```

Or, if you prefer using Docker Compose for local building:

```bash
docker compose up --detach --build
```

The addon will be available at `http://localhost:8000`. To install it, paste `http://localhost:8000/manifest.json` into your Stremio search bar.

## Environment Variables

You can customize the addon via Docker environment variables.

<table>
  <tr>
    <th>Variable</th>
    <th>Description</th>
    <th>Default</th>
  </tr>
  <tr>
    <td><code>PORT</code></td>
    <td>Port to run the FastAPI app</td>
    <td><code>8000</code></td>
  </tr>
  <tr>
    <td><code>HOST</code></td>
    <td>Host interface to bind to</td>
    <td><code>0.0.0.0</code></td>
  </tr>
  <tr>
    <td><code>REQUEST_TIMEOUT</code></td>
    <td>Timeout for backend requests</td>
    <td><code>15</code></td>
  </tr>
  <tr>
    <td><code>LOG_LEVEL</code></td>
    <td>Application logging level</td>
    <td><code>INFO</code></td>
  </tr>
  <tr>
    <td><code>MOVIEBOX_SECRET_KEY_DEFAULT</code></td>
    <td>Default signing key</td>
    <td>provided internally</td>
  </tr>
</table>

## Development

The project uses `uv` for dependency management.

1. Install `uv`: `pip install uv`
2. Sync dependencies: `uv sync`
3. Run the development server: `uv run fastapi dev server/app.py`
