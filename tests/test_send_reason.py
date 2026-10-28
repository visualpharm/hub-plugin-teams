"""send_blocked защиты источника называет причину (hub-core m637023, 20.10): машинный код reason и фраза error,
различающая случаи. Раньше любая причина давала одну фразу «Current source verification unavailable or changed»,
а настоящая была видна только в hub-up.log — гадали, «ушло или нет». Только подставные чат и транспорт."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['HUB_STATE_DIR'] = tempfile.mkdtemp(prefix='teams-send-reason-')  # не живое состояние плагина
os.environ['HUB_EXTENSION'] = 'tolaysha:teams'
import main
import inbox_delivery as delivery

OLD = 'Current source verification unavailable or changed; reply retained'
SOURCE_AT = '2026-10-15T12:00:00Z'


def state():
    ref = {'chat': 'chat-a', 'msg': 'source-id'}
    st = {'me': {'id': 'account-a'}, 'cfg': {'inbox_guard': True},
          'hours': {'from': '00:00', 'to': '24:00', 'weekends': True}}
    delivery.observe(st, {'key': 'a', 'text': 'Verified facts', 'at': SOURCE_AT, 'src': 'dm', 'box': 'chat-a',
                          'ref': ref, 'from': 'Person', 'contact': 'chat-a'})
    st['refs'] = {'a': dict(ref)}
    st['open'] = {'a': ['chat-a', SOURCE_AT]}
    return st


def original():
    return {'id': 'source-id', 'messageType': 'message', 'createdDateTime': SOURCE_AT,
            'from': {'user': {'id': 'counterpart'}}, 'body': {'content': 'Verified facts'}}


def reader_for(change):
    """Подставной Graph: текущий пользователь и последние сообщения чата."""
    rows = [original()]
    if change == 'newer':
        rows.insert(0, {**original(), 'id': 'later-id', 'createdDateTime': '2026-10-15T12:05:00Z'})
    if change == 'source-text':
        rows[0]['body']['content'] = 'Edited outside collector'
    def graph(tool, args, **kw):
        if tool == 'get-current-user':
            return {'id': 'account-b' if change == 'account' else 'account-a'}
        if tool == 'list-chat-messages':
            if change == 'graph-down':
                raise OSError('MCP connection reset')
            return {'error': 'throttled'} if change == 'no-rows' else {'value': copy.deepcopy(rows)}
        raise AssertionError('transport must not be reached: ' + tool)
    if change == 'no-reader':
        return type('Reader', (), {'close': lambda self: None})()
    mcp = Mock(); mcp.call.side_effect = graph
    return type('Reader', (), {'mcp': mcp, 'close': lambda self: None})()


class SendReason(unittest.TestCase):
    def request(self, st, rid='r1'):
        return {'id': 'a', 'rid': rid, 'text': 'Verified reply', 'inbox': delivery.context(st, 'a')}

    def send(self, st, q, reader):
        out = []
        with patch.object(main, 'save'), patch.object(main, 'deliver') as transport:
            main.send_replies(st, reader, [q], out.append)
        transport.assert_not_called()
        return out

    def test_each_source_guard_cause_has_its_own_reason_and_phrase(self):
        cases = {'newer': 'newer_messages', 'graph-down': 'source_unreadable', 'no-rows': 'source_unreadable',
                 'no-reader': 'source_unreadable', 'account': 'source_changed', 'source-text': 'source_changed'}
        phrases = {}
        for change, reason in cases.items():
            with self.subTest(change=change):
                st = state()
                out = self.send(st, self.request(st), reader_for(change))
                self.assertEqual([p['kind'] for p in out], ['send_blocked'])
                self.assertEqual(out[0]['reason'], reason)
                self.assertIsInstance(out[0]['error'], str)
                self.assertNotEqual(out[0]['error'], OLD)
                self.assertFalse(st['inbox_delivery']['claims'])  # до deliver не дошло — «не ушло» верно
                phrases.setdefault(reason, set()).add(out[0]['error'])
        self.assertEqual(len({p for s in phrases.values() for p in s}), len(phrases))  # фраза по причине, не общая
        self.assertIn('newer message', next(iter(phrases['newer_messages'])))

    def test_unexpected_guard_failure_is_unknown(self):
        st = state(); out = []
        with patch.object(main, 'save'), patch.object(main, 'deliver') as transport, \
                patch.object(main, 'preflight_guarded', side_effect=RuntimeError('bug')):
            main.send_replies(st, reader_for('none'), [self.request(st)], out.append)
        transport.assert_not_called()
        self.assertEqual((out[0]['kind'], out[0]['reason']), ('send_blocked', 'unknown'))
        self.assertIsInstance(out[0]['error'], str)

    def test_same_rid_replays_the_same_event_with_reason_without_reading_again(self):
        st = state(); q = self.request(st)
        first = self.send(st, q, reader_for('newer'))
        st = json.loads(json.dumps(st))  # перезапуск: отказ записан в состояние по rid
        again = self.send(st, q, reader_for('none'))
        self.assertEqual(again, first)
        self.assertEqual(again[0]['reason'], 'newer_messages')

    def test_typed_guard_errors_stay_value_errors_with_reason(self):
        st = state()
        for change, reason in (('newer', 'newer_messages'), ('account', 'source_changed'), ('graph-down', 'source_unreadable')):
            with self.subTest(change=change):
                with self.assertRaises(ValueError) as caught:
                    main.preflight_guarded(st, reader_for(change), {'id': 'a'})
                self.assertEqual(caught.exception.reason, reason)
        main.preflight_guarded(st, reader_for('none'), {'id': 'a'})


if __name__ == '__main__':
    unittest.main()
