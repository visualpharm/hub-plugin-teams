"""Открытая владельцем переписка получает ответ мимо плагина (`send wa` другой сессии, телефон) — сборщик сам дочитывает
историю и публикует новый thread (26.10, d1034600). Без сети: подставные источники."""
import json
import os
import sys
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.environ["HUB_STATE_DIR"] = "/tmp/teams-ext-test"
os.environ.pop("HUB_EXTENSION", None)

import collect  # noqa: E402
import main  # noqa: E402
import sources  # noqa: E402

KEY = "wa:whatsapp:5491100000000@c.us:IN1"
BOX = "wa:whatsapp:5491100000000@c.us"
REF = {"wa": "whatsapp", "to": "5491100000000@c.us", "account": "5491100000001", "cmd": "/bin/wa"}
T0 = 1_800_000_000.0


class R:
    mcp = None

    def close(self):
        pass

    def connect(self, st):
        raise AssertionError("WhatsApp не ходит в Teams")


class ThreadRefresh(unittest.TestCase):
    def setUp(self):
        self.out, self.calls = [], []
        self.rows = [{"at": "2026-10-26T19:53:00Z", "from": "Финка", "me": False, "text": "pasame tus datos"}]
        self.real = sources.history
        sources.history = lambda ref, top=20, before=None, search=None: self.calls.append(ref) or list(self.rows)
        sources.OUT.clear()
        main.LAST_OUT.clear()
        self.st = {"refs": {KEY: REF}, "me": {"id": "me"}}

    def tearDown(self):
        sources.history = self.real
        sources.OUT.clear()
        main.LAST_OUT.clear()

    def open_thread(self, now):
        main.history(self.st, R(), {"history": KEY, "ts": now}, self.out.append, now=now)

    def reply_elsewhere(self, t, text="Te paso los datos"):
        self.rows.append({"at": "2026-10-26T19:58:00Z", "from": "Ivan B", "me": True, "text": text})
        sources.OUT[BOX] = t   # wa new: out_last_t переписки

    def threads(self):
        return [p for p in self.out if p["kind"] == "thread"]

    def test_outgoing_past_the_plugin_republishes_the_open_thread(self):
        self.open_thread(T0)
        self.assertEqual(len(self.threads()), 1)
        self.reply_elsewhere(T0 + 60)
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + main.THREAD_REFRESH)
        got = self.threads()
        self.assertEqual(len(got), 2)
        self.assertEqual(got[-1]["id"], KEY)
        self.assertEqual(got[-1]["items"][-1]["text"], "Te paso los datos")
        self.assertTrue(got[-1]["items"][-1]["me"])
        self.assertTrue(all(p["kind"] == "thread" for p in self.out))   # ни отправки, ни thread_failed
        # больше нового нет — переписку не перечитываем
        n = len(self.calls)
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + 3 * main.THREAD_REFRESH)
        self.assertEqual(len(self.calls), n)

    def test_without_an_earlier_thread_nothing_is_read_or_published(self):
        self.reply_elsewhere(T0 + 60)
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + main.THREAD_REFRESH)
        self.assertEqual(self.out, [])
        self.assertEqual(self.calls, [])

    def test_at_most_once_per_interval_per_conversation(self):
        self.open_thread(T0)
        self.reply_elsewhere(T0 + 30)
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + 60)   # только что открывал — рано
        self.assertEqual(len(self.threads()), 1)
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + main.THREAD_REFRESH)
        self.assertEqual(len(self.threads()), 2)
        self.reply_elsewhere(T0 + main.THREAD_REFRESH + 10, "¿Alias?")
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + main.THREAD_REFRESH + 60)   # рано
        self.assertEqual(len(self.threads()), 2)
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + 2 * main.THREAD_REFRESH)
        self.assertEqual(len(self.threads()), 3)
        self.assertEqual(self.threads()[-1]["items"][-1]["text"], "¿Alias?")

    def test_saved_copy_lagging_is_reread_then_given_up(self):
        self.open_thread(T0)
        sources.OUT[BOX] = T0 + 60   # исходящее есть, а в копии его ещё нет
        for n in range(1, main.THREAD_TRIES + 2):
            main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + n * main.THREAD_REFRESH)
        self.assertEqual(len(self.threads()), 1)              # одинаковое не публикуем
        self.assertEqual(len(self.calls), 1 + main.THREAD_TRIES)  # перечитали THREAD_TRIES раз и ждём нового исходящего

    def test_watch_expires(self):
        self.open_thread(T0)
        self.reply_elsewhere(T0 + main.THREAD_WATCH + 10)
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + main.THREAD_WATCH + 60)
        self.assertEqual(len(self.threads()), 1)
        self.assertNotIn(BOX, self.st["thread_watch"])

    def test_paging_and_search_do_not_start_a_watch(self):
        main.history(self.st, R(), {"history": KEY, "ts": T0, "search": "datos"}, self.out.append, now=T0)
        self.assertNotIn(BOX, self.st.get("thread_watch") or {})

    def test_teams_chat_uses_owner_last_and_graph(self):
        key, ref = "k1", {"chat": "c1", "msg": "m1"}
        rows = [{"at": "2026-10-26T19:53:00Z", "from": "Алекс", "me": False, "text": "вопрос"}]
        real = collect.history
        collect.history = lambda mcp, ref, me: list(rows)

        class T(R):
            mcp = object()
        st = {"refs": {key: ref}, "me": {"id": "me"}}
        try:
            main.history(st, T(), {"history": key, "ts": T0}, self.out.append, now=T0)
            rows.append({"at": "2026-10-26T19:58:00Z", "from": "Ivan", "me": True, "text": "ответ"})
            box = collect.key("c1", "")
            main.thread_refresh(st, T(), {box: "2026-10-26T19:58:00Z"}, self.out.append, now=T0 + main.THREAD_REFRESH,
                                teams_ok=False)   # Teams не читался — его переписки не трогаем
            self.assertEqual(len(self.threads()), 1)
            main.thread_refresh(st, T(), {box: "2026-10-26T19:58:00Z"}, self.out.append, now=T0 + main.THREAD_REFRESH)
        finally:
            collect.history = real
        self.assertEqual(len(self.threads()), 2)
        self.assertEqual(self.threads()[-1]["items"][-1]["text"], "ответ")

    def test_conversations_opened_before_the_update_are_watched_from_now_on(self):
        self.st["hist"] = {f"{KEY}||": T0, f"{KEY}||datos": T0, "чужой||": T0}
        sources.OUT[BOX] = T0 - 600   # ответ, который он уже видел
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + main.THREAD_REFRESH)
        self.assertEqual(self.out, [])
        self.assertEqual(list(self.st["thread_watch"]), [BOX])
        self.reply_elsewhere(T0 + main.THREAD_REFRESH + 10)
        main.thread_refresh(self.st, R(), {}, self.out.append, now=T0 + main.THREAD_REFRESH + 60)
        self.assertEqual(self.threads()[-1]["items"][-1]["text"], "Te paso los datos")

    def test_sources_record_last_outgoing(self):
        real = sources.run
        rows = [{"chat_id": "5491100000000@c.us", "name": "Финка", "unread": 0, "out_last_t": 1234,
                 "messages": [{"id": "IN1", "t": 1200, "type": "chat"}]}]
        sources.run = lambda cmd, timeout=0: json.dumps(rows)
        try:
            sources.whatsapp({"channels": ["whatsapp"]}, main.datetime.now(main.timezone.utc))
            sources.telegram({}, main.datetime.now(main.timezone.utc))
        finally:
            sources.run = real
        self.assertEqual(sources.OUT.get(BOX), 1234)
        self.assertEqual(sources.OUT.get("tg:5491100000000@c.us"), 1234)


if __name__ == "__main__":
    unittest.main()
