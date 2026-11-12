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
const { mergeVerdict, whyLine, verdictLine } = new Function(`${cut("whyLine")}\nconst WHY_LABEL = ${/WHY_LABEL = (\/.*\/i);/.exec(src)[1]};\n${cut("mergeVerdict")}\n${cut("verdictLine")}\nreturn { mergeVerdict, whyLine, verdictLine };`)();
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
assert.deepEqual(mergeVerdict(c, { kind: "item", post: "p4", s: "done" }), c);

// следующий шаг — из последнего вердикта (как InboxWhy.merge): новый вердикт без него прежний снимает, item и delegated не трогают
let n = run({ kind: "verdict", item: "p5", do: "draft", why: "Synthetic bank asks about the card.", next_action: "Call back" });
assert.equal(n.next, "Call back");
n = from(n, { kind: "item", post: "p5", s: "draft", why: "Synthetic bank asks about the card.", next_action: "Ignore" }, { kind: "delegated", item: "p5", who: "noe", next_action: "Ignore" });
assert.equal(n.next, "Call back", "item и delegated шаг вердикта не меняют");
n = mergeVerdict(n, { kind: "verdict", item: "p5", do: "draft" });
assert.equal(n.next, "", "вердикт без шага снимает прежний"); assert.equal(why(n), "Synthetic bank asks about the card.", "вердикт без why прежний why не стирает");

// показ: обрезок и шаг одной строкой — многоточие остаётся, точку после него не ставим
assert.equal(verdictLine({ why: "Synthetic aunt invites you to...", next: "Reply yes or no" }), "Synthetic aunt invites you to... Reply yes or no");
assert.equal(verdictLine({ why: "Synthetic aunt invites you to…", next: "Reply yes or no" }), "Synthetic aunt invites you to… Reply yes or no");
assert.equal(verdictLine({ why: "Dinner at 7?", next: "Reply" }), "Dinner at 7? Reply");
assert.equal(verdictLine({ why: "Synthetic bank asks about the card;", next: "call back" }), "Synthetic bank asks about the card. Call back");
// длинный why (больше обрезка хаба) — целиком, без своего обрезания
const long = "Synthetic supplier confirms the order, ".repeat(8).trim();
assert.equal(verdictLine(run({ kind: "verdict", item: "p6", why: long })), long);
// суть в CSS переносится целиком: у .tm-verdict нет обрезания строкой
const css = readFileSync(new URL("../web/teams.css", import.meta.url), "utf8");
const rules = [...css.matchAll(/([^{}]*\.tm-verdict[^{}]*)\{([^}]*)\}/g)].map((m) => m[2]).join(";");
assert.doesNotMatch(rules, /line-clamp|text-overflow|nowrap|max-height|overflow:\s*hidden/, "суть не обрезается стилем");
assert.match(src, /history\.append\(valueElement\(el, "div", "tm-verdict", analysed\)\)/, "суть показывается строкой verdictLine целиком");

// смена хаба: разбор — в памяти страницы (Map модуля), не в хранилище браузера: другой хаб — другая страница, разбор с нуля
assert.match(src, /\nconst verdicts=new Map\(\);\n/);
const uses = src.match(/verdicts\.[a-z]+\(/g) || [];
assert.deepEqual([...new Set(uses)].sort(), ["verdicts.get(", "verdicts.set("], "разбор не сохраняется и не переносится");
assert.doesNotMatch(src, /Storage[^\n]*verdicts|verdicts[^\n]*Storage/);
console.log("verdict-why ok");
