"""«Почему здесь» в переписке — ровно один узел: один вызов whyNote, одна сборка .tm-note-box, одна вставка в историю.
Кадры «свёрнуто» и «развёрнуто» — два состояния одного узла (aria-expanded), не два элемента."""
import re
import unittest
from pathlib import Path

SRC = (Path(__file__).resolve().parent.parent / "web" / "main.js").read_text(encoding="utf-8")


class NoteIsSingle(unittest.TestCase):
    def test_one_call_one_box_one_insertion(self):
        self.assertEqual(len(re.findall(r"\bfunction whyNote\(", SRC)), 1)
        self.assertEqual(SRC.count('"tm-note-box"'), 1, "узел заметки собирает только whyNote")
        calls = [m for m in re.finditer(r"\bwhyNote\(", SRC) if not SRC[max(0, m.start() - 9):m.start()].endswith("function ")]
        self.assertEqual(len(calls), 1, calls)
        line = SRC[SRC.rfind("\n", 0, calls[0].start()) + 1:SRC.find("\n", calls[0].start())]
        self.assertIn(".tm-conversation-source", line)
        self.assertIn(".after(", line, "одна вставка после строки источника, не append в историю")

    def test_two_states_share_one_toggle_and_one_body(self):
        body = SRC[SRC.index("function whyNote("):]
        body = body[:body.index("\n}\n")]
        self.assertEqual(body.count('"tm-note-toggle"'), 1)
        self.assertEqual(body.count("tm-note-body"), 1)
        self.assertIn("aria-expanded", body)


if __name__ == "__main__":
    unittest.main()
