"""Межагентная переписка не попадает в Inbox (27.10): сообщение агента коллеги публикуется видом `agent_msg`
(клиенты неизвестный вид пропускают), живое сообщение человека — `msg`; `surface` от разборщика возвращает пункт в Inbox."""
import os, sys, unittest
from datetime import datetime, timezone
from unittest import mock

sys.dont_write_bytecode = True
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, HERE)
os.environ["HUB_STATE_DIR"] = "/tmp/teams-ext-test"
os.environ.pop("HUB_EXTENSION", None)
import main  # noqa: E402

NOW = datetime(2026, 10, 27, 11, tzinfo=timezone.utc)
RULES = {"sources": ["teams"]}


def item(k, text, at="2026-10-27T10:00:00Z"):
    return {"key": k, "box": "b", "src": "dm", "where": "Личка", "from": "Pavel Malay", "text": text, "at": at,
            "link": "l", "mention": False}


class AgentLeak(unittest.TestCase):
    def tick(self, items, st=None):
        st, out = {} if st is None else st, []
        with mock.patch.object(main, "load_colleagues", return_value=RULES):
            main.tick(st, items, {}, NOW, out.append)
        return st, out

    def test_agent_signatures_go_to_agent_msg(self):
        for n, text in enumerate([
            "Статус по больнице готов.\n\n— 🤖 агент hospital, хаб Павла",
            "[агент hospital] нужен доступ",
            "Готово. — 🤖 написано агентом",
            "ok, sent via Claude Code🤖",
            "Привет (агент хаба)",
        ]):
            _, out = self.tick([item(f"a{n}", text)])
            self.assertEqual([p["kind"] for p in out], ["agent_msg"], text)
            self.assertEqual(out[0]["id"], f"a{n}")

    def test_human_message_stays_msg(self):
        for text in ["Иван, мой агент вчера что-то сломал, посмотри", "Созвонимся в 5?"]:
            _, out = self.tick([item("h1", text)])
            self.assertEqual([p["kind"] for p in out], ["msg"], text)

    def test_agent_from_non_colleague_stays_msg(self):
        st, out = {}, []
        with mock.patch.object(main, "load_colleagues", return_value={"sources": [], "names": ["никто"]}):
            main.tick(st, [item("n1", "— 🤖 агент x, хаб Y")], {}, NOW, out.append)
        self.assertEqual([p["kind"] for p in out], ["msg"])

    def test_surface_republishes_as_msg(self):
        st, out = self.tick([item("a1", "[агент hospital] нужен ваш ответ")])
        self.assertEqual([p["kind"] for p in out], ["agent_msg"])
        self.assertIn("a1", st["agent_held"])
        out2 = []
        main.surface("a1", st, out2.append)
        self.assertEqual([(p["kind"], p["id"]) for p in out2], [("msg", "a1")])
        self.assertEqual(out2[0]["text"], "[агент hospital] нужен ваш ответ")
        out3 = []
        main.surface("a1", st, out3.append)   # повтор — молча
        self.assertEqual(out3, [])

    def test_held_is_bounded(self):
        st = {}
        for n in range(main.AGENT_HELD_MAX + 20):
            st, _ = self.tick([item(f"k{n}", "[агент z] x")], st)
        self.assertLessEqual(len(st["agent_held"]), main.AGENT_HELD_MAX)

    def test_surface_accepted_only_from_triage_plugin(self):
        self.assertIn(b"surface", main.OWNER_KINDS.pattern)


if __name__ == "__main__":
    unittest.main()
