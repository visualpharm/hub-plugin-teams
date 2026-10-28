"""Automatic resend after a CAS-only refusal (Ivan m612908). Mocked transport, no real send."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_inbox_delivery as base   # module import: its TestCase is not collected twice
delivery, state = base.delivery, base.state

STALE = 'Inbox changed'


class StaleResend(unittest.TestCase):
    run_send = base.Delivery.run_send

    def stale(self):
        """Own hold and release moved the edit version after the client took its token: refused before transport."""
        st = state(); token = delivery.context(st, 'a')
        for action in ('hold', 'release'):
            delivery.control(st, {'id':'a', 'rid':action, 'inbox':delivery.context(st, 'a'), 'action':action, 'editor':'web-a'})
        q1 = {'id':'a', 'rid':'first', 'text':'Pressed reply', 'inbox':token, 'editor':'web-a'}
        out, calls, _ = self.run_send(st, [q1], {'id':'external-1'})
        self.assertEqual(calls, [])
        return st, q1, out[-1]

    def test_stale_refusal_carries_the_current_token_without_text_or_destination(self):
        st, _, blocked = self.stale()
        self.assertEqual(blocked['kind'], 'send_blocked')
        self.assertTrue(blocked['error'].startswith(STALE))
        self.assertEqual(blocked['inbox'], delivery.context(st, 'a'))
        self.assertEqual(set(blocked['inbox']), {'v', 'version', 'manual_followup', 'edit_version', 'held', 'holder'})

    def test_one_replacement_sends_once_and_a_second_replacement_of_the_same_rid_is_refused(self):
        st, q1, blocked = self.stale()
        q2 = {**q1, 'rid':'second', 'replaces':'first', 'inbox':blocked['inbox']}
        out, calls, _ = self.run_send(st, [q2], {'id':'external-2'})
        self.assertEqual(len(calls), 1)
        self.assertEqual([p['kind'] for p in out], ['sent', 'answered'])
        # Another tab (or client) replacing the same refused rid with the current token: no second delivery.
        q3 = {**q1, 'rid':'third', 'replaces':'first', 'inbox':delivery.context(st, 'a')}
        out, calls, _ = self.run_send(st, [q3], {'id':'external-3'})
        self.assertEqual(calls, [])
        self.assertEqual(out[-1]['kind'], 'send_blocked')
        # The replacement itself replayed: the original outcome, still one delivery.
        out, calls, _ = self.run_send(st, [q2], {'id':'external-4'})
        self.assertEqual(calls, [])

    def test_only_a_stale_refusal_of_the_same_item_can_be_replaced_and_only_once(self):
        st, q1, blocked = self.stale()
        fresh = blocked['inbox']
        for replaces in ('unknown-rid', 'first-other-item', ''):
            out, calls, _ = self.run_send(st, [{**q1, 'rid':'r-'+replaces, 'replaces':replaces, 'inbox':fresh}], {'id':'x'})
            self.assertEqual(calls, [], replaces)
            self.assertEqual(out[-1]['kind'], 'send_blocked', replaces)
        # A refusal for another reason (here: another client holds the editor) is not replaceable.
        st2 = state()
        delivery.control(st2, {'id':'a', 'rid':'h', 'inbox':delivery.context(st2, 'a'), 'action':'hold', 'editor':'other'})
        q = {'id':'a', 'rid':'held-first', 'text':'Pressed reply', 'inbox':delivery.context(st2, 'a'), 'editor':'web-a'}
        out, calls, _ = self.run_send(st2, [q], {'id':'x'})
        self.assertFalse(out[-1]['error'].startswith(STALE))
        out, calls, _ = self.run_send(st2, [{**q, 'rid':'held-second', 'replaces':'held-first'}], {'id':'x'})
        self.assertEqual(calls, [])
        self.assertIn('replace', out[-1]['error'])
        # A replacement refused as stale again is not replaced a second time (one automatic resend).
        delivery.control(st, {'id':'a', 'rid':'h2', 'inbox':fresh, 'action':'hold', 'editor':'web-a'})
        out, calls, _ = self.run_send(st, [{**q1, 'rid':'second', 'replaces':'first', 'inbox':fresh}], {'id':'x'})
        self.assertTrue(out[-1]['error'].startswith(STALE))
        out, calls, _ = self.run_send(st, [{**q1, 'rid':'third', 'replaces':'second', 'inbox':out[-1]['inbox']}], {'id':'x'})
        self.assertEqual(calls, [])
        self.assertEqual(out[-1]['kind'], 'send_blocked')


if __name__ == '__main__':
    unittest.main()
