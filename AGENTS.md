# Butler session instructions

Read context/README.md, context/STATUS.md, README.md and recent
context/ACTIVITY.md before work. Inspect Git branch/status/log and relevant code.
Parent workspace instructions apply; sibling project instructions do not.
Keep this repository independent. Do not modify the existing Codex tree outside
Butler. Never use sudo, restart unrelated services or change Caddy without explicit
approval. Bind development to 127.0.0.1:3501; reserve 3500.

After meaningful changes: run targeted tests and frontend build when applicable,
update current status and append a dated activity entry with results and next
steps. Stable decisions belong in docs/ARCHITECTURE.md, operational instructions
in README.md; avoid duplicating them. Record failures and unverified behavior.
Before committing describe changes, affected components and checks. Commit only
project files, never runtime data or secrets. No remotes/push without instruction.
Internal checks do not replace user confirmation.
