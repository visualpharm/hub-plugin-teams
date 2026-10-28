import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Разбор proactivity над перепиской (d839998): «почему» одной строкой из вердикта / поста дела / поручения, без меток;
// поздний пост без why прежний не стирает. Запуск: node tests/verdict.test.mjs web/main.js
const src = readFileSync(process.argv[2] || "web/main.js", "utf8");
const cut = (name) => { const a = src.indexOf(`export function ${name}`), b = src.indexOf("\n}\n", a) + 2; return src.slice(a, b).replace("export function", "function"); };
const { whyLine, mergeVerdict } = new Function(`${cut("whyLine")}\nconst WHY_LABEL = ${/WHY_LABEL = (\/.*\/i);/.exec(src)[1]};\n${cut("mergeVerdict")}\nreturn { whyLine, mergeVerdict };`)();

const why = "Илья Казаков обращается к Ivan Pupynin (другой Иван), не к Ивану Бойко; отвечать не нужно";
assert.equal(mergeVerdict(undefined, { kind: "verdict", item: "p1", why }), why);
assert.equal(mergeVerdict(undefined, { kind: "verdict", why: "Почему: просит встречу\nNext action: ответить до пятницы" }), "просит встречу. Ответить до пятницы");
assert.equal(mergeVerdict(why, { kind: "item", post: "p1", s: "answered" }), why, "пост без why прежнее не стирает");
assert.equal(mergeVerdict(why, { kind: "item", why: "Новое" }), "Новое");
assert.equal(mergeVerdict(undefined, { kind: "item" }), "");
assert.equal(mergeVerdict(undefined, { why: 5 }), "");

// показ: строка есть только в открытой переписке (detail), над историей, и берётся у последнего сообщения с разбором
assert.match(src, /const analysed = detail && \[\.\.\.ms\]\.reverse\(\)\.map\(\(m\) => verdicts\.get\(m\.post\)\)\.find\(Boolean\);/);
assert.ok(src.indexOf('el("div", "tm-verdict", analysed)') < src.indexOf('const history = el("div", "tm-history")'));
assert.match(readFileSync(new URL("../web/teams.css", import.meta.url), "utf8"), /\.tm-verdict \{[^}]*flex: none/);
console.log("verdict ok");
