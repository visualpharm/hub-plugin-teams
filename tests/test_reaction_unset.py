"""Снять свою реакцию в Teams и реакции Teams как источник правды — без сети: поддельный Graph (ms365 MCP)."""
import json
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.environ["HUB_STATE_DIR"] = "/tmp/teams-ext-test"
os.environ.pop("HUB_EXTENSION", None)

import collect  # noqa: E402
import main  # noqa: E402

ME = "me"
CHAT = {"chat": "c1", "msg": "m1"}
CHANNEL = {"team": "t1", "channel": "ch1", "root": "r1", "msg": "r1"}


class Graph:
    """Поддельный ms365: пишет вызовы; refuse — инструмент, который отвечает ошибкой Graph."""

    def __init__(self, refuse=None):
        self.calls, self.refuse = [], refuse

    def call(self, tool, args, empty_ok=False):
        self.calls.append((tool, args))
        if tool == self.refuse:
            raise OSError(f"ms365 {tool}: Forbidden")
        return {}


class Reader:
    def __init__(self, mcp):
        self.mcp = mcp

    def close(self):
        pass


class Unset(unittest.TestCase):
    def setUp(self):
        self.save = main.save
        main.save = lambda st: None

    def tearDown(self):
        main.save = self.save

    def send(self, ref, q, graph):
        st, out = {"refs": {"k1": ref}, "open": {"k1": {}}}, []
        main.send_one(st, Reader(graph), {"id": "k1", "rid": "r", "react": "👍", **q}, out.append)
        return st, out

    def test_unset_goes_to_graph_for_chat_and_channel(self):
        for ref, tool, args in ((CHAT, "unset-chat-message-reaction", {"chatId": "c1", "chatMessageId": "m1"}),
                                (CHANNEL, "unset-channel-message-reaction",
                                 {"teamId": "t1", "channelId": "ch1", "chatMessageId": "r1"})):
            graph = Graph()
            st, out = self.send(ref, {"unset": True}, graph)
            self.assertEqual(graph.calls, [(tool, {**args, "body": {"reactionType": "👍"}})])
            self.assertEqual([e["kind"] for e in out], ["unreacted"])
            self.assertEqual(out[0]["emoji"], "👍")
            self.assertIn("k1", st["open"])   # снятая реакция не отвечает на сообщение

    def test_unset_of_a_chat_bubble_goes_to_that_message(self):
        graph = Graph()
        self.send(CHAT, {"unset": True, "reply_to": "m0"}, graph)
        self.assertEqual(graph.calls[0][1]["chatMessageId"], "m0")

    def test_set_still_answers(self):
        graph = Graph()
        st, out = self.send(CHAT, {}, graph)
        self.assertEqual(graph.calls[0][0], "set-chat-message-reaction")
        self.assertEqual([e["kind"] for e in out], ["reacted", "answered"])
        self.assertNotIn("k1", st["open"])

    def test_refusal_is_unreact_failed_and_set_refusal_stays_react_failed(self):
        _, out = self.send(CHAT, {"unset": True}, Graph(refuse="unset-chat-message-reaction"))
        self.assertEqual([e["kind"] for e in out], ["unreact_failed"])
        self.assertIn("Forbidden", out[0]["error"])
        _, out = self.send(CHAT, {}, Graph(refuse="set-chat-message-reaction"))
        self.assertEqual([e["kind"] for e in out], ["react_failed"])

    def test_unset_outside_teams_fails_without_a_send(self):
        _, out = self.send({"tg": "123", "msg": "5"}, {"unset": True}, Graph())
        self.assertEqual([e["kind"] for e in out], ["unreact_failed"])

    def test_channel_reply_is_refused_not_moved_to_the_thread_root(self):
        for q in ({}, {"unset": True}):
            graph = Graph()
            _, out = self.send(CHANNEL, {**q, "reply_to": "reply-7"}, graph)
            self.assertEqual(graph.calls, [])
            self.assertTrue(out[0]["kind"].endswith("react_failed"))

    def test_replay_of_the_rid_with_set_is_not_the_unset_outcome(self):
        self.assertNotEqual(main.reply_print({"id": "k1", "react": "👍"}),
                            main.reply_print({"id": "k1", "react": "👍", "unset": True}))
        self.assertEqual(main.reply_outcome({}, {"id": "k1", "rid": "r", "react": "👍", "unset": True})["kind"],
                         "unreact_failed")

    def test_owner_unreact_post_is_taken_and_others_are_not(self):
        def ev(body, **data):
            return json.dumps({"seq": 1, "type": "ext.post", "data": {"plugin": "teams", "text": json.dumps(body), **data}})
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(ev({"kind": "unreact", "id": "k1", "rid": "u1", "emoji": "👍", "msg": "m0", "target": "t"},
                       owner=True, channel="web") + "\n")
            f.write(ev({"kind": "unreact", "id": "k1", "rid": "u2", "emoji": "👍"}, channel="session", sender="hub") + "\n")
        c = main.Choice(f.name)
        c.poll()
        os.unlink(f.name)
        self.assertEqual(c.take_sends(), [{"react": "👍", "unset": True, "id": "k1", "rid": "u1", "reply_to": "m0",
                                           "target": "t"}])

    def test_config_offers_unset(self):
        with open(os.path.join(HERE, "main.py"), encoding="utf-8") as f:
            self.assertIn("'reaction_unset':1", f.read())


class ProviderReactions(unittest.TestCase):
    def msg(self, mid, reactions):
        return {"id": mid, "messageType": "message", "createdDateTime": f"2026-11-17T21:2{mid[-1]}:00Z",
                "from": {"user": {"id": "ilnur", "displayName": "Colleague"}}, "body": {"content": "text " + mid},
                "reactions": [{"reactionType": t, "user": {"user": {"id": u}}} for t, u in reactions]}

    def test_history_carries_teams_reactions_and_marks_the_item_message(self):
        class Chat:
            def call(me, tool, args, empty_ok=False):
                return {"value": [self.msg("m1", [("👍", "kate"), ("like", ME), ("❤️", "alex")]),
                                  self.msg("m2", [])]}
        items = collect.history(Chat(), CHAT, ME)
        first = next(i for i in items if i["id"] == "m1")
        self.assertEqual(first["reactions"], [{"emoji": "👍", "n": 2, "mine": True}, {"emoji": "❤️", "n": 1}])
        self.assertTrue(first["source"])
        second = next(i for i in items if i["id"] == "m2")
        self.assertNotIn("reactions", second)
        self.assertNotIn("source", second)

    def test_after_unset_in_teams_the_owner_is_not_among_reactions(self):
        class Chat:
            def call(me, tool, args, empty_ok=False):
                return {"value": [self.msg("m1", [("👍", "kate")])]}
        self.assertEqual(collect.history(Chat(), CHAT, ME)[0]["reactions"], [{"emoji": "👍", "n": 1}])


if __name__ == "__main__":
    unittest.main()
