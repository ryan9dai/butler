# Current handoff — 2026-11-12

Foundation implemented and internally verified; user confirmation pending.
Initial commit planned: `feat: establish private persistent Butler foundation`.

## Running

Butler is detached in tmux `butler-dev`, bound only to 127.0.0.1:3501. Uses
existing scheduler and explicit gemma26b model. No boot auto-start. Scripts and
Windows SSH forwarding instructions are in README. 3500 remains reserved.
One synthetic approved foundation-verification event is in ignored runtime data.

## Checks

- `.venv/bin/pytest -q`: 10 passed; one upstream Starlette/httpx deprecation warning.
- `npm --prefix frontend run build`: TypeScript and Vite build pass.
- Live HTTP: UI 200, SQLite health ok, local model extraction → pending approval
  → approved calendar entry; repeated approval idempotent.
- Actual Butler stop/start: completed state and calendar entry survived.
- Listener confirmed 127.0.0.1:3501 only. Windows/browser visual checks unperformed.
- Initial 400-token model output budget returned no usable JSON; 1600 tokens and
  JSON response format succeeded. BUTLER_MAX_TOKENS is explicit/configurable.

## Blockers and pending work

- Dashboard and directory down. Their configured Colima daemon is unavailable;
  safe service-only recovery is not possible. No infrastructure started/changed.
- Caddy route is prepared, unapplied. Explicit approval and ACL review required
  before editing/reloading existing Caddy. Windows can use the documented tunnel.
- User should verify scheduling interpretation, UI, rejection and Windows access.
- No application login, tenant isolation, browser automation test or boot service.
- Ambiguous model extraction fails with a safe generic error rather than a
  conversational clarification turn. New request/key is required to retry.
- Mock calendar and email only; MockEmail defines draft listing, no send capability.
- Memory retrieval, consolidation, continuous operation and sleep are design only.
- Future remote actions need durable outbox/reconciliation and stronger identity.

Next: obtain user feedback; add authentication before mesh-wide use; request
Caddy approval if direct access is desired; evaluate structured extraction with
ambiguous/timezone/DST fixtures; implement a read-only real calendar connector
before permitting external writes. Stabilize schema migrations and data controls
before introducing real personal information.
