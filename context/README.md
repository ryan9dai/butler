# Project context

Butler is a private, reusable personal assistant platform, intended to grow into
a persistent adaptive organizationally continuous process (PAO). Start with a
reliable approval-gated scheduling slice; integrations remain mocks.

Startup order is in AGENTS.md. STATUS.md holds the current handoff and pending
work; ACTIVITY.md is append-only milestone history. README.md owns commands and
environment controls; docs/ARCHITECTURE.md owns stable decisions and PAO design.
Update those after meaningful changes and before ending each session. Keep
personal data, secrets, transient command transcripts and unrelated project
information out of continuity documents.

This follows the observed Codex workspace pattern: parent AGENTS.md loads shared
context; project context startup instructions reference current state, root
README and history; dated entries record outcomes and tests. Related projects
use context/history/README.md, STATUS.md, PLAN.md and dedicated handoff docs.
Butler separates status and history to avoid repeated copies. Files are loaded
by agent instructions and explicit reads, not an automatic application memory
loader. No existing Codex files were changed during foundation work.
