// Значки строки списка стоят по центру первой строки записи (имя / подпись), а не по базовой линии и не по центру всей записи.
// Читает CSS как текст; поведение в браузере проверено замером смещений (кадры до/после в задаче).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../web/teams.css", import.meta.url), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
// все блоки одного селектора подряд: позднее правило перекрывает раннее
const rule = (sel) => [...css.matchAll(new RegExp("(?:^|\\})\\s*" + sel.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\s*\\{([^}]*)\\}", "g"))].map((m) => m[1]).join(" ");

// закреплённый значок в шапке строки (одна строка, имя flex:1): по центру шапки, иначе при baseline он сидит ниже середины имени
assert.match(rule(".tm-person .tm-pinned"), /align-self:\s*center/);

// значок рядом с подписью вложения: подпись может занять две строки — значок у центра первой, не по baseline
assert.match(rule(".tm-media-label"), /align-items:\s*flex-start/);
assert.match(rule(".tm-media-label > .tm-native-icon"), /margin-block-start:\s*calc\(\(1lh\s*-\s*14px\)\s*\/\s*2\)/);

console.log("icon-align ok");
