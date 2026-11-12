import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Строка «почему» разбора proactivity — как InboxWhy.merge в iPhone/Mac: ранняя догадка (item early:true) не держится
// против слов хаба; обрезанный хабом why (item, delegated) не заменяет только полный why, началом которого он является;
// разбор — этого хаба. Запуск: node tests/verdict-why.test.mjs web/main.js
const src = readFileSync(process.argv[2] || "web/main.js", "utf8");
const cut = (name) => {   // функция целиком по скобкам
  const a = src.indexOf(`export function ${name}`), open = src.indexOf("{", src.indexOf(")", a));
  let depth = 0, i = open;
  for (; i < src.length; i++) { if (src[i] === "{") depth++; else if (src[i] === "}" && --depth === 0) break; }
  return src.slice(a, i + 1).replace("export function", "function");
};
const { mergeVerdict, whyLine, verdictShown } = new Function(`${cut("whyLine")}\nconst WHY_LABEL = ${/WHY_LABEL = (\/.*\/i);/.exec(src)[1]};\n${cut("mergeVerdict")}\n${cut("verdictShown")}\nreturn { mergeVerdict, whyLine, verdictShown };`)();
const from = (start, ...posts) => posts.reduce((a, d) => mergeVerdict(a, d), start);
const run = (...posts) => from(undefined, ...posts);
const why = (a) => whyLine(a?.why);

// полный why и его обрезок: обрезок item и delegated полный не заменяет — в обоих порядках
const full = "Two synthetic voice notes from a business account.";
assert.equal(why(run({ kind: "verdict", item: "p1", do: "draft", why: full }, { kind: "item", post: "p1", s: "answered", why: "Two synthetic voice notes from a…" })), full, "обрезок item не заменяет свой полный why");
assert.equal(why(run({ kind: "verdict", item: "p1", do: "delegated", why: full }, { kind: "delegated", item: "p1", who: "noe", why: "Two synthetic voice notes from a..." })), full, "обрезок delegated не заменяет свой полный why");
assert.equal(why(run({ kind: "item", post: "p1", s: "delegated", why: "Synthetic aunt invites you to…" }, { kind: "verdict", item: "p1", do: "draft", why: "Synthetic aunt invites you to dinner at 7." })), "Synthetic aunt invites you to dinner at 7.", "полный вердикт после обрезка — главнее");
// «…» вердикта — его слова, не обрезок хаба
assert.equal(why(run({ kind: "verdict", item: "p1", why: "Call back the bank about the card." }, { kind: "verdict", item: "p1", why: "Call back…" })), "Call back…");

// ранняя суть: видна до итога, итог её заменяет, поздняя ранняя итог не затирает
let a = run({ kind: "item", post: "p2", s: "new", early: true, why: "Synthetic aunt: dinner tonight?" });
assert.equal(why(a), "Synthetic aunt: dinner tonight?");
a = from(a, { kind: "verdict", item: "p2", do: "draft", why: "Synthetic aunt invites you to dinner at 7; reply yes or no." },
  { kind: "item", post: "p2", s: "draft", early: true, why: "Synthetic aunt: dinner tonight?" });
assert.equal(why(a), "Synthetic aunt invites you to dinner at 7; reply yes or no.");
assert.equal(why(run({ kind: "item", post: "p2", early: true, why: "Synthetic aunt: dinner tonight?" },
  { kind: "verdict", item: "p2", do: "draft", why: "Synthetic aunt invites you to dinner at 7." },
  { kind: "item", post: "p2", s: "draft", early: true, why: "Synthetic aunt: dinner" })), "Synthetic aunt invites you to dinner at 7.", "поздняя ранняя не затирает вердикт");
// новый why позднего поста без early по-прежнему заменяет вердикт
assert.equal(why(run({ kind: "verdict", item: "p2", why: "Synthetic aunt invites you." }, { kind: "item", post: "p2", s: "answered", why: "Aunt confirmed by phone." })), "Aunt confirmed by phone.");
// вердикт без why и повтор показанного why постом без early ранний не закрепляют
let b = run({ kind: "item", post: "p3", s: "new", early: true, why: "Synthetic bank: card" }, { kind: "verdict", item: "p3", do: "draft" },
  { kind: "item", post: "p3", s: "draft", early: true, why: "Synthetic bank: card blocked" });
assert.equal(why(b), "Synthetic bank: card blocked"); assert.equal(b.judged, false, "вердикт без why ранний не закрепляет");
b = run({ kind: "item", post: "p3", s: "new", early: true, why: "Synthetic bank: card" }, { kind: "item", post: "p3", s: "draft", why: "Synthetic bank: card" },
  { kind: "item", post: "p3", s: "draft", early: true, why: "Synthetic bank: card blocked" });
assert.equal(why(b), "Synthetic bank: card blocked", "повтор ранней сути постом без early её не закрепляет");
// поздний item без early несёт why вердикта (вердикта в окне нет): ранняя после него не затирает
assert.equal(why(run({ kind: "item", post: "p3", s: "draft", why: "Synthetic bank asks to call back about the card." },
  { kind: "item", post: "p3", s: "draft", early: true, why: "Synthetic bank: card" })), "Synthetic bank asks to call back about the card.");

// ранняя после обрезка: обрезанный why — слова хаба, заменяет раннюю суть и закрепляется
let c = run({ kind: "item", post: "p4", s: "new", early: true, why: "Synthetic aunt: dinner tonight?" },
  { kind: "item", post: "p4", s: "draft", why: "Synthetic aunt invites you to…" },
  { kind: "item", post: "p4", s: "draft", early: true, why: "Synthetic aunt: dinner" });
