# Architecture and decisions

## Foundation

Use a single host-local FastAPI process, a compiled React/TypeScript interface
served on the same origin, and SQLite WAL persistence. This keeps deployment
small and portable while providing a client-neutral API for later mobile apps.
No separate queue, embedding database, agent framework or inference server.
Existing inference infrastructure remains independently owned.

`models.py` validates timezone-aware structured extraction; `inference.py` defines
a replaceable inference protocol and local OpenAI-compatible and deterministic
mock implementations. `service.py` owns task transitions, approvals and recovery;
`connectors.py` owns calendar/email contracts and mocks; `storage.py` owns schema;
`app.py` is HTTP/security/static delivery. Configuration belongs to the environment.
Calendar and service use a shared transaction in V1 to guarantee atomic mock
execution. A future remote connector needs an outbox and reconciliation contract,
not a claim that SQLite can atomically commit an external action.

## State and safety

Task lifecycle: extracting → pending_approval or conflict or failed;
pending_approval/conflict → rejected; pending_approval → completed after approval
and conflict recheck. Conflict approval remains blocked. Restart marks extracting
tasks interrupted; a user may resubmit with a new key. Completed/rejected tasks
are terminal; repeated identical decisions are idempotent. There is no edit of
an approved payload. Reusing a request key with a different request returns 409.
Concurrent approvals serialize through BEGIN IMMEDIATE. Half-open UTC intervals
permit adjacent appointments. Audit, commitment and calendar writes commit with
the task state. Real connector execution will need approved/executing/reconciling
states, stable connector idempotency keys and explicit ambiguous-outcome recovery.

SQLite separates task state, calendar records, audit history, operational state,
and memory. Memory kinds distinguish preferences, facts, episodes and commitments;
provenance, confidence, validity interval, supersession and timestamps prepare
for reconciliation. V1 only writes scheduling episodes and commitments. It does
not infer personal facts, consolidate or search memory automatically. Version 1
schema uses user_version; future schema updates require explicit migrations and
backup tests. Customer databases/configuration stay outside shared source code.

Model output is untrusted data. Strict validation forbids unknown fields and
naive/inverted timestamps. Ambiguous output fails safely; an incorrect but valid
model interpretation still requires human review. Capabilities must eventually
be enabled by measured extraction accuracy, tool reliability, latency and budgets,
not hardware names. Scheduler model enumeration is available at /v1/models;
model selection is explicit and failures observable, without silent substitution.

No email sending or WeChat automation. Future connectors: Google Calendar/Gmail,
Microsoft Graph/Outlook, Apple Calendar, WeChat desktop, macOS Accessibility and
other messaging systems, each with narrowly scoped permissions and credential
references to a secret provider. Add read-only discovery and mock contract tests
before consequential actions. External actions require durable human approval.

## Future continuous operation and sleep (proposal only)

Persistent state → bounded activity → recorded experience → reconciled state →
subsequent activity. A future worker claims a durable work-cycle record with a
lease, checkpoint, remaining inference/time budget and pause flag. Each cycle
retrieves relevant durable context before planning. Permissions gate reads,
recommendations and effects separately; communication still requires approval.
Use backoff and a maximum attempt budget, interruption recovery and observable
run summaries. Schedule periodic reviews for new commitments, source changes and
unresolved work; do not implement an unrestricted loop.

Sleep is a scheduled bounded job over a checkpointed episode range: retrieve
recent experiences; propose deduplication and contradiction resolutions; retain
source citations/confidence and temporal relevance; write versioned proposals;
apply permitted consolidations transactionally; preserve provenance and rollback
history; surface uncertain conflicts and forgotten commitments for review. Track
budgets and retention, avoid destructive deletion, and prepare next-day context.
Pause/resume and idempotent range checkpoints survive restarts, updates and model
changes. Evaluate against fixtures before enabling memory mutation or autonomy.
None of this background processing is enabled in V1.

## Existing environment observed 2026-11-12

Caddy runs through a Homebrew user LaunchAgent. It binds routes individually to
the private mesh IP and proxies loopback services. Dashboard: Compose service
`dashboard`, container `ultra-dashboard`, port 3000, health /api/status, restart
unless-stopped. Directory: Compose `homepage`, container `personal-homepage`,
loopback 3001 → container 80, health /health, same restart policy. Both are down;
Ryan's default Colima socket is unavailable. Recovery requires infrastructure
outside the authorized scope; neither restarted, rebuilt or reconfigured.
Tailscale reports the Ultra online at 100.64.0.7. Local inference scheduler
/v1/models responds with gemma26b, qwen and gemma4-chat. No existing service changed.

## Continuity investigation

Read-only traversal covered the Codex tree and Markdown files, including hidden
instruction directories, excluding generated dependency caches, Git internals
and model binaries from content inspection. Actual startup/handoff conventions
were inspected in workspace AGENTS/context, GoL and Longfin management/history,
Whiteboard context/activity and Turbo handoff documents. Other project planning,
status and instruction locations were inventoried. No automatic global session
summary loader or universal shutdown hook was established by this evidence;
continuity relies on explicit instruction-driven reads and document maintenance.
No unrelated private content was copied. Parent workspace activity was not
modified because the request requires existing Codex files to remain read-only.
