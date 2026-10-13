import { readFileSync } from "fs";
// Черновик хаба (web/main.js: splitDraft): текст отдельно, заметка «Почему» отдельно — в правку и отправку идёт
// только текст. Запуск: node tests/draft.test.mjs web/main.js
const src = readFileSync(process.argv[2], "utf8");
const a = src.indexOf("export function splitDraft"), b = src.indexOf("\n}\n", a) + 2;
const splitDraft = new Function(src.slice(a, b).replace("export function", "function") + "; return splitDraft;")();
const cases = [
  ["Привет, посмотрю завтра.\n---\nПочему: просит глянуть MR, срочности нет", "Привет, посмотрю завтра.", "просит глянуть MR, срочности нет"],
  ["Просто текст", "Просто текст", ""],
  ["Строка\n---\nещё строка\n---\nWhy: because", "Строка\n---\nещё строка", "because"],
  ["Текст\n\n ---  \n\nпочему: так", "Текст", "так"],
  ["👍\n---\nПочему: хватит реакции", "👍", "хватит реакции"],
  ["a --- b", "a --- b", ""],
];
let fail = 0;
for (const [input, text, why] of cases) {
  const r = splitDraft(input);
  if (r.text !== text || r.why !== why) { fail++; console.log("FAIL", JSON.stringify(input), r); }
}
console.log(fail ? `FAIL ${fail}` : "ALL OK");
process.exitCode = fail ? 1 : 0;
