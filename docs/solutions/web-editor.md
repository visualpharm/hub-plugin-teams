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


### Consume only the captured action-spool snapshot
The browser can write a new fact while the fixture is inspecting an earlier one.
Deleting every directory entry after spool.take can remove an unfinished atomic
`.tmp` file or a newer completed request that the test never inspected. Consume
only the exact paths returned by take. The deterministic fixture regression
keeps an in-flight file and inserts a second fact after the snapshot; both must
remain available. This is fixture ownership, not a product retry or a weakened
recipient/delivery assertion.


### Preserve conversation menu state across feed refresh
The conversation header is rebuilt while message/media rows retain identity.
An open details menu and its focused action therefore need explicit restoration
only when the stable conversation key still matches. Scope persisted local
preferences independently from provider read state. Lazy storage access keeps
browsers that refuse localStorage from breaking module initialization; failed
writes must not be reflected as a saved pin.

Local preference caches must compare their stored serialization before mutations;
a cache keyed only by Hub silently loses changes made in another already-open tab.
Use the storage event to refresh visible state, preserving the current draft.
Shared menu styling does not justify reusing an editor-specific selector on an
unrelated conversation control: give each control its own semantic class.


### Local unread is a reminder, not a provider action
Do not implement Mark unread by deleting a seen ID alone: a provider unread=false
flag would immediately hide the reminder. Store an explicit local override using
exact Hub/source/conversation/message identity. Opening sets a local read override
without sending any provider action. Copy the cached Map before a write: a refused
setItem must not mutate the visible reminder. Keep draft storage independent and
return focus to the exact conversation row after marking unread.

Unread failure and flat-card actions restore focus to the same visible menu
summary. After a failed storage write, rendering a closed menu cannot focus its
now-hidden action; an explicit summary target is required. A grouped reminder
returns focus to its exact conversation row instead.


### 2026-10-17 — Read preference failures stay visible
Opening a conversation surfaces a failed local read write, leaves the reminder
unchanged, and keeps the editor usable. A successful retry clears that error.
Empty targets cannot report a saved reminder. Read preferences refuse growth
beyond 256 Ki characters per Hub, without deleting old reminders, to limit their
share of origin storage. This is a bounded stop, not a guarantee of free browser
quota; compaction and stable Hub rename migration remain separate work.


### Provider read recovery and menu bounds
`provider-read.js` owns a separate per-Hub receipt ledger, never the local unread reminder. Reload/replay reuses the original request; a source rebind has another target and cannot consume an old receipt. The 256 Ki-character bound compacts settled success records, reserves room for bounded failure receipts, and refuses growth instead of evicting unresolved IDs or drafts. Web Locks serialize request admission across browser tabs. Refused receipt persistence stays pending for same-rid recovery. Do not infer provider success from HTTP acceptance.

Conversation menus are anchored before two other header controls. A viewport-wide max-width can still place their left edge offscreen. Bound width to the space available before those controls and allow status text to wrap. The provider-read browser scenario checks actual menu edges at seven widths, light and dark when capturing.

Native header pseudo-element backdrops can cover positioned menu anchors even when their dropdown is layered. Keep both conversation and editor menu anchors above the backdrop; test hit targets with the actual header decoration, not visibility alone.

### Reply storage admission
A visible draft-storage warning is insufficient if the Send callback proceeds. Check persistence of the pending rid before invoking transport in both shared and fallback composers. If it fails, remove the local unsent pending claim, retain text/files, and restore the shared composer through its existing error-return path. A guarded editor's delivery token is still only local at this point and can be released; never clear a claim after transport has run. Synthetic browser tests cover quota refusal, recovery, guarded/external sources and attachments; the fallback VM test rejects transport while storage is blocked.

### A draft is not the pending delivery ledger
The draft's pendingRid alone does not prevent duplicate sends after reload: typing replaces the draft, and the in-memory sends map disappears. Save the exact request separately before transport and consult that record at admission. Restore guarded delivery context from that record so a receipt must match its original version, not just a visible message id. Preserve newer text independently, settle only the matching request, and never replace an uncertain operation with a fresh rid. Definitive refusal and cancellation release admission; unresolved outcomes do not.

