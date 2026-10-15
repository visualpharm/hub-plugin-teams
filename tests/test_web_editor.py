"""Real web renderer + isolated journal. No collector/account/provider send."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import unittest
from unittest import mock
from tests.test_web_e2e import PageInChrome


class InboxWebAcceptance(PageInChrome):
    def test_tablet_detail_uses_the_available_content_width(self):
        self.seed_inbox(); self.queued("draft_control")
        got = self.page({"shot": str(Path(self.state) / "tablet-detail.png"), "width": 834, "height": 900},
                        {"eval": "({detail:document.querySelector('.tm-detail').clientWidth,list:getComputedStyle(document.querySelector('.tm-list-pane')).display,overflow:document.documentElement.scrollWidth-innerWidth})"})
        row = got[-1]["eval"]
        self.assertGreaterEqual(row["detail"], 440, row)
        self.assertEqual(row["list"], "none", row)
        self.assertEqual(row["overflow"], 0, row)
        self.shot("tablet-detail")

    def test_whole_inbox_instruction_preserves_exact_text_and_is_dispatch_only(self):
        self.seed_inbox()
        self.queued("draft_control")
        raw = "  Review every open conversation.\nKeep unresolved deadlines.  "
        self.page({"eval": "document.querySelector('.tm-close-conversation').click();true"},
                  {"eval": "(()=>{const t=document.querySelector('.tm-whole-prompt textarea');t.value=" + json.dumps(raw) + ";t.dispatchEvent(new Event('input',{bubbles:true}));t.closest('form').requestSubmit();return true})()"})
        q = self.queued("manage")
        self.assertEqual(q["text"], raw)
        self.feed({"kind": "manage_asked", "rid": q["rid"], "coverage": {"scope": "collector-known-open", "upstream_exhaustive": False}})
        self.page({"wait": "Instruction sent for review."})
        self.assertFalse([e for e in self.spooled() if e["type"] == "message.received"])

    def test_long_history_keeps_the_reply_visible_and_same_target(self):
        self.seed_inbox(); request = self.queued("draft_control"); self.acknowledge(request)
        for n in range(16):
            self.feed({"kind": "msg", "id": "history-" + str(n), "contact": "synthetic-account/conversation-a", "src": "dm", "from": "Review colleague",
                       "text": "Specific source detail. " * 20, "at": datetime.now(timezone.utc).isoformat(), "reply": True})
        got = self.page({"until": "document.querySelectorAll('.tm-detail .tm-line').length===17"},
                        {"shot": str(Path(self.state) / "long-history.png"), "width": 390, "height": 844},
                        {"eval": "(()=>{const r=document.querySelector('.tm-shared-compose .composer').getBoundingClientRect(),h=document.querySelector('.tm-detail .tm-history');return {bottom:r.bottom,top:r.top,scroll:h.scrollHeight>h.clientHeight,target:document.querySelector('.tm-shared-compose .composer textarea').dataset.compose,overflow:document.documentElement.scrollWidth-innerWidth}})()"})
        self.assertTrue(got[0]["until"], got)
        row = got[-1]["eval"]
        self.assertLessEqual(row["bottom"], 844, row); self.assertGreater(row["top"], 0, row)
        self.assertTrue(row["scroll"], row); self.assertEqual(row["target"], "source-a"); self.assertEqual(row["overflow"], 0)
        self.shot("long-history-reply-phone")

    def test_only_the_matching_receipt_closes_the_editor_and_retrieves_sent_detail(self):
        self.seed_inbox(); self.acknowledge(self.queued("draft_control")); self.edit("Owner approved reply")
        self.page({"eval": "document.querySelector('.tm-shared-compose .composer').requestSubmit();true"})
        q = self.queued("send")
        self.feed({"kind": "sent", "id": "source-a", "rid": q["rid"], "submitted_inbox": {**self.token, "version": "other"},
                   "inbox": self.token, "receipt": {"id": "wrong-version-receipt"}})
        got = self.page({"sleep": 400}, {"eval": "!!document.querySelector('.tm-shared-compose textarea')"})
        self.assertTrue(got[-1]["eval"])
        self.feed({"kind": "sent", "id": "source-a", "rid": q["rid"], "submitted_inbox": self.token,
                   "inbox": {**self.token, "held": False, "holder": None, "edit_version": 2}, "receipt": {"id": "synthetic-confirmed-receipt"}})
        got = self.page({"until": "!document.querySelector('.tm-shared-compose textarea')"}, {"click": "Разобранные"},
                        {"until": "!!document.querySelector('.tm-person')"}, {"eval": "document.querySelector('.tm-person').click();true"},
                        {"until": "!!document.querySelector('.tm-mine-ok')"},
                        {"eval": "document.querySelector('.tm-mine-ok')?.textContent"})
        self.assertTrue(got[-2]["until"], got); self.assertIn("Owner approved reply", got[-1]["eval"])
        self.shot("confirmed-sent-detail-phone")

    def feed(self, data):
        self.ev("ext.post", None, plugin="teams", channel="plugin", sender="teams", text=json.dumps(data))

    def seed_inbox(self, start_editing=True):
        cfg = Path(self.state) / "inbox.json"
        cfg.write_text(json.dumps({"extensions": {"teams": {"path": str(Path(__file__).resolve().parents[1]), "web": "web/main.js"}}}))
        env = mock.patch.dict(os.environ, {"HUB_CONFIG": str(cfg)}); env.start(); self.addCleanup(env.stop)
        self.ev("session.requested", "hub", session_id="s-hub", cwd="/workspace", kind="hub", channel="cli", owner=True)
        self.ev("session.started", "hub", session_id="s-hub")
        self.token = {"v": 1, "version": "synthetic-source-A", "edit_version": 0, "held": False, "holder": None}
        self.feed({"kind": "config", "inbox_protocol": {"version": 1, "editor_cas": True}})
        self.feed({"kind": "msg", "id": "source-a", "contact": "synthetic-account/conversation-a", "src": "dm", "from": "Review colleague",
                   "text": "Please check the navigation.", "at": datetime.now(timezone.utc).isoformat(), "reply": True, "inbox": self.token})
        self.page({"go": f"http://127.0.0.1:{self.port}/#/x/inbox"}, {"until": "!!document.querySelector('.tm-person')"},
                  {"eval": "document.querySelector('.tm-person').click();true"},
                  {"eval": "document.querySelector('[aria-label=\"Ответить: Review colleague\"]').click();true"})

        if start_editing:
            self.edit("")

    def test_open_and_generated_fill_do_not_hold_until_owner_input(self):
        self.seed_inbox(start_editing=False)
        got = self.page({"eval": "document.querySelector('.tm-shared-compose textarea').value"})
        self.assertEqual(got[-1]["eval"], "")
        self.assertFalse([e for e in self.spooled() if e["type"] == "ext.post"])
        self.page({"click": "Close editor"}, {"until": "!document.querySelector('.tm-shared-compose textarea')"})
        self.assertFalse([e for e in self.spooled() if e["type"] == "ext.post"])
        self.page({"eval": "document.querySelector('[aria-label=\"Ответить: Review colleague\"]').click();document.querySelector('.tm-instruction summary').click();true"},
                  {"eval": "(()=>{const t=document.querySelector('.tm-instruction textarea');t.value='Keep my wording';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"})
        self.acknowledge(self.queued("draft_control"))
        self.edit("Intentional owner reply")
        self.edit("")
        self.assertFalse([e for e in self.spooled() if e["type"] == "ext.post"])

    def queued(self, kind):
        posts = [json.loads(e["data"]["text"]) for e in self.spooled() if e["type"] == "ext.post"]
        found = [p for p in posts if p.get("kind") == kind]
        self.assertEqual(len(found), 1, posts)
        return found[0]

    def acknowledge(self, q):
        self.token = {**self.token, "edit_version": self.token["edit_version"] + 1, "held": True, "holder": q["editor"]}
        self.feed({"kind": "draft_state", "id": "source-a", "rid": q["rid"], "inbox": self.token})
        got = self.page({"until": "document.querySelector('.tm-shared-compose .tm-editor-feedback')?.hidden===true"})
        self.assertTrue(got[-1]["until"], got)

    def edit(self, text):
        return self.page({"eval": "(()=>{const t=document.querySelector('.tm-shared-compose .composer textarea');t.value=" + json.dumps(text) + ";t.dispatchEvent(new Event('input',{bubbles:true}));return t.value})()"})

    def shot(self, name):
        if os.environ.get("HUB_INBOX_SCREENSHOTS"):
            out = Path(os.environ["HUB_INBOX_SCREENSHOTS"]); out.mkdir(parents=True, exist_ok=True)
            self.page({"shot": str(out / (name + ".png")), "width": 390, "height": 844})

    def test_private_proposal_is_explicit_and_delivery_stays_truthful(self):
        self.seed_inbox()
        self.acknowledge(self.queued("draft_control"))
        self.edit("Owner exact edit")
        self.page({"eval": "document.querySelector('.tm-instruction summary').click();true"})
        self.page({"eval": "(()=>{const t=document.querySelector('.tm-instruction textarea');t.value='Suggest 11 instead.';t.dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('.tm-instruction .btn').click();return true})()"})
        request = self.queued("ask")
        self.assertEqual(request["draft"], "Owner exact edit")
        self.assertEqual(request["instruction"], "Suggest 11 instead.")
        self.acknowledge(request)
        proposal = {"kind": "draft_proposal", "id": "source-a", "post": request["post"], "rid": request["rid"],
                    "editor": request["editor"], "inbox": self.token, "text": "Could we meet at 11?", "context": "The time changed.",
                    "next_action": "Review the reply.", "requires_apply": True}
        self.feed(proposal)
        self.page({"wait": "Apply draft"})
        got = self.page({"shot": str(Path(self.state) / "proposal-fit.png"), "width": 390, "height": 844},
                        {"eval": "(()=>{const b=document.querySelector('.tm-proposal button'),r=b.getBoundingClientRect();return {visible:r.top>=0&&r.bottom<=innerHeight&&document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===b,replyBottom:document.querySelector('.tm-shared-compose .composer').getBoundingClientRect().bottom}})()"})
        self.assertTrue(got[-1]["eval"]["visible"], got)
        self.assertLessEqual(got[-1]["eval"]["replyBottom"], 844, got)
        got = self.page({"eval": "document.querySelector('.tm-shared-compose .composer textarea').value"})
        self.assertEqual(got[-1]["eval"], "Owner exact edit")
        self.edit("Newer owner edit")
        got = self.page({"click": "Apply draft"}, {"wait": "Your reply or instruction changed"},
                        {"eval": "document.querySelector('.tm-shared-compose .composer textarea').value"})
        self.assertEqual(got[-1]["eval"], "Newer owner edit")
        self.page({"click": "Revise draft"})
        request = self.queued("ask"); self.acknowledge(request)
        self.feed({**proposal, "rid": request["rid"], "inbox": self.token})
        got = self.page({"until": "document.querySelector('.tm-proposal')?.dataset.rid===" + json.dumps(request["rid"])},
                        {"click": "Apply draft"},
                        {"until": "document.querySelector('.tm-shared-compose .composer textarea')?.value==='Could we meet at 11?'"})
        self.assertTrue(got[-1]["until"], got)
        self.shot("applied-draft-phone")
        self.page({"eval": "document.querySelector('.tm-shared-compose .composer').requestSubmit();true"})
        send = self.queued("send")
        self.assertEqual(send["text"], "Could we meet at 11?")
        self.assertNotIn("instruction", send)
        self.page({"until": "document.querySelector('.tm-shared-compose .composer textarea')?.value==='Could we meet at 11?'"})
        self.feed({"kind": "sent", "id": "source-a", "rid": send["rid"], "submitted_inbox": self.token, "inbox": self.token})
        self.page({"sleep": 400})
        got = self.page({"eval": "!!document.querySelector('.tm-shared-compose .composer textarea')"})
        self.assertTrue(got[-1]["eval"], "Missing receipt must not close the editor")
        self.feed({"kind": "send_uncertain", "id": "source-a", "rid": send["rid"], "inbox": self.token, "error": "Delivery needs reconciliation."})
        self.page({"wait": "Delivery needs reconciliation."})
        self.shot("uncertain-draft-retained-phone")
        self.assertFalse([e for e in self.spooled() if e["type"] == "message.received"])


def load_tests(loader, suite, pattern):
    return unittest.TestSuite(InboxWebAcceptance(n) for n in InboxWebAcceptance.__dict__ if n.startswith("test_"))
