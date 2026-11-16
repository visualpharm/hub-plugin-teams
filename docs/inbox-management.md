# Private Inbox management protocol, version 1

This is candidate source. Installation, client adoption and operational activation
are independent gates. It does not activate a model, account, source or send policy.

```mermaid
sequenceDiagram
    participant Client
    participant Collector
    participant Hub
    participant Source
    Client->>Collector: draft_control (current token, hold)
    Collector-->>Client: persisted draft_state
    Client->>Collector: ask (id, post, rid, token, instruction, draft)
    Collector->>Hub: private request with source and generation-bound nonce
    Hub->>Collector: revision_result (nonce, rid, post, text, context, next_action)
    Collector-->>Client: verified draft_proposal, requires_apply
    Client->>Collector: deliberate release or current-version Send
    Collector->>Source: verify current account and exact source facts
    Collector->>Collector: persist shared claim
    Collector->>Source: one transport submission
    Source-->>Collector: actual message ID, or unresolved outcome
    Collector-->>Client: sent with receipt + submitted/current token, or uncertain state
    Note over Client,Collector: Only confirmed delivery grants a manual follow-up token; each next claim rechecks its source
```

## Current item and editor

New canonical `msg` posts may include `inbox`:
`{v:1, version:<opaque source/conversation hash>, edit_version:<integer>, held:<boolean>, holder:<editor ID or null>, manual_followup:<boolean>}`.
This token binds the collector's account, exact destination, current source facts
and conversation generation. It is a consistency token, not a signature.

Owner `draft_control` carries `id`, unique `rid`, current `inbox`, stable per-Hub
client `editor` identity and an explicit
`action` of `hold`, `release` or `takeover`. The collector compares source/editor versions,
persists the change, and publishes `draft_state` with the new token. Replay of an
identical request returns current state; reused request IDs with different input
are rejected. A fresh same-client hold increments edit_version, even if already
held, invalidating older proposals; replay of the same request does not increment.
Another client cannot release an acknowledged hold and cannot acquire it with
`hold`; it may only take it over explicitly (below). Navigation and restart never
release a hold; inactivity ends it only after the hold term (below). Hold ownership and `edit_version` belong to the
verified source account plus exact conversation, rather than an incoming row ID.
A newly observed row immediately exposes any existing conversation hold; already
observed sibling rows share it too. A client does not need to poll or reassert the
hold to prevent an automatic send after a new message arrives. Source `version`
still binds each item and the current conversation facts; old source tokens fail.
Cancellation
of a protected scheduled reply retains the item and acquires a hold.

Candidate state upgrades legacy row holds into conversation editor records,
preserving every active holder and the highest edit revision. Conflicting legacy
holders block sends; each may explicitly release only its own hold with a current
token, or one client replaces them all with `takeover`. An unowned cancellation hold must
be explicitly adopted before release. This state upgrade does not enable the guard.

### Takeover

The owner is one person on several clients. A client that shows the conversation
held by another editor offers an explicit action (for example "Continue here") and
sends:

```json
{"kind":"draft_control","id":"<item id>","rid":"<new unique id>",
 "inbox":{"v":1,"version":"…","edit_version":7,"held":true,"holder":"web-1","manual_followup":false},
 "editor":"phone-1","action":"takeover"}
```

`inbox` is the current token exactly as received (the one that names the other
holder). Success is the usual `draft_state` with the same `id` and `rid`:

```json
{"kind":"draft_state","id":"<item id>","rid":"<same rid>",
 "inbox":{"v":1,"version":"…","edit_version":8,"held":true,"holder":"phone-1","manual_followup":false}}
```

The requester now holds the conversation and sends as after its own `hold`.
`edit_version` grows by one, so the displaced client's token is stale: its
`hold`, `release` and Send are refused, it keeps its local text and may take the
conversation back only with its own explicit `takeover`. A scheduled reply the
displaced client left pending carries the old token and is refused at its hour
instead of going out next to the new reply. Refusal is `draft_control_failed`
with `id`, `rid`, `error`: stale token (refresh and repeat with a new `rid`),
missing `editor`, or a delivery already claimed for this version. Takeover of a
free or unowned hold equals `hold`. A collector older than this contract answers
`draft_control_failed` to `takeover`; the client then keeps the previous
behaviour. Takeover is never implied by Send: a non-holder Send stays refused.