### Send options on different composer versions
Check composerTrailing before using the optional right-side slot and place the menu in leading when absent. Both routes use the same DOM control and grid placement. Keep the date picker outside the parent form's validation association, handle its Enter explicitly, and consume the scheduling intent only for a valid nonempty submission. Otherwise a rejected empty scheduling attempt can silently schedule the next ordinary reply. Preserve focused menu nodes through feed repaint, and check actual popup bounds, Escape and focus at phone/tablet/desktop widths. More-specific existing last-child grid rules can place the trailing menu over Send despite correct DOM order.


### Await the actual request in synthetic acceptance

`requestSubmit()` returns before Web Locks and fetch complete. A single spool snapshot falsely failed three existing delivery cases after durable admission added an asynchronous lock. `queued(kind)` now waits up to five seconds for the actual matching queue event while consuming only completed spool files. A deterministic delayed-event regression covers this; delivery, receipt and newer-draft assertions remain unchanged.


### A conditional folder must fit the same toolbar

The unresolved-reply state adds a fourth folder. Live captures revealed that existing 8px gaps plus 52px padded folder icons pushed Inbox options beyond a 360px viewport and over the desktop conversation pane. The shared toolbar now removes redundant gaps, uses 44px folder targets and 8px outer padding. A seven-width test requires every visible toolbar control to remain within its own list pane and be hit-testable; it preserves folder/sort behavior and draft state.


### A matching request id is not enough for a delivery receipt

Bind the original target alongside rid and preserve it independently from editable draft text. Reject mismatched or missing target before editorFact can apply a receipt; guarded editor-state also rejects it directly. Owner echo must not overwrite a known original target. On reload, restore that binding from the pending request. Browser regressions cover external and guarded replies, wrong/missing target, trusted completion after reload, and newer-draft preservation. Scheduling and the fallback composer propagate the same target. Legacy targetless receipts remain supported only for targetless original requests.


### Recover the original request, not the current draft
An explicit replay can first-submit a request lost before collector admission. Label it Retry original reply, require the trusted reply_replay capability and a target-bound durable request, and send the saved object unchanged. Revalidate the current conversation and pending record inside the handler, because a detached button may outlive a source/config/storage change. Coalesce transport attempts, keep unknown outcomes pending, and preserve newer draft text/files. Guarded duplicate receipts must match the original version before either the editor or outgoing bubble changes state; rejecting settlement alone still falsely paints success and hides recovery.

Capability revocation tests must first observe the enabled control before awaiting its disappearance. Awaiting an already absent control can return before the revocation fact arrives and falsely characterize a stale-button click as a runtime failure.

A replay success can arrive without a live guarded editor to perform cleanup. Mirror fresh-success cleanup in the feed reducer: settle original request, accept only its matching draft tombstone, record answered state, and clear an unguarded composer only if no newer owner draft exists. Regressions cover unchanged external drafts and guarded success after reload with the editor closed.

Live synthetic rendering caught a separate stale global transport alert after confirmed delivery. Reply callers already own unresolved status; mark(send) must not also create a global Hub-unavailable banner that survives the receipt. Shared and fallback paths retain their pending reply and recoverable feedback; unrelated action/storage errors keep their own handling.


### Next opening belongs to the Hub calendar
Use trusted collector hours and the exact contact exception, not the browser timezone or a universal next morning. Resolve the opening as civil time in the configured IANA zone, with an explicit collector offset only as fallback; enumerate offsets across transitions to handle gaps and repeated hours. Labels belong to the device timezone. Recompute on opening and activation so a stale menu never sends a past instant. Keep the shortcut hidden when configuration is absent, and route submission through the existing durable admission rather than adding another transport path. Module checks cover strict-future boundaries, weekend inversions, custom openings, DST transitions and zone fallback; browser checks cover live configuration changes, preserved draft, click-time recalculation and reachable phone/tablet/desktop menu geometry.

A target can change while a draft-key-stable composer remains mounted. Revalidate menu submission identity and explain that the editor must reopen; a silently inert shortcut looks broken. Browser regression preserves the draft and requires zero sends after a target replacement. Config-revocation coverage must first observe the enabled shortcut, and weekday assertions must use the device timezone.


### A reaction is also a destination-bound operation
Binding replies alone left reactions with an id/rid pair and no target. A changed provider reference could receive the reaction, while a wrong-target receipt painted success. Carry target through the request, parser and receipt; verify it before updating reaction state. Detach old reaction requests when the source/contact/target identity changes, reject late owner echoes for the former target, and revalidate the current message when an old DOM control is activated. Keep the local ownership marker when its own echo arrives so a later unrelated echo cannot replace an in-flight local action. Legacy targetless events remain compatible; no automatic resend is introduced.
