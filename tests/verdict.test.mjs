import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Разбор proactivity над перепиской (d839998): «почему» одной строкой из вердикта / поста дела / поручения, без меток;
// поздний пост без why прежний не стирает. Запуск: node tests/verdict.test.mjs web/main.js
const src = readFileSync(process.argv[2] || "web/main.js", "utf8");
const cut = (name) => { const a = src.indexOf(`export function ${name}`), b = src.indexOf("\n}\n", a) + 2; return src.slice(a, b).replace("export function", "function"); };
const { whyLine, mergeVerdict, verdictLine } = new Function(`${cut("whyLine")}\nconst WHY_LABEL = ${/WHY_LABEL = (\/.*\/i);/.exec(src)[1]};\n${cut("mergeVerdict")}\nconst verdictLine = (v) => v ? whyLine([v.why, v.next].filter(Boolean).join("\\n")) : "";
return { whyLine, mergeVerdict, verdictLine };`)();

const why = "Илья Казаков обращается к Ivan Pupynin (другой Иван), не к Ивану Бойко; отвечать не нужно";
assert.equal(mergeVerdict(undefined, { kind: "verdict", item: "p1", why }).why, why);
assert.equal(verdictLine(mergeVerdict(undefined, { kind: "verdict", why: "Почему: просит встречу\nNext action: ответить до пятницы" })), "просит встречу. Ответить до пятницы");
assert.equal(mergeVerdict({ why, next: "" }, { kind: "item", post: "p1", s: "answered" }).why, why, "пост без why прежнее не стирает");
assert.equal(mergeVerdict({ why, next: "" }, { kind: "item", why: "Новое" }).why, "Новое");
assert.equal(mergeVerdict(undefined, { kind: "item" }), undefined);
assert.equal(mergeVerdict(undefined, { why: 5 }), undefined);

// показ: строка есть только в открытой переписке (detail), над историей, и берётся у последнего сообщения с разбором
assert.match(src, /const analysed = detail && \[\.\.\.ms\]\.reverse\(\)\.map\(\(m\) => verdictLine\(verdicts\.get\(m\.post\)\)\)\.find\(Boolean\);/);
// внутри прижатого вниз блока истории, перед подгруженными и текущими репликами
assert.ok(src.indexOf('history.append(el("div", "tm-verdict", analysed))') > src.indexOf('const history = el("div", "tm-history")'));
assert.match(readFileSync(new URL("../web/teams.css", import.meta.url), "utf8"), /\.tm-verdict \{/);
console.log("verdict ok");
