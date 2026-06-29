# Claude Handoff — cyber_companion_saas

## Project
Local AI companion web app prototype with FastAPI backend + plain HTML/CSS/JS frontend.

## Root
`C:\Users\User\cyber_companion_saas`

## Current working URLs
- Frontend: `http://127.0.0.1:5500/`
- Backend health: `http://127.0.0.1:8000/health`
- Backend model list: `http://127.0.0.1:8000/models`

## How to run
Backend:
```bash
cd backend
source .venv/Scripts/activate
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Frontend:
```bash
cd frontend
python -m http.server 5500 --bind 127.0.0.1
```

## Tests
Frontend static feature tests:
```bash
cd frontend
node feature_tests.js
```

Backend API tests:
```bash
cd backend
.venv/Scripts/python api_tests.py
```

Python syntax:
```bash
cd backend
.venv/Scripts/python -m py_compile main.py ai_engine.py model_registry.py database.py monetization.py api_tests.py soul_manager.py persona_store.py
```

## Important current state
- Git repo initialized.
- Latest commits:
  - `eb25b0c fix: chat API supports missing reasoning_effort & fast_mode`
  - `0901c05 fix: restore working LINE app and models`
- Frontend is LINE-style chat UI.
- Backend exposes `/models`, `/model`, `/souls`, `/persona`, `/webhook/chat`.
- Persona / harem / SOUL.md-style custom character payload is partially implemented.
- Model runtime controls are represented in payload fields:
  - `thinking_enabled`
  - `fast_mode`
  - `reasoning_effort` (`low`, `medium`, `high`)
  - `persona_profile`

## Known recent bug fixed
Buttons looked dead because frontend sent runtime/persona fields that backend Pydantic schema did not accept, causing FastAPI `422`. Fixed by updating `ChatRequest`, `ChatResponse`, `generate_reply` signature, and tests.

## Next recommended tasks
1. Polish persona drawer UI so it visibly exposes custom name / birthday / personality / soul text editing.
2. Persist `/persona` to disk or SQLite instead of only in-memory `GLOBAL_PERSONA_OVERRIDE`.
3. Add explicit SOUL.md import/export: upload/paste markdown, parse metadata, save under `backend/souls/<id>.md`.
4. Improve button feedback: after quick action click, show success/failure chip and re-enable send button on all API error paths.
5. Add Playwright/browser interaction tests for the real UI, not only static Node string tests.

## Safety / maintenance note
Do not commit `.venv`, `__pycache__`, runtime DB snapshots, or generated backup folders in future packages. This handoff zip excludes those by default.
