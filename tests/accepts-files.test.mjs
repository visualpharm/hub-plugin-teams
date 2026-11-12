import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Скрепка в ответе WhatsApp/Telegram/почте. Опубликованное ядро (API 1.28) объявляет транспорт поля
// composerTransport: 1 — его поле отдаёт файлы в send(body).attachments, значит ответ с файлами принят.
// Старый форк объявляет composerFiles. Без обоих признаков — только текст.
// Запуск: node tests/accepts-files.test.mjs web/main.js
const src = readFileSync(process.argv[2] || "web/main.js", "utf8");
const a = src.indexOf("const EXTERNAL_REPLIES ="), b = src.indexOf("\n", src.indexOf("const acceptsFiles =", a));
assert.ok(a > 0 && b > a, "acceptsFiles в main.js");
const make = (capabilities, historyAvailable = true, inboxProtocol = null) =>
  new Function("hub", "historyAvailable", "inboxProtocol", src.slice(a, b) + "; return acceptsFiles;")({ capabilities }, historyAvailable, inboxProtocol);

const wa = { src: "whatsapp" }, tg = { src: "telegram" }, mail = { src: "email" }, teams = { src: "teams" };
// опубликованное ядро
const flagman = make({ composerTransport: 1, composerLeading: 1 });
for (const m of [wa, tg, mail]) assert.equal(flagman(m), true, m.src + ": скрепка на опубликованном ядре");
assert.equal(flagman(teams), false, "Teams — только текст");
assert.equal(flagman({ src: "telegram", inbox: true }), false, "ответ под защитой — только текст");
assert.equal(make({ composerTransport: 1 }, false)(tg), false, "без истории переписки — без файлов");
// старый форк
assert.equal(make({ composerFiles: 1 })(tg), true, "форк с composerFiles");
// ядро без транспорта поля и без файлов
assert.equal(make({})(tg), false, "без признаков — только текст");
assert.equal(make(undefined)(tg), false, "старое ядро без capabilities");
assert.equal(make({ composerTransport: 2 })(tg), false, "чужая версия транспорта — не угадываем");
console.log("accepts-files ok");
