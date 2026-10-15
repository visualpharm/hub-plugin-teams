---
title: Shared Inbox delivery and private revision binding
scope: repo
area: inbox
tags: [delivery, revision, identity]
created: 2026-10-15
status: active
---

## Problem
Different manual/automatic request IDs could submit the same source version;
private instructions and empty edits were dropped, and empty success looked Sent.

## Root cause
Request-ID deduplication had no canonical version/editor claim. Raw assistant output
and transport exit success lacked source-bound completion evidence.

## Solution
The one collector writer persists a source/account/conversation claim before IO.
Versioned editor holds persist across restart. Check the actual account/source
immediately before transport; require a real message ID. Unknown outcomes stay held.
Bind private proposals to canonical Hub generation, request nonce, source and editor;
publish a plugin-authored explicit-Apply proposal, never an unsafe raw replacement.

## How to apply
Use docs/inbox-management.md and the full offline local gate. Keep guard disabled
until every active client adopts it. Mocked receipts prove code behavior, not live
delivery. Unsupported adapters and incomplete canonical coverage remain explicit.
