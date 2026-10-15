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

## 2026-10-15 · One Inbox suggestion contract across assistant request paths
Decided: retain the selected server's canonical Hub route, plugin authorship and existing raw reply-to-post
format. Share owner cfg.prompt and verified-context/one-next-action guidance across automatic, manual draft
and work request builders. A leading separator permits private context without inventing recipient text.
Keep recipient approval and source/identity restrictions; do not force browser/source fallbacks for a draft.
Why: manual requests previously omitted the owner's instructions, and one-phrase Why did not explain what to do.
Undo: revert this prompt/helper change; no source state, credential, recipient or client schema migration.
These are source instructions and parser fixtures, not proof of actual model output, result-generation
authentication, native acceptance or release. Native owners retain response/hub/thread/edit protection.
By: agent within the existing Inbox producer task; install/activation remains separately coordinated.

## 2026-10-15 · Routine authority and current-version delivery
Decided: routine correspondence within established delegated authority may proceed
without repeated approval; owner presence/inactivity never adds authority. Preserve
money/legal/health/infrastructure/strategic and owner-information decisions. This
supersedes the previous blanket recipient-approval wording for routine handling.
Technical choice: existing collector owns one durable manual/auto claim, explicit
editor holds, source preflight and actual transport receipts. Private revisions
return authenticated explicit-Apply proposals. Whole requests preserve exact private
text and report canonical coverage limits. See inbox-management.md for the wire.
Why: prompt-only approval and client-local versions cannot prevent duplicate sends
or unsafe late editor replacement. Unknown outcomes cannot authorize retries.
Undo: revert candidate source while preserving journal/claim history; do not clear
uncertainty or enable an older automatic path. By: agent within authorized scope.
Source is not installed; all-client adoption and coordinated activation remain required.

## 2026-10-15 · Rejection replay and complete guidance
Decided: persist pre-submission rejection disposition, so journal replay cannot
turn a previously rejected request into a new send. Publish complete exact triage
guidance through bounded hashed chunks independently of the legacy settings size.
Why: transport recovery must not resurrect old actions, and truncated/stale owner
guidance cannot govern automated replies. Undo: revert source without deleting
request, claim or instruction history. By: agent within the same authorized slice.

## 2026-10-15 — Web Inbox uses the shared composer and collector confirmations

The web consumer reuses the page composer only when composerTransport:1 is advertised.
The existing node/focus/set facade remains intact. Provider submission uses an explicit callback;
it never falls through to a session send. New collector-protocol editors require an acknowledged
current hold, private revision stays source/request/editor-bound, and Apply remains local and explicit.
Serialized envelopes are bounded before the 2000-character feed limit can truncate them.
Queued and uncertain submissions retain drafts; a matching actual receipt closes the editor.
Conversation grouping follows contact/box identity and never guesses from a repeated name.
Unsupported guarded adapters and attachments remain held under the collector contract.
Undo: revert this web consumer slice; it changes no collector policy, account or journal schema.
Installation and live acceptance require the existing scoped integration safe point.

## 2026-10-15 — Acquire web editor holds on owner input
A reply preview or generated fill alone does not acquire a hold. The first actual
reply/private-instruction edit does, including intentional empty edits. Existing
holds persist through navigation; provider delivery still requires the matching
collector receipt.
