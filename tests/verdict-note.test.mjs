import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Резюме в переписке один раз (как InboxWhy.shown в iPhone/Mac): разбор proactivity над письмом не повторяет заметку
// черновика хаба («Почему здесь» — плашкой первым блоком, видна и при открытом поле ответа); «что дальше» остаётся.
// Запуск: node tests/verdict-note.test.mjs web/main.js
const src = readFileSync(process.argv[2] || "web/main.js", "utf8");
const cut = (name) => {   // функция целиком по скобкам — однострочная и многострочная
  const a = src.indexOf(`export function ${name}`), open = src.indexOf("{", src.indexOf(")", a));
  let depth = 0, i = open;
  for (; i < src.length; i++) { if (src[i] === "{") depth++; else if (src[i] === "}" && --depth === 0) break; }
  return src.slice(a, i + 1).replace("export function", "function");
};
const { verdictLine } = new Function(`${cut("whyLine")}\nconst WHY_LABEL = ${/WHY_LABEL = (\/.*\/i);/.exec(src)[1]};\n${cut("verdictLine")}\nreturn { verdictLine };`)();

const v = { why: "Отель требует оплатить бронь за 48 часов, иначе снимет её", next: "" };
// заметка черновика повторяет «почему» разбора — над письмом его нет (одно резюме — плашка)
assert.equal(verdictLine(v, "Отель требует  оплатить бронь за 48 часов, иначе снимет её.\nОтвет — подтверждение оплаты"), "");
// своё «что дальше» у порученного дела остаётся
assert.equal(verdictLine({ ...v, next: "Олег: оплатить до пятницы" }, v.why), "Олег: оплатить до пятницы");
// заметка о другом — разбор на месте; без заметки — как прежде
assert.equal(verdictLine(v, "Черновик: вежливый отказ"), v.why);
assert.equal(verdictLine(v), v.why);
assert.equal(verdictLine(undefined, "x"), "");
// в переписке разбор получает ту же заметку, что рисует плашку
const thread = src.slice(src.indexOf("function thread("));
assert.match(thread, /verdictLine\(verdicts\.get\(m\.post\), noteWhy\)/);
assert.match(thread, /const noteLine = noteWhy && whyLine\(noteWhy\)/);
console.log("ok verdict-note");
