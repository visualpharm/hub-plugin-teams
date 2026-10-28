"""link-fade, шаг 2 (28.10): ответ владельца в WhatsApp/Telegram/почте закрывает открытую запись `open` и шлёт `answered`
с отметкой исходящего (`out`) — по ней proactivity гасит соседей; снятый «Не показывать» собеседник не держит `open`.
Ключи нейтральные. Без сети: подставные источники."""
import os
import sys
import unittest
from datetime import datetime, timezone

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.environ["HUB_STATE_DIR"] = "/tmp/teams-ext-test"
os.environ.pop("HUB_EXTENSION", None)

import main  # noqa: E402
import sources  # noqa: E402

NOW = datetime(2026, 10, 27, 21, 0, tzinfo=timezone.utc)
T_IN = datetime(2026, 10, 27, 20, 48, tzinfo=timezone.utc).timestamp()
T_OUT = datetime(2026, 10, 27, 21, 33, tzinfo=timezone.utc).timestamp()
BOX = "wa:whatsapp:5490000000001@c.us"
KEY = BOX + ":IN1"


def item(key, box, at="2026-10-27T20:48:00Z", **kw):
    return {"key": key, "box": box, "src": "whatsapp", "where": "WhatsApp", "from": "Контакт", "text": "hola", "at": at,
            "contact": box, **kw}


class LinkFade(unittest.TestCase):
    def setUp(self):
        sources._WA_OUT_AT.clear()
        sources.OUT.clear()
        self.out = []
        self.st = {"open": {KEY: [BOX, "2026-10-27T20:48:00Z"]}, "seen": [KEY], "who": {}}

    def tearDown(self):
        sources.OUT.clear()

    def tick(self, items=(), owner_last=None):
        owner_last = {} if owner_last is None else owner_last
        main.merge_out(owner_last)
        main.tick(self.st, list(items), owner_last, NOW, self.out.append)

    def answered(self):
        return [p for p in self.out if p.get("kind") == "answered"]

    def test_a_whatsapp_reply_past_the_plugin_closes_the_open_record_and_marks_the_outgoing(self):
        sources.OUT[BOX] = T_OUT
        self.tick()
        self.assertEqual(self.st["open"], {})
        (post,) = self.answered()
        self.assertEqual(post["id"], KEY)
        self.assertEqual(post["out"], "2026-10-27T21:33:00Z")   # по метке proactivity отличает ответ от «пришло новое»

    def test_an_outgoing_before_the_message_does_not_close_it(self):
        sources.OUT[BOX] = T_IN - 600
        self.tick()
        self.assertIn(KEY, self.st["open"])
        self.assertEqual(self.answered(), [])

    def test_an_outgoing_in_a_neighbour_thread_of_the_same_contact_does_not_close_it(self):
        sources.OUT["wa:whatsapp:5490000000009@c.us"] = T_OUT
        self.tick()
        self.assertIn(KEY, self.st["open"])
        self.assertEqual(self.answered(), [])

    def test_a_reply_after_the_close_is_not_posted_twice(self):
        sources.OUT[BOX] = T_OUT
        self.tick()
        self.tick()
        self.assertEqual(len(self.answered()), 1)

    def test_a_record_of_an_ignored_contact_is_closed_even_when_ignore_ran_before_it_was_remembered(self):
        self.st["ignored"] = {BOX: {"name": "Контакт"}}
        self.st["who"] = {KEY: {"contact": BOX, "from": "Контакт", "src": "whatsapp", "where": ""}}
        self.tick()
        self.assertEqual(self.st["open"], {})
        (post,) = self.answered()
        self.assertEqual(post["id"], KEY)
        self.assertNotIn("out", post)   # не ответ владельца

    def test_the_mail_thread_with_a_later_sent_message_is_marked_as_answered(self):
        box = "mail:me@example.com:t1"
        self.st["open"] = {box + ":k": [box, "2026-10-27T20:48:00Z"]}
        real = sources.run
        sources.run = lambda cmd, timeout=90: ('{"thread": {"messages": ['
                                               '{"internalDate": "%d", "labelIds": ["INBOX"], "payload": {}},'
                                               '{"internalDate": "%d", "labelIds": ["SENT"], "payload": {}}]}}'
                                               % (T_IN * 1000, T_OUT * 1000))
        try:
            sources.mail_out_open("gog", self.st["open"], now=NOW.timestamp())
        finally:
            sources.run = real
        self.assertAlmostEqual(sources.OUT[box], T_OUT, delta=1)
        self.tick()
        self.assertEqual(self.st["open"], {})

    def test_f_reply_from_the_phone_is_found_in_the_saved_thread_when_the_tab_is_gone(self):
        # 28.10, Fincas: Chrome закрыт, `wa new` падает, OUT пуст; ответ владельца с телефона лежит в копии переписки
        real, asked = sources.run, []

        def fake(cmd, timeout=90):
            asked.append(cmd)
            return ('{"messages": [{"out": false, "t": %d}, {"out": true, "t": %d}, {"out": false, "t": %d}]}'
                    % (T_IN, T_OUT, T_IN - 5))
        sources.run = fake
        try:
            sources.wa_out_open("wa", self.st["open"], now=NOW.timestamp())
            sources.wa_out_open("wa", self.st["open"], now=NOW.timestamp() + 60)   # не чаще раза в 10 минут
        finally:
            sources.run = real
        self.assertEqual(len(asked), 1)
        self.assertEqual(asked[0][:3], ["wa", "thread", "5490000000001"])
        self.assertIn("--cached", asked[0])
        self.tick()
        self.assertEqual(self.st["open"], {})
        self.assertEqual(self.answered()[0]["out"], "2027-01-15T21:33:00Z".replace("2027-01-15", "2026-10-27"))

    def test_an_unanswered_thread_in_the_saved_copy_leaves_the_record_open(self):
        real = sources.run
        sources.run = lambda cmd, timeout=90: '{"messages": [{"out": false, "t": %d}, {"out": true, "t": %d}]}' % (T_IN, T_IN - 900)
        try:
            sources.wa_out_open("wa", self.st["open"], now=NOW.timestamp() + 7200)
        finally:
            sources.run = real
        self.tick()
        self.assertIn(KEY, self.st["open"])


if __name__ == "__main__":
    unittest.main()