assert.equal(why(c), "Synthetic aunt invites you to…", "обрезок заменяет раннюю суть, поздняя ранняя его не затирает");
assert.equal(c.judged, true);
// обрезок за обрезком: другое начало — новее, заменяет; тот же обрезок или его начало — нет
c = mergeVerdict(c, { kind: "item", post: "p4", s: "answered", why: "Synthetic aunt confirmed by phone, nothing to…" });
assert.equal(why(c), "Synthetic aunt confirmed by phone, nothing to…", "обрезок с другим началом сменяет прежний");
assert.equal(why(mergeVerdict(c, { kind: "item", post: "p4", why: "Synthetic aunt confirmed…" })), "Synthetic aunt confirmed by phone, nothing to…", "обрезок короче — начало известного, не заменяет");
// пост без why прежний не стирает и итог не сбрасывает
const d4 = mergeVerdict(c, { kind: "item", post: "p4", s: "done" });
assert.equal(d4.why, c.why); assert.equal(d4.judged, c.judged); assert.equal(d4.state, "done");

// следующий шаг — из последнего вердикта (как InboxWhy.merge): новый вердикт без него прежний снимает, item и delegated не трогают
let n = run({ kind: "verdict", item: "p5", do: "draft", why: "Synthetic bank asks about the card.", next_action: "Call back" });
assert.equal(n.next, "Call back");
n = from(n, { kind: "item", post: "p5", s: "draft", why: "Synthetic bank asks about the card.", next_action: "Ignore" }, { kind: "delegated", item: "p5", who: "noe", next_action: "Ignore" });
assert.equal(n.next, "Call back", "item и delegated шаг вердикта не меняют");
n = mergeVerdict(n, { kind: "verdict", item: "p5", do: "draft" });
assert.equal(n.next, "", "вердикт без шага снимает прежний"); assert.equal(why(n), "Synthetic bank asks about the card.", "вердикт без why прежний why не стирает");

// показ (как InboxWhy.shown): шаг — только у открытого дела, порученного другому, и отдельной второй строкой
const lead = (who) => `Handled by ${who}`, shown = (...posts) => verdictShown(run(...posts), lead);
const cutWhy = "Synthetic supplier confirms the order and asks to move the truck...";
assert.deepEqual(shown({ kind: "verdict", item: "p7", do: "draft", why: cutWhy, next_action: "Approve the window" }),
  { why: cutWhy, next: "" }, "у обычного письма шаг не показан, обрезок в сути — как есть");
assert.deepEqual(shown({ kind: "verdict", item: "p7", do: "delegated", why: "Two synthetic voice notes from…", next_action: "Call the client back" }, { kind: "delegated", item: "p7", who: "noe" }),
  { why: "Two synthetic voice notes from…", next: "noe: Call the client back" }, "у поручённого — «кто: шаг» второй строкой");
assert.equal(shown({ kind: "verdict", item: "p7", do: "delegated", why: "x", next_action: "noe opens the chat" }, { kind: "delegated", item: "p7", who: "noe" }).next, "noe opens the chat", "шаг с имени — без префикса");
assert.equal(shown({ kind: "verdict", item: "p7", do: "delegated", why: "x" }, { kind: "delegated", item: "p7", who: "noe" }).next, "Handled by noe", "шага нет — «Ведёт noe»");
assert.equal(shown({ kind: "item", post: "p7", s: "delegated", who: "noe", why: "x" }, { kind: "verdict", item: "p7", next_action: "Call back" }).next, "noe: Call back", "поручено по состоянию item");
assert.equal(shown({ kind: "verdict", item: "p7", do: "delegated", why: "x", next_action: "Call back" }, { kind: "delegated", item: "p7", who: "noe" }, { kind: "item", post: "p7", s: "done" }).next, "", "закрытое дело — без второй строки");
assert.equal(shown({ kind: "verdict", item: "p7", do: "delegated", why: "x", next_action: "Call back" }).next, "", "без who — без второй строки");
// длинный why (больше обрезка хаба) — целиком, без своего обрезания
const long = "Synthetic supplier confirms the order, ".repeat(8).trim();
assert.equal(shown({ kind: "verdict", item: "p6", why: long }).why, long);
// суть в CSS переносится целиком: у .tm-verdict и её строк нет обрезания
const css = readFileSync(new URL("../web/teams.css", import.meta.url), "utf8");
const rules = [...css.matchAll(/([^{}]*\.tm-verdict[^{}]*)\{([^}]*)\}/g)].map((m) => m[2]).join(";");
assert.doesNotMatch(rules, /line-clamp|text-overflow|nowrap|max-height|overflow:\s*hidden/, "суть не обрезается стилем");
assert.match(src, /box\.append\(valueElement\(el, "div", "tm-verdict-why", analysed\.why\)\)/);
assert.match(src, /box\.append\(valueElement\(el, "div", "tm-verdict-next", analysed\.next\)\)/, "шаг — отдельной строкой");

// смена хаба: разбор — в памяти страницы (Map модуля), не в хранилище браузера: другой хаб — другая страница, разбор с нуля
assert.match(src, /\nconst verdicts=new Map\(\);\n/);
const uses = src.match(/verdicts\.[a-z]+\(/g) || [];
assert.deepEqual([...new Set(uses)].sort(), ["verdicts.get(", "verdicts.set("], "разбор не сохраняется и не переносится");
assert.doesNotMatch(src, /Storage[^\n]*verdicts|verdicts[^\n]*Storage/);
console.log("verdict-why ok");
