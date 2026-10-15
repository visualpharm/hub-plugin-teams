# Decisions

## 2026-10-15 · Offline source gate
Decided: retain the existing mocked Python and Node checks under one reviewed local
argv gate. Require the core dependency through PYTHONPATH or HUB_CORE.
Why: a plugin source change must be checkable without reading real accounts or
starting its collector. Undo: remove the wrapper and use the documented commands.
By: agent, within the authorized Inbox source adaptation.
