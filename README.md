<!-- WARNING: This project is under active development. Expect breaking changes. -->
<!-- Remove or replace this flag when the project reaches production readiness. -->

![](https://img.shields.io/badge/status-under%20development-orange)

# Foundry Playground (Under development)

⚠️ **Under Development** — This project is a community-driven developer playground for Microsoft Foundry Local. The codebase is actively worked on, features may be incomplete, and behavior may change. If you're using this repository, expect occasional breaking changes and frequent updates.

Table of contents
- Overview
- Quickstart
- Configuration
- Backend (Flask)
- Frontend (React/Vite)
- Foundry CLI & REST notes
- API Endpoints (Detailed)
- Database & Migrations
- Common Troubleshooting & Tips
- Contributing & Next Steps

---

## Overview

Foundry Playground provides a developer-friendly API and GUI for interacting with Microsoft Foundry Local models. It aims to give a familiar OpenAI-like interface while building tooling for local development, model management, training, RAG, and more.

This README covers a comprehensive development workflow, how to run the project locally, and troubleshooting tips based on current known issues.

---

## Quickstart (Windows)

1. Ensure prerequisites installed:
   - Python 3.8+
   - Node.js 16+
   - Microsoft Foundry Local & Foundry CLI (foundry)

2. Start Foundry Local (if you need it locally):

```powershell
foundry service start
```

3. Backend (local dev):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Create DB tables (SQLite default)
python -c "from app import app, db; app.app_context().push(); db.create_all()"
python app.py
```

Default backend server: http://localhost:5000

4. Frontend (local dev):

```powershell
cd frontend
npm install
npm run dev
```

Default frontend URL: http://localhost:5173

---

## Installing Foundry Local (detailed)

Foundry Local is a separate Microsoft product and is required to run models and interact with the local runtime. The exact installation and license process may vary over time and across Microsoft channels. Always prefer the official Microsoft Learn documentation when installing Foundry Local.

General steps (platform-agnostic):
1. Download Foundry Local from Microsoft (or the channel provided by your organization). It may come as an installer package, a ZIP/tarball, or a container image.
2. Install the Foundry CLI (commonly named `foundry`) or ensure the installed package adds a `foundry` binary to your PATH.
3. Start the Foundry runtime/service using the `foundry` CLI:

```powershell
# Start the Foundry local service
foundry service start

# Optional health check
foundry service status
foundry --version
```

Windows notes
- You may get an MSI installer, a ZIP, or an explicit installer script.
- After installation, ensure `foundry` is listed in your system `Path` and that you can run `foundry --version` from PowerShell.

Linux notes
- If a Linux installer or tarball is provided, unpack and run the vendor-provided install script. If a service is provided, enable and start the service via systemd as recommended by the vendor.

macOS notes
- Use the vendor-provided package or script; ensure the `foundry` CLI is in your PATH.

Important: some Foundry Local installations require authentication or a license key — if that is the case for your installation, follow the official Microsoft or enterprise documentation to register the runtime.

Verification commands (when installation completes):

```powershell
foundry --version
foundry service status
foundry model list
foundry model list --available --json
```

If these commands work and `foundry model list` produces a catalog or the CLI can list models, you're ready to continue with Foundry Playground.

---

---

## Configuration & Environment Variables

Create or update `backend/.env` (or a system environment variable) for the backend config.

Important environment variables:
- `FOUNDRY_BASE_URL` — Foundry REST base URL, default `http://127.0.0.1:56831`
- `FOUNDRY_API_KEY` — API key for Foundry REST (optional)
- `DATABASE_URL` — SQLAlchemy-compatible DB URL, default `sqlite:///foundry_playground.db`
- `SECRET_KEY` — Flask secret key

Example `.env`:

```
FOUNDRY_BASE_URL=http://127.0.0.1:56831
FOUNDRY_API_KEY=
DATABASE_URL=sqlite:///foundry_playground.db
SECRET_KEY=dev-secret-key-change-in-production
```

For development on Windows, prefer using PowerShell and the `.venv` activation commands above.

---

## Backend (Flask) Overview

Key files/folders
- `backend/app.py` — Flask app and blueprint registrations.
- `backend/api/routes/` — API routes, including `models`, `pull`, `stop`, `chat`, `generate`, `train`, etc.
- `backend/models.py` — SQLAlchemy models for conversations, messages, and AIModel.

Important behavior and patterns:
- Model listing uses `foundry` CLI for robust listing even when the Foundry REST server is unreachable.
- Starting a model (`pull/run`) uses the foundry CLI and includes fallback tests for different ID formats and heuristics.
- Endpoints gracefully fall back to DB state where appropriate (e.g., for running models when REST is unreachable).
- CLI output decoding uses UTF-8 with `errors='replace'` to avoid UnicodeDecodeErrors.

Slash routes (registered under `/api`):
- `/api/models` — list downloaded/cached models.
- `/api/models/pull` — list models available to pull.
- `/api/models/pull/<id>` — start/run/pull a model via foundry CLI.
- `/api/models/all` — list all models from the CLI catalog.
- `/api/models/running` — query running models (uses Foundry REST if available, fallback to DB).
- `/api/models/stop/<id>` — stop a running model using Foundry REST (or DB fallback).
- `/api/chat` (and `/api/chat/<conversation_id>`) — chat endpoint; uses Foundry Local REST for chat completions if available.

Blueprints and modularization
- The backend uses Flask blueprints for modular routes (models, chat, generate, RAG, etc). Register new routes under `backend/api/routes` and add blueprints in `backend/app.py`.

---

## Frontend Overview (React / Vite)

Structure
- `frontend/src/` — React source code.
- `frontend/src/api/api.jsx` — central HTTP client wrapper for calling the backend API.
- `frontend/src/containers/MainApp.jsx` — core application logic, model lists, and chat components.
- `frontend/src/components/` — UI components: RightSidebar, LeftSidebar, ChatArea, InputArea.

Developer tips
- Use `VITE_API_BASE_URL` to point to the backend dev server if you're running it on a different port.
- The frontend uses normalized `id` strings for display (dashes instead of colon separators) but sends `rawId` to the backend when interacting with Foundry.
- The `MainApp` container fetches `downloaded`, `available`, and `all` model lists and also `running` models to indicate current model status.

Running locally (dev mode)

```powershell
cd frontend
npm run dev
```

---

## Foundry CLI vs REST: Key Notes

- The `foundry` CLI is often used for listing and starting models; the CLI can work even if the REST service is down.
- The backend uses the CLI for listing (`foundry model list`) and uses heuristics to parse output from different Foundry CLI versions.
- Some endpoints prefer Foundry REST (`/models/running`, `/models/stop`, chat/compl API); when REST is unreachable, the backend will fall back to DB or return a 503 with a detailed message.
- If you run into `ConnectionRefused` or 503s from the backend, confirm whether Foundry REST or CLI is the source of the problem:
  - CLI: `foundry model list`
  - REST: `curl http://127.0.0.1:56831/health` (or use the CLI `foundry service status` depending on your version)

Common CLI pitfalls
- Unicode output — we use `encoding='utf-8'` with `errors='replace'` to avoid decode exceptions.
- Different CLI versions or output formats may require fallback parsing; our backend includes fallback parsing heuristics.

---

## API Endpoints (Detailed)

Base: `http://localhost:5000/api`

### GET /models
- Lists models currently available on disk (cache / downloaded models). This uses the `~/.foundry/cache/models/Microsoft/` directory.

### GET /models/pull
- Lists models that are available to pull (from the catalog). This uses the CLI `foundry model list --available` and parses JSON or tabular output.

### GET /models/all
- Lists all available models from the Foundry catalog (non-filtered). Falls back to a table parse if the CLI version lacks JSON support.

### POST /models/pull/<model_id>
- Runs `foundry model run <model_id>` using the CLI. The backend attempts a few common id normalization heuristics if a run fails.
- Returns `success: true` on success and includes `tried_ids` and `stdout/stderr` on failure.

### POST /models/stop/<model_id>
- Calls Foundry REST `/models/stop` to stop a model. If REST is not reachable, the DB `AIModel` record is marked inactive and a 200 + warning response is returned.

### GET /models/running
- Lists running models. Attempts to call Foundry REST `/models/running` and falls back to DB-based `is_active` models on errors.

### Chat endpoints
- `/api/chat` and `/api/chat/<conversation_id>` — send a chat message and receive completion. If Foundry REST is unreachable, the endpoint may return an error (503) depending on server availability.

### Conversations
- Basic CRUD for conversations: `/api/conversations`, `/api/conversations/<id>`, and messages via `/api/conversations/<id>/messages`.

---

## Database & Migrations

DB: SQLAlchemy with default SQLite database `foundry_playground.db`.

To create DB and tables:

```powershell
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

To run migrations (Flask-Migrate is included):

```powershell
flask db init   # only once
flask db migrate
flask db upgrade
```

Note: Check `backend/models.py` for the schema; DB fallback (is_active flags) is used in certain endpoints when Foundry REST is unreachable.

---

## Common Troubleshooting & Tips

- App reloads due to file changes: The dev server automatically reloads when backend files change. You may see a restart if `pull.py` is edited. If you hit spurious restarts because of the corrupted `pull.py`, consider removing it or renaming.
- `UnicodeDecodeError` when invoking the `foundry` CLI — resolved by using `encoding='utf-8', errors='replace'` in subprocess calls; if you still see these, ensure your terminal uses UTF-8 or set code page accordingly.
- `Connection refused` to Foundry REST: Confirm Foundry server running using `foundry service status` or `curl <foundry_url>/health`.
- CLI vs REST mismatch: Some functionality requires Foundry REST (chat completions, stop), while others (listing models, starting via CLI) can be managed via the CLI. The backend uses a combination and provides fallbacks.

Debugging tips
- Check backend logs in the terminal where `python app.py` runs; we log all `foundry` CLI stdout/stderr snippets for debugging.
- The `pull_model` route returns `tried_ids` and raw CLI `stderr`/`stdout` when a run fails. Use these details for faster diagnosis.

Foundry-specific troubleshooting
- `foundry` command not found: Ensure you added the `foundry` binary to your PATH and you can run `foundry --version` globally.
- `foundry service status` or `/health` failing: Ensure the service is running and accessible on `FOUNDRY_BASE_URL`. Use `foundry service start` to start it.
- Permission errors when reading `~/.foundry/cache/models/`: Ensure the user running the backend has permissions to read the cache directory.
- Unicode or CLI parsing issues: If you see `UnicodeDecodeError` or malformed output, the backend sets `errors='replace'` for the CLI calls; ensure your terminal encoding is UTF-8.
- Model IDs and normalization: The CLI may report model IDs using `:` delimiter (e.g., `...:cpu:4`) while local directories use `-` (e.g., `...-cpu-4`) — the backend normalizes IDs but occasionally fallback heuristics are needed.


---

## Contributing

We welcome contributors!

Guidelines:
- Fork repository and open a PR
- Write tests where appropriate
- Follow Python & JS formatting conventions

Local dev tests:
- Run backend locally and manually verify endpoints with `curl` or the frontend.
- Ensure linting checks (optional) and tests (if added) pass.

---

## Next Steps & TODOs

- Remove any corrupted legacy route files (e.g., `backend/api/routes/model/pull.py`) and use the new `pull_clean.py` or rename `pull_clean.py` to `pull.py` for consistency.
- Add a `status` endpoint for long-running pulls (returning live progress)
- Add a `validate` endpoint to perform both CLI & REST health checks
- Build a background worker (e.g., Celery/Redis) to manage long model downloads and provide progress updates to the UI
- Add unit & integration tests for endpoints

---

If anything in the README is unclear or you see outdated info, please open an issue or PR. Thank you for using Foundry Playground — remember it is still under active development!

---

Made with ❤️ — Community contributors
# Foundry Playground

A community-driven API and GUI layer on top of Microsoft Foundry Local, making it easier for developers to use Foundry's local AI models with familiar OpenAI/Claude-style APIs.

## 🚀 Features

- **Simple API Endpoints**: Text generation, embeddings, chat, and more
- **Model Management**: List and interact with any model supported by Foundry Local
- **Custom Training**: Upload your own data for fine-tuning workflows
- **RAG Support**: Build retrieval-augmented generation systems locally
- **Web GUI**: User-friendly interface for model interaction without terminal usage
- **Open Source**: Community-driven development on GitHub

## 📋 Requirements

- Python 3.8+
- Node.js 16+
- Microsoft Foundry Local installed and running

## 🛠️ Installation & Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **Microsoft Foundry Local** installed

### 🚀 Quick Start (Windows)

1. **Start Foundry Local:**

```bash
foundry service start
```

You should see: `🟢 Service is already running on http://127.0.0.1:56831/`

2. **Start Foundry Playground:**

```bash
# From the project root directory
start.bat
```

3. **Open your browser:**

- Frontend: http://localhost:5173
- Backend API: http://localhost:5000

### Manual Setup

#### Backend Setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt

# Initialize the database (creates SQLite tables)
python -c "from app import app, db; app.app_context().push(); db.create_all()"

python app.py
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### ⚙️ Configuration

The app is pre-configured for Foundry Local on `http://127.0.0.1:56831/`. To customize:

Edit `backend/.env`:

```env
FOUNDRY_BASE_URL=http://127.0.0.1:56831
DATABASE_URL=sqlite:///foundry_playground.db
```

## 📖 API Documentation

### Base URL

```
http://localhost:5000/api
```

### Endpoints

#### GET /models

List all available models in Foundry Local.

**Response:**

```json
{
  "success": true,
  "models": [
    {
      "id": "model-1",
      "name": "GPT-2 Small",
      "description": "Small GPT-2 model"
    }
  ],
  "count": 1
}
```

#### POST /generate

Generate text using a Foundry Local model.

**Request:**

```json
{
  "model": "gpt2-small",
  "prompt": "Hello, how are you?",
  "max_tokens": 100,
  "temperature": 0.7
}
```

**Response:**

```json
{
  "success": true,
  "generated_text": "Hello, how are you? I'm doing well, thank you for asking!",
  "model": "gpt2-small",
  "usage": {
    "tokens": 15
  }
}
```

#### POST /embeddings

Generate embeddings for text.

**Request:**

```json
{
  "model": "embedding-model",
  "input": "Your text here"
}
```

#### POST /upload

Upload data files for training or RAG.

**Request:** Form data with `file` field.

**Response:**

```json
{
  "success": true,
  "file_id": "uuid-here",
  "filename": "data.txt",
  "file_path": "/path/to/file"
}
```

#### POST /train

Start a training/fine-tuning job.

**Request:**

```json
{
  "model": "base-model",
  "training_data": "file_id_or_data",
  "type": "fine-tune",
  "parameters": {}
}
```

#### POST /rag

Create a RAG system with uploaded documents.

**Request:**

```json
{
  "documents": ["file_id_1", "file_id_2"],
  "model": "embedding-model",
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

## 🔧 Configuration

### Environment Variables

- `FOUNDRY_BASE_URL`: URL where Foundry Local is running (default: http://localhost:8080)
- `FOUNDRY_API_KEY`: API key for Foundry Local authentication (optional)

### Supported File Types for Upload

- Text files (.txt)
- PDFs (.pdf)
- JSON files (.json)
- CSV files (.csv)
- Markdown files (.md)

## 🤝 Contributing

We welcome contributions! This is a community-driven project.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test them
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

**This project is a MenteE initiative and does not belong to Microsoft.** It is an independent, community-driven effort to create developer-friendly tooling around Microsoft's Foundry Local AI runtime. Microsoft is not affiliated with, nor does it endorse, this project.

## 🙏 Acknowledgments

- Microsoft for creating Foundry Local
- The open-source AI community
- All contributors to this project

## 📞 Support

- Create an issue on GitHub
- Join our community discussions
- Check the documentation for common solutions

---

Made with ❤️ by the community
