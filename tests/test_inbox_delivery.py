"""Canonical collector delivery races: only synthetic accounts and transport."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('HUB_STATE_DIR', '/tmp/teams-inbox-delivery-test')
import main
import inbox_delivery as delivery


def incoming(key='a', text='Verified facts', chat='chat-a'):
    return {'key':key, 'text':text, 'at':'2026-10-15T12:00:00Z', 'src':'dm',
            'box':chat, 'ref':{'chat':chat}, 'from':'Person', 'contact':chat}


def state():
    st = {'me':{'id':'account-a'}, 'cfg':{'inbox_guard':True},
          'hours':{'from':'00:00','to':'24:00','weekends':True}}
    delivery.observe(st, incoming())
    st['refs'] = {'a':{'chat':'chat-a'}}
    st['open'] = {'a':['chat-a','2026-10-15T12:00:00Z']}
    return st


class Delivery(unittest.TestCase):
    def test_second_collector_writer_cannot_enter_shared_state(self):
        with tempfile.TemporaryDirectory() as folder:
            with delivery.writer_lock(str(Path(folder,'collector.lock'))):
                with self.assertRaises(OSError):
                    with delivery.writer_lock(str(Path(folder,'collector.lock'))):
                        self.fail('Second collector entered')
            with delivery.writer_lock(str(Path(folder,'collector.lock'))):
                pass

    def request(self, st, rid='manual', automatic=False):
        return {'id':'a', 'rid':rid, 'text':'Verified reply', 'inbox':delivery.context(st, 'a'),
                'automatic':automatic}

    def run_send(self, st, queue, result=None, error=None):
        out, calls, saved = [], [], []
        def send(*args, **kwargs):
            calls.append((args, kwargs))
            if error: raise error
            return result
        reader = type('Reader', (), {'close':lambda self:None})()
        with patch.object(main, 'save', side_effect=lambda s:saved.append(copy.deepcopy(s))), \
                patch.object(main, 'deliver', side_effect=send),patch.object(main,'preflight_guarded'):
            main.send_replies(st, reader, queue, out.append)
        return out, calls, saved

    def test_manual_auto_race_and_restart_have_one_commit(self):
        for reverse in (False, True):
            st = state()
            queue = [self.request(st), self.request(st,'auto',True)]
            if reverse: queue.reverse()
            out, calls, saved = self.run_send(st, queue, {'id':'external-123'})
            self.assertEqual(len(calls),1)
            self.assertTrue(any(s.get('inbox_delivery',{}).get('claims') for s in saved))
            self.assertEqual(len([p for p in out if p['kind']=='sent']),1)
            st = json.loads(json.dumps(st))
            self.assertEqual(self.run_send(st, [queue[-1]], {'id':'different'})[1],[])

    def test_hold_and_intentional_empty_survive_restart_release_is_explicit_cas(self):
        st = state(); old = delivery.context(st,'a')
        held = delivery.control(st, {'id':'a','rid':'edit','inbox':old,'action':'hold','editor':'client-a','draft':''})
        self.assertTrue(held['held'])
        st = json.loads(json.dumps(st))
        self.assertEqual(self.run_send(st,[self.request(st,'auto',True)],{'id':'x'})[1],[])
        with self.assertRaises(ValueError):
            delivery.control(st, {'id':'a','rid':'release','inbox':old,'action':'release','editor':'client-a'})
        current = delivery.context(st,'a')
        released = delivery.control(st, {'id':'a','rid':'release','inbox':current,'action':'release','editor':'client-a'})
        self.assertFalse(released['held'])

    def test_manual_send_atomically_consumes_own_hold_without_auto_activation(self):
        st=state(); st['cfg']['inbox_guard']=False
        held=delivery.control(st,{'id':'a','rid':'edit','inbox':delivery.context(st,'a'),
                                  'action':'hold','editor':'client-a'})
        for automatic,editor in ((True,'client-a'),(False,'client-b')):
            self.assertEqual(self.run_send(st,[{**self.request(st,'loser',automatic),'editor':editor}],{'id':'x'})[1],[])
        out,calls,saved=self.run_send(st,[{**self.request(st),'editor':'client-a'}],{'id':'external-id'})
        self.assertEqual(len(calls),1)
        self.assertEqual(out[0]['kind'],'sent')
        claimed=next(s for s in saved if s['inbox_delivery']['claims'])
        self.assertFalse(delivery.context(claimed,'a')['held'])
        self.assertTrue(claimed['inbox_delivery']['claims'])

    def test_other_client_cannot_steal_or_release_hold_and_replay_does_not_increment(self):
        st=state(); q={'id':'a','rid':'edit','inbox':delivery.context(st,'a'),'action':'hold','editor':'client-a'}
        held=delivery.control(st,q)
        self.assertEqual(delivery.control(st,q),held)
        for action in ('hold','release'):
            with self.assertRaises(ValueError):
                delivery.control(st,{**q,'rid':action,'inbox':held,'action':action,'editor':'client-b'})
        fresh=delivery.control(st,{**q,'rid':'new-edit','inbox':held})
        self.assertEqual(fresh['edit_version'],held['edit_version']+1)

    def test_new_facts_and_destination_change_refuse_old_version(self):
        for change in ('new-message','same-item','account','destination'):
            st = state(); q = self.request(st)
            if change=='new-message': delivery.observe(st,incoming('b','Later facts'))
            elif change=='same-item': delivery.observe(st,incoming(text='Changed facts'))
            elif change=='account': st['me']['id']='account-b'
            else: st['refs']['a']={'chat':'chat-b'}
            out,calls,_ = self.run_send(st,[q],{'id':'x'})
            self.assertEqual(calls,[],change)
            self.assertFalse(any(p['kind']=='sent' for p in out))

    def test_missing_receipt_and_timeout_remain_uncertain_never_answered(self):
        for result,error in ((None,None),('ok',None),({'success':True},None),(None,TimeoutError('after submission'))):
            st=state(); q=self.request(st)
            out,calls,_=self.run_send(st,[q],result,error)
            self.assertEqual(len(calls),1)
            self.assertFalse(any(p['kind'] in ('sent','answered') for p in out))
            self.assertEqual(out[-1]['kind'],'send_uncertain')
            st=json.loads(json.dumps(st))
            q['rid']='retry-new-id'
            self.assertEqual(self.run_send(st,[q],{'id':'x'})[1],[])
            self.assertIn('a',st['open'])

    def test_new_facts_do_not_release_an_uncertain_conversation_claim(self):
        st=state()
        self.run_send(st,[self.request(st)],None,TimeoutError('unknown'))
        delivery.observe(st,incoming(text='New facts'))
        self.assertEqual(self.run_send(st,[self.request(st,'new-version')],{'id':'x'})[1],[])

    def test_deferred_request_keeps_version_and_rechecks_new_facts_at_due_time(self):
        from datetime import datetime,timezone
        st=state(); q={**self.request(st),'at':'2030-01-01T08:00:00Z'}
        with patch.object(main,'save'),patch.object(main,'deliver') as send:
            main.send_replies(st,type('Reader',(),{})(),[q],lambda _:None,
                              datetime(2026,1,1,tzinfo=timezone.utc))
            self.assertEqual(st['later'][q['rid']]['inbox'],q['inbox'])
            delivery.observe(st,incoming(text='Later source facts'))
            main.send_replies(st,type('Reader',(),{})(),[],lambda _:None,
                              datetime(2031,1,1,tzinfo=timezone.utc))
            send.assert_not_called()

    def test_immediate_source_read_checks_actual_account_and_newer_messages(self):
        from unittest.mock import Mock
        item=incoming(); item['ref']['msg']='source-id'
        st={'me':{'id':'account-a'},'refs':{'a':item['ref']}}
        delivery.observe(st,item)
        original={'id':'source-id','messageType':'message','createdDateTime':item['at'],
                  'from':{'user':{'id':'counterpart'}},'body':{'content':'Verified facts'}}
        for change in ('none','account','source-text','new-incoming','new-owner','missing'):
            rows=[copy.deepcopy(original)]
            if change=='source-text': rows[0]['body']['content']='Changed source'
            if change in ('new-incoming','new-owner'):
                rows.insert(0,{**original,'id':'later-id','createdDateTime':'2026-10-15T12:01:00Z',
                               'from':{'user':{'id':'account-a' if change=='new-owner' else 'counterpart'}}})
            if change=='missing': rows=[]
            mcp=Mock(); mcp.call.side_effect=[{'id':'account-b' if change=='account' else 'account-a'},
                                            {'value':rows,'@odata.nextLink':'older-page'}]
            reader=type('Reader',(),{'mcp':mcp})()
            with self.subTest(change=change):
                if change=='none': main.preflight_guarded(st,reader,{'id':'a'})
                else:
                    with self.assertRaises(ValueError): main.preflight_guarded(st,reader,{'id':'a'})

    def test_automatic_reply_respects_current_contact_hours_before_transport(self):
        from datetime import datetime,timezone
        st=state(); st['hours']={'from':'08:00','to':'20:00','weekends':False}
        q=self.request(st,'auto',True); out=[]
        with patch.object(main,'save'),patch.object(main,'preflight_guarded'),patch.object(main,'deliver') as send, \
                patch.object(main.hours,'local',side_effect=lambda now:now):
            main.send_replies(st,None,[q],out.append,datetime(2026,10,17,12,tzinfo=timezone.utc))
            send.assert_not_called()
        self.assertEqual(out[0]['kind'],'scheduled')
        self.assertEqual(out[0]['held'],'hours')
        self.assertIn(q['rid'],st['later'])

    def test_precommit_claim_survives_crash(self):
        st=state(); q=self.request(st)
        delivery.claim(st,q)
        st=json.loads(json.dumps(st)); q['rid']='second'
        self.assertEqual(self.run_send(st,[q],{'id':'x'})[1],[])

    def test_legacy_client_and_unverified_source_cannot_enable_auto_send(self):
        st=state(); st['cfg']['inbox_guard']=False
        self.assertEqual(self.run_send(st,[self.request(st,'auto',True)],{'id':'x'})[1],[])
        st=state(); st['refs']['a']={'tg':'peer'}
        self.assertEqual(self.run_send(st,[self.request(st,'auto',True)],{'id':'x'})[1],[])


class PrivateInstruction(unittest.TestCase):
    def test_legacy_settings_preserve_guard_without_reposting_config_forever(self):
        st={'cfg':{'inbox_guard':True,'prompt':'Kept owner guidance'}}
        choice=type('Choice',(),{'settings':{'signature':'','autodraft':True,'prompt':'Kept owner guidance'},'hours':None})()
        out=[]
        main.settings(st,choice,out.append)
        main.settings(st,choice,out.append)
        self.assertTrue(st['cfg']['inbox_guard'])
        self.assertEqual(len(out),1)

    def test_choice_preserves_private_instruction_and_intentional_empty_draft(self):
        choice=main.Choice('/unused')
        event={'type':'ext.post','seq':10,'ts':1000,'data':{'plugin':main.NAME,'channel':'web','owner':True,
            'text':json.dumps({'kind':'ask','what':'draft','rid':'r','post':'p123','instruction':'Verified owner direction','draft':''})}}
        choice.line(json.dumps(event).encode())
        q,=choice.take_sends()
        self.assertEqual(q['instruction'],'Verified owner direction')
        self.assertIn('draft',q)
        self.assertEqual(q['draft'],'')

    def test_legacy_private_comment_refuses_unbound_editor_replacement(self):
        out,told=[],[]
        with patch.object(main,'save'),patch.object(main,'deliver',side_effect=AssertionError('send forbidden')):
            main.ask_hub({'cfg':{}},{'ask':'draft','rid':'r','post':'p123','instruction':'Verified direction','draft':''},out.append,told.append,1000)
        self.assertEqual(told,[])
        self.assertEqual(out[0]['kind'],'ask_failed')
        self.assertNotIn('instruction',out[0])


if __name__=='__main__': unittest.main()
