# Web Inbox parity

Owner m333740 reports missing controls, mixed old design, repeated refresh and trapped navigation.
The shared client design is HubbaHub v5 with file 22, Inbox prompt and action,
etag 1792090255859803. Native d332010 owns no plugin-web source. Existing collector
management work owns the protocol; this slice changes only its web consumer.

- Use the real shared composer when composerTransport:1 is present. Preserve old-page compatibility.
- Keep list/detail navigation, thread reading, exact draft, selection and explicit close usable at phone/tablet/desktop widths.
- Group by source conversation identity, never display name; unknown identities stay separate.
- A current editor acquires an acknowledged CAS hold. Navigation never releases it.
- Private instructions remain private, including intentional empty drafts.
- Bind proposals to item/post/request/editor/source revision. Explicit Apply cannot overwrite newer local edits.
- Whole-Inbox instructions retain exact owner text and use collector manage, independent of visible pagination. Dispatch is not completion.
- Queued, refused, uncertain and receipt-confirmed delivery remain distinct. Preserve replies until an actual matching receipt.
- Preserve source restrictions. The guarded collector currently supports text-only Teams chat replies; omit unsupported attachment controls.
- Keep a bounded history scroller and visible reply field. Reuse the shared icon pack, type, surfaces and 44px controls.
- Verify real renderer with synthetic journal/source events, then coordinate exact integration/activation and actual live acceptance separately.

## Exact-message controls recovered from native (2026-10-17)
- Native0597a826 iPhone54 menu: Copy, Hand This Message to Hub, Draft Reply to This Message.
- Right-click, long press, and keyboard access must act on the selected message, not the newest item in its conversation.
- Work prefills the Hub composer with the selected quote; it never sends automatically or discards a reply draft.
- Historical Draft uses the native ask protocol: original source post plus trusted thread-post location, provider message id, sender and time. Display row ids are never collector ids.
- Rebinding, navigation and dismissal cannot apply an old menu to a different message. Copy tests use an isolated fake clipboard.
- Render phone/tablet/desktop in actual light/dark themes and retain normal scrolling, text selection and keyboard focus.

## Native send options (recovered 2026-10-18)
- Pinned Mac menu-inbox-send-options and iPhone34 expose five controls: Send now, remembered Send and Archive, next contact working start, custom later, Weekends Too. Reuse native placement and order; whole menu must remain reachable with the keyboard open.
- Weekends Too reads the trusted collector configuration for this exact contact, not an optimistic local toggle. Changing it requires the current target and correlated collector capability; HTTP acceptance is not confirmation. Persist original id/contact/target/rid/value before sending and use the same request for explicit retry after reload.
- Wrong receipts, revoked capabilities, stale controls and changed destinations cannot mutate a replacement conversation. Preserve newer reply drafts. Unknown or refused setting changes stay visible.
- Native Send and Archive and its remembered default remain a separate unfinished requirement.

## Native context and action comparison (2026-10-18)
- Pinned0597a826 Letter.origin renders provider plus distinct supplied place once. Teams DM must not read “Teams · Личка · Личка”; Telegram must not repeat its own name.
- Shared row actions use one icon size at each layout width: existing22px labelled and28px compact. Keep44px targets. Verify360–1440 including tablet single-pane widths.
- Pinned native reset feed at402×874 and1240×780 is the content baseline. Preserve mock photo bytes through a same-origin blob URL when capturing actual live static UI with intercepted APIs. Compare both themes; fixture parity alone is not pixel parity.
