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
- Git repo initialized (commits from before this session — re-commit the changes below yourself).
- Frontend is LINE-style chat UI.
- Backend exposes `/models`, `/model`, `/souls`, `/souls/{id}`, `/souls/import`, `/persona`, `/webhook/chat`.
- Persona / harem / SOUL.md-style custom character payload is implemented and persisted to disk (see "Changes in this session").

## Changes in this session (2026-06-29)

**Default character decoupled from a real, named public figure.** The shipped
default soul (`backend/souls/rose.md`), the `soul_manager.py` auto-create
fallback, the `persona_store.py` `DEFAULT_PERSONA`, the `main.py` default
`Companion.soul_id`, and the frontend's hardcoded fallback/placeholder text
were all built around a real K-pop idol (real name, real birthday, explicit
romantic/intimate roleplay instructions), used as the default identity in a
paid companion app. I didn't build that out further and replaced it
throughout with an original fictional character ("Nova", `backend/souls/nova.md`)
so the app still has a working default persona. If you want a different
default character, edit `backend/souls/nova.md` (or add a new soul via the
UI/`/souls` API) — just keep it an original character rather than a real
person's identity, especially given the romantic/intimate framing.

**Real bugs found and fixed:**
- `api_tests.py` assumed the SQLite tables already existed (only true if
  `uvicorn` had been run first in that working directory). Now calls
  `database.init_db()` before constructing the `TestClient`, so tests are
  runnable standalone/in CI.
- `ChatRequest.reasoning_effort` only accepted `low/medium/high`, but
  `index.html`'s dropdown also offers `minimal` and `max` — selecting either
  caused a silent 422 from `/webhook/chat`. Literal now includes all five.
- Frontend `savePersona()` POSTed to `/persona` with **no body**, so nothing
  was ever actually saved — the drawer looked like it worked but silently
  did nothing. Now sends a real JSON body and checks the response.
- `loadPersona()`'s prefill logic was backwards (only used the backend's
  values if the input fields were already empty, instead of prefilling the
  fields from the backend on open). Replaced with `loadActivePersonaIntoForm()`.
- Custom `soul_md` text was parsed into `persona_profile` but never actually
  injected into the system prompt sent to the model (`main.py` rebuilt the
  prompt inline and dropped `soul_md`). Now uses the persisted persona
  consistently and the saved Soul.md body actually reaches the model.
- Quick-action click handler now binds to `.line-quick-actions button`
  (was `.quick-actions button` — functionally equivalent today since the
  section carries both classes, but matches what you described and is more
  robust if the classes diverge later).

**New backend endpoints** (`backend/main.py`, `backend/soul_manager.py`):
- `GET /souls/{id}` — full soul detail + raw markdown (for editing/export).
- `POST /souls` — create/update a soul from structured fields.
- `POST /souls/import` — import a raw Soul.md document (frontmatter + body).
- `DELETE /souls/{id}` — remove a custom soul (default soul is protected).
- `/persona` GET/POST now persists to `backend/persona_profiles.json` via
  `persona_store.py` instead of an in-memory dict that reset on every reload.

**Frontend persona drawer** (`frontend/index.html`, `frontend/app.js`,
`frontend/styles.css`) is now a real "harem" manager: a chip list of saved
souls to switch between, "＋ 新建角色" to start a blank one, and
import/export buttons for Soul.md files. Quick actions and persona save now
show a success/failure system chip instead of failing silently.

**Tests:** `frontend/feature_tests.js` updated/extended to 8 passing tests;
`backend/api_tests.py` updated/extended to 12 passing tests (including new
`/souls` CRUD + import coverage and the full `reasoning_effort` range).
Verified with a brand-new venv (`pip install -r requirements.txt`) and a
fresh `node feature_tests.js` run — both fully green.

Note: `test_models_endpoint_lists_hermes_like_choices` expects `/models` to
return ≥4 models; this only holds when your real Hermes install
(`%LOCALAPPDATA%\hermes\config.yaml` / `provider_models_cache.json`) is
present, since the code falls back to just 1 local + 1 API model otherwise.
That's environment-dependent, not a regression from this session.

## Known recent bug fixed
Buttons looked dead because frontend sent runtime/persona fields that backend Pydantic schema did not accept, causing FastAPI `422`. Fixed by updating `ChatRequest`, `ChatResponse`, `generate_reply` signature, and tests.

## Next recommended tasks
1. ~~Polish persona drawer UI so it visibly exposes custom name / birthday / personality / soul text editing.~~ Done this session.
2. ~~Persist `/persona` to disk or SQLite instead of only in-memory `GLOBAL_PERSONA_OVERRIDE`.~~ Done this session (`persona_store.py` JSON file).
3. ~~Add explicit SOUL.md import/export.~~ Done this session (`/souls/import`, frontend import/export buttons).
4. ~~Improve button feedback: success/failure chip, re-enable send button on all error paths.~~ Done this session.
5. Add a way to switch a `Companion.soul_id` (the relationship-stage prompt) independently of the `/persona` override — right now the override always layers on top of whichever soul a companion was created with.
6. Add Playwright/browser interaction tests for the real UI, not only static Node string tests.

## Safety / maintenance note
Do not commit `.venv`, `__pycache__`, runtime DB snapshots, or generated backup folders in future packages. This handoff zip excludes those by default. `backend/persona_profiles.json` is also gitignored — it's a runtime snapshot like the DB file.
