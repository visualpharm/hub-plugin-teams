import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Черновик идёт за перепиской (d660171, натив Inbox+Chain.swift): собеседник дописал — прежний пункт закрыт (answered с
// newer или соседним постом), черновик хаба и ✨ прежнего видны у нового; пометка proactivity «Перенесён из pN…» сырой
// не показывается. Запуск: node tests/carry.test.mjs web/main.js
const src = readFileSync(process.argv[2] || "web/main.js", "utf8");
const a = src.indexOf("export function splitDraft"), b = src.indexOf("\n}\n", a) + 2;
const splitDraft = new Function(src.slice(a, b).replace("export function", "function") + "; return splitDraft;")();
const { conversationChain, chainReplies, chainAsked } = await import("data:text/javascript," +
  encodeURIComponent(readFileSync(new URL("../web/conversation-chain.js", import.meta.url), "utf8")));

// 1) пометка переноса: текст ответа тот же, номер поста владельцу не показываем, остальное пояснение хаба остаётся
const carried = "Да, в пятницу удобно.\n---\nПеренесён из p812: черновик к прежнему сообщению этой переписки — сверь с новым.\nПочему: просит подтвердить встречу";
let r = splitDraft(carried);
assert.equal(r.text, "Да, в пятницу удобно.");
assert.equal(r.carried, true);
assert.equal(r.why, "просит подтвердить встречу");
assert.ok(!/p812|Перенес/.test(r.why), r.why);
r = splitDraft("Ок\n---\nПеренесён из p9: черновик к прежнему сообщению этой переписки — сверь с новым.");
assert.deepEqual([r.text, r.why, r.carried], ["Ок", "", true]);
r = splitDraft("Ок\n---\nПочему: Перенесён из офиса");   // только строка-пометка, не слова внутри пояснения
assert.deepEqual([r.why, r.carried], ["Перенесён из офиса", false]);
assert.equal(splitDraft("Перенесён из p1\nтекст").carried, false, "без «---» это текст ответа");

// фраза перенесённого черновика — EN/RU/ES, как draft.carried натива
assert.ok(src.includes('"Черновик к прежнему сообщению — сверь с новым."'));
assert.ok(src.includes('"Draft for the earlier message — check it against the new one."'));
assert.ok(src.includes('"Borrador para el mensaje anterior: revisalo con el nuevo."'));
const ui = readFileSync(new URL("../web/ui-text.js", import.meta.url), "utf8");
assert.match(ui, /export const T = \(ru, en, es\)/);

// 2) цепочка: answered с newer
const posts = new Map([["old", "p10"], ["new", "p12"], ["older", "p5"]]);
const replies = new Map([["p10", [{ by: "hub", text: "Черновик старого", ts: 100 }]]]);
const postOf = (id) => posts.get(id), repliesOf = (p) => replies.get(p);
let chain = conversationChain();
chain.closed("old", "new", 11);
assert.deepEqual(chain.predecessors("new"), ["old"]);
let got = chainReplies(chain, { id: "new", post: "p12" }, postOf, repliesOf);
assert.equal(got.carried, true); assert.equal(got.list.at(-1).text, "Черновик старого");
// свой черновик нового главнее перенесённого
replies.set("p12", [{ by: "proactivity", text: "Свой", ts: 200 }]);
got = chainReplies(chain, { id: "new", post: "p12" }, postOf, repliesOf);
assert.deepEqual([got.carried, got.list.at(-1).text], [false, "Свой"]);
replies.delete("p12");
// ✨ у прежнего — «готовит черновик» и устаревание у нового
const asked = new Map([["old", 150]]);
assert.equal(chainAsked(chain, { id: "new" }, (id) => asked.get(id)), 150);
asked.set("new", 300);
assert.equal(chainAsked(chain, { id: "new" }, (id) => asked.get(id)), 300);
// цепочка из нескольких замен: ближайший с черновиком
chain.closed("older", "old", 9);
assert.deepEqual(chain.predecessors("new"), ["old", "older"]);
replies.delete("p10"); replies.set("p5", [{ by: "hub", text: "Самый старый", ts: 50 }]);
got = chainReplies(chain, { id: "new", post: "p12" }, postOf, repliesOf);
assert.deepEqual([got.carried, got.list.at(-1).text], [true, "Самый старый"]);

// 3) старый сборщик без newer: закрытие и следующим постом новое сообщение той же переписки — замена
chain = conversationChain();
chain.closed("old", undefined, 20); chain.opened("new", 21, () => true);
assert.deepEqual(chain.predecessors("new"), ["old"]);
// не соседний пост, другая переписка или ответ владельца — не замена
chain = conversationChain();
chain.closed("old", undefined, 20); chain.opened("new", 23, () => true);
assert.deepEqual(chain.predecessors("new"), []);
chain.closed("old", undefined, 30); chain.opened("other", 31, () => false);
assert.deepEqual(chain.predecessors("other"), []);
chain.closed("old", "", 40); chain.opened("x", 42, () => true);
assert.deepEqual(chain.predecessors("x"), []);
// закрытие с newer на себя — не цикл
chain = conversationChain(); chain.closed("a", "a", 1);
assert.deepEqual(chain.predecessors("a"), []);
chain.closed("a", "b", 2); chain.closed("b", "a", 3);
assert.ok(chain.predecessors("a").length <= 1);

// 4) main.js ведёт цепочку: answered с newer и соседний пост; черновик, ✨ и «готовит» берутся по цепочке
for (const needle of ["chain.closed(d.id, d.newer", "chain.opened(", "chainReplies(chain", "chainAsked(chain"])
  assert.ok(src.includes(needle), needle);
assert.ok(!/replies\.get\(m\.post\)/.test(src.replace(/function hubDrafts[\s\S]*?\n}\n/, "")), "черновик строки — только через цепочку");
console.log("ALL OK");
