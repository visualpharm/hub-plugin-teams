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
