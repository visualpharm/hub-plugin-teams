# Decisions

## 2026-10-15 · Offline source gate
Decided: retain the existing mocked Python and Node checks under one reviewed local
argv gate. Require the core dependency through PYTHONPATH or HUB_CORE.
Why: a plugin source change must be checkable without reading real accounts or
starting its collector. Undo: remove the wrapper and use the documented commands.
By: agent, within the authorized Inbox source adaptation.

## 2026-10-15 · Explicit core task relationship
Decided: feature-detect the shared body/decision helpers and accept only an explicit
task_id matching a real core snapshot item before showing task actions. Source prose
never supplies an identity. Keep existing reply/delivery controls and older-hub text.
Why: Inbox and core task IDs represent different state; guessed associations can
complete unrelated work. Queue/error/closure stays in the existing message context.
Undo: remove the web adapter; no channel migration or collector change.
By: agent, within the authorized task-flow scope. Installation remains held.

## 2026-10-15 · False closure and mixed history correction
Decided: unread-source disappearance never supplies an owner reply timestamp. Keep
actual Teams reply facts, successful-send receipts, explicit dismissals and newer
message supersession. Add an operator correction referencing the exact original
message and false closure, accepted only via the owner or the plugin's own process.
Recheck current accepted feed and stored destination before changing the projection;
successful sends, later closures, superseded sources and missing evidence refuse.
Why: reading, filtering, source errors and restarts can remove unread markers.
Reposting a message loses its original post/draft identity. Corrections retain all
raw posts, original source and drafts, and invalidate contaminated derived history.
WhatsApp history validates expected channel/account/peer, raw peer-qualified row ID
and dated per-row provenance before publishing any row. Missing expected account or
legacy provenance fails closed. This is identity consistency, not a signed source.
Undo: revert this source change; never delete correction or original journal posts.
By: agent, within the authorized Inbox repair; runtime activation and rendered
acceptance remain held pending coordinated producer, web and native adoption.
