import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Красный ТЕКСТ (пункт «Не показывать этого собеседника», плашки ошибок) — токен ядра --destructive-text: --destructive —
// заливка, в светлой Clean как текст он 3,6:1. Запасное значение — для хабов, где токена ещё нет.
// Запуск: node tests/text-danger.test.mjs
const css = readFileSync(new URL("../web/teams.css", import.meta.url), "utf8");
const bad = css.split("\n").map((line, i) => [i + 1, line]).filter(([, line]) => /(?<![\w-])color:\s*var\(--destructive\)/.test(line));
assert.deepEqual(bad.map(([n]) => n), [], "красный текст — var(--destructive-text, var(--destructive))");
assert.match(css, /\.menu-item\.tm-danger[^{]*\{[^}]*color: var\(--destructive-text, var\(--destructive\)\)/);
console.log("ok text-danger");
