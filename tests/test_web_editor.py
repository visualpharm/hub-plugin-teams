"""Real web renderer + isolated journal. No collector/account/provider send."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import unittest
from unittest import mock
from tests.test_web_e2e import PageInChrome


class InboxWebAcceptance(PageInChrome):
    def test_unsent_reply_survives_reload_and_stays_with_exact_source(self):
        self.seed_inbox();self.acknowledge(self.queued('draft_control'));self.edit('Exact unsent reply after reload')
        self.page({'go':'about:blank'},{'until':"location.href==='about:blank' && document.readyState==='complete'"},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"!!document.querySelector('.tm-person')"},{'tapSelector':'.tm-person'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],'Exact unsent reply after reload')
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])
        self.feed({'kind':'msg','id':'source-a','contact':'different-account/conversation-b','src':'dm','from':'Review colleague','text':'Same name, different account','reply':True,'inbox':self.token,'at':datetime.now(timezone.utc).isoformat()})
        self.page({'until':"document.querySelector('.tm-list').textContent.includes('Same name, different account')"},{'go':'about:blank'},{'until':"location.href==='about:blank' && document.readyState==='complete'"},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"document.querySelector('.tm-list')?.textContent.includes('Same name, different account')"},{'tapSelector':'.tm-person'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],'')

    def test_delivery_receipt_cannot_erase_a_newer_draft_even_after_reload(self):
        self.seed_inbox();self.acknowledge(self.queued('draft_control'));self.edit('First approved reply')
        self.page({'eval':"document.querySelector('.tm-shared-compose .composer').requestSubmit();true"})
        q=self.queued('send');self.edit('Newer reply still being written')
        self.feed({'kind':'sent','id':'source-a','rid':q['rid'],'submitted_inbox':self.token,
                   'inbox':{**self.token,'held':False,'holder':None,'edit_version':2},'receipt':{'id':'accepted-first'}})
        self.page({'until':"document.querySelector('.tm-mine-ok')?.textContent.includes('First approved reply')"})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],'Newer reply still being written')
        self.page({'go':'about:blank'},{'until':"location.href==='about:blank' && document.readyState==='complete'"},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"!!document.querySelector('.tm-person')"},{'tapSelector':'.tm-person'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],'Newer reply still being written')
        sends=[json.loads(e['data']['text']) for e in self.non_history_actions() if e['type']=='ext.post' and json.loads(e['data']['text']).get('kind')=='send']
        self.assertEqual(sends,[], 'The original request was consumed by queued(); reload must not send another.')

    def test_blocked_draft_storage_is_visible_without_losing_current_text(self):
        self.seed_inbox(start_editing=False)
        self.page({'eval':"Storage.prototype.setItem=function(){throw new DOMException('Blocked','QuotaExceededError')};true"})
        self.edit('Keep this page text')
        self.page({'wait':'This browser could not save the draft.'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],'Keep this page text')

    def test_narrow_conversation_has_one_header_and_keeps_draft_when_returning(self):
        self.seed_inbox(start_editing=False)
        self.edit("Keep my exact draft")
        self.acknowledge(self.queued("draft_control"))
        for width in (360,402,834,992):
            got=self.page({"viewport":{"width":width,"height":874}},{"sleep":100},
              {"eval":"(()=>{const header=document.querySelector('.view-nav'),h=document.querySelector('.tm-thread > .tm-head'),back=document.querySelector('.tm-close-conversation');return {outer:header.getBoundingClientRect().height,top:h.getBoundingClientRect().top,back:back.getBoundingClientRect().width,overflow:document.documentElement.scrollWidth-innerWidth}})()"})[-1]['eval']
            self.assertEqual(got['outer'],0,got);self.assertLess(got['top'],30,got);self.assertGreaterEqual(got['back'],44,got);self.assertEqual(got['overflow'],0,got)
        self.page({"tapSelector":".tm-close-conversation"})
        self.assertGreater(self.page({"eval":"document.querySelector('.view-nav').getBoundingClientRect().height"})[-1]['eval'],0)
        self.page({"tapSelector":".tm-person"})
        self.assertEqual(self.page({"eval":"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],"Keep my exact draft")
        self.assertTrue(self.page({"eval":"!!document.querySelector(\'.tm-editor-options use[href=\"/static/icons.svg#i-menu\"]\')"})[-1]["eval"])
        self.page({"tapSelector":".tm-editor-options > summary"})
        self.assertTrue(self.page({"eval":"document.querySelector('.tm-editor-options').open"})[-1]['eval'])
        self.page({"key":"Escape"})
        self.assertFalse(self.page({"eval":"document.querySelector('.tm-editor-options').open"})[-1]['eval'])
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])

    def test_short_history_stacks_above_actions_and_own_links_stay_readable(self):
        self.seed_inbox(start_editing=False)
        self.feed({"kind":"thread","id":"source-a","part":0,"of":1,"more":False,"items":[
            {"id":"own-link","me":True,"at":"2026-01-01T12:00:00Z","text":"See https://example.test/meeting"}]})
        self.page({"until":"!document.querySelector('.tm-earlier').disabled"},{"tapSelector":".tm-earlier"})
        for width,theme in ((360,"light"),(402,"dark"),(1440,"light")):
            got=self.page({"media":theme},{"viewport":{"width":width,"height":874}},
                {"eval":"""(()=>{const h=document.querySelector('.tm-history'),last=h.lastElementChild,a=document.querySelector('.tm-own .tm-text a'),bubble=a.closest('.tm-text');return {
                  gap:h.getBoundingClientRect().bottom-last.getBoundingClientRect().bottom,
                  foreground:getComputedStyle(a).color,background:getComputedStyle(bubble).backgroundColor,
                  overflow:document.documentElement.scrollWidth-innerWidth};})()"""})[-1]['eval']
            self.assertLessEqual(got['gap'],2,got)
            self.assertNotEqual(got['foreground'],got['background'],got)
            self.assertEqual(got['overflow'],0,got)
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])

    def test_native_sort_uses_highest_conversation_priority_and_persists_choice(self):
        self.seed_inbox(start_editing=False)
        self.page({"tapSelector":".tm-close-conversation"})
        self.feed({"kind":"msg","id":"source-b","contact":"synthetic-account/conversation-b","src":"email","from":"Older important","text":"Review invoice","at":"2026-01-01T12:00:00Z","reply":True})
        self.feed({"kind":"msg","id":"source-b-new","contact":"synthetic-account/conversation-b","src":"email","from":"Older important","text":"Later neutral reply","at":"2026-01-02T12:00:00Z","reply":True})
        self.page({"until":"document.querySelectorAll('.tm-person').length===2"})
        post=self.page({"eval":"fetch('/api/feed?plugin=teams').then(r=>r.json()).then(x=>x.posts.find(p=>{try{return JSON.parse(p.text).id==='source-b'}catch{return false}}).id)"})[-1]['eval']
        self.page({"eval":"(()=>{const real=fetch;window.__rankFail=true;window.fetch=(u,o)=>String(u).startsWith('/api/feed?plugin=proactivity')&&__rankFail?Promise.resolve(new Response('{}',{status:503})):real(u,o);return true})()"})
        self.ev("ext.post",None,plugin="proactivity",channel="session",sender="hub",text=json.dumps({"kind":"item","post":post,"s":"escalated","urgent":True,"risk":["money"]}))
        self.page({"wait":"Importance could not be updated."},{"eval":"window.__rankFail=false"},{"click":"Retry importance"})
        got=self.page({"until":"document.querySelector('.tm-person')?.textContent.includes('Older important')"})
        self.assertTrue(got[-1]['until'],got)
        self.page({"tapSelector":".tm-sort summary"},{"tapSelector":"[data-sort=time]"})
        self.assertIn("Review colleague",self.page({"eval":"document.querySelector('.tm-person').textContent"})[-1]['eval'])
        self.page({"go":f"http://127.0.0.1:{self.port}/#/x/inbox"},{"until":"!!document.querySelector('.tm-person')"},{"tapSelector":".tm-sort summary"})
        self.assertEqual(self.page({"eval":"document.querySelector('[data-sort=time]').getAttribute('aria-checked')"})[-1]['eval'],'true')
        self.page({"tapSelector":"[data-sort=importance]"},{"until":"document.querySelector('.tm-person').textContent.includes('Older important')"})
        for width,theme in ((360,"light"),(402,"dark"),(834,"light"),(1440,"dark")):
            got=self.page({"media":theme},{"viewport":{"width":width,"height":874}},{"tapSelector":".tm-sort summary"},
                          {"eval":"(()=>{const s=document.querySelector('.tm-sort summary').getBoundingClientRect(),m=document.querySelector('.tm-sort-choices').getBoundingClientRect();return {target:s.height,left:m.left,right:m.right,overflow:document.documentElement.scrollWidth-innerWidth}})()"})[-1]['eval']
            self.assertGreaterEqual(got['target'],44);self.assertGreaterEqual(got['left'],0);self.assertLessEqual(got['right'],width);self.assertEqual(got['overflow'],0)
            if os.environ.get("HUB_INBOX_SCREENSHOTS"):
                Path(os.environ["HUB_INBOX_SCREENSHOTS"]).mkdir(parents=True,exist_ok=True)
                self.page({"media":theme},{"shot":str(Path(os.environ["HUB_INBOX_SCREENSHOTS"])/f"sort-{theme}-{width}.png"),"width":width,"height":874})
            self.page({"eval":"document.querySelector('.tm-sort summary').focus();true"},{"key":"Escape"})
            self.assertFalse(self.page({"eval":"document.querySelector('.tm-sort').open"})[-1]['eval'])
        self.assertFalse([e for e in self.spooled() if e['type']=='message.received'])

    def test_history_refresh_preserves_reading_position_and_other_conversation(self):
        self.seed_inbox(start_editing=False)
        self.queued("history")
        self.feed({"kind":"thread","id":"source-a","part":0,"of":1,"more":False,"items":[
            {"id":f"old-{i}","at":f"2026-01-01T12:{i:02d}:00Z","text":f"Earlier item {i} with enough text to wrap across the phone screen."} for i in range(10)]})
        self.page({"until":"!document.querySelector('.tm-earlier').disabled"},{"tapSelector":".tm-earlier"},
                  {"eval":"document.querySelector('.tm-history').scrollTop=250"})
        position=self.page({"eval":"document.querySelector('.tm-history').scrollTop"})[-1]['eval']
        self.assertGreater(position,0)
        self.feed({"kind":"msg","id":"source-b","contact":"synthetic-account/conversation-b","src":"dm","from":"Other colleague","text":"Different conversation","at":"2026-01-02T12:00:00Z","reply":True})
        self.page({"until":"document.querySelectorAll('.tm-person').length===2"})
        self.assertAlmostEqual(self.page({"eval":"document.querySelector('.tm-history').scrollTop"})[-1]['eval'],position,delta=1)
        self.page({"tapSelector":".tm-close-conversation"},{"tapSelector":".tm-person:last-child"})
        self.assertEqual(self.queued("history")["id"],"source-b")
        self.feed({"kind":"thread","id":"source-a","part":0,"of":1,"more":False,"items":[{"id":"late-a","text":"Late result for first conversation"}]})
        self.feed({"kind":"thread","id":"source-b","part":0,"of":1,"more":False,"items":[{"id":"old-b","text":"History for second conversation"}]})
        got=self.page({"until":"!document.querySelector('.tm-earlier').disabled"},{"tapSelector":".tm-earlier"},{"eval":"document.querySelector('.tm-history').textContent"})[-1]['eval']
        self.assertIn("History for second conversation",got);self.assertNotIn("Late result for first conversation",got)

    def test_history_chunks_pagination_refusal_and_retry_keep_exact_conversation(self):
        self.seed_inbox(start_editing=False)
        q=self.queued("history");self.assertEqual(q["id"],"source-a")
        self.feed({"kind":"thread","id":"source-a","part":0,"of":2,"more":True,"items":[{"id":"old-1","at":"2026-01-01T12:00:00Z","from":"Review colleague","text":"Historical detail"}]})
        self.page({"sleep":100})
        self.assertNotIn("Historical detail",self.page({"eval":"document.querySelector('.tm-detail').textContent"})[-1]['eval'])
        self.feed({"kind":"thread","id":"source-a","part":1,"of":2,"more":True,"items":[{"id":"old-2","at":"2026-01-02T12:00:00Z","from":"Owner","me":True,"text":"Older reply"},
                    {"at":datetime.now(timezone.utc).isoformat(),"from":"Review colleague","text":"Please check the navigation."}]})
        self.page({"until":"!document.querySelector('.tm-earlier').disabled"},{"tapSelector":".tm-earlier"})
        got=self.page({"eval":"document.querySelector('.tm-history').textContent"})[-1]['eval']
        self.assertIn("Historical detail",got);self.assertIn("Older reply",got);self.assertEqual(got.count("Please check the navigation."),1,got)
        self.edit("Reply survives history retry");self.acknowledge(self.queued("draft_control"))
        self.page({"tapSelector":".tm-earlier"})
        q=self.queued("history");self.assertEqual(q["id"],"source-a");self.assertEqual(q["before"],"old-1")
        self.feed({"kind":"thread_failed","id":"source-a","error":"Synthetic history refused"})
        self.page({"wait":"Synthetic history refused"},{"tapSelector":".tm-earlier"})
        retry=self.queued("history");self.assertEqual(retry["id"],"source-a");self.assertEqual(retry["before"],"old-1")
        self.feed({"kind":"thread","id":"source-a","before":"old-1","part":0,"of":1,"more":False,"items":[
            {"id":"old-0","at":"2025-12-01T12:00:00Z","from":"Review colleague","text":"Earliest detail"},
            {"id":"old-1","at":"2026-01-01T12:00:00Z","from":"Review colleague","text":"Historical detail"}]})
        got=self.page({"wait":"Earliest detail"},{"eval":"({text:document.querySelector('.tm-history').textContent,draft:document.querySelector('.tm-shared-compose .composer textarea').value})"})[-1]['eval']
        self.assertEqual(got['text'].count('Historical detail'),1,got);self.assertEqual(got['draft'],'Reply survives history retry')

    def test_open_conversation_has_reply_without_opening_keyboard_or_holding_editor(self):
        self.seed_inbox(start_editing=False,open_editor=False)
        got=self.page({"eval":"({reply:!!document.querySelector('.tm-shared-compose .composer textarea'),focused:document.activeElement.tagName,extra:!!document.querySelector('[aria-label=\"Ответить: Review colleague\"]')})"})[-1]["eval"]
        self.assertTrue(got["reply"],got);self.assertNotEqual(got["focused"],"TEXTAREA",got);self.assertFalse(got["extra"],got)
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])
        self.edit("Preserved while browsing");self.acknowledge(self.queued("draft_control"))
        self.page({"tapSelector":".tm-close-conversation"},{"tapSelector":".tm-person"})
        self.assertEqual(self.page({"eval":"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],"Preserved while browsing")

    def test_initial_plain_draft_is_selected_without_claiming_editor(self):
        self.seed_inbox(start_editing=False)
        post=self.page({"eval":"fetch('/api/feed?plugin=teams').then(r=>r.json()).then(d=>d.posts.find(p=>{try{return JSON.parse(p.text).id==='source-a'}catch{return false}}).id)"})[-1]['eval']
        self.page({"tapSelector":".tm-editor-options > summary"},{"click":"Close editor"})
        self.ev("ext.post",None,plugin="teams",channel="session",owner=False,sender="hub",reply_to=post,text="Suggested exact reply\n---\nWhy: Keep this explanation separate")
        self.page({"wait":"Suggested exact reply"},{"tapSelector":".tm-close-conversation"},{"tapSelector":".tm-person"})
        got=self.page({"eval":"(()=>{const t=document.querySelector('.tm-shared-compose .composer textarea');t.focus();return {text:t.value,start:t.selectionStart,end:t.selectionEnd}})()"})[-1]['eval']
        self.assertEqual(got,{"text":"Suggested exact reply","start":0,"end":21},got)
        order=self.page({"eval":"(()=>{const g=document.querySelector('.tm-guidance').getBoundingClientRect(),a=document.querySelector('.tm-thread > .tm-acts').getBoundingClientRect();return {guide:g.bottom,actions:a.top,count:document.querySelectorAll('.tm-guidance').length}})()"})[-1]['eval']
        self.assertLessEqual(order['guide'],order['actions'],order);self.assertEqual(order['count'],1)
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])

    def test_native_folders_separate_delivery_archive_and_failure_keep_reply(self):
        self.seed_inbox(); self.acknowledge(self.queued("draft_control")); self.edit("Keep this Inbox reply")
        for mid,name in (("sent-one","Sent colleague"),("archived-one","Archived colleague"),("failed-one","Failed colleague"),("later-one","Scheduled colleague")):
            self.feed({"kind":"msg","id":mid,"contact":"synthetic/"+mid,"src":"dm","from":name,"text":name,"reply":True,"at":datetime.now(timezone.utc).isoformat()})
        def owner(d): self.ev("ext.post",None,plugin="teams",channel="web",owner=True,text=json.dumps(d))
        owner({"kind":"send","id":"sent-one","rid":"sent-r","text":"Delivered reply"})
        self.feed({"kind":"sent","id":"sent-one","rid":"sent-r","receipt":{"id":"receipt-1"}})
        owner({"kind":"hide","ids":["archived-one","later-one"]})
        owner({"kind":"send","id":"later-one","rid":"later-r","text":"Later reply"})
        self.feed({"kind":"scheduled","id":"later-one","rid":"later-r","at":"2030-01-01T12:00:00Z"})
        owner({"kind":"send","id":"failed-one","rid":"failed-r","text":"Failed reply"})
        self.feed({"kind":"send_failed","id":"failed-one","rid":"failed-r","error":"Synthetic refusal"})
        self.page({"tapSelector":".tm-close-conversation"},{"until":"document.querySelectorAll('.tm-person').length===2"})
        self.assertTrue(self.page({"eval":"!!document.querySelector('[aria-label=\"Sent conversations\"]')"})[-1]["eval"])
        for label,names in (("Sent conversations",["Sent colleague","Scheduled colleague"]),("Archived conversations",["Archived colleague","Scheduled colleague"]),("Failed replies",["Failed colleague"])):
            self.page({"tapSelector":f"[aria-label='{label}']"})
            got=self.page({"eval":"[...document.querySelectorAll('.tm-person .tm-from')].map(n=>n.textContent)"})[-1]["eval"]
            self.assertEqual(set(got),set(names),(label,got))
        self.page({"tapSelector":"[aria-label='Inbox conversations'] button[data-folder='new']"})
        self.page({"eval":"[...document.querySelectorAll('.tm-person')].find(n=>n.textContent.includes('Review colleague')).click();true"})
        self.assertEqual(self.page({"eval":"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]["eval"],"Keep this Inbox reply")
        self.page({"tapSelector":".tm-close-conversation"},{"viewport":{"width":402,"height":874}})
        got=self.page({"eval":"({bottom:document.querySelector('.tm-top').getBoundingClientRect().bottom,filterVisible:!!document.querySelector('.tm-srcs').getClientRects().length,overflow:document.documentElement.scrollWidth-innerWidth})"})[-1]["eval"]
        self.assertLess(got["bottom"],155,got);self.assertFalse(got["filterVisible"],got);self.assertEqual(got["overflow"],0,got)
        self.page({"tapSelector":".tm-options summary"})
        self.assertTrue(self.page({"eval":"!!document.querySelector('.tm-srcs').getClientRects().length"})[-1]["eval"])
        self.page({"key":"Escape"})
        self.assertFalse(self.page({"eval":"document.querySelector('.tm-options').open"})[-1]["eval"])

    def test_inbox_media_and_unread_state_survive_navigation_without_source_read(self):
        self.seed_inbox(start_editing=False)
        self.feed({"kind":"msg", "id":"photo-a", "contact":"synthetic/media-a", "src":"whatsapp", "from":"Media colleague", "text":"[media]",
                   "at":datetime.now(timezone.utc).isoformat(), "reply":True, "media":[{"kind":"image","url":"api/file?path=photo.png","name":"Photo.png"},
                    {"kind":"voice","url":"/api/file?path=voice.wav","text":"Voice transcript"}, {"kind":"file","url":"/api/file?path=review.pdf","name":"Review.pdf"}, {"kind":"file","url":"javascript:alert(1)","name":"Unavailable.pdf"}]})
        self.page({"tapSelector":".tm-close-conversation"}, {"until":"document.querySelectorAll('.tm-person').length===2"})
        got=self.page({"eval":"({thumb:!!document.querySelector('.tm-person img'),unread:document.querySelectorAll('.tm-person .tm-unread').length,raw:document.querySelector('.tm-list').textContent.includes('[media]')})"})[-1]["eval"]
        self.assertTrue(got["thumb"],got);self.assertEqual(got["unread"],1,got);self.assertFalse(got["raw"],got)
        self.page({"tapSelector":".tm-person:first-child"},{"until":"!!document.querySelector('.tm-media img')"})
        got=self.page({"eval":"({audio:document.querySelector('.tm-media audio')?.getAttribute('src'),unsafe:!!document.querySelector('[src^=\"javascript:\"],[href^=\"javascript:\"]'),unavailable:document.querySelector('.tm-media').textContent})"})[-1]["eval"]
        self.assertEqual(got["audio"],f"http://127.0.0.1:{self.port}/api/file?path=voice.wav");self.assertFalse(got["unsafe"]);self.assertIn("Unavailable.pdf",got["unavailable"])
        link=self.page({"eval":"(()=>{const a=document.querySelector('.tm-media-file'),s=getComputedStyle(a);return {color:s.color,decoration:s.textDecorationLine}})()"})[-1]['eval']
        self.assertEqual(link['color'],'rgb(10, 132, 255)',link);self.assertEqual(link['decoration'],'none',link)
        self.page({"tapSelector":".tm-media .tm-photo"},{"until":"!!document.querySelector('.lightbox:not([hidden])')"})
        self.assertFalse(self.page({"eval":"!!document.querySelector('.lightbox textarea')"})[-1]["eval"])
        self.page({"tapSelector":".lb-close"},{"tapSelector":".tm-close-conversation"})
        self.assertEqual(self.page({"eval":"document.querySelectorAll('.tm-unread').length"})[-1]["eval"],0)
        self.assertFalse([e for e in self.non_history_actions() if e["type"] in ("ext.post","message.received")], "Opening media must not send a read receipt or message")

    def test_conversation_search_retains_history_target_and_unsent_reply(self):
        self.seed_inbox(); self.acknowledge(self.queued("draft_control")); self.edit("Unsent exact reply")
        self.feed({"kind":"msg", "id":"older-a", "contact":"synthetic-account/conversation-a", "src":"dm", "from":"Review colleague",
                   "text":"Old telescope discussion", "at":"2026-01-01T12:00:00Z", "reply":True})
        self.feed({"kind":"msg", "id":"source-b", "contact":"synthetic-account/conversation-b", "src":"dm", "from":"Review colleague",
                   "text":"Different conversation", "at":"2026-01-02T12:00:00Z", "reply":True})
        self.page({"tapSelector":".tm-close-conversation"}, {"until":"document.querySelectorAll('.tm-person').length===2"})
        self.assertTrue(self.page({"eval":"!!document.querySelector('input[aria-label=\"Search conversations\"]')"})[-1]["eval"])
        def search(value):
            return self.page({"eval":"(()=>{const s=document.querySelector('.tm-conversation-search input');s.value="+json.dumps(value)+";s.dispatchEvent(new Event('input',{bubbles:true}));return true})()"})
        search("TELESCOPE")
        got=self.page({"until":"document.querySelectorAll('.tm-person').length===1"}, {"tapSelector":".tm-person"},
                      {"eval":"({count:document.querySelectorAll('.tm-detail .tm-line').length,text:document.querySelector('.tm-detail .tm-history').textContent,draft:document.querySelector('.tm-shared-compose .composer textarea').value})"})[-1]["eval"]
        self.assertEqual(got["count"],2,got); self.assertIn("Please check the navigation",got["text"]); self.assertEqual(got["draft"],"Unsent exact reply")
        self.page({"viewport":{"width":1440,"height":900}})
        search("no possible match")
        self.page({"wait":"No matching conversations"})
        self.assertEqual(self.page({"eval":"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]["eval"],"Unsent exact reply")
        self.page({"tapSelector":"[aria-label='Clear conversation search']"},{"until":"document.querySelectorAll('.tm-person').length===2"})
        self.assertEqual(self.page({"eval":"document.activeElement.getAttribute('aria-label')"})[-1]["eval"],"Search conversations")
        self.page({"tapSelector":".tm-close-conversation"})
        for width,theme in ((360,"light"),(402,"dark"),(834,"light"),(1440,"dark")):
            got=self.page({"media":theme},{"viewport":{"width":width,"height":874}}, {"eval":"(()=>{const r=document.querySelector('.tm-conversation-search').getBoundingClientRect(),p=document.querySelector('.tm-person').getBoundingClientRect();return {bottom:r.bottom,height:r.height,row:p.height,overflow:document.documentElement.scrollWidth-innerWidth}})()"})[-1]["eval"]
            self.assertLessEqual(got["bottom"],874,got);self.assertGreaterEqual(got["height"],44,got);self.assertGreaterEqual(got["row"],44,got);self.assertEqual(got["overflow"],0,got)
            if os.environ.get("HUB_INBOX_SCREENSHOTS"):
                self.page({"media":theme},{"shot":str(Path(os.environ["HUB_INBOX_SCREENSHOTS"])/f"list-{theme}-{width}.png"),"width":width,"height":874})

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
        self.page({"tapSelector":"[aria-label='Sent conversations']"},{"until":"!!document.querySelector('.tm-person')"},{"tapSelector":".tm-person"})
        self.assertEqual(self.page({"eval":"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]["eval"],"Keep my unsent reply")
        got=self.page({"eval":"({attached:!!document.querySelector('.tm-line .tm-reaction-status'),notice:document.querySelector('.tm-note')?.textContent||''})"})[-1]["eval"]
        self.assertTrue(got["attached"],got)
        self.assertNotIn("Вы ответили",got["notice"])
        self.shot("reaction-confirmed-draft-retained")
        self.page({"go":f"http://127.0.0.1:{self.port}/#/x/inbox"},{"until":"!!document.querySelector('[aria-label=\"Sent conversations\"]')"},{"tapSelector":"[aria-label='Sent conversations']"},
                  {"until":"!!document.querySelector('.tm-person')"},{"tapSelector":".tm-person"},{"wait":"Reaction sent"})
        self.assertIn("❤️",self.page({"eval":"document.querySelector('.tm-reaction-status').textContent"})[-1]["eval"])

    def test_whole_inbox_instruction_preserves_exact_text_and_is_dispatch_only(self):
        self.seed_inbox()
        self.queued("draft_control")
        raw = "  Review every open conversation.\nKeep unresolved deadlines.  "
        self.page({"tapSelector": ".tm-close-conversation"},{"tapSelector":".tm-options summary"},
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
        got = self.page({"until": "!document.querySelector('.tm-shared-compose textarea')"}, {"tapSelector": "[aria-label='Sent conversations']"},
                        {"until": "!!document.querySelector('.tm-person')"}, {"eval": "document.querySelector('.tm-person').click();true"},
                        {"until": "!!document.querySelector('.tm-mine-ok')"},
                        {"eval": "document.querySelector('.tm-mine-ok')?.textContent"})
        self.assertTrue(got[-2]["until"], got); self.assertIn("Owner approved reply", got[-1]["eval"])
        self.shot("confirmed-sent-detail-phone")

    def feed(self, data):
        self.ev("ext.post", None, plugin="teams", channel="plugin", sender="teams", text=json.dumps(data))

    def seed_inbox(self, start_editing=True, open_editor=True):
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
                  {"eval": "document.querySelector('.tm-person').click();true"})
        if open_editor:
            self.page({"eval": "document.querySelector('[aria-label=\"Ответить: Review colleague\"]')?.click();true"})

        if start_editing:
            self.edit("")

    def test_open_and_generated_fill_do_not_hold_until_owner_input(self):
        self.seed_inbox(start_editing=False)
        got = self.page({"eval": "document.querySelector('.tm-shared-compose .composer textarea').value"})
        self.assertEqual(got[-1]["eval"], "")
        self.assertFalse([e for e in self.non_history_actions() if e["type"] == "ext.post"])
        self.page({"tapSelector":".tm-editor-options > summary"},{"click": "Close editor"}, {"until": "!document.querySelector('.tm-shared-compose textarea')"})
        self.assertFalse([e for e in self.non_history_actions() if e["type"] == "ext.post"])
        self.page({"eval": "document.querySelector('[aria-label=\"Ответить: Review colleague\"]').click();document.querySelector('.tm-editor-options').open=true;document.querySelector('.tm-instruction summary').click();true"},
                  {"eval": "(()=>{const t=document.querySelector('.tm-instruction textarea');t.value='Keep my wording';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"})
        self.acknowledge(self.queued("draft_control"))
        self.edit("Intentional owner reply")
        self.edit("")
        self.assertFalse([e for e in self.non_history_actions() if e["type"] == "ext.post"])

    def non_history_actions(self):
        return [e for e in self.spooled() if not (e["type"] == "ext.post" and json.loads(e["data"]["text"]).get("kind") == "history")]

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
        self.page({"eval": "document.querySelector('.tm-editor-options').open=true;document.querySelector('.tm-instruction summary').click();true"})
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
