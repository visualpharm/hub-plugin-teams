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
        for width in (390, 768, 834, 1024, 1280, 1440):
            with self.subTest(width=width):
                got = self.page({"shot": str(Path(self.state) / f"detail-{width}.png"), "width": width, "height": 900},
                                {"eval": "({root:document.querySelector('.tm-container').clientWidth,detail:document.querySelector('.tm-detail').clientWidth,list:getComputedStyle(document.querySelector('.tm-list-pane')).display,overflow:document.documentElement.scrollWidth-innerWidth})"})
                row = got[-1]["eval"]
                single = row["root"] <= 900
                self.assertEqual(row["list"], "none" if single else "flex", row)
                self.assertGreaterEqual(row["detail"], row["root"] - 1 if single else 560, row)
                self.assertEqual(row["overflow"], 0, row)
        self.shot("tablet-detail")

    def test_actions_and_source_link_stay_above_reply_at_every_width(self):
        self.seed_inbox(start_editing=False)
        for width,theme in ((390,"light"),(834,"light"),(1240,"light"),(390,"dark"),(1240,"dark")):
            got=self.page({"media":theme},{"viewport":{"width":width,"height":844}}, {"eval":"(()=>{const a=document.querySelector('.tm-thread > .tm-acts').getBoundingClientRect(),c=document.querySelector('.tm-shared-compose .composer').getBoundingClientRect();return {scheme:getComputedStyle(document.documentElement).colorScheme,actions:a.bottom,composer:c.top,footer:c.bottom,overflow:document.documentElement.scrollWidth-innerWidth}})()"})[-1]["eval"]
            self.assertEqual(got["scheme"],theme,got)
            self.assertLessEqual(got["actions"],got["composer"],got)
            self.assertLessEqual(got["footer"],844,got)
            self.assertEqual(got["overflow"],0,got)
            if os.environ.get("HUB_INBOX_SCREENSHOTS"):
                out=Path(os.environ["HUB_INBOX_SCREENSHOTS"]);out.mkdir(parents=True,exist_ok=True)
                self.page({"media":theme},{"shot":str(out/f"actions-{theme}-{width}.png"),"width":width,"height":844})
        link=self.page({"eval":"({href:document.querySelector('.tm-thread > .tm-head .tm-link')?.href,label:document.querySelector('.tm-thread > .tm-head .tm-link')?.getAttribute('aria-label'),actions:[...document.querySelectorAll('.tm-thread > .tm-acts .tm-action')].map(b=>b.getAttribute('aria-label'))})"})[-1]["eval"]
        self.assertEqual(link["href"],"https://teams.microsoft.com/l/message/synthetic-source-a",link)
        self.assertEqual(link["label"],"Open in Teams",link)
        self.assertEqual(link["actions"],["Скрыть сообщения Review colleague","React to Review colleague","Черновик ответа для Review colleague","В работу: сообщение Review colleague"],link)

    def test_reaction_targets_exact_message_and_keeps_draft_on_refusal(self):
        self.seed_inbox(start_editing=False)
        self.edit("Keep my unsent reply"); self.acknowledge(self.queued("draft_control"))
        self.page({"tapSelector":".tm-react-trigger"},{"until":"document.querySelectorAll('.tm-reactions button').length===7"})
        for width,theme in ((360,"light"),(390,"dark"),(1240,"light"),(1240,"dark")):
            steps=[{"media":theme},{"viewport":{"width":width,"height":844}}]
            if os.environ.get("HUB_INBOX_SCREENSHOTS"):
                steps.append({"shot":str(Path(os.environ["HUB_INBOX_SCREENSHOTS"])/f"picker-{theme}-{width}.png"),"width":width,"height":844})
            steps.append({"eval":"({overflow:document.documentElement.scrollWidth-innerWidth,buttons:[...document.querySelectorAll('.tm-reactions button')].map(b=>{const r=b.getBoundingClientRect();return {w:r.width,h:r.height,right:r.right}})})"})
            got=self.page(*steps)[-1]["eval"]
            self.assertEqual(got["overflow"],0,got)
            for b in got["buttons"]:
                self.assertGreaterEqual(b["w"],44,b);self.assertGreaterEqual(b["h"],44,b);self.assertLessEqual(b["right"],width,b)
        self.page({"tapSelector":".tm-reactions button:first-child"},{"wait":"Sending reaction"})
        request=self.queued("react")
        self.assertEqual(request["id"],"source-a");self.assertEqual(request["emoji"],"👍")
        self.feed({"kind":"reacted","id":"other-source","rid":request["rid"],"emoji":"👍"})
        self.page({"sleep":250})
        self.assertIn("Sending reaction",self.page({"eval":"document.querySelector('.tm-reaction-status').textContent"})[-1]["eval"])
        self.feed({"kind":"react_failed","id":"source-a","rid":request["rid"],"error":"Synthetic reaction refused"})
        self.page({"wait":"Synthetic reaction refused"})
        self.assertEqual(self.page({"eval":"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]["eval"],"Keep my unsent reply")
        self.page({"tapSelector":".tm-react-trigger"},{"tapSelector":".tm-reactions button:nth-child(2)"})
        retry=self.queued("react");self.assertNotEqual(retry["rid"],request["rid"])
        self.feed({"kind":"reacted","id":"source-a","rid":retry["rid"],"emoji":"❤️"})
        self.page({"wait":"Reaction sent"})
        self.feed({"kind":"answered","id":"source-a"})
        self.page({"click":"Разобранные"},{"until":"!!document.querySelector('.tm-person')"},{"tapSelector":".tm-person"})
        self.assertEqual(self.page({"eval":"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]["eval"],"Keep my unsent reply")
        self.shot("reaction-confirmed-draft-retained")
        self.page({"go":f"http://127.0.0.1:{self.port}/#/x/inbox"},{"click":"Разобранные"},
                  {"until":"!!document.querySelector('.tm-person')"},{"tapSelector":".tm-person"},{"wait":"Reaction sent"})
        self.assertIn("❤️",self.page({"eval":"document.querySelector('.tm-reaction-status').textContent"})[-1]["eval"])

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
                   "text": "Please check the navigation.", "react": True, "link": "https://teams.microsoft.com/l/message/synthetic-source-a", "at": datetime.now(timezone.utc).isoformat(), "reply": True, "inbox": self.token})
        self.page({"go": f"http://127.0.0.1:{self.port}/#/x/inbox"}, {"until": "!!document.querySelector('.tm-person')"},
                  {"eval": "document.querySelector('.tm-person').click();true"},
                  {"eval": "document.querySelector('[aria-label=\"Ответить: Review colleague\"]').click();true"})

        if start_editing:
            self.edit("")

    def test_open_and_generated_fill_do_not_hold_until_owner_input(self):
        self.seed_inbox(start_editing=False)
        got = self.page({"eval": "document.querySelector('.tm-shared-compose .composer textarea').value"})
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
