import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Разбор proactivity над перепиской: «почему» одной строкой из вердикта / поста дела / поручения, без меток;
// поздний пост без why прежний не стирает. Запуск: node tests/verdict.test.mjs web/main.js
const src = readFileSync(process.argv[2] || "web/main.js", "utf8");
const cut = (name) => { const a = src.indexOf(`export function ${name}`), b = src.indexOf("\n}\n", a) + 2; return src.slice(a, b).replace("export function", "function"); };
const { whyLine, mergeVerdict, verdictShown } = new Function(`${cut("whyLine")}\nconst WHY_LABEL = ${/WHY_LABEL = (\/.*\/i);/.exec(src)[1]};\n${cut("mergeVerdict")}\n${cut("verdictShown")}
return { whyLine, mergeVerdict, verdictShown };`)();

const why = "Илья Казаков обращается к Oleg Petrov (другой Олег), не к Олегу Смирнову; отвечать не нужно";
assert.equal(mergeVerdict(undefined, { kind: "verdict", item: "p1", why }).why, why);
assert.equal(verdictShown(mergeVerdict(undefined, { kind: "verdict", why: "Почему: просит встречу\nКонтекст: в пятницу" }), (w) => w).why, "просит встречу. В пятницу");
assert.equal(mergeVerdict({ why, next: "" }, { kind: "item", post: "p1", s: "answered" }).why, why, "пост без why прежнее не стирает");
assert.equal(mergeVerdict({ why, next: "" }, { kind: "item", why: "Новое" }).why, "Новое");
assert.equal(mergeVerdict(undefined, { kind: "item" }), undefined);
assert.equal(mergeVerdict(undefined, { why: 5 }), undefined);

// показ: строка есть только в открытой переписке (detail), над историей, и берётся у последнего сообщения с разбором
assert.match(src, /const analysed = detail && \[\.\.\.ms\]\.reverse\(\)\.map\(\(m\) => verdictShown\(verdicts\.get\(m\.post\), /);
// внутри прижатого вниз блока истории, перед подгруженными и текущими репликами
assert.ok(src.indexOf('history.append(box)') > src.indexOf('const history = el("div", "tm-history")'));
assert.match(readFileSync(new URL("../web/teams.css", import.meta.url), "utf8"), /\.tm-verdict \{/);
console.log("verdict ok");
