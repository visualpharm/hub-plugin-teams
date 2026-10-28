"""Ответ в группу WhatsApp и отказ send до отправки (21.10): группа и @lid открываются только по названию в списке
чатов (send wa --title); отказ команды до транспорта — send_blocked, а не «итог неизвестен». Без сети: поддельные
wa/send. Запуск — как test_sources (PYTHONPATH — код хаба)."""
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.environ["HUB_STATE_DIR"] = tempfile.mkdtemp(prefix="teams-wa-group-")   # не состояние живого хаба
os.environ.pop("HUB_EXTENSION", None)

import main  # noqa: E402
import sources  # noqa: E402

NOW = datetime(2026, 10, 21, 15, 0, tzinfo=timezone.utc)
GROUP = "120363999@g.us"
REFUSED = ("send failed: WhatsApp Web: WhatsApp Web sender opens direct chats by phone number only; "
           f"'{GROUP}' is a group or @lid chat — pass its chat-list title to send there")


def failing(line):
    e = OSError(line[:200])   # как sources.run: короткая строка в тексте, целиком — в .full
    e.full = line
    return e


class GroupReply(unittest.TestCase):
    def setUp(self):
        self.run, self.knows = sources.run, sources.send_knows
        sources.send_knows = lambda cmd, flag: True
        self.calls = []

    def tearDown(self):
        sources.run, sources.send_knows = self.run, self.knows

    def fake(self, chats=(), send_error=None):
        def run(cmd, timeout=90):
            self.calls.append(cmd)
            if cmd[1:2] == ["chats"]:
                return json.dumps(list(chats))
            if cmd[1:2] == ["wa"] and send_error:
                raise failing(send_error)
            return ""
        sources.run = run

    def sent(self):
        return [c for c in self.calls if c[1:2] == ["wa"]]

    def test_collected_group_ref_carries_its_chat_list_title_outside_the_address(self):
        sources._WA_OPENED.clear(); sources._WA_READ.clear(); sources._WA_TEXT.clear(); sources._WA_WHO.clear()
        chat = {"chat_id": GROUP, "name": "Ремонт дома", "unread": 0, "out_last_t": 100,
                "last": "2026-10-21T11:36-03:00", "preview": "",
                "messages": [{"id": "g4", "t": 400, "type": "chat", "text": "Подтверди, пожалуйста", "cached": True,
                              "from": "Аня"}]}
        sources.run = lambda cmd, timeout=90: json.dumps([chat])
        items, _, _ = sources.whatsapp({"channels": ["whatsapp"], "groups": ["Ремонт дома"]}, NOW)
        ref = items[0]["ref"]
        self.assertEqual(ref["title"], "Ремонт дома")
        # название — не адрес: пункты, опубликованные без него, не получат «переписка сменилась»
        self.assertEqual(main.target_of(ref), main.target_of({k: v for k, v in ref.items() if k != "title"}))
        self.assertIn("title", sources.CONTACT_KEYS)

    def test_group_reply_passes_title_to_send(self):
        self.fake()
        sources.reply({"wa": "whatsapp", "to": GROUP, "send": "send", "cmd": "wa", "title": "Ремонт дома"}, "Ок")
        self.assertEqual(self.sent(), [["send", "wa", "--to", GROUP, "--channel", "whatsapp", "--title", "Ремонт дома",
                                        "--text", "Ок"]])

    def test_direct_chat_reply_has_no_title(self):
        self.fake()
        sources.reply({"wa": "whatsapp", "to": "5491100000007@c.us", "send": "send", "title": "Вася"}, "Ок")
        self.assertNotIn("--title", self.sent()[0])

    def test_group_ref_without_title_finds_it_in_the_chat_list(self):
        """Пункты, опубликованные до правки: названия в адресе нет — берём из списка чатов, чат не открывая."""
        self.fake(chats=[{"chat_id": "549110@c.us", "name": "Чужой"}, {"chat_id": GROUP, "name": "Ремонт дома"}])
        sources.reply({"wa": "whatsapp", "to": GROUP, "send": "send", "cmd": "wa"}, "Ок")
        self.assertEqual(self.calls[0], ["wa", "chats", "120363999", "--json", "--channel", "whatsapp"])
        self.assertIn(["--title", "Ремонт дома"], [self.sent()[0][i:i + 2] for i in range(len(self.sent()[0]))])

    def test_group_not_in_chat_list_is_refused_before_sending(self):
        self.fake(chats=[])
        with self.assertRaises(sources.NotSent):
            sources.reply({"wa": "whatsapp", "to": GROUP, "send": "send", "cmd": "wa"}, "Ок")
        self.assertEqual(self.sent(), [])

    def test_send_refusal_before_submit_is_not_sent(self):
        self.fake(send_error=REFUSED)
        with self.assertRaises(sources.NotSent):
            sources.reply({"wa": "whatsapp", "to": GROUP, "send": "send", "title": "Ремонт дома"}, "Ок")

    def test_send_maybe_stays_unknown_even_when_the_line_is_long(self):
        maybe = ("send failed: WhatsApp Web: WhatsApp Web driver failed: RuntimeError: " + "x" * 250
                 + "; reconcile before retry")
        self.fake(send_error=maybe)
        with self.assertRaises(OSError) as got:
            sources.reply({"wa": "whatsapp", "to": "5491100000007@c.us", "send": "send"}, "Ок")
        self.assertNotIsInstance(got.exception, sources.NotSent)

    def test_refusal_about_a_second_file_stays_unknown(self):
        """Несколько файлов: первый мог уйти, отказ — о следующем."""
        self.fake(send_error="send failed: WhatsApp Web: chat did not open within 60s (state='x', dialog='')")
        with self.assertRaises(OSError) as got:
            sources.reply({"wa": "whatsapp", "to": "5491100000007@c.us", "send": "send"}, "Ок",
                          files=["/a/1.png", "/a/2.png"])
        self.assertNotIsInstance(got.exception, sources.NotSent)


class Receipt(unittest.TestCase):
    """main.send_one: отказ до отправки — send_blocked (разбор кладёт черновик с причиной), иначе send_failed."""

    def setUp(self):
        self.run, self.knows = sources.run, sources.send_knows
        sources.send_knows = lambda cmd, flag: True

    def tearDown(self):
        sources.run, sources.send_knows = self.run, self.knows

    def receipt(self, send_error):
        def run(cmd, timeout=90):
            raise failing(send_error)
        sources.run = run
        key = f"wa:whatsapp:{GROUP}:g4"
        st = {"refs": {key: {"wa": "whatsapp", "to": GROUP, "send": "send", "cmd": "wa", "title": "Ремонт дома"}},
              "open": {key: {}}}
        got = []
        reader = type("R", (), {"close": lambda self: None, "mcp": None})()
        main.send_one(st, reader, {"id": key, "rid": "pa-1", "text": "Ок"}, put=got.append)
        return [e for e in got if e.get("rid") == "pa-1"]

    def test_refused_before_transport_is_blocked(self):
        got = self.receipt(REFUSED)
        self.assertEqual([e["kind"] for e in got], ["send_blocked"])

    def test_unknown_outcome_stays_send_failed(self):
        got = self.receipt("send failed: WhatsApp Web: submitted, but no outgoing bubble appeared; reconcile before retry")
        self.assertEqual([e["kind"] for e in got], ["send_failed"])


if __name__ == "__main__":
    unittest.main()