### Hold term

A hold lasts `inbox_hold_ttl` seconds from its last `hold` or `takeover`
(default 1800; owner `settings` field `inbox_hold_ttl`, integer 0–604800, 0 = no
term; the current value is in the `config` post). A fresh `hold` from the holder
restarts the term. When it ends the collector clears the hold, increases
`edit_version` and publishes for every open item of the conversation

```json
{"kind":"draft_state","id":"<item id>","rid":"expired:<edit_version>:<item id>","reason":"expired",
 "inbox":{"v":1,"version":"…","edit_version":9,"held":false,"holder":null,"manual_followup":false}}
```

Any client may then `hold` and send as usual; clients that know nothing of the
term keep working: a Send with the older token gets the existing stale
`send_blocked` carrying the fresh token. The former holder keeps its local text
and must `hold` again before sending. Expiry is not the owner's release:
automatic sends for the same conversation generation stay refused until an
explicit `hold`/`takeover` and `release`, a manual send, or a new incoming
message. A hold that carries a scheduled reply does not expire while that reply
waits. A hold stored before the term existed gets a full term from the first
check after upgrade.

Clients must acquire and confirm the hold when an editor or private directive
becomes active, preserve intentional empty edits, and handle a competing committed
send honestly. A late acknowledgement cannot make a committed message look unsent.
Automatic operation must stay disabled until every active client uses the protocol.
The existing owner settings path has an additive `inbox_guard` boolean; it defaults
to false and is preserved across legacy settings writes. No source update enables it.

## Private revision

Owner `ask` with `what:"draft"` includes `id`, exact original `post`, unique `rid`,
current `inbox`, the same `editor`, nonempty `instruction` and optional `draft`. An empty draft remains
an intentional value. Private requests lacking a token receive `ask_failed`, not
an unbound JSON replacement. Ordinary legacy draft requests remain compatible.

The collector persists a hold and request, then addresses the existing canonical
Hub alias. The assistant returns a session-authored `revision_result` containing
`rid`, `post`, collector nonce, `text`, `context`, `next_action`. The collector checks
the actual canonical Hub name/session/generation, exact accepted source post and
current editor/source token. Another session, source, request, generation or newer
edit is rejected. Valid output becomes a plugin-authored `draft_proposal` with
`id, post, rid, inbox, text, context, next_action, requires_apply:true`.

Native/web adoption must display one editable proposal and explicitly Apply it
only against the matching server/account/thread/request/editor revision. Neither
raw session JSON nor `asked.rid` is authenticated draft completion. A proposal never
releases the hold or sends. Private instructions/context/actions never join outgoing
text. The protocol deliberately adds no unsafe automatic replacement behavior.

## Whole Inbox

Owner `manage` carries unique `rid` and exact `text` (nonempty, at most 2000
characters). The collector retains the exact text and its whole known-open
manifest, independent of a client's loaded page, and sends bounded batches through
the canonical Hub route with existing `cfg.prompt`. `manage_asked` is dispatch only.
Separate trusted `triage_config`/`triage_prompt` facts transmit exact owner guidance
in envelope-bounded chunks with a content hash. Proactivity acts only after the
whole guidance is verified, and binds verdicts to that guidance ID. Large settings
cannot silently leave an older prompt governing automatic actions.
Coverage reports `scope:"collector-known-open"`, count, unavailable post/token count,
source warnings and `upstream_exhaustive:false`. Missing original posts or failed
source pages stay explicit blockers. No request, receipt or snapshot claims that
all upstream correspondence was handled. Recent-ID/ref caches never evict open work.

## Shared delivery

Manual and plugin-automatic `send` carry the same current `inbox` token. A manual
Send carrying its matching `editor` atomically consumes that client's hold and
persists the delivery claim together; it does not require a separate release or
automatic-policy activation. When the
guard is enabled, legacy unversioned sends fail closed. All automatic requests
require the guard; there is no legacy fallback. One collector writer lock and a
persisted claim serialize both paths, across restart and differing request IDs.
New source facts, destination/account changes, active edits and unresolved claims
reject a send. A losing request receives `send_duplicate` with original request,
version and actual state/receipt when known. It does not authorize another attempt.
The collector checks conversation hold and source/editor versions again at the
final claim after preflight. A hold acquired while source reads are in progress
cannot be bypassed. A deliberate matching-client Send consumes its conversation
hold and stores its current-source claim in one persisted mutation.

