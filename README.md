# Butler

Private, persistent assistant foundation. FastAPI, React/TypeScript and SQLite.
Development only: single trusted user, mock calendar/email, no external sending,
no autonomous loop. User confirmation of browser behavior is pending.

## Run

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
npm --prefix frontend ci
npm --prefix frontend run build
cp .env.example .env  # optional; defaults already match this Ultra
./scripts/start
curl http://127.0.0.1:3501/api/health
./scripts/stop
```

`./scripts/run` runs in the foreground. `start` uses a detached tmux session
named `butler-dev`, logs to ignored `var/service.log`, and does not install a
login/reboot service. Restart after code/config changes. Never run two instances
against the same DB: startup recovery assumes one worker. Port 3500 is reserved.
No Docker is needed for this host development instance; existing user Docker
is unavailable. Backend binds strictly to loopback.

## Windows access

From PowerShell, using your existing SSH account/key:

```powershell
ssh -N -L 3501:127.0.0.1:3501 ryan@100.64.0.7
```

Keep that window open; visit **http://localhost:3501**. This uses existing
Tailscale SSH connectivity without changing ingress. If your SSH alias differs,
substitute it. Windows verification remains pending.

The minimal proposed private Caddy route is `deploy/Caddyfile.example`.
It has NOT been applied. After explicit approval, validate the complete existing
Caddyfile, confirm mesh ACL authorization, add the block, and gracefully reload
through its established management mechanism. Proposed URL afterward:
`http://100.64.0.7:3501`. No public exposure.

## Scheduling

Ask, for example: “Schedule a design review on December 20, 2026 from 10:00
to 11:00 Europe/Monaco.” The local model extracts a proposal. Review the actual
date/time/title before approval. Overlaps prevent approval. Reject to cancel.
The Approvals tab shows proposals and the durable mock calendar; System shows
runtime configuration and audit events. The interface displays browser-local
times; model interpretation uses `BUTLER_TIMEZONE` (default Europe/Monaco).

`BUTLER_INFERENCE=openai` uses the existing priority scheduler on loopback
18081, model `gemma26b`. Set `BUTLER_MODEL` explicitly to another available ID;
`BUTLER_MAX_TOKENS` defaults to 1600 to allow reasoning plus JSON output;
no assumption that a model is permanently available and no silent fallback.
Unavailable/invalid inference produces a failed, audited task. Retry by
submitting again. Backend supports bounded retries only for transient inference
errors. No side effects are retried outside approval transactions.

For offline demo/testing set `BUTLER_INFERENCE=mock` and restart. Mock input:
`Schedule Review from 2026-12-20T10:00:00+01:00 to 2026-12-20T11:00:00+01:00`.
Other configuration is listed in `.env.example`; it is loaded by `scripts/run`.
Do not put credentials in it; future connectors should use Keychain or a secret
provider. Never commit `.env`, databases, user requests or logs.

## API and checks

`GET /api/health`, `/api/state`, `/api/integrations`; `POST /api/tasks` with
`{text,key}`; `POST /api/tasks/{id}/decision` with `{approve}`. Mutations require
`X-Butler-Client: browser`, same-origin requests, and allowed Host. No CORS.
API docs: `/docs`. This client-neutral API can later serve mobile applications
once authentication and client authorization are implemented.

```sh
.venv/bin/pytest -q
npm --prefix frontend run build
```

SQLite `data/butler.db` survives restart. Stop Butler before making a consistent
backup using SQLite's backup API; do not copy only the DB while WAL writes run.
Data is sensitive and unencrypted at application level; directory/file modes
restrict local access. Host disk security remains relevant. This is not ready
for multiple tenants or deployment to untrusted mesh users: add authentication,
tenant isolation, retention/export/delete controls and ingress authorization first.

Session startup: read `AGENTS.md`, `context/README.md`, `context/STATUS.md` and
recent `context/ACTIVITY.md`; inspect Git. Architecture lives in `docs/ARCHITECTURE.md`.
