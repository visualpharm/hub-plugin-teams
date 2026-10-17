"""Real web renderer + isolated journal. No collector/account/provider send."""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import unittest
from unittest import mock
from tests.test_web_e2e import PageInChrome


class InboxWebAcceptance(PageInChrome):
    def spooled(self, theme=False):
        # Consume only facts observed in this snapshot. A browser request may
        # still be writing its atomic temporary file or arrive after take().
        from core import spool
        ready = spool.take(os.path.join(self.state, "spool"))
        for path, _ in ready:
            os.unlink(path)
        return [event for _, event in ready if theme or event["type"] != "owner.theme"]

    def test_pin_survives_reload_and_preserves_draft_and_conversation_order(self):
        self.seed_inbox(start_editing=False)
        self.edit("Keep this exact draft")
        self.queued("draft_control")
        self.feed({"kind":"msg","id":"newer","contact":"synthetic-account/other","src":"dm","from":"Newer colleague","text":"Newer item","at":"2099-01-01T12:00:00Z"})
        self.page({"tapSelector":".tm-conversation-options > summary"},{"tapSelector":"[data-action=pin-conversation]"})
        self.assertEqual(self.page({"eval":"document.querySelector('.tm-shared-compose textarea').value"})[-1]["eval"],"Keep this exact draft")
        self.page({"tapSelector":".tm-close-conversation"})
        got=self.page({"eval":"[...document.querySelectorAll('.tm-person')].map(n=>({text:n.innerText,pinned:!!n.querySelector('.tm-pinned')}))"})[-1]["eval"]
        self.assertIn("Review colleague",got[0]["text"]);self.assertTrue(got[0]["pinned"])
        self.assertEqual(self.non_history_actions(),[])
        self.page({"go":f"http://127.0.0.1:{self.port}/#/x/inbox"},{"until":"document.querySelectorAll('.tm-person').length===2"})
        self.assertIn("Review colleague",self.page({"eval":"document.querySelector('.tm-person').innerText"})[-1]["eval"])
        self.page({"tapSelector":".tm-person"},{"tapSelector":".tm-conversation-options > summary"},{"tapSelector":"[data-action=pin-conversation]"},{"tapSelector":".tm-close-conversation"})
        self.assertIn("Newer colleague",self.page({"eval":"document.querySelector('.tm-person').innerText"})[-1]["eval"])
        self.assertEqual(self.non_history_actions(),[])

    def test_pin_menu_widths_focus_filter_and_storage_failure(self):
        self.seed_inbox(start_editing=False)
        self.edit("Preserved pin draft");self.queued("draft_control")
        rows=[]
        for index,width in enumerate((360,390,768,834,1024,1280,1440)):
            theme='dark' if index%2 else 'light'
            steps=[{'media':theme},{'viewport':{'width':width,'height':874}},{'sleep':150},
              {'tapSelector':'.tm-conversation-options > summary'},{'until':"document.querySelector('.tm-conversation-options').open"}]
            if os.environ.get('HUB_INBOX_SCREENSHOTS'):
                out=Path(os.environ['HUB_INBOX_SCREENSHOTS']);out.mkdir(parents=True,exist_ok=True)
                steps.append({'shot':str(out/f'pin-menu-{theme}-{width}.png'),'width':width,'height':874})
            steps.append({'eval':"(()=>{const b=document.querySelector('[data-action=pin-conversation]'),r=b.getBoundingClientRect(),s=b.closest('details').querySelector('summary').getBoundingClientRect();return {left:r.left,right:r.right,height:r.height,target:s.height,overflow:document.documentElement.scrollWidth-innerWidth,theme:getComputedStyle(document.documentElement).colorScheme}})()"})
            got=self.page(*steps)[-1]['eval'];self.assertGreaterEqual(got['left'],0);self.assertLessEqual(got['right'],width)
            self.assertGreaterEqual(got['height'],44);self.assertGreaterEqual(got['target'],44);self.assertEqual(got['overflow'],0);self.assertEqual(got['theme'],theme);rows.append(got)
            self.page({'key':'Escape'})
            self.assertTrue(self.page({'eval':"!document.querySelector('.tm-conversation-options').open && document.activeElement===document.querySelector('.tm-conversation-options > summary')"})[-1]['eval'])
        self.page({'tapSelector':'.tm-conversation-options > summary'},
          {'eval':"document.querySelector('[data-action=pin-conversation]').focus();true"})
        self.feed({'kind':'status','src':'dm','ok':True})
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-conversation-options').open && document.activeElement.dataset.action==='pin-conversation'"})[-1]['eval'])
        self.page({'key':'Escape'})
        self.page({'eval':"window.__save=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k.startsWith('hub.inbox.pinned.'))throw Error('quota');return window.__save.call(this,k,v)};true"},
          {'tapSelector':'.tm-conversation-options > summary'},{'tapSelector':'[data-action=pin-conversation]'})
        self.assertTrue(self.page({'eval':"document.body.innerText.includes('Could not save the pin')"})[-1]['eval'])
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Preserved pin draft')
        self.page({'eval':'Storage.prototype.setItem=window.__save;true'},
          {'tapSelector':'.tm-conversation-options > summary'},{'tapSelector':'[data-action=pin-conversation]'})
        self.assertFalse(self.page({'eval':"document.body.innerText.includes('Could not save the pin')"})[-1]['eval'])
        self.assertTrue(self.page({'eval':"document.activeElement===document.querySelector('.tm-conversation-options > summary')"})[-1]['eval'])
        self.page({'tapSelector':'.tm-close-conversation'})
        self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-pinned') && getComputedStyle(document.querySelector('.tm-pinned')).maskImage!=='none'"})[-1]['eval'])
        if os.environ.get('HUB_INBOX_SCREENSHOTS'):
            for theme in ('light','dark'):
                for width in (390,1440):
                    self.page({'media':theme},{'viewport':{'width':width,'height':874}}, {'shot':str(out/f'pin-list-{theme}-{width}.png'),'width':width,'height':874})
        self.page({'eval':"const s=document.querySelector('.tm-conversation-search input');s.value='not a matching phrase';s.dispatchEvent(new Event('input',{bubbles:true}));true"})
        self.assertEqual(self.page({'eval':"document.querySelectorAll('.tm-person').length"})[-1]['eval'],0)
        self.assertEqual(self.non_history_actions(),[])

    def test_pin_storage_event_refreshes_list_without_losing_draft(self):
        self.seed_inbox(start_editing=False);self.edit('Cross-tab draft');self.queued('draft_control')
        self.page({'eval':"localStorage.setItem('hub.inbox.pinned.v1:hub',JSON.stringify([JSON.stringify(['teams','synthetic-account/conversation-a'])]));window.dispatchEvent(new StorageEvent('storage',{key:'hub.inbox.pinned.v1:hub'}));true"})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Cross-tab draft')
        self.page({'tapSelector':'.tm-close-conversation'})
        self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-pinned')"})[-1]['eval'])
        self.page({'eval':"localStorage.removeItem('hub.inbox.pinned.v1:hub');window.dispatchEvent(new StorageEvent('storage',{key:'hub.inbox.pinned.v1:hub'}));true"})
        self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-pinned')"})[-1]['eval'])
        self.assertEqual(self.non_history_actions(),[])

    def test_pin_flat_cards_keep_exact_menu_focus(self):
        self.seed_inbox(start_editing=False)
        for n in (1,2):self.feed({'kind':'msg','id':f'channel-{n}','contact':'teams/synthetic-thread','src':'channel','from':'Synthetic channel','text':f'Message {n}','at':f'2099-01-0{n}T12:00:00Z'})
        self.page({'tapSelector':'.tm-close-conversation'},{'until':"document.querySelectorAll('.tm-person').length===2"},{'tapSelector':'.tm-options > summary'},
          {'eval':"[...document.querySelectorAll('.tm-srcs button')].find(n=>n.textContent.includes('Каналы')).click();document.querySelector('.tm-options').open=false;true"})
        self.page({'until':"document.querySelectorAll('.tm-list .tm-conversation-options').length===2"})
        self.assertEqual(self.page({'eval':"document.querySelectorAll('.tm-list .tm-conversation-options').length"})[-1]['eval'],2)
        self.page({'eval':"const menu=document.querySelectorAll('.tm-list .tm-conversation-options')[1];window.__option=menu.dataset.optionKey;menu.querySelector('summary').click();menu.querySelector('button').focus();true"})
        self.feed({'kind':'status','src':'channel','ok':True})
        self.assertTrue(self.page({'eval':"document.activeElement.closest('.tm-conversation-options').dataset.optionKey===window.__option"})[-1]['eval'])
        self.page({'key':'Enter'})
        self.assertTrue(self.page({'eval':"document.activeElement.tagName==='SUMMARY' && document.activeElement.closest('.tm-conversation-options').dataset.optionKey===window.__option"})[-1]['eval'])
        self.assertEqual(self.non_history_actions(),[])

    def menu_history(self):
        self.seed_inbox(start_editing=False);self.page({'tapSelector':'.tm-earlier'});self.queued('history')
        self.feed({'kind':'thread','id':'source-a','part':0,'of':1,'more':False,'items':[
          {'id':'turn-first','at':'2026-10-17T12:00:00Z','from':'Earlier colleague','text':'First question'},
          {'id':'turn-second','at':'2026-10-17T12:01:00Z','from':'Earlier colleague','text':'Second question'}]})
        got=self.page({'until':"document.querySelectorAll('.tm-history-row').length===2"});self.assertTrue(got[-1]['until'],got)

    def test_message_menu_switches_touch_target_without_second_gesture(self):
        self.menu_history()
        self.page({'eval':"navigator.clipboard.writeText=async t=>window.__copied=t;document.querySelector('.tm-history-row').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,clientX:100,clientY:300}));true"},
          {'eval':"document.querySelectorAll('.tm-history-row')[1].dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerType:'touch',clientX:100,clientY:360}));true"},{'sleep':650})
        self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-message-menu')"})[-1]['eval'])
        self.page({'tapSelector':'.tm-message-menu button:first-child'})
        self.assertEqual(self.page({'eval':'window.__copied'})[-1]['eval'],'Second question')
        self.assertEqual(self.non_history_actions(),[])

    def test_message_menu_historical_work_quotes_exact_thread_post(self):
        self.menu_history()
        thread_post=self.page({'eval':"fetch('/api/feed?plugin=teams').then(r=>r.json()).then(d=>d.posts.find(p=>{try{return JSON.parse(p.text).kind==='thread'}catch{return false}}).id)"})[-1]['eval']
        self.page({'eval':"document.querySelector('.tm-history-row').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,clientX:100,clientY:300}));true"},
          {'tapSelector':'.tm-message-menu button:nth-child(2)'},{'until':"location.hash==='#/s/hub'"},{'sleep':150})
        quote=self.page({'eval':"import('/static/js/state.js').then(m=>m.S.replyTarget?.quote)"})[-1]['eval']
        self.assertIn('post '+thread_post,quote);self.assertIn('turn-first',quote)
        self.assertIn('First question',quote);self.assertNotIn('Please check the navigation',quote)
        self.assertEqual(self.non_history_actions(),[])

    def test_message_menu_focus_survives_flat_refresh_and_tab(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram')
        self.page({'tapSelector':'.tm-close-conversation'},{'tapSelector':'.tm-options > summary'},
          {'eval':"[...document.querySelectorAll('.tm-srcs button')].find(n=>n.textContent.includes('Telegram')).click();true"},
          {'eval':"document.querySelector('.tm-options').open=false;const row=document.querySelector('[data-message=\"external-telegram\"]');window.__oldRow=row;row.focus();row.dispatchEvent(new KeyboardEvent('keydown',{key:'ContextMenu',bubbles:true,cancelable:true}));true"})
        self.feed({'kind':'status','src':'telegram','ok':True})
        got=self.page({'until':"!window.__oldRow.isConnected"});self.assertTrue(got[-1]['until'],got)
        self.page({'key':'Escape'})
        self.assertEqual(self.page({'eval':"document.activeElement.dataset.message"})[-1].get('eval'),'external-telegram')
        self.page({'eval':"document.activeElement.dispatchEvent(new KeyboardEvent('keydown',{key:'ContextMenu',bubbles:true,cancelable:true}));true"},{'key':'Tab'})
        self.assertTrue(self.page({'eval':"document.activeElement!==document.body && !document.querySelector('.tm-message-menu')"})[-1]['eval'])

    def test_message_menu_does_not_copy_media_placeholder(self):
        self.seed_inbox(start_editing=False)
        self.feed({'kind':'msg','id':'source-a','contact':'synthetic-account/conversation-a','src':'dm','from':'Review colleague','text':'[media]','reply':True,
          'at':datetime.now(timezone.utc).isoformat(),'media':[{'kind':'photo','url':'/api/file?path=synthetic.png'}]})
        self.page({'until':"!!document.querySelector('[data-message=\"source-a\"] .tm-media')"},
          {'eval':"document.querySelector('[data-message=\"source-a\"]').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,clientX:100,clientY:300}));true"})
        self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-message-menu')"})[-1]['eval'])
        self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-message-menu .tm-icon-copy')"})[-1]['eval'])

    def test_native_message_menu_touch_widths_and_work_prefill(self):
        self.seed_inbox(start_editing=False)
        rows=[]
        for index,width in enumerate((360,390,768,834,1024,1280,1440)):
            theme='dark' if index%2 else 'light'
            steps=[{'media':theme},{'touch':True},{'viewport':{'width':width,'height':874}},{'sleep':150},
              {'eval':"document.querySelector('[data-message=\"source-a\"]').dispatchEvent(new PointerEvent('pointerdown',{pointerType:'touch',clientX:innerWidth-12,clientY:860,bubbles:true}));true"},{'sleep':650}]
            if os.environ.get('HUB_INBOX_SCREENSHOTS'):
                out=Path(os.environ['HUB_INBOX_SCREENSHOTS']);out.mkdir(parents=True,exist_ok=True)
                steps.append({'shot':str(out/f'message-menu-{theme}-{width}.png'),'width':width,'height':874})
            steps.append({'eval':"(()=>{const m=document.querySelector('.tm-message-menu'),r=m.getBoundingClientRect();return {theme:getComputedStyle(document.documentElement).colorScheme,left:r.left,right:r.right,top:r.top,bottom:r.bottom,overflow:document.documentElement.scrollWidth-innerWidth,masks:[...m.querySelectorAll('.tm-native-icon')].map(n=>getComputedStyle(n).maskImage),heights:[...m.querySelectorAll('button')].map(n=>n.getBoundingClientRect().height)}})()"})
            got=self.page(*steps)[-1];self.assertIn('eval',got,got);got=got['eval'];self.assertEqual(got['theme'],theme);self.assertEqual(got['overflow'],0)
            self.assertGreaterEqual(got['left'],0);self.assertLessEqual(got['right'],width)
            self.assertGreaterEqual(got['top'],0);self.assertLessEqual(got['bottom'],874)
            self.assertTrue(all(h>=44 for h in got['heights']),got)
            self.assertTrue(all(mask!='none' for mask in got['masks']),got);rows.append({'width':width,**got})
            self.page({'key':'Escape'})
        self.page({'eval':"document.querySelector('[data-message=\"source-a\"]').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:100,clientY:300}));true"},
          {'tapSelector':'.tm-message-menu button:nth-child(2)'},
          {'until':"location.hash==='#/s/hub' && !!document.querySelector('form.composer textarea')"})
        self.assertEqual(self.page({'eval':"document.querySelector('form.composer textarea').value"})[-1]['eval'],'Разбери.')
        self.assertEqual(self.non_history_actions(),[])
        if os.environ.get('HUB_INBOX_SCREENSHOTS'):(out/'geometry.json').write_text(json.dumps(rows,indent=2))

    def test_native_message_menu_copies_exact_text_and_preserves_editor(self):
        self.seed_inbox();self.acknowledge(self.queued('draft_control'));self.edit('Keep my unfinished reply')
        self.page({'eval':"navigator.clipboard.writeText=async text=>{window.__copied=text};document.querySelector('[data-message=\"source-a\"]').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:100,clientY:300}));true"})
        got=self.page({'eval':"[...document.querySelectorAll('.tm-message-menu [role=menuitem]')].map(n=>n.textContent)"})[-1]['eval']
        self.assertEqual(len(got),3,got)
        self.page({'tapSelector':'.tm-message-menu button:first-child'})
        self.assertEqual(self.page({'eval':'window.__copied'})[-1]['eval'],'Please check the navigation.')
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Keep my unfinished reply')
        self.assertEqual(self.non_history_actions(),[])

    def test_native_message_menu_historical_draft_uses_exact_provider_turn(self):
        self.seed_inbox(start_editing=False);self.page({'tapSelector':'.tm-earlier'});self.queued('history')
        self.feed({'kind':'thread','id':'source-a','part':0,'of':1,'more':False,'items':[
          {'id':'provider-first','at':'2026-10-17T12:00:00Z','from':'Earlier colleague','text':'First exact question'},
          {'id':'provider-second','at':'2026-10-17T12:01:00Z','from':'Earlier colleague','text':'Second different question'}]})
        got=self.page({'until':"document.querySelectorAll('.tm-history-row').length===2"});self.assertTrue(got[-1]['until'],got)
        self.page({'eval':"document.querySelector('.tm-history-row').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:100,clientY:300}));true"},
          {'tapSelector':'.tm-message-menu button:last-child'},{'sleep':100})
        q=self.queued('ask');self.assertEqual(q['what'],'draft');self.assertEqual(q['msg'],'provider-first')
        self.assertEqual(q['from'],'Earlier colleague');self.assertEqual(q['at'],'2026-10-17T12:00:00Z')
        self.assertRegex(q['post'],r'^p\d+$');self.assertRegex(q['place'],r'^post p\d+ \(thread, part 1 of 1\)$')
        self.assertNotIn('text',q);self.assertNotIn('instruction',q);self.assertNotIn('id',q)

    def test_native_message_menu_keyboard_dismissal_and_rebound_source(self):
        self.seed_inbox(start_editing=False)
        self.page({'eval':"(()=>{const r=document.querySelector('[data-message=\"source-a\"]');r.dispatchEvent(new PointerEvent('pointerdown',{pointerType:'touch',clientX:100,clientY:300,bubbles:true}));r.dispatchEvent(new PointerEvent('pointermove',{pointerType:'touch',clientX:100,clientY:340,bubbles:true}));return true})()"},{'sleep':650})
        self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-message-menu')"})[-1]['eval'])
        self.page({'eval':"(()=>{const r=document.querySelector('[data-message=\"source-a\"]');r.focus();r.dispatchEvent(new KeyboardEvent('keydown',{key:'F10',shiftKey:true,bubbles:true,cancelable:true}));return true})()"})
        self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-message-menu')"})[-1]['eval'])
        self.page({'key':'End'})
        self.assertTrue(self.page({'eval':"document.activeElement===document.querySelector('.tm-message-menu button:last-child')"})[-1]['eval'])
        self.page({'key':'Escape'})
        self.assertTrue(self.page({'eval':"!document.querySelector('.tm-message-menu') && document.activeElement.dataset.message==='source-a'"})[-1]['eval'])
        self.page({'eval':"document.querySelector('[data-message=\"source-a\"]').dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:100,clientY:300}));true"})
        self.feed({'kind':'msg','id':'source-a','contact':'different-account/new-contact','src':'dm','from':'Different recipient','text':'Different message','reply':True,'at':datetime.now(timezone.utc).isoformat()})
        got=self.page({'until':"!document.querySelector('.tm-message-menu')"});self.assertTrue(got[-1]['until'],got)
        self.assertEqual(self.non_history_actions(),[])

    def test_suggested_reply_lost_acknowledgement_cannot_create_second_delivery(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram')
        post=self.page({'eval':"fetch('/api/feed?plugin=teams').then(r=>r.json()).then(d=>d.posts.find(p=>{try{return JSON.parse(p.text).id==='external-telegram'}catch{return false}}).id)"})[-1]['eval']
        self.ev('ext.post',None,plugin='teams',channel='session',owner=False,sender='hub',reply_to=post,text='Exact suggested reply')
        self.page({'tapSelector':'.tm-editor-options > summary'},{'click':'Close editor'},
          {'until':"!!document.querySelector('.tm-draft button.primary')"},
          {'eval':"window.__fetch=window.fetch;window.fetch=async(url,opts)=>{const r=await __fetch(url,opts);if(String(url).endsWith('/api/feed/post')&&JSON.parse(opts?.body||'{}').text?.includes('\\\"kind\\\":\\\"send\\\"'))throw new Error('Synthetic lost acknowledgment after acceptance');return r};true"},
          {'tapSelector':'.tm-draft button.primary'},{'sleep':200})
        q=self.queued('send');self.assertEqual(q['text'],'Exact suggested reply')
        got=self.page({'eval':"({unknown:!!document.querySelector('.tm-mine-unresolved'),blocked:!document.querySelector('.tm-draft button.primary') || document.querySelector('.tm-draft button.primary').disabled})"})[-1]['eval']
        self.assertEqual(got,{'unknown':True,'blocked':True})
        self.page({'eval':"window.fetch=__fetch;document.querySelector('.tm-draft button.primary')?.click();true"},{'sleep':100})
        self.assertEqual(self.non_history_actions(),[])
        self.feed({'kind':'sent','id':q['id'],'rid':q['rid']})
        self.page({'tapSelector':"[aria-label='Sent conversations']"},
          {'until':"!!document.querySelector('.tm-person')"},{'tapSelector':'.tm-person'})
        got=self.page({'until':"!!document.querySelector('.tm-mine-ok')"});self.assertTrue(got[-1]['until'],got)

    def test_suggested_draft_cannot_bypass_a_pending_reply(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram');self.edit('Already pending exact reply')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100});q=self.queued('send')
        post=self.page({'eval':"fetch('/api/feed?plugin=teams').then(r=>r.json()).then(d=>d.posts.find(p=>{try{return JSON.parse(p.text).id==='external-telegram'}catch{return false}}).id)"})[-1]['eval']
        self.ev('ext.post',None,plugin='teams',channel='session',owner=False,sender='hub',reply_to=post,text='Different suggested reply')
        self.page({'tapSelector':'.tm-editor-options > summary'},{'click':'Close editor'},
          {'until':"!!document.querySelector('.tm-draft button.primary')"})
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-draft button.primary').disabled"})[-1]['eval'])
        self.assertEqual(self.non_history_actions(),[])
        self.feed({'kind':'send_failed','id':q['id'],'rid':q['rid'],'error':'Definitive refusal'})
        got=self.page({'until':"!document.querySelector('.tm-draft button.primary').disabled"});self.assertTrue(got[-1]['until'],got)
        self.page({'tapSelector':'.tm-draft button.primary'},{'sleep':100})
        retry=self.queued('send');self.assertEqual(retry['text'],'Different suggested reply');self.assertEqual(retry['id'],q['id'])

    def test_canceled_reply_cannot_follow_a_rebound_source(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram');self.edit('Reply only for original contact')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100});q=self.queued('send')
        self.feed({'kind':'scheduled','id':q['id'],'rid':q['rid'],'at':'2030-01-01T12:00:00Z'})
        self.page({'until':"!!document.querySelector('.tm-unschedule')"},{'tapSelector':'.tm-unschedule'},{'sleep':100})
        self.queued('cancel')
        self.feed({'kind':'msg','id':q['id'],'contact':'different-account/new-contact','src':'telegram','from':'Synthetic telegram',
          'text':'Rebound source','reply':True,'at':datetime.now(timezone.utc).isoformat()})
        self.feed({'kind':'canceled','id':q['id'],'rid':q['rid']})
        self.page({'until':"document.querySelector('.tm-list').textContent.includes('Rebound source')"},{'sleep':200})
        self.assertEqual(self.page({'eval':"Object.keys(localStorage).filter(k=>k.startsWith('hub.inbox.draft.v1:')&&k.includes('different-account')).map(k=>JSON.parse(localStorage[k]).text)"})[-1]['eval'],[])
        self.assertEqual(self.page({'eval':"Object.keys(localStorage).filter(k=>k.startsWith('hub.inbox.draft.v1:')&&k.includes('synthetic/telegram')).map(k=>JSON.parse(localStorage[k]).text)"})[-1]['eval'],['Reply only for original contact'])
        self.page({'tapSelector':'.tm-person[aria-label*="Synthetic telegram"]'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-detail:not([hidden]) .tm-shared-compose textarea').value"})[-1]['eval'],'')
        self.feed({'kind':'scheduled','id':q['id'],'rid':q['rid'],'at':'2030-01-01T12:00:00Z'})
        self.page({'sleep':200})
        self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-mine')"})[-1]['eval'])

    def test_reply_unknown_failure_never_enables_a_new_delivery(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram');self.edit('Original uncertain reply')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100});q=self.queued('send')
        self.feed({'kind':'send_failed','id':q['id'],'rid':q['rid'],'unresolved':True,'error':'Synthetic unknown delivery'})
        got=self.page({'until':"!!document.querySelector('.tm-mine-unresolved')"});self.assertTrue(got[-1]['until'],got)
        self.assertNotIn('не отправлено',self.page({'eval':"document.querySelector('.tm-mine').textContent"})[-1]['eval'])
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100})
        self.assertEqual(self.non_history_actions(),[])
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Original uncertain reply')

    def test_cancel_timeout_survives_duplicate_scheduled_receipt(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram');self.edit('Scheduled exact reply')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100});q=self.queued('send')
        scheduled={'kind':'scheduled','id':q['id'],'rid':q['rid'],'at':'2030-01-01T12:00:00Z'}
        self.feed(scheduled)
        self.page({'until':"!!document.querySelector('.tm-unschedule')"},
          {'eval':"window.__timeout=window.setTimeout;window.setTimeout=(f,ms,...a)=>{if(ms===30000){window.__cancelTimeout=f;return 0}return __timeout(f,ms,...a)};true"},
          {'tapSelector':'.tm-unschedule'},{'sleep':100});self.queued('cancel')
        self.feed({**scheduled,'at':'2030-02-02T12:00:00Z'})
        got=self.page({'until':"document.querySelector('.tm-mine-later').textContent.includes('феврал')"});self.assertTrue(got[-1]['until'],got)
        self.page({'eval':'__cancelTimeout();true'})
        self.assertFalse(self.page({'eval':"document.querySelector('.tm-unschedule').disabled"})[-1]['eval'])
        self.page({'tapSelector':'.tm-unschedule'},{'sleep':100})
        self.assertEqual(self.queued('cancel')['rid'],q['rid'])

    def prepare_new_message(self):
        self.seed_inbox(start_editing=False)
        self.page({'tapSelector':'.tm-close-conversation'},{'tapSelector':'.tm-new-trigger'},
          {'eval':"(()=>{const t=document.querySelector('.tm-new-search');t.value='Test';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"},{'sleep':650})
        q=self.queued('contacts')
        self.feed({'kind':'contacts','rid':q['rid'],'q':'Test','items':[{'src':'telegram','to':'telegram:synthetic-person','name':'Synthetic recipient'}]})
        self.page({'until':"!!document.querySelector('.tm-new-contact')"},{'tapSelector':'.tm-new-contact'},
          {'eval':"(()=>{const t=document.querySelector('.tm-new-text');t.value='Original exact message';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"})

    def test_new_message_hung_send_recovers_without_changing_original_request(self):
        self.prepare_new_message()
        self.page({'eval':"window.__fetch=window.fetch;window.fetch=(url,opts)=>{if(String(url).endsWith('/api/feed/post')&&JSON.parse(opts?.body||'{}').text?.includes('send_new')){window.__attempt=JSON.parse(JSON.parse(opts.body).text);return new Promise(()=>{})}return __fetch(url,opts)};true"},
          {'tapSelector':'.tm-new-send'},{'sleep':100})
        attempt=self.page({'eval':'__attempt'})[-1]['eval']
        self.page({'go':'about:blank'},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"!!document.querySelector('.tm-new-trigger')"},{'tapSelector':'.tm-new-trigger'})
        self.assertEqual(self.non_history_actions(),[])
        self.assertFalse(self.page({'eval':"document.querySelector('.tm-new-send').disabled"})[-1]['eval'])
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-new-chosen button').disabled"})[-1]['eval'])
        self.page({'eval':"(()=>{const t=document.querySelector('.tm-new-text');t.value='Newer unsent message';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"})
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-new-pending').textContent.includes('Original exact message') && document.querySelector('.tm-new-pending').textContent.includes('Synthetic recipient')"})[-1]['eval'])
        if os.environ.get('HUB_INBOX_SCREENSHOTS'):
            out=Path(os.environ['HUB_INBOX_SCREENSHOTS']);out.mkdir(parents=True,exist_ok=True)
            for width,theme in ((360,'light'),(1240,'dark')):
                got=self.page({'media':theme},{'touch':width<600},{'shot':str(out/f'pending-{theme}-{width}.png'),'width':width,'height':874},
                  {'eval':"({theme:getComputedStyle(document.documentElement).colorScheme,overflow:document.documentElement.scrollWidth-innerWidth,right:document.querySelector('.tm-new-send').getBoundingClientRect().right})"})[-1]['eval']
                self.assertEqual(got['theme'],theme);self.assertEqual(got['overflow'],0);self.assertLessEqual(got['right'],width)
        self.page({'tapSelector':'.tm-new-send'},{'sleep':100})
        self.assertEqual(self.queued('send_new'),attempt)
        self.feed({'kind':'sent','rid':attempt['rid'],'to':attempt['to']})
        got=self.page({'until':"!document.querySelector('.tm-new-send').disabled"});self.assertTrue(got[-1]['until'],got)
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-new-text').value"})[-1]['eval'],'Newer unsent message')

    def test_new_message_search_enter_and_storage_failure_are_visible(self):
        self.seed_inbox(start_editing=False)
        self.page({'tapSelector':'.tm-close-conversation'},{'tapSelector':'.tm-new-trigger'},
          {'eval':"(()=>{const t=document.querySelector('.tm-new-search');t.value='Keyboard';t.dispatchEvent(new Event('input',{bubbles:true}));t.focus();return true})()"},{'key':'Enter'},{'sleep':100})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-new-status').textContent"})[-1]['eval'],'')
        q=self.queued('contacts')
        self.feed({'kind':'contacts','rid':q['rid'],'q':'Keyboard','items':[]})
        got=self.page({'until':"document.querySelector('.tm-new-results').textContent.includes('Никого')"});self.assertTrue(got[-1]['until'],got)
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-new-search').getAttribute('aria-controls')===document.querySelector('.tm-new-results').id && document.querySelector('.tm-new-results').getAttribute('aria-live')==='polite'"})[-1]['eval'],True)
        self.page({'eval':"Storage.prototype.setItem=function(){throw new DOMException('Blocked','QuotaExceededError')};const t=document.querySelector('.tm-new-text');t.value='Keep current draft';t.dispatchEvent(new Event('input',{bubbles:true}));true"})
        self.assertIn('сохранить',self.page({'eval':"document.querySelector('.tm-new-storage').textContent"})[-1]['eval'])
        self.page({'key':'Escape'})
        self.assertTrue(self.page({'eval':"document.activeElement===document.querySelector('.tm-new-trigger')"})[-1]['eval'])
        self.page({'tapSelector':'.tm-new-trigger'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-new-text').value"})[-1]['eval'],'Keep current draft')

    def test_new_message_collector_uncertainty_never_becomes_a_new_delivery(self):
        self.prepare_new_message()
        self.page({'tapSelector':'.tm-new-send'},{'sleep':100});q=self.queued('send_new')
        self.feed({'kind':'send_failed','rid':q['rid'],'to':q['to'],'unresolved':True,'error':'Synthetic unknown provider outcome'})
        got=self.page({'until':"document.querySelector('.tm-new-status').textContent.includes('Synthetic unknown')"});self.assertTrue(got[-1]['until'],got)
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-new-chosen button').disabled"})[-1]['eval'])
        self.page({'tapSelector':'.tm-new-send'},{'sleep':100})
        self.assertEqual(self.queued('send_new'),q)
        self.page({'go':'about:blank'},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},
          {'until':"!!document.querySelector('.tm-new-trigger')"},{'tapSelector':'.tm-new-trigger'},
          {'tapSelector':'.tm-new-send'},{'sleep':100})
        self.assertEqual(self.queued('send_new'),q)

    def test_new_message_missing_receipt_watchdog_retries_only_original(self):
        self.prepare_new_message()
        self.page({'eval':"window.__timeout=window.setTimeout;window.setTimeout=(f,ms,...a)=>{if(ms===30000){window.__watchdog=f;return 0}return __timeout(f,ms,...a)};true"},
          {'tapSelector':'.tm-new-send'},{'sleep':100})
        q=self.queued('send_new')
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-new-send').disabled"})[-1]['eval'])
        self.page({'eval':"__watchdog();true"})
        self.assertFalse(self.page({'eval':"document.querySelector('.tm-new-send').disabled"})[-1]['eval'])
        self.page({'tapSelector':'.tm-new-send'},{'sleep':100})
        self.assertEqual(self.queued('send_new'),q)
        self.feed({'kind':'sent','rid':q['rid'],'to':q['to']})
        self.page({'until':"!document.querySelector('.tm-new').open"},{'eval':"__watchdog();true"},{'tapSelector':'.tm-new-trigger'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-new-status').textContent"})[-1]['eval'],'Отправлено')

    def test_new_message_unknown_ack_retries_same_request_after_reload(self):
        self.seed_inbox(start_editing=False)
        self.page({'tapSelector':'.tm-close-conversation'},{'tapSelector':'.tm-new-trigger'},
          {'eval':"(()=>{const t=document.querySelector('.tm-new-search');t.value='Test';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"},{'sleep':650})
        lookup=self.queued('contacts')
        self.feed({'kind':'contacts','rid':lookup['rid'],'q':'Test','items':[],'errors':{'telegram':'Synthetic search refusal'}})
        got=self.page({'until':"document.querySelector('.tm-new-results').textContent.includes('Synthetic search refusal')"});self.assertTrue(got[-1]['until'],got)
        self.page({'tapSelector':'.tm-new-results button'},{'sleep':100});lookup=self.queued('contacts')
        self.feed({'kind':'contacts','rid':lookup['rid'],'q':'Test','items':[{'src':'whatsapp','to':'whatsapp:test-account:test-person','name':'Synthetic person'}]})
        self.page({'until':"!!document.querySelector('.tm-new-contact')"},{'tapSelector':'.tm-new-contact'},
          {'eval':"""(()=>{const t=document.querySelector('.tm-new-text');t.value='Exact retry';t.dispatchEvent(new Event('input',{bubbles:true}));window.__fetch=window.fetch;window.fetch=async (url,opts)=>{if(String(url).endsWith('/api/feed/post')&&JSON.parse(opts?.body||'{}').text?.includes('send_new')){window.__attempt=JSON.parse(JSON.parse(opts.body).text);throw new Error('Synthetic lost acknowledgement')}return __fetch(url,opts)};return true})()"""},
          {'tapSelector':'.tm-new-send'},{'until':"!document.querySelector('.tm-new-send').disabled && document.querySelector('.tm-new-status').textContent.includes('Подтверждения нет')"})
        attempt=self.page({'eval':'__attempt'})[-1]['eval']
        self.page({'go':'about:blank'},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"!!document.querySelector('.tm-new-trigger')"},{'tapSelector':'.tm-new-trigger'},
          {'tapSelector':'.tm-new-send'},{'sleep':100})
        retry=self.queued('send_new');self.assertEqual(retry,attempt)
        self.feed({'kind':'sent','rid':retry['rid'],'to':retry['to']})
        got=self.page({'until':"!document.querySelector('.tm-new').open"});self.assertTrue(got[-1]['until'],got)

    def test_new_recipient_search_and_pending_receipt_cannot_replace_newer_input(self):
        self.seed_inbox(start_editing=False)
        self.page({'tapSelector':'.tm-close-conversation'},{'tapSelector':'.tm-new-trigger'})
        requests=[]
        for query in ('Earlier','Current'):
            self.page({'eval':f"(()=>{{const t=document.querySelector('.tm-new-search');t.value={query!r};t.dispatchEvent(new Event('input',{{bubbles:true}}));return true}})()"},{'sleep':650})
            requests.append(self.queued('contacts'))
        self.feed({'kind':'contacts','rid':requests[0]['rid'],'q':'Earlier','items':[{'src':'telegram','to':'telegram:old','name':'Stale recipient'}]})
        self.page({'sleep':100});self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-new-contact')"})[-1]['eval'])
        self.feed({'kind':'contacts','rid':requests[1]['rid'],'q':'Current','items':[{'src':'telegram','to':'telegram:current','name':'Current recipient','hint':'Synthetic account'}]})
        self.page({'until':"document.querySelector('.tm-new-contact')?.textContent.includes('Current recipient')"},{'tapSelector':'.tm-new-contact'},
          {'eval':"(()=>{const t=document.querySelector('.tm-new-text');t.value='First exact message';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"})
        if os.environ.get('HUB_INBOX_SCREENSHOTS'):
            out=Path(os.environ['HUB_INBOX_SCREENSHOTS']);out.mkdir(parents=True,exist_ok=True)
            for width,theme in ((360,'light'),(402,'dark'),(834,'light'),(1240,'dark')):
                got=self.page({'media':theme},{'touch':width<600},{'shot':str(out/f'new-message-{theme}-{width}.png'),'width':width,'height':874},
                  {'eval':"({theme:getComputedStyle(document.documentElement).colorScheme,overflow:document.documentElement.scrollWidth-innerWidth,right:document.querySelector('.tm-new-send').getBoundingClientRect().right,form:document.querySelector('.tm-new').getBoundingClientRect().width})"})[-1]['eval']
                self.assertEqual(got['theme'],theme);self.assertEqual(got['overflow'],0);self.assertLessEqual(got['right'],width);self.assertLessEqual(got['form'],width)
        self.page({'eval':"document.querySelector('.tm-new form').requestSubmit();document.querySelector('.tm-new form').requestSubmit();true"},{'sleep':100})
        actions=[e for e in self.non_history_actions() if e['type']=='ext.post' and json.loads(e['data']['text']).get('kind')=='send_new']
        self.assertEqual(len(actions),1);q=json.loads(actions[0]['data']['text'])
        self.page({'go':'about:blank'},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"!!document.querySelector('.tm-new-trigger')"},{'tapSelector':'.tm-new-trigger'})
        self.assertFalse(self.page({'eval':"document.querySelector('.tm-new-send').disabled"})[-1]['eval'])
        self.page({'eval':"(()=>{const t=document.querySelector('.tm-new-text');t.value='Newer unsent message';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"})
        self.feed({'kind':'sent','rid':q['rid'],'to':'telegram:wrong'})
        self.page({'sleep':100});self.assertFalse(self.page({'eval':"document.querySelector('.tm-new-send').disabled"})[-1]['eval'])
        self.feed({'kind':'sent','rid':q['rid'],'to':q['to']})
        got=self.page({'until':"!document.querySelector('.tm-new-send').disabled"})
        self.assertTrue(got[-1]['until'],got)
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-new').open && document.querySelector('.tm-new-text').value==='Newer unsent message'"})[-1]['eval'])
        self.page({'key':'Escape'},{'until':"!document.querySelector('.tm-new').open"},
          {'until':"(()=>{const b=document.querySelector('.tm-new-trigger'),r=b.getBoundingClientRect();return b.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))})()"},{'tapSelector':'.tm-new-trigger'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-new-text').value"})[-1]['eval'],'Newer unsent message')

    def test_new_recipient_reply_keeps_exact_target_and_refused_draft_across_reload(self):
        self.seed_inbox(start_editing=False)
        self.edit('Existing conversation draft')
        self.page({'tapSelector':'.tm-close-conversation'},{'tapSelector':'.tm-new-trigger'},{'until':"!!document.querySelector('.tm-new[open]')"},
          {'eval':"(()=>{const t=document.querySelector('.tm-new-search');t.value='Ada';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"},{'sleep':650})
        lookup=self.queued('contacts')
        self.feed({'kind':'contacts','rid':lookup['rid'],'q':'Ada','items':[{'src':'email','to':'email:synthetic-account:ada@example.invalid','name':'Ada Review','hint':'ada@example.invalid'}],'errors':{}})
        self.page({'until':"!!document.querySelector('.tm-new-contact')"},{'tapSelector':'.tm-new-contact'},
          {'eval':"(()=>{for(const [s,v] of [['.tm-new-text','Exact first message'],['.tm-new-subject','Exact subject']]){const t=document.querySelector(s);t.value=v;t.dispatchEvent(new Event('input',{bubbles:true}))}return true})()"},
          {'tapSelector':'.tm-new-send'},{'sleep':100})
        q=self.queued('send_new');self.assertEqual(q['to'],'email:synthetic-account:ada@example.invalid');self.assertEqual(q['text'],'Exact first message');self.assertEqual(q['subject'],'Exact subject')
        self.feed({'kind':'send_failed','rid':q['rid'],'to':q['to'],'error':'Synthetic first-message refusal'})
        got=self.page({'until':"document.querySelector('.tm-new-status')?.textContent.includes('Synthetic first-message refusal')"})
        self.assertTrue(got[-1]['until'],got)
        self.page({'go':'about:blank'},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"!!document.querySelector('.tm-new-trigger')"},
          {'tapSelector':'.tm-new-trigger'},{'until':"document.querySelector('.tm-new-text')?.value==='Exact first message'"})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-new-subject').value"})[-1]['eval'],'Exact subject')
        self.page({'tapSelector':'.tm-new-send'},{'sleep':100});retry=self.queued('send_new')
        self.assertNotEqual(retry['rid'],q['rid']);self.assertEqual(retry['to'],q['to']);self.assertEqual(retry['text'],q['text'])
        self.feed({'kind':'sent','rid':q['rid'],'to':q['to']})
        self.page({'sleep':100});self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-new[open]')"})[-1]['eval'])
        self.feed({'kind':'sent','rid':retry['rid'],'to':retry['to']})
        got=self.page({'until':"!document.querySelector('.tm-new[open]')"});self.assertTrue(got[-1]['until'],got)
        self.page({'tapSelector':'.tm-person'},{'until':"!!document.querySelector('.tm-shared-compose textarea')"})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Existing conversation draft')

    def test_outgoing_native_delivery_indicators_are_exact_assets(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram')
        for state,name in (('scheduled','clock'),('send_failed','warning'),('sent','double-tick')):
            rid='synthetic-'+name
            self.ev('ext.post',None,plugin='teams',channel='web',owner=True,text=json.dumps({'kind':'send','id':'external-telegram','rid':rid,'text':'Reply '+name}))
            self.feed({'kind':state,'id':'external-telegram','rid':rid,'at':'2030-01-01T12:00:00Z','error':'Synthetic refusal'})
        self.page({'tapSelector':'.tm-close-conversation'},{'tapSelector':"[aria-label='Sent conversations']"},
          {'until':"[...document.querySelectorAll('.tm-person')].some(n=>n.textContent.includes('Synthetic telegram'))"},
          {'eval':"[...document.querySelectorAll('.tm-person')].find(n=>n.textContent.includes('Synthetic telegram')).click();true"})
        got=self.page({'until':"document.querySelectorAll('.tm-sent-chat .tm-native-icon').length===3"});self.assertTrue(got[-1]['until'],got)
        for name in ('clock','warning','double-tick'):
            got=self.page({'eval':f"(()=>{{const n=document.querySelector('.tm-draft-text .tm-icon-{name}'),s=getComputedStyle(n);return {{width:s.width,mask:s.maskImage}}}})()"})[-1]['eval']
            self.assertEqual(got['width'],'16px');self.assertIn('/icons/'+name+'.svg',got['mask'])
        if os.environ.get('HUB_INBOX_SCREENSHOTS'):
            out=Path(os.environ['HUB_INBOX_SCREENSHOTS']);out.mkdir(parents=True,exist_ok=True)
            for width in (402,1240):
                for theme in ('light','dark'):
                    got=self.page({'media':theme},{'touch':width<600},{'shot':str(out/f'delivery-icons-{theme}-{width}.png'),'width':width,'height':874},
                      {'eval':"({theme:getComputedStyle(document.documentElement).colorScheme,overflow:document.documentElement.scrollWidth-innerWidth})"})[-1]['eval']
                    self.assertEqual(got,{'theme':theme,'overflow':0})

    def test_pending_reply_has_owner_attribution_and_native_chat_bubble(self):
        self.seed_inbox(start_editing=False)
        for source in ('telegram','email'):
            with self.subTest(source=source):
                self.open_external_source(source);self.edit('Exact outgoing reply')
                self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100});q=self.queued('send')
                self.assertTrue(self.page({'eval':"document.querySelector('.tm-mine .tm-draft-by').textContent.startsWith('Вы · ')"})[-1]['eval'])
                self.feed({'kind':'scheduled','id':q['id'],'rid':q['rid'],'at':'2030-01-01T12:00:00Z'})
                self.page({'until':"!!document.querySelector('.tm-unschedule')"})
                got=self.page({'eval':"(()=>{const n=document.querySelector('.tm-mine'),b=n.querySelector('.tm-draft-text'),s=n.querySelector('.tm-draft-by');return {chat:n.classList.contains('tm-sent-chat'),color:getComputedStyle(b).backgroundColor,bodyBottom:b.getBoundingClientRect().bottom,statusTop:s.getBoundingClientRect().top}})()"})[-1]['eval']
                self.assertEqual(got['chat'],source!='email')
                if source!='email':
                    self.assertEqual(got['color'],'rgb(31, 127, 59)');self.assertLessEqual(got['bodyBottom'],got['statusTop'])
                if os.environ.get('HUB_INBOX_SCREENSHOTS'):
                    out=Path(os.environ['HUB_INBOX_SCREENSHOTS']);out.mkdir(parents=True,exist_ok=True)
                    for width,theme in ((402,'light'),(1240,'dark')):
                        got=self.page({'media':theme},{'touch':width<600},{'shot':str(out/f'outgoing-{source}-{theme}-{width}.png'),'width':width,'height':874},
                          {'eval':"({theme:getComputedStyle(document.documentElement).colorScheme,overflow:document.documentElement.scrollWidth-innerWidth})"})[-1]['eval']
                        self.assertEqual(got,{'theme':theme,'overflow':0})

    def test_scheduled_cancel_waits_for_exact_receipt_and_keeps_newer_draft(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram');self.edit('Original scheduled reply')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100})
        q=self.queued('send')
        self.feed({'kind':'scheduled','id':q['id'],'rid':q['rid'],'at':'2030-01-01T12:00:00Z'})
        got=self.page({'until':"!!document.querySelector('.tm-unschedule')"});self.assertTrue(got[-1]['until'],got)
        self.edit('Newer separate reply')
        self.page({'tapSelector':'.tm-unschedule'},{'sleep':100})
        cancel=self.queued('cancel');self.assertEqual(cancel['rid'],q['rid']);self.assertEqual(cancel['id'],q['id'])
        self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-mine-later') && document.querySelector('.tm-unschedule').disabled"})[-1]['eval'])
        self.feed({'kind':'canceled','id':'wrong-source','rid':q['rid']})
        self.page({'sleep':100});self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-mine-later')"})[-1]['eval'])
        self.feed({'kind':'canceled','id':q['id'],'rid':q['rid']})
        got=self.page({'until':"!document.querySelector('.tm-mine-later')"});self.assertTrue(got[-1]['until'],got)
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Newer separate reply')
        self.page({'go':'about:blank'},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},
          {'until':"[...document.querySelectorAll('.tm-person')].some(n=>n.textContent.includes('Synthetic telegram'))"},
          {'eval':"[...document.querySelectorAll('.tm-person')].find(n=>n.textContent.includes('Synthetic telegram')).click();true"},
          {'until':"!!document.querySelector('.tm-shared-compose textarea')"})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Newer separate reply')
        self.assertEqual(self.non_history_actions(),[])
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100});new=self.queued('send')
        self.page(
          {'go':'about:blank'},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},
          {'until':"[...document.querySelectorAll('.tm-person')].some(n=>n.textContent.includes('Synthetic telegram'))"},
          {'eval':"[...document.querySelectorAll('.tm-person')].find(n=>n.textContent.includes('Synthetic telegram')).click();true"},
          {'until':"!!document.querySelector('.tm-shared-compose textarea')"})
        self.assertEqual(self.page({'eval':"Object.keys(localStorage).filter(k=>k.startsWith('hub.inbox.draft.v1:')&&k.includes('external-telegram')).map(k=>JSON.parse(localStorage.getItem(k)).pendingRid)"})[-1]['eval'],[new['rid']])
        self.feed({'kind':'sent','id':new['id'],'rid':new['rid']})
        got=self.page({'until':"!document.querySelector('.tm-detail:not([hidden]) .tm-shared-compose textarea')"});self.assertTrue(got[-1]['until'],got)

    def test_scheduled_cancel_preserves_collector_editor_hold(self):
        self.seed_inbox();self.acknowledge(self.queued('draft_control'));self.edit('Guarded scheduled reply')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100});q=self.queued('send')
        self.feed({'kind':'scheduled','id':q['id'],'rid':q['rid'],'at':'2030-01-01T12:00:00Z'})
        self.page({'until':"!!document.querySelector('.tm-unschedule')"},{'tapSelector':'.tm-unschedule'},{'sleep':100})
        cancel=self.queued('cancel');self.assertEqual(cancel['editor'],q['editor'])
        token={**self.token,'edit_version':self.token['edit_version']+1}
        self.feed({'kind':'draft_state','id':q['id'],'rid':q['rid'],'inbox':token})
        self.feed({'kind':'canceled','id':q['id'],'rid':q['rid']})
        got=self.page({'until':"!document.querySelector('.tm-mine-later')"});self.assertTrue(got[-1]['until'],got)
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100})
        retry=self.queued('send');self.assertEqual(retry['inbox'],token);self.assertEqual(retry['editor'],q['editor'])
        self.assertEqual(retry['text'],q['text']);self.assertNotEqual(retry['rid'],q['rid'])

    def test_scheduled_cancel_recovers_original_reply_after_refused_request(self):
        self.seed_inbox(start_editing=False);self.open_external_source('whatsapp');self.edit('Keep scheduled reply')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100});q=self.queued('send')
        self.feed({'kind':'scheduled','id':q['id'],'rid':q['rid'],'at':'2030-01-01T12:00:00Z'})
        got=self.page({'until':"!!document.querySelector('.tm-unschedule')"});self.assertTrue(got[-1]['until'],got)
        if os.environ.get('HUB_INBOX_SCREENSHOTS'):
            out=Path(os.environ['HUB_INBOX_SCREENSHOTS']);out.mkdir(parents=True,exist_ok=True)
            for width,theme in ((402,'light'),(1240,'dark')):
                got=self.page({'media':theme},{'touch':width<600},{'shot':str(out/f'unschedule-{theme}-{width}.png'),'width':width,'height':874},
                  {'eval':"({theme:getComputedStyle(document.documentElement).colorScheme,overflow:document.documentElement.scrollWidth-innerWidth})"})[-1]['eval']
                self.assertEqual(got,{'theme':theme,'overflow':0})
        self.page({'eval':"window.__fetch=window.fetch;window.fetch=async(url,opts)=>{if(String(url).endsWith('/api/feed/post')&&JSON.parse(opts?.body||'{}').text?.includes('cancel'))return new Response(JSON.stringify({error:'Synthetic cancel refusal'}),{status:503});return __fetch(url,opts)};true"},
          {'tapSelector':'.tm-unschedule'},{'until':"!!document.querySelector('.tm-cancel-error')"})
        self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-mine-later') && !document.querySelector('.tm-unschedule').disabled"})[-1]['eval'])
        self.page({'eval':'window.fetch=__fetch;true'},{'tapSelector':'.tm-unschedule'},{'sleep':100})
        self.assertEqual(self.queued('cancel')['rid'],q['rid'])
        self.feed({'kind':'canceled','id':q['id'],'rid':q['rid']})
        self.page({'until':"!document.querySelector('.tm-mine-later')"})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Keep scheduled reply')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100})
        retry=self.queued('send');self.assertNotEqual(retry['rid'],q['rid']);self.assertEqual(retry['text'],q['text']);self.assertEqual(retry['id'],q['id'])

    def test_scheduled_hub_reply_keeps_text_time_and_distinct_owner_attribution(self):
        self.seed_inbox(start_editing=False)
        self.feed({'kind':'scheduled','id':'source-a','rid':'automatic-later','text':'Automatic exact reply','at':'2030-01-01T12:00:00Z'})
        got=self.page({'until':"[...document.querySelectorAll('.tm-draft-by')].some(n=>n.textContent.startsWith('Хаб · '))"})
        self.assertTrue(got[-1]['until'],got)
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-history').textContent.includes('Automatic exact reply') && !document.querySelector('.tm-history').textContent.includes('Invalid Date')"})[-1]['eval'])
        self.ev('ext.post',None,plugin='teams',channel='web',owner=True,text=json.dumps({'kind':'send','id':'source-a','rid':'owner-later','text':'Owner exact reply'}))
        self.feed({'kind':'scheduled','id':'source-a','rid':'owner-later','at':'2030-01-02T12:00:00Z'})
        got=self.page({'until':"[...document.querySelectorAll('.tm-draft-by')].some(n=>n.textContent.startsWith('Вы · '))"})
        self.assertTrue(got[-1]['until'],got)
        rows=self.page({'eval':"[...document.querySelectorAll('.tm-draft-by')].map(n=>({by:n.textContent,text:n.parentNode.querySelector('.tm-draft-text').textContent}))"})[-1]['eval']
        self.assertEqual([(r['by'].split(' · ')[0],r['text']) for r in rows],[('Хаб','Automatic exact reply'),('Вы','Owner exact reply')])

    def open_external_source(self, source, token=False):
        self.feed({'kind':'config','v':3,'inbox_protocol':{'version':1,'editor_cas':True}})
        self.feed({'kind':'msg','id':'external-'+source,'contact':'synthetic/'+source,'src':source,'from':'Synthetic '+source,
                   'text':'Please review this source.','reply':True,'at':datetime.now(timezone.utc).isoformat(),
                   **({'inbox':self.token} if token else {})})
        self.page({'go':'about:blank'},{'until':"location.href==='about:blank'"},
          {'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},
          {'until':f"[...document.querySelectorAll('.tm-person')].some(n=>n.textContent.includes('Synthetic {source}'))"},
          {'eval':f"[...document.querySelectorAll('.tm-person')].find(n=>n.textContent.includes('Synthetic {source}')).click();true"},
          {'until':"!!document.querySelector('.tm-shared-compose textarea')"})

    def attach_synthetic_file(self, name='review.txt'):
        got=self.page({'eval':"""(()=>{const dt=new DataTransfer();dt.items.add(new File(['Synthetic attachment bytes'],%s,{type:'text/plain'}));document.querySelector('.tm-shared-compose form').dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt}));return true})()""" % json.dumps(name)},
          {'until':"!!document.querySelector('.tm-shared-compose .pchip') && !document.querySelector('.tm-shared-compose .pchip').textContent.match(/uploading|загружаю/)"})
        self.assertTrue(got[-1]['until'],got)

    def test_supported_external_sources_send_uploaded_file_without_text(self):
        self.seed_inbox(start_editing=False)
        for source in ('whatsapp','telegram','email'):
            with self.subTest(source=source):
                self.open_external_source(source)
                self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-shared-compose .attach')"})[-1]['eval'])
                self.attach_synthetic_file(source+'.txt')
                layout=self.page({'eval':"(()=>{const c=document.querySelector('.tm-shared-compose .composer'),a=c.querySelector('.attach').getBoundingClientRect(),b=c.querySelector('button[type=submit]').getBoundingClientRect();return {height:c.getBoundingClientRect().height,offset:Math.abs(a.top-b.top)}})()"})[-1]['eval']
                self.assertLessEqual(layout['height'],96,layout);self.assertLessEqual(layout['offset'],2,layout)
                if source=='whatsapp' and os.environ.get('HUB_INBOX_SCREENSHOTS'):
                    out=Path(os.environ['HUB_INBOX_SCREENSHOTS']);out.mkdir(parents=True,exist_ok=True)
                    for width,theme in ((402,'light'),(402,'dark'),(1240,'light'),(1240,'dark')):
                        got=self.page({'media':theme},{'touch':width<600},{'shot':str(out/f'files-{theme}-{width}.png'),'width':width,'height':874},
                          {'eval':"({theme:getComputedStyle(document.documentElement).colorScheme,overflow:document.documentElement.scrollWidth-innerWidth})"})[-1]['eval']
                        self.assertEqual(got,{'theme':theme,'overflow':0})
                self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100})
                q=self.queued('send');self.assertEqual(q['id'],'external-'+source);self.assertEqual(q['text'],'')
                self.assertEqual(len(q['files']),1);self.assertTrue(q['files'][0].endswith(source+'.txt'));self.assertNotIn('inbox',q)
                self.assertTrue(Path(q['files'][0]).is_file());self.assertEqual(Path(q['files'][0]).read_text(),'Synthetic attachment bytes')
                self.feed({'kind':'sent','id':q['id'],'rid':q['rid']})
                got=self.page({'until':"!document.querySelector('.tm-detail:not([hidden]) .tm-shared-compose textarea')"})
                self.assertTrue(got[-1]['until'],got)

    def test_uploaded_draft_survives_reload_and_collector_refusal_then_retries_exact_file(self):
        self.seed_inbox(start_editing=False);self.open_external_source('whatsapp');self.attach_synthetic_file()
        self.edit('Keep this caption')
        self.open_external_source('telegram')
        self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-shared-compose .pchip')"})[-1]['eval'])
        self.page({'go':'about:blank'},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},
          {'until':"[...document.querySelectorAll('.tm-person')].some(n=>n.textContent.includes('Synthetic whatsapp'))"},
          {'eval':"[...document.querySelectorAll('.tm-person')].find(n=>n.textContent.includes('Synthetic whatsapp')).click();true"},
          {'until':"!!document.querySelector('.tm-shared-compose .pchip')"})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Keep this caption')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100})
        q=self.queued('send');self.assertEqual(len(q['files']),1)
        self.feed({'kind':'send_failed','id':q['id'],'rid':q['rid'],'error':'Synthetic file delivery refusal'})
        self.page({'until':"document.querySelector('.tm-mine-fail')?.textContent.includes('Synthetic file delivery refusal')"})
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-shared-compose .pchip')?.textContent.includes('review.txt')"})[-1]['eval'])
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100})
        retry=self.queued('send');self.assertNotEqual(retry['rid'],q['rid']);self.assertEqual(retry['files'],q['files']);self.assertEqual(retry['text'],q['text'])
        self.feed({'kind':'sent','id':retry['id'],'rid':retry['rid']})
        got=self.page({'until':"!document.querySelector('.tm-detail:not([hidden]) .tm-shared-compose textarea')"})
        self.assertTrue(got[-1]['until'],got)
        self.assertFalse(self.page({'eval':"Object.values(localStorage).some(v=>v.includes('review.txt'))"})[-1]['eval'])

    def test_older_receipt_cannot_discard_a_new_file_still_uploading(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram');self.edit('First reply')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100})
        q=self.queued('send')
        self.page({'eval':"""window.__fetch=window.fetch;window.fetch=(url,opts)=>String(url).includes('/api/upload/raw')?new Promise(resolve=>{window.__releaseUpload=()=>resolve(__fetch(url,opts))}):__fetch(url,opts);
          const dt=new DataTransfer();dt.items.add(new File(['Second file'],'second.txt',{type:'text/plain'}));document.querySelector('.tm-shared-compose form').dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt}));true"""})
        self.feed({'kind':'sent','id':q['id'],'rid':q['rid']})
        got=self.page({'until':"!!document.querySelector('.tm-mine-ok')"},
          {'eval':"!!document.querySelector('.tm-detail:not([hidden]) .tm-shared-compose .pchip')"})
        self.assertTrue(got[-1]['eval'],got)
        self.page({'eval':"__releaseUpload();true"},{'until':"document.querySelector('.tm-shared-compose .pchip')?.textContent.includes('second.txt') && !document.querySelector('.tm-shared-compose .pchip')?.textContent.match(/uploading|загружаю/)"})
        self.assertTrue(self.page({'eval':"Object.values(localStorage).some(v=>v.includes('second.txt'))"})[-1]['eval'])

    def test_discard_uploaded_file_draft_does_not_return_on_reload(self):
        self.seed_inbox(start_editing=False);self.open_external_source('telegram');self.attach_synthetic_file()
        self.page({'tapSelector':'.tm-discard'})
        self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-shared-compose .pchip')"})[-1]['eval'])
        self.open_external_source('telegram')
        self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-shared-compose .pchip')"})[-1]['eval'])
        self.assertFalse([json.loads(e['data']['text']) for e in self.non_history_actions() if e['type']=='ext.post' and json.loads(e['data']['text']).get('kind')=='send'])

    def test_external_text_replies_do_not_inherit_teams_editor_protocol(self):
        self.seed_inbox(start_editing=False)
        for source in ('whatsapp','telegram','email'):
            with self.subTest(source=source):
                self.open_external_source(source)
                self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-instruction')"})[-1]['eval'])
                self.edit('Exact '+source+' reply')
                self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':100})
                q=self.queued('send');self.assertEqual(q['id'],'external-'+source);self.assertEqual(q['text'],'Exact '+source+' reply')
                self.assertNotIn('inbox',q);self.assertNotIn('editor',q)
                self.feed({'kind':'sent','id':q['id'],'rid':q['rid']})
                got=self.page({'until':"!document.querySelector('.tm-detail:not([hidden]) .tm-shared-compose textarea')"},
                  {'tapSelector':'[aria-label="Sent conversations"]'},
                  {'eval':f"[...document.querySelectorAll('.tm-person')].find(n=>n.textContent.includes('Synthetic {source}')).click();true"},
                  {'until':"!!document.querySelector('.tm-detail:not([hidden]) .tm-mine-ok')"})
                self.assertTrue(got[0]['until'],got)
                self.assertTrue(got[-1]['until'],got)

    def test_teams_without_token_still_refuses_plain_reply(self):
        self.seed_inbox(start_editing=False)
        self.open_external_source('dm')
        self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-instruction')"})[-1]['eval'])
        self.edit('Never bypass the Teams guard')
        self.page({'tapSelector':'.tm-shared-compose button[type=submit]'},{'sleep':150})
        posts=[json.loads(e['data']['text']) for e in self.non_history_actions() if e['type']=='ext.post']
        self.assertFalse([p for p in posts if p.get('kind')=='send'],posts)
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose textarea').value"})[-1]['eval'],'Never bypass the Teams guard')

    def test_explicit_source_token_keeps_guard_even_for_external_channel(self):
        self.seed_inbox(start_editing=False)
        self.open_external_source('whatsapp',token=True)
        self.edit('Guard this exact source')
        q=self.queued('draft_control');self.assertEqual(q['id'],'external-whatsapp');self.assertEqual(q['inbox'],self.token)
        self.assertFalse(self.page({'eval':"!!document.querySelector('.tm-shared-compose .attach')"})[-1]['eval'])

    def test_quick_hub_uploaded_file_survives_reload_and_targets_only_hub(self):
        self.seed_inbox(start_editing=False);self.page({'tapSelector':'.tm-quick-trigger'})
        self.page({'eval':"(()=>{const dt=new DataTransfer();dt.items.add(new File(['Quick synthetic file'],'quick.txt',{type:'text/plain'}));document.querySelector('.tm-quick form').dispatchEvent(new DragEvent('drop',{bubbles:true,cancelable:true,dataTransfer:dt}));return true})()"},
          {'until':"!!document.querySelector('.tm-quick .pchip') && !document.querySelector('.tm-quick .pchip').textContent.match(/uploading|загружаю/)"},
          {'tapSelector':'.tm-quick-close'},{'go':'about:blank'},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},
          {'until':"!!document.querySelector('.tm-person')"},{'tapSelector':'.tm-person'},{'tapSelector':'.tm-quick-trigger'})
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-quick .pchip')?.textContent.includes('quick.txt') || false"})[-1]['eval'])
        self.page({'tapSelector':'.tm-quick button[type=submit]'},{'until':"!document.querySelector('.tm-quick[open]')"})
        sent=[e['data'] for e in self.spooled() if e['type']=='message.received']
        self.assertEqual(len(sent),1,sent);self.assertEqual(sent[0]['to'],'hub');self.assertEqual(sent[0]['text'],'(вложения)');self.assertEqual(sent[0]['attachments'][0]['name'],'quick.txt')
        self.assertFalse(self.page({'eval':"Object.values(localStorage).some(v=>v.includes('quick.txt'))"})[-1]['eval'])

    def test_quick_hub_acceptance_does_not_hide_or_delete_newer_draft(self):
        self.seed_inbox(start_editing=False);self.page({'tapSelector':'.tm-quick-trigger'},
          {'eval':"(()=>{const t=document.querySelector('.tm-quick textarea');t.value='First quick message';t.dispatchEvent(new Event('input',{bubbles:true}));window.__fetch=window.fetch;window.fetch=(url,opts)=>String(url)==='/api/send'?new Promise(resolve=>{window.__releaseQuick=()=>resolve(__fetch(url,opts))}):__fetch(url,opts);return true})()"},
          {'tapSelector':'.tm-quick button[type=submit]'},
          {'eval':"(()=>{const t=document.querySelector('.tm-quick textarea');t.value='Newer quick draft';t.dispatchEvent(new Event('input',{bubbles:true}));__releaseQuick();return true})()"}, {'sleep':200})
        self.assertTrue(self.page({'eval':"!!document.querySelector('.tm-quick[open]')"})[-1]['eval'])
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-quick textarea').value"})[-1]['eval'],'Newer quick draft')
        self.assertTrue(self.page({'eval':"Object.values(localStorage).includes('Newer quick draft')"})[-1]['eval'])

    def test_quick_voice_cannot_close_while_recording_and_cancel_sends_nothing(self):
        with mock.patch.dict(os.environ,{'VOICE_CMD':'true'}):
            self.seed_inbox(start_editing=False);self.page({'tapSelector':'.tm-quick-trigger'},
              {'until':"!!document.querySelector('.tm-quick .mic')"},
              {'eval':"navigator.permissions.query=()=>Promise.resolve({state:'granted'});navigator.mediaDevices.getUserMedia=()=>Promise.resolve(new AudioContext().createMediaStreamDestination().stream);true"},
              {'tapSelector':'.tm-quick .mic'}, {'until':"!!document.querySelector('.tm-quick [data-rec-clock]')"},
              {'tapSelector':'.tm-quick-close'})
            got=self.page({'eval':"({open:!!document.querySelector('.tm-quick[open]'),recording:!!document.querySelector('.tm-quick .rec'),notice:!document.querySelector('.tm-quick-notice').hidden})"})[-1]['eval']
            self.assertEqual(got,{'open':True,'recording':True,'notice':True})
            got=self.page({'tapSelector':'.tm-quick .recstrip .linkbtn'},{'until':"!document.querySelector('.tm-quick .rec')"},{'tapSelector':'.tm-quick-close'},
              {'eval':"!document.querySelector('.tm-quick[open]')"})
            self.assertTrue(got[-1]['eval'],got)
        self.assertFalse([e for e in self.spooled() if e['type']=='message.received'])

    def test_quick_hub_refusal_retains_text_and_escape_keeps_conversation(self):
        self.seed_inbox(start_editing=False)
        self.page({'tapSelector':'.tm-quick-trigger'},{'eval':"(()=>{const t=document.querySelector('.tm-quick textarea');t.value='Keep refused quick message';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"})
        act=self.web.act
        with mock.patch.object(self.web,'act',side_effect=lambda path,body:(403,'Synthetic quick refusal') if path=='/api/send' else act(path,body)) as calls:
            got=self.page({'tapSelector':'.tm-quick button[type=submit]'},{'until':"document.querySelector('.tm-quick .error-text')?.textContent.includes('Synthetic quick refusal')"},{'eval':"({open:document.querySelector('.tm-quick')?.open,text:document.querySelector('.tm-quick')?.textContent})"})[-1]['eval']
            self.assertIn('Synthetic quick refusal',got['text'],(got,str(calls.call_args_list)))
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-quick[open] textarea').value"})[-1]['eval'],'Keep refused quick message')
        for width,theme in ((360,'light'),(402,'dark'),(834,'light'),(1240,'dark')):
            steps=[{'media':theme},{'viewport':{'width':width,'height':874}},{'eval':"(()=>{const r=document.querySelector('.tm-quick').getBoundingClientRect();return {left:r.left,right:r.right,bottom:r.bottom,overflow:document.documentElement.scrollWidth-innerWidth}})()"}]
            got=self.page(*steps)[-1]['eval'];self.assertGreaterEqual(got['left'],0);self.assertLessEqual(got['right'],width);self.assertLessEqual(got['bottom'],874);self.assertEqual(got['overflow'],0)
            if os.environ.get('HUB_INBOX_SCREENSHOTS'):
                out=Path(os.environ['HUB_INBOX_SCREENSHOTS']);out.mkdir(parents=True,exist_ok=True)
                shot=self.page({'media':theme},{'touch':width<600},{'shot':str(out/f'quick-{theme}-{width}.png'),'width':width,'height':874},{'eval':"getComputedStyle(document.documentElement).colorScheme"})[-1]['eval']
                self.assertEqual(shot,theme)
        self.page({'key':'Escape'},{'until':"!document.querySelector('.tm-quick[open]')"})
        self.assertEqual(self.page({'eval':'location.hash'})[-1]['eval'],'#/x/inbox')
        self.assertFalse([e for e in self.spooled() if e['type'] in ('ext.post','message.received')])

    def test_quick_hub_message_preserves_reply_and_its_own_draft(self):
        self.seed_inbox(start_editing=False);self.edit('Keep recipient reply');self.acknowledge(self.queued('draft_control'))
        self.page({'tapSelector':'.tm-quick-trigger'},{'until':"!!document.querySelector('.tm-quick[open] textarea')"},
          {'eval':"(()=>{const t=document.querySelector('.tm-quick textarea');t.value='Unsent quick Hub message';t.dispatchEvent(new Event('input',{bubbles:true}));return true})()"},
          {'tapSelector':'.tm-quick-close'},{'tapSelector':'.tm-quick-trigger'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-quick textarea').value"})[-1]['eval'],'Unsent quick Hub message')
        self.assertFalse([e for e in self.non_history_actions() if e['type'] in ('ext.post','message.received')])
        self.page({'tapSelector':'.tm-quick-close'},{'go':'about:blank'},{'until':"location.href==='about:blank' && document.readyState==='complete'"},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"!!document.querySelector('.tm-person')"},{'tapSelector':'.tm-person'},{'tapSelector':'.tm-quick-trigger'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-quick textarea').value"})[-1]['eval'],'Unsent quick Hub message')
        self.page({'tapSelector':'.tm-quick button[type=submit]'},{'until':"!document.querySelector('.tm-quick[open]')"})
        sent=[e for e in self.spooled() if e['type']=='message.received'];self.assertEqual(len(sent),1,sent);self.assertEqual(sent[0]['data']['to'],'hub');self.assertEqual(sent[0]['data']['text'],'Unsent quick Hub message')
        got=self.page({'eval':"({route:location.hash,reply:document.querySelector('.tm-shared-compose textarea').value})"})[-1]['eval']
        self.assertEqual(got,{'route':'#/x/inbox','reply':'Keep recipient reply'})
        self.page({'tapSelector':'.tm-quick-trigger'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-quick textarea').value"})[-1]['eval'],'')

    def test_voice_failure_is_visible_and_transcript_stays_in_the_bubble(self):
        self.seed_inbox(start_editing=False)
        self.page({'tapSelector':'.tm-earlier'});self.queued('history')
        self.feed({'kind':'thread','id':'source-a','part':0,'of':1,'more':False,'items':[{'id':'voice','text':'','media':[{'kind':'voice','url':'/api/file?path=missing-voice.wav','dur':6,'text':'Retain this transcript'}]}]})
        got=self.page({'until':"!!document.querySelector('.tm-voice .tm-media-error:not([hidden])')"},{'eval':"(()=>{const v=document.querySelector('.tm-voice'),b=v.querySelector('button'),r=b.getBoundingClientRect();return {text:v.textContent,native:!v.querySelector('audio').controls,label:b.getAttribute('aria-label'),width:r.width,height:r.height}})()"})[-1]['eval']
        self.assertIn('Retain this transcript',got['text']);self.assertTrue(got['native']);self.assertIn(got['label'],('Play','Воспроизвести'));self.assertGreaterEqual(got['width'],44);self.assertGreaterEqual(got['height'],44)
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])

    def test_reply_composer_keeps_one_row_with_or_without_discard(self):
        self.seed_inbox(start_editing=False)
        for width in (360,402,834,1240):
            self.page({'viewport':{'width':width,'height':874}})
            for text in ('','Short reply'):
                self.edit(text)
                got=self.page({'eval':"(()=>{const c=document.querySelector('.tm-shared-compose .composer'),d=c.querySelector('.tm-discard'),t=c.querySelector('textarea'),a=c.querySelector('.composer-actions > :last-child'),r=x=>x.getBoundingClientRect();return {height:r(c).height,discard:d.hidden,overlap:!d.hidden && r(d).right>r(t).left+1,actionOverlap:r(t).right>r(a).left+1,overflow:document.documentElement.scrollWidth-innerWidth}})()"})[-1]['eval']
                self.assertLessEqual(got['height'],50,(width,text,got));self.assertEqual(got['discard'],not bool(text));self.assertFalse(got['overlap']);self.assertFalse(got['actionOverlap']);self.assertEqual(got['overflow'],0)

    def test_link_preview_keeps_exact_destination_and_treats_metadata_as_text(self):
        self.seed_inbox(start_editing=False)
        with mock.patch.object(self.web.previews,'get',return_value={'url':'https://wrong.example/','title':'Lighting <img src=x onerror=alert(1)>','site':'Design studio','image':'javascript:alert(1)'}) as preview:
            self.page({'tapSelector':'.tm-earlier'});self.queued('history')
            self.feed({'kind':'thread','id':'source-a','part':0,'of':1,'more':False,'items':[{'id':'link-a','me':True,'text':'See https://example.com/lighting','at':'2026-01-01T12:00:00Z'}]})
            got=self.page({'until':"!!document.querySelector('.tm-link-preview strong')"},{'eval':"(()=>{const p=document.querySelector('.tm-link-preview');return {href:p.href,text:p.textContent,unsafe:!!p.querySelector('img'),blank:p.target,rel:p.rel}})()"})[-1]['eval']
            self.assertEqual(got['href'],'https://example.com/lighting');self.assertIn('<img src=x onerror=alert(1)>',got['text']);self.assertFalse(got['unsafe']);self.assertEqual(got['blank'],'_blank');self.assertIn('noopener',got['rel'])
            preview.assert_called_once_with('https://example.com/lighting')
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])

    def test_history_retains_native_reply_context_and_file_details(self):
        self.seed_inbox(start_editing=False)
        self.feed({'kind':'msg','id':'source-a','contact':'synthetic-account/conversation-a','src':'dm','where':'Synthetic account','from':'Review colleague','text':'Please check the navigation.','reply':True,'inbox':self.token,'at':datetime.now(timezone.utc).isoformat()})
        self.page({'wait':'Synthetic account'})
        self.assertEqual(self.page({'eval':"document.querySelectorAll('.tm-person[aria-current=true]').length"})[-1]['eval'],1)
        self.page({'tapSelector':'.tm-earlier'});self.queued('history')
        self.feed({'kind':'thread','id':'source-a','part':0,'of':1,'more':False,'items':[
            {'id':'quoted','me':True,'text':'The reply itself','at':'2026-01-01T12:00:00Z','reply':{'from':'Alex','text':'Which document <img src=x onerror=alert(1)>?'},'reactions':[{'emoji':'👍','n':2}]},
            {'id':'forwarded','text':'Updated attachment','fwd':'Design studio','edited':True,'at':'2026-01-01T12:01:00Z','media':[{'kind':'file','name':'Estimate.pdf','url':'/api/file?path=estimate.pdf','size':184320}]}]})
        got=self.page({'wait':'The reply itself'},{'eval':"(()=>{const own=document.querySelector('.tm-own'),file=document.querySelector('.tm-media-file');return {quote:own.querySelector('.tm-quote')?.textContent,unsafe:!!own.querySelector('.tm-quote img'),reaction:own.querySelector('.tm-received-reactions')?.textContent,color:getComputedStyle(own.querySelector('.tm-text')).backgroundColor,file:file.textContent,icon:!!file.querySelector('.tm-file-icon'),context:document.querySelector('.tm-history').textContent}})()"})[-1]['eval']
        self.assertIn('Alex',got.get('quote') or '',got);self.assertIn('<img src=x onerror=alert(1)>',got['quote']);self.assertFalse(got['unsafe'])
        self.assertEqual(got['reaction'],'👍 2');self.assertEqual(got['color'],'rgb(31, 127, 59)')
        self.assertIn('184 KB',got['file']);self.assertTrue(got['icon']);self.assertIn('Design studio',got['context']);self.assertRegex(got['context'],r'Edited|Изменено')
        for width in (360,402,768,834,1024,1240,1440):
            got=self.page({'viewport':{'width':width,'height':874}},{'eval':"({page:document.documentElement.scrollWidth-innerWidth,history:document.querySelector('.tm-history').scrollWidth-document.querySelector('.tm-history').clientWidth})"})[-1]['eval']
            self.assertEqual(got,{'page':0,'history':0},(width,got))

    def test_unrelated_feed_keeps_media_node_and_existing_message_text(self):
        self.seed_inbox(start_editing=False)
        self.feed({'kind':'msg','id':'audio-a','src':'dm','contact':'synthetic/audio','from':'Audio colleague','text':'Keep media message text','reply':True,'at':datetime.now(timezone.utc).isoformat(),'media':[{'kind':'voice','url':'/api/file?path=synthetic.wav'}]})
        self.page({'tapSelector':'.tm-close-conversation'},{'until':"document.querySelectorAll('.tm-person').length===2"},{'tapSelector':'.tm-person:first-child'},
          {'eval':"window.__originalPlayer=document.querySelector('.tm-history audio');true"})
        self.feed({'kind':'msg','id':'another-a','src':'dm','contact':'synthetic/another','from':'Another colleague','text':'Unrelated feed refresh','reply':True,'at':datetime.now(timezone.utc).isoformat()})
        got=self.page({'until':"document.querySelector('.tm-list').textContent.includes('Unrelated feed refresh')"},{'eval':"({same:__originalPlayer===document.querySelector('.tm-history audio'),text:document.querySelector('.tm-history').textContent})"})[-1]['eval']
        self.assertTrue(got['same'],got);self.assertIn('Keep media message text',got['text'])

    def test_discard_clears_only_local_draft_and_stays_cleared_after_reload(self):
        self.seed_inbox();self.acknowledge(self.queued('draft_control'));self.edit('Discard this local reply')
        self.page({'tapSelector':'.tm-shared-compose .composer [aria-label="Discard draft"]'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],'')
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])
        self.page({'go':'about:blank'},{'until':"location.href==='about:blank' && document.readyState==='complete'"},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"!!document.querySelector('.tm-person')"},{'tapSelector':'.tm-person'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],'')
        self.edit('New reply after discard')
        got=self.page({'viewport':{'width':402,'height':874}},{'eval':"(()=>{const b=document.querySelector('.tm-discard'),r=b.getBoundingClientRect();return {visible:!b.hidden,width:r.width,height:r.height,inComposer:!!b.closest('.composer'),overflow:document.documentElement.scrollWidth-innerWidth}})()"})[-1]['eval']
        self.assertTrue(got['visible']);self.assertTrue(got['inComposer']);self.assertGreaterEqual(got['width'],44);self.assertGreaterEqual(got['height'],44);self.assertEqual(got['overflow'],0)

    def test_history_is_requested_only_by_earlier_action(self):
        self.seed_inbox(start_editing=False)
        self.assertFalse([e for e in self.spooled() if e['type']=='ext.post'])
        self.assertIn(self.page({'eval':"document.querySelector('.tm-earlier').textContent"})[-1]['eval'],['Earlier messages','Показать более ранние'])
        self.page({'tapSelector':'.tm-earlier'})
        self.assertEqual(self.queued('history')['id'],'source-a')
        self.assertTrue(self.page({'eval':"document.querySelector('.tm-earlier').disabled"})[-1]['eval'])
        self.feed({'kind':'thread','id':'source-a','part':0,'of':1,'more':False,'items':[{'id':'older-one','text':'Earlier visible after one click'}]})
        self.page({'wait':'Earlier visible after one click'})

    def test_first_send_waits_for_editor_confirmation_without_second_click(self):
        self.seed_inbox(start_editing=False)
        self.edit('Single deliberate send')
        self.page({'tapSelector':'.tm-shared-compose .composer button[type=submit]'})
        hold=self.queued('draft_control');self.acknowledge(hold)
        self.page({'until':"document.querySelector('.tm-mine-wait')?.textContent.includes('Single deliberate send')"})
        q=self.queued('send');self.assertEqual(q['text'],'Single deliberate send')
        self.assertEqual(q['inbox'],self.token)

    def test_send_waiting_for_confirmation_cancels_after_edit_and_keeps_both_texts(self):
        self.seed_inbox(start_editing=False);self.edit('Attempted reply')
        self.page({'tapSelector':'.tm-shared-compose .composer button[type=submit]'})
        hold=self.queued('draft_control');self.edit('Newer unsent text')
        self.page({'wait':'The draft or conversation changed.'});self.acknowledge(hold)
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])
        expected='Attempted reply\nNewer unsent text'
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],expected)
        self.page({'go':'about:blank'},{'until':"location.href==='about:blank' && document.readyState==='complete'"},{'go':f'http://127.0.0.1:{self.port}/#/x/inbox'},{'until':"!!document.querySelector('.tm-person')"},{'tapSelector':'.tm-person'})
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],expected)

    def test_send_waiting_for_confirmation_cancels_after_back_navigation(self):
        self.seed_inbox(start_editing=False);self.edit('Keep this pending reply')
        self.page({'tapSelector':'.tm-shared-compose .composer button[type=submit]'})
        hold=self.queued('draft_control')
        self.page({'tapSelector':'.tm-close-conversation'})
        self.token={**self.token,'edit_version':1,'held':True,'holder':hold['editor']}
        self.feed({'kind':'draft_state','id':'source-a','rid':hold['rid'],'inbox':self.token})
        self.page({'sleep':200},{'tapSelector':'.tm-person'},{'wait':'The draft or conversation changed.'})
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],'Keep this pending reply')

    def test_first_send_refusal_keeps_reply_and_never_posts_send(self):
        self.seed_inbox(start_editing=False);self.edit('Keep refused reply')
        self.page({'tapSelector':'.tm-shared-compose .composer button[type=submit]'})
        hold=self.queued('draft_control')
        self.feed({'kind':'draft_control_failed','id':'source-a','rid':hold['rid'],'error':'Synthetic editor refusal'})
        self.page({'wait':'Synthetic editor refusal'})
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])
        self.assertEqual(self.page({'eval':"document.querySelector('.tm-shared-compose .composer textarea').value"})[-1]['eval'],'Keep refused reply')

    def test_untouched_suggestion_sends_once_after_its_first_confirmation(self):
        self.seed_inbox(start_editing=False)
        post=self.page({'eval':"fetch('/api/feed?plugin=teams').then(r=>r.json()).then(d=>d.posts.find(p=>{try{return JSON.parse(p.text).id==='source-a'}catch{return false}}).id)"})[-1]['eval']
        self.page({'tapSelector':'.tm-editor-options > summary'},{'click':'Close editor'})
        self.ev('ext.post',None,plugin='teams',channel='session',owner=False,sender='hub',reply_to=post,text='Untouched suggestion')
        self.page({'wait':'Untouched suggestion'},{'tapSelector':'.tm-close-conversation'},{'tapSelector':'.tm-person'})
        self.assertFalse([e for e in self.non_history_actions() if e['type']=='ext.post'])
        self.page({'tapSelector':'.tm-shared-compose .composer button[type=submit]'})
        self.acknowledge(self.queued('draft_control'))
        self.page({'until':"document.querySelector('.tm-mine-wait')?.textContent.includes('Untouched suggestion')"})
        self.assertEqual(self.queued('send')['text'],'Untouched suggestion')

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
        self.page({'wait':'See https://example.test/meeting'})
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

    def test_history_long_links_never_scroll_the_conversation_sideways(self):
        self.seed_inbox(start_editing=False);self.page({'tapSelector':'.tm-earlier'});self.queued('history')
        target='https://example.test/'+('long-path-'*24)
        self.feed({'kind':'thread','id':'source-a','part':0,'of':1,'more':False,'items':[{'id':'own-long','me':True,'text':'Exact link '+target}]})
        self.page({'wait':'Exact link'})
        for width in (360,402,834,1240):
            got=self.page({'viewport':{'width':width,'height':874}},{'eval':"(()=>{const h=document.querySelector('.tm-history'),a=h.querySelector('.tm-own a');return {width:h.clientWidth,scroll:h.scrollWidth,href:a.href}})()"})[-1]['eval']
            self.assertEqual(got['href'],target);self.assertLessEqual(got['scroll'],got['width'],got)

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
            self.assertGreaterEqual(got['target'],43.99);self.assertGreaterEqual(got['left'],0);self.assertLessEqual(got['right'],width);self.assertEqual(got['overflow'],0)
            if os.environ.get("HUB_INBOX_SCREENSHOTS"):
                Path(os.environ["HUB_INBOX_SCREENSHOTS"]).mkdir(parents=True,exist_ok=True)
                self.page({"media":theme},{"shot":str(Path(os.environ["HUB_INBOX_SCREENSHOTS"])/f"sort-{theme}-{width}.png"),"width":width,"height":874})
            self.page({"eval":"document.querySelector('.tm-sort summary').focus();true"},{"key":"Escape"})
            self.assertFalse(self.page({"eval":"document.querySelector('.tm-sort').open"})[-1]['eval'])
        self.assertFalse([e for e in self.spooled() if e['type']=='message.received'])

    def test_history_refresh_preserves_reading_position_and_other_conversation(self):
        self.seed_inbox(start_editing=False)
        self.page({'tapSelector':'.tm-earlier'})
        self.queued("history")
        self.feed({"kind":"thread","id":"source-a","part":0,"of":1,"more":False,"items":[
            {"id":f"old-{i}","at":f"2026-01-01T12:{i:02d}:00Z","text":f"Earlier item {i} with enough text to wrap across the phone screen."} for i in range(10)]})
        self.page({"wait":"Earlier item 0"},
                  {"eval":"document.querySelector('.tm-history').scrollTop=250"})
        position=self.page({"eval":"document.querySelector('.tm-history').scrollTop"})[-1]['eval']
        self.assertGreater(position,0)
        self.feed({"kind":"msg","id":"source-b","contact":"synthetic-account/conversation-b","src":"dm","from":"Other colleague","text":"Different conversation","at":"2026-01-02T12:00:00Z","reply":True})
        self.page({"until":"document.querySelectorAll('.tm-person').length===2"})
        self.assertAlmostEqual(self.page({"eval":"document.querySelector('.tm-history').scrollTop"})[-1]['eval'],position,delta=1)
        self.page({"tapSelector":".tm-close-conversation"},{"tapSelector":".tm-person:last-child"},{'tapSelector':'.tm-earlier'})
        self.assertEqual(self.queued("history")["id"],"source-b")
        self.feed({"kind":"thread","id":"source-a","part":0,"of":1,"more":False,"items":[{"id":"late-a","text":"Late result for first conversation"}]})
        self.feed({"kind":"thread","id":"source-b","part":0,"of":1,"more":False,"items":[{"id":"old-b","text":"History for second conversation"}]})
        got=self.page({"wait":"History for second conversation"},{"eval":"document.querySelector('.tm-history').textContent"})[-1]['eval']
        self.assertIn("History for second conversation",got);self.assertNotIn("Late result for first conversation",got)

    def test_history_chunks_pagination_refusal_and_retry_keep_exact_conversation(self):
        self.seed_inbox(start_editing=False)
        self.page({'tapSelector':'.tm-earlier'})
        q=self.queued("history");self.assertEqual(q["id"],"source-a")
        self.feed({"kind":"thread","id":"source-a","part":0,"of":2,"more":True,"items":[{"id":"old-1","at":"2026-01-01T12:00:00Z","from":"Review colleague","text":"Historical detail"}]})
        self.page({"sleep":100})
        self.assertNotIn("Historical detail",self.page({"eval":"document.querySelector('.tm-detail').textContent"})[-1]['eval'])
        self.feed({"kind":"thread","id":"source-a","part":1,"of":2,"more":True,"items":[{"id":"old-2","at":"2026-01-02T12:00:00Z","from":"Owner","me":True,"text":"Older reply"},
                    {"at":datetime.now(timezone.utc).isoformat(),"from":"Review colleague","text":"Please check the navigation."}]})
        self.page({"wait":"Historical detail"})
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
        link=self.page({"eval":"(()=>{const a=document.querySelector('.tm-media-file'),s=getComputedStyle(a);return {color:s.color,expected:getComputedStyle(document.querySelector('.tm')).color,decoration:s.textDecorationLine}})()"})[-1]['eval']
        self.assertEqual(link['color'],link['expected'],link);self.assertEqual(link['decoration'],'none',link)
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
    suite = unittest.TestSuite(InboxWebAcceptance(n) for n in InboxWebAcceptance.__dict__ if n.startswith("test_"))
    suite.addTests(loader.loadTestsFromTestCase(SpoolFixtureAcceptance))
    return suite


class SpoolFixtureAcceptance(unittest.TestCase):
    def test_consuming_a_snapshot_preserves_inflight_and_new_facts(self):
        import tempfile
        from types import SimpleNamespace
        from core import spool
        with tempfile.TemporaryDirectory() as state:
            box=Path(state)/"spool"
            spool.put(str(box),"ext.post",data={"text":"first"})
            inflight=box/".writer.tmp"
            inflight.write_text("unfinished atomic write")
            take=spool.take
            def arrival(path):
                ready=take(path)
                spool.put(str(box),"ext.post",data={"text":"arrived after snapshot"})
                return ready
            fixture=SimpleNamespace(state=state)
            with mock.patch.object(spool,"take",side_effect=arrival):
                consumed=InboxWebAcceptance.spooled(fixture)
            self.assertEqual([e["data"]["text"] for e in consumed],["first"])
            self.assertTrue(inflight.exists(),"The fixture deleted the writer's atomic temporary file")
            self.assertEqual([e["data"]["text"] for _,e in take(str(box))],["arrived after snapshot"])