### Manual replies after a confirmed Send

Only a real successful transport receipt advances the conversation source version.
The collector persists the sent message ID and normalized outgoing body as the next
source anchor, then returns `sent` with the actual `receipt`, canonical
`submitted_inbox` for the committed request and a fresh current `inbox` token.
Its additive `manual_followup:true` permits another deliberate manual text reply
to the same selected conversation without a new inbound or reopening automatic work.
Use a new request ID, that exact token and the persistent `editor`; actual typing
acquires the shared hold as usual. Never invent, rebase or increment a token locally.
An omitted or false capability does not grant this closed-item exception.

Before each follow-up claim the collector checks the actual source account and
reads the latest ordered chat page. Its recorded sent ID must still be a message
from that account with exactly the normalized sent body, no attachments/deletion,
a valid timestamp and no newer incoming or outgoing facts. A subsequent confirmed
Send issues another fresh token. New source facts invalidate the old follow-up
anchor; changed/missing source, unsupported adapters and unanchored legacy Sent
records fail closed. There is no client-side legacy-token upgrade.

Automatic replies always require a current open incoming item; a manual follow-up
token never opens that path. Uncertain delivery produces no next source version
and sets `manual_followup:false`; it never authorizes a retry. Holds and unresolved
claims continue to exclude other clients and automatic work.

`send_duplicate` requires the original source/account and exact text/files/quote/
reply-target payload. It includes the persisted receipt/state, original submitted
token when recorded, and current collector `inbox`; different payload receives no
old Sent receipt. Replaying the identical completed request after restart returns
this evidence without transport IO, including if the original `sent` post was lost.
Changing intent under the same request ID is rejected. A duplicate receipt is a
readback of the earlier commit, never acknowledgement of a different reply.
This manual-send capability does not authorize a private revision against a closed
original post; that path still requires its independently verified current source.

Before submission, the existing connected Graph reader verifies current user and
the exact text-only chat source against the latest ordered message page; newer
incoming or outgoing facts reject it. Source errors block before transport.
The `send_blocked` event names the cause in `reason` (`newer_messages`,
`source_unreadable`, `source_changed`, `unknown`) next to a distinct `error`
phrase; nothing reached transport for any of them. This
candidate currently protects text-only Teams chat replies. Channel/media replies
and other adapters lack the required verified source/account/receipt contract and
remain blocked on this automatic path. No credential or transport fallback is added.

Automatic replies respect configured contact hours as well as producer gates;
deferred requests retain and recheck the original version. A real returned Graph
message ID is required for `sent` and closure. Empty success, generic stdout and
exceptions remain `send_uncertain`; they never retry automatically. Unresolved
claims also block new-version sends in the same conversation until independently
reconciled. There is intentionally no command to clear that uncertainty by fiat.
Pre-submission rejections are also durable: replaying the journal after recovery
cannot turn an already rejected request into an unseen send. A re-evaluated action
uses a new request ID; existing verified delivery state is returned when present.

## Activation gate

`tests/fixtures/native-inbox-v1.json` binds synthetic request shapes to immutable
native `6bb89c9` and later `05afabb` source hashes. `test_native_inbox_wire.py` sends
those shapes through the real Choice parser and collector, including empty private
drafts, editor holds, fresh-token manual follow-up and uncertain outcomes. This is
producer compatibility evidence, not captured Swift execution or native UI proof.
The historical `6bb89c9` lacks current sent-token/outcome adoption; the inspected
`05afabb` updates current tokens but still maps confirmed duplicate receipts to
failed/uncertain. Receipt/submitted/current-token adoption remains with the native
owner; no producer fixture turns those missing consumer behaviors into acceptance.

Adopt the complete contract in all active clients; validate exact source coverage
and every required source adapter; run permitted runtime/model and rendered checks;
coordinate one allowed plugin activation. Only then enable the shared guard and
the separately chosen routine-management policy. Keep unverified source routes
and unresolved delivery outcomes held. Source checks alone do not release this gate.
Before downgrading this candidate, settle active conversation holds: older code
only understands row-scoped editor state and cannot preserve this exclusion.
