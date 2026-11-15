// Экран Inbox без повторов: «Inbox» написано один раз (на вкладке), пустой список говорит одну короткую фразу,
// а верхняя кнопка быстрого сообщения уступает плавающей кнопке страницы. Читает исходники как текст.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const js = readFileSync(new URL("../web/main.js", import.meta.url), "utf8");
const css = readFileSync(new URL("../web/teams.css", import.meta.url), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");

// заголовка раздела нет: имя раздела несёт активная вкладка
assert.doesNotMatch(js, /"tm-title"/);
assert.doesNotMatch(css, /\.tm-title(-row)?\s*\{/);
assert.match(js, /if \(tab === key\) b\.append\(el\("span","tm-folder-label",title\)\)/);
// у каждой вкладки-значка есть подсказка
assert.match(js, /b\.dataset\.folder=key;[^\n]*b\.title=title/);

// пустой список: одна фраза без пояснения про соседнюю вкладку
assert.doesNotMatch(js, /Разобранные — во вкладке рядом/);
assert.match(js, /T\("Новых сообщений нет", "No new messages"/);
// и без второй надписи «Сообщение не выбрано» рядом
assert.match(js, /ui\.emptyDetail\.hidden = !grouped \|\| !!dmPerson \|\| !matching\.length;/);

// плавающая кнопка страницы видна — своей в шапке нет
assert.match(css, /:root:has\(\.qp-fab:not\(\[hidden\]\)\) \.tm-quick-trigger\s*\{\s*display:\s*none;?\s*\}/);

console.log("inbox-chrome ok");
