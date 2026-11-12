"""Inbox shows only what triage left to the owner. While a triage plugin owns incoming messages (sources.json
"triage"), a fresh message is posted as `held_msg` (clients render only `msg`) and kept here until the triage plugin
asks to show it (`surface`) or closes it (`dismiss` — published as answered, so it lands in Done, not in New). Safety
net: a held message nobody judged within HOLD_MAX is published as a normal `msg` by itself."""
import os, sys, unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

sys.dont_write_bytecode = True
HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, HERE)
os.environ["HUB_STATE_DIR"] = "/tmp/teams-ext-test"
os.environ.pop("HUB_EXTENSION", None)
import main  # noqa: E402

NOW = datetime(2026, 11, 12, 19, 48, 42, tzinfo=timezone.utc)
RULES = {"sources": ["teams"]}


def item(k, text="Should I talk to the contact?", at="2026-11-12T19:46:00Z", box="wa:b"):
    return {"key": k, "box": box, "src": "dm", "where": "WhatsApp", "from": "Contact", "text": text, "at": at,
            "link": "l", "mention": False}


class TriageHold(unittest.TestCase):
    def tick(self, items, st=None, now=NOW, triage="proactivity", owner_last=None):
        st, out = {} if st is None else st, []
        with mock.patch.object(main, "load_colleagues", return_value=RULES), \
                mock.patch.object(main, "triage_plugin", return_value=triage):
            main.tick(st, items, owner_last or {}, now, out.append)
        return st, out

    def test_fresh_message_is_held_while_triage_owns_it(self):
        st, out = self.tick([item("k1")])
        self.assertEqual([(p["kind"], p["id"]) for p in out], [("held_msg", "k1")])
        self.assertIn("k1", st["triage_held"])

    def test_without_triage_plugin_message_is_shown_at_once(self):
        _, out = self.tick([item("k1")], triage=None)
        self.assertEqual([p["kind"] for p in out], ["msg"])

    def test_already_answered_message_is_not_held(self):
        _, out = self.tick([item("k1")], owner_last={"wa:b": "2026-11-12T19:47:00Z"})
        self.assertEqual([(p["kind"], p["answered"]) for p in out], [("msg", True)])

    def test_agent_message_keeps_its_own_hold(self):
        _, out = self.tick([item("a1", "[агент hospital] нужен доступ")])
        self.assertEqual([p["kind"] for p in out], ["agent_msg"])

    def test_surface_shows_held_message_once(self):
        st, _ = self.tick([item("k1")])
        out = []
        self.assertTrue(main.surface("k1", st, out.append))
        self.assertEqual([(p["kind"], p["id"], p["answered"]) for p in out], [("msg", "k1", False)])
        self.assertNotIn("k1", st["triage_held"])
        again = []
        self.assertFalse(main.surface("k1", st, again.append))
        self.assertEqual(again, [])

    def test_dismissed_held_message_goes_to_done_not_new(self):
        st, _ = self.tick([item("k1")])
        out = []
        self.assertTrue(main.release_dismissed("k1", st, out.append))
        self.assertEqual([(p["kind"], p["id"], p["answered"]) for p in out], [("msg", "k1", True)])
        self.assertNotIn("k1", st["triage_held"])
        self.assertFalse(main.release_dismissed("k1", st, [].append))

    def test_dismiss_request_releases_held_message_as_answered(self):
        st, _ = self.tick([item("k1")])
        out = []
        with mock.patch.object(main, "archive_after", side_effect=lambda st, put: put):
            main.send_replies(st, None, [{"dismiss": "k1"}], out.append)
        kinds = [(p["kind"], p.get("answered")) for p in out]
        self.assertIn(("msg", True), kinds)
        self.assertNotIn(("msg", False), kinds)

    def test_unjudged_message_is_shown_after_hold_max(self):
        st, _ = self.tick([item("k1")])
        st, out = self.tick([item("k1")], st, now=NOW + timedelta(seconds=main.HOLD_MAX - 5))
        self.assertEqual([p for p in out if p["kind"] == "msg"], [])
        st, out = self.tick([item("k1")], st, now=NOW + timedelta(seconds=main.HOLD_MAX + 5))
        self.assertEqual([(p["kind"], p["id"]) for p in out if p["kind"] == "msg"], [("msg", "k1")])
        self.assertNotIn("k1", st["triage_held"])

    def test_turning_triage_off_shows_everything_held(self):
        st, _ = self.tick([item("k1")])
        st, out = self.tick([], st, triage=None)
        self.assertEqual([(p["kind"], p["id"]) for p in out if p["kind"] == "msg"], [("msg", "k1")])

    def test_late_text_of_held_message_stays_held(self):
        st, _ = self.tick([item("k1", "Should I")])
        st, out = self.tick([item("k1", "Should I talk to the contact?")], st)
        self.assertEqual([(p["kind"], p["text"]) for p in out], [("held_msg", "Should I talk to the contact?")])
        self.assertEqual(st["triage_held"]["k1"]["post"]["text"], "Should I talk to the contact?")

    def test_late_text_of_shown_message_is_not_hidden_again(self):
        st, _ = self.tick([item("k1", "Should I")])
        main.surface("k1", st, [].append)
        st, out = self.tick([item("k1", "Should I talk to the contact?")], st)
        self.assertEqual([p["kind"] for p in out], ["msg"])

    def test_message_open_before_triage_is_not_hidden_on_late_text(self):
        st, _ = self.tick([item("k1", "Should I")], triage=None)
        st, out = self.tick([item("k1", "Should I talk to the contact?")], st)
        self.assertEqual([p["kind"] for p in out], ["msg"])

    def test_owner_reply_closes_held_message_into_done(self):
        st, _ = self.tick([item("k1")])
        st, out = self.tick([item("k1")], st, owner_last={"wa:b": "2026-11-12T19:50:00Z"})
        kinds = [(p["kind"], p.get("answered")) for p in out]
        self.assertEqual(kinds[:2], [("msg", True), ("answered", None)])
        self.assertNotIn("k1", st["triage_held"])

    def test_sent_reply_closes_held_message_into_done(self):
        st, _ = self.tick([item("k1")])
        out = []
        put = main.held_aware(st, out.append)
        put({"kind": "sent", "id": "k1", "rid": "r1"})
        self.assertEqual([(p["kind"], p.get("answered")) for p in out], [("msg", True), ("sent", None)])

    def test_overflow_shows_the_oldest_instead_of_forgetting_it(self):
        st = {}
        shown = []
        for n in range(main.AGENT_HELD_MAX + 3):
            st, out = self.tick([item(f"k{n}", box=f"wa:{n}")], st)
            shown += [p["id"] for p in out if p["kind"] == "msg"]
        self.assertLessEqual(len(st["triage_held"]), main.AGENT_HELD_MAX)
        self.assertEqual(shown, ["k0", "k1", "k2"])


if __name__ == "__main__":
    unittest.main()
