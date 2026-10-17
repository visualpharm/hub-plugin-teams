---
title: A shared reply editor must retain collector identity and delivery truth
scope: repo
area: web
tags: [composer, inbox, identity, delivery]
created: 2026-10-15
status: active
---

## Problem
The legacy textarea lacked shared behavior and could group unrelated people with
the same display name. A visual migration could also lose collector CAS/receipt checks.

## Root cause
Editor and transport state lived in separate ad hoc UI handlers. Names doubled as
conversation keys. A queued feed post had no delivery authority.

## Solution
Use capability-gated shared input with explicit transport. Keep a protocol state
controller for acknowledged holds, exact private revision and local explicit Apply.
Retain submitted text through queued/unknown outcomes; only a matching receipt
closes the editor. Group by source contact/box identity; never merge unknown names.
Bound serialized requests before the feed can truncate them.

## How to apply
Run tools/check.py with HUB_CORE set to the matching web source. Browser fixtures
use an isolated real journal and synthetic collector facts, never provider accounts.
Assert prerequisite acknowledgements and matching proposal IDs before clicking.
Capture both themes and responsive widths. Offline receipts establish controller
behavior only; installation, policy activation and live delivery remain separate.

## Actual editing boundary
Opening or prefilling the editor does not acquire a new hold. The first owner
reply or private instruction input confirms it; intentional empty edits remain
held. Existing holds survive navigation, and closing a never-edited preview does
not release another editor. Incidental group/filter totals are omitted; explicit
bulk-action confirmation counts remain.

## Proposal visibility
The proposal body is bounded and scrolls separately from its Apply button. It
lives outside the private instruction disclosure, so receiving a result never
hides Apply below that disclosure's clipping boundary or moves the pinned reply.
The real-browser check verifies hit-testing the visible Apply action on390px.

## Durable owner text
Keep owner text in origin-local storage keyed by source, exact account/conversation,
and inbound message. Store the submitted request ID alongside a pending draft.
A matching accepted receipt may clear that record, but must never erase a newer
edit. Navigation and reload do not acquire a hold or replay a send. A blocked
store keeps the current text and displays an explicit save warning.
Browser action-spool reads consume events: after `queued("send")` asserts the
original request, the reload assertion must expect zero additional requests.

## Media continuity during feed updates
Keep the active conversation and unchanged media subtrees connected while replacing
other content. Replacing the whole thread resets a playing audio/video element.
Shared task-body renderers move their cached text nodes into the newly rendered
row, so retaining an old row wholesale loses text. Refresh its non-media children
and retain only the identical media subtree. The pinned native fixture with a
valid synthetic MP4 proves playback, pause and audio continuity during an unrelated
incoming message; the normal plugin gate also checks node identity and retained text.


### New-message interrupted delivery
A pending POST restored after reload is uncertain, not permanently sending. Keep its original rid, recipient and payload; lock recipient switching and show the original message beside an explicitly labelled retry. Text edited meanwhile remains a separate draft. A 30s receipt watchdog offers the same recovery without automatic submission. Search Enter must search rather than implicitly submit the form. Failed browser storage must be visible, and contact results need live announcements and an explicit control relationship. Hostile-review findings were reproduced with real synthetic browser interactions before repair; no provider calls.


### Scheduled replies and unknown collector outcomes
Unschedule posts the existing cancel protocol with the exact source id, delivery rid and editor identity. Keep the scheduled item visible until the collector confirms the matching source and rid; refusal/timeout leaves a retry. Cancellation releases only the local pending marker, preserving later text/files and the collector editor hold. A send_failed fact with unresolved:true is not a definitive refusal: retain the original pending delivery and same-rid recovery, including across reload. Never turn uncertainty into a fresh delivery id.

Cancellation facts are replayed from history on reload. Only release a stored pendingRid when it equals the canceled rid (or this page initiated the active cancellation); never clear a newer pending reply. A real reload regression reproduced the old cancellation clearing the new receipt binding, and checks the new matching receipt still clears the delivered draft.

### Suggested reply with a lost web acknowledgment
The legacy suggested-reply button treated a failed HTTP acknowledgment as a definitive
delivery refusal, enabling another Send with a new rid. Preserve unresolved state and
the original draft until a matching collector receipt arrives, as the shared composer
already does. Only change a still-waiting request: a collector outcome arriving first
must not be overwritten by a late HTTP failure. Reproduce by accepting the synthetic
POST, then throwing away its response; verify the suggestion remains disabled and the
exact sent receipt resolves it without another request.


### Context menus for historical messages
A history row has no ordinary source post of its own. Preserve the trusted thread post
and chunk location when ingesting history, then send the native ask fields: source
post, place, provider msg, from and at. Do not substitute the display row ID or raw
message text. Resolve menu identity again at activation, and close on source rebind.
Keep context menus inside the viewport at narrow widths; verify their actual masks
as well as dimensions, because missing CSS mask bindings render solid icon squares.


Context-menu follow-through: outside-dismiss handlers must run before a new row's
long-press timer is armed, or the same bubbling event cancels the next gesture.
Re-resolve the row element after refresh before opening or restoring focus. Work
quotes need the same trusted history location as Draft; the latest source post is
not the historical message. Copy the display text, omitting media placeholders.
