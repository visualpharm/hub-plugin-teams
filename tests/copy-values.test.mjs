import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Значок «скопировать» у значений в Inbox (hub-ios design-plans/kit/copy-value.md): правило Sources/CopyValues.swift
// перенесено как есть (как web-look 0.3.73); примеры — tools/copy-values-check/main.swift один в один (номер сообщения,
// имя машины и домашний каталог — синтетические той же формы). Запуск: node tests/copy-values.test.mjs web/main.js
const src = readFileSync(process.argv[2] || "web/main.js", "utf8");
const url = (source) => "data:text/javascript;base64," + Buffer.from(source).toString("base64");
const textURL = url(readFileSync(new URL("../web/ui-text.js", import.meta.url), "utf8"));
const { bindHub } = await import(textURL);
const hub = { lang: "ru" }; bindHub(hub);
const { copyValues, copyValueControl, decorateValues, valueElement, copyText, tieOf } = await import(url(
  readFileSync(new URL("../web/copy-values.js", import.meta.url), "utf8").replace(/from ["']\.\/ui-text\.js["']/g, "from " + JSON.stringify(textURL))));
const values = (text) => copyValues(text).map((v) => v.value);
// хвост связки со значком: последний сегмент (после / - _ : пробела) до 12 знаков, длиннее — последние 6
const tieCases = [["~/.claude/x.log", "x.log"], ["66cb2db0", "66cb2db0"], ["hub restart web", "web"], ["4F2A9C1E-0B7D-4E5A-9C3B-2D1E0F7A8B6C", "2D1E0F7A8B6C"], ["0123456789abcdef0123", "ef0123"], ["app.agentshub.client.proto", ".proto"], ["~/a/", "a/"]];

const screen = "Открой ссылку, нажми «+» → «Новое приложение»: платформа iOS, имя Hub Proto, язык English (U.S.), Bundle ID " +
  "app.agentshub.client.proto, SKU hub-proto, доступ полный → «Создать». Через API Apple создать приложение нельзя, " +
  "а входа в App Store Connect в браузерах хаба нет. Сборку загружу сам.\nhttps://appstoreconnect.apple.com/apps";
const cases = [
  [screen, ["app.agentshub.client.proto", "hub-proto"], "скрин Ивана: Bundle ID и SKU, без ссылки и U.S."],
  ["и т.д. и т.п., v1.4.0, e.g. это", [], "сокращения и версия — без значка"],
  ["Влито 66cb2db0, задача d837401, сообщение m800001.", ["66cb2db0", "d837401", "m800001"], "хеш и id хаба"],
  ["Кадры в ~/.claude/artifacts/hub-clients/copy-pieces/ и /tmp/x.log", ["~/.claude/artifacts/hub-clients/copy-pieces/", "/tmp/x.log"], "пути"],
  ["ID 4F2A9C1E-0B7D-4E5A-9C3B-2D1E0F7A8B6C готов", ["4F2A9C1E-0B7D-4E5A-9C3B-2D1E0F7A8B6C"], "UUID после ID"],
  ["ключ к успеху, token words", [], "метка без значения-токена"],
  ["token: abcdef, ключ: sk_live", ["abcdef", "sk_live"], "метка с двоеточием"],
  ["Команда: hub restart web", ["hub restart web"], "команда с двоеточием — до конца строки"],
  ["смотри https://host.example.ts.net/a/b.c.d и host.example.ts.net", ["host.example.ts.net"], "хост вне ссылки — да, внутри — нет"],
  ["photo-1.png и README.md", [], "имя файла из двух частей — нет"],
  ["abcdefab и 12345678", [], "хеш без цифр или без букв — нет"],
  ["Версии 1.92 и 0.3.53, в 08:00, 2026-10-24, apple.com, ул.Ленина.дом.пять", [], "версии, время, дата, два сегмента, русские слова через точку"],
  ['Лог: "~/Library/Application Support/HubbaHub/run.log" и «/Users/sample/My Files/a.txt»', ["~/Library/Application Support/HubbaHub/run.log", "/Users/sample/My Files/a.txt"], "путь с пробелом в кавычках — без кавычек"],
];
for (const [text, want, what] of cases) assert.deepEqual(values(text), want, what);
// Смещения — в исходной строке (UTF-16, как NSRange натива); одно значение дважды — дважды.
const twice = "😀 SKU hub-proto и hub-proto, SKU hub-proto";
for (const v of copyValues(twice)) assert.equal(twice.slice(v.start, v.end), v.value);
assert.deepEqual(values(twice), ["hub-proto", "hub-proto"]);

// Маленький DOM: текстовые узлы (nodeType 3), after(), replaceChildren — как в браузере.
function text(data) {
  const t = { nodeType: 3, data: String(data), parentNode: null,
    after(...xs) { const p = t.parentNode, i = p.childNodes.indexOf(t); for (const x of xs) x.parentNode = p; p.childNodes.splice(i + 1, 0, ...xs); },
    get textContent() { return t.data; } };
  return t;
}
function el(tag, cls, content) {
  const n = { tagName: tag.toUpperCase(), className: cls || "", childNodes: [], attrs: {}, parentNode: null, title: "", type: "",
    classList: { contains: (c) => n.className.split(" ").includes(c) },
    append(...xs) { for (let x of xs) { if (typeof x === "string") x = text(x); x.parentNode = n; n.childNodes.push(x); } },
    replaceChildren(...xs) { n.childNodes = []; n.append(...xs); },
    setAttribute(k, v) { n.attrs[k] = String(v); },
    get textContent() { return n.childNodes.map((x) => x.textContent).join(""); },
    set textContent(v) { n.childNodes = []; if (v) n.append(text(v)); } };
  if (content != null && content !== "") n.append(text(content));
  return n;
}
const tree = (n) => [n, ...(n.childNodes || []).flatMap(tree)];
const controls = (root) => tree(root).filter((n) => n.className === "tm-copy-at");
// Текст перед значком: хвост в связке .tm-copy-tie и узел перед ней.
const prev = (n) => { const p = n.parentNode; return p.childNodes[p.childNodes.indexOf(n) - 1]; };
const before = (at) => { const tie = at.parentNode; assert.equal(tie.className, "tm-copy-tie"); return (prev(tie)?.textContent || "") + prev(at).textContent; };
function clock() {
  let t = 0, seq = 0; const timers = new Map();
  return { now: () => t, setTimer: (fn, ms) => { timers.set(++seq, [t + ms, fn]); return seq; }, clearTimer: (id) => timers.delete(id),
    delays: () => [...timers.values()].map(([at]) => at - t),
    async tick(ms) { t += ms; for (const [id, [at, fn]] of [...timers]) if (at <= t) { timers.delete(id); await fn(); } } };
}

// Значок: значение в буфер, галочка 1,5 с, имя и невидимый статус на ru/en/es; отказ буфера — имя «не удалось».
for (const [lang, copy, copied, failed] of [["ru", "Копировать", "Скопировано", "Не удалось скопировать"], ["en", "Copy", "Copied", "Could not copy"], ["es", "Copiar", "Copiado", "No se pudo copiar"]]) {
  hub.lang = lang;
  const c = clock(), calls = [], at = copyValueControl(el, "app.agentshub.client.proto." + lang, { copy: async (v) => calls.push(v), ...c });
  const [button, note] = at.childNodes;
  assert.equal(at.className, "tm-copy-at"); assert.equal(button.type, "button"); assert.equal(button.className, "tm-copy-value");
  assert.equal(button.attrs["aria-label"], copy); assert.equal(button.title, copy);
  assert.equal(button.childNodes.length, 1); assert.equal(button.childNodes[0].className, "tm-native-icon tm-icon-copy");
  assert.equal(button.childNodes[0].attrs["aria-hidden"], "true");
  assert.equal(note.className, "tm-sr-only"); assert.equal(note.attrs.role, "status"); assert.equal(note.attrs["aria-live"], "polite");
  assert.equal(at.textContent, "", "значок не добавляет текста — выделение и копирование куска прежние");
  let stopped = false; await button.onclick({ stopPropagation: () => { stopped = true; } });
  assert.ok(stopped, "нажатие не открывает строку и меню под значком");
  assert.deepEqual(calls, ["app.agentshub.client.proto." + lang]);
  assert.equal(button.childNodes[0].className, "tm-native-icon tm-icon-check"); assert.equal(button.attrs["aria-label"], copied);
  assert.equal(button.attrs["data-copied"], "true"); assert.equal(note.textContent, copied); assert.equal(button.textContent, "", "без видимой строки");
  assert.deepEqual(c.delays(), [1500]);
  // перерисовка в эти 1,5 с: новый значок того же значения — сразу галочкой, до конца своего срока
  await c.tick(500);
  const redrawn = copyValueControl(el, "app.agentshub.client.proto." + lang, { copy: async () => {}, ...c });
  assert.equal(redrawn.childNodes[0].childNodes[0].className, "tm-native-icon tm-icon-check");
  assert.equal(redrawn.childNodes[1].textContent, "", "статус уже объявлен — второй раз не читается");
  await c.tick(999); assert.equal(button.childNodes[0].className, "tm-native-icon tm-icon-check");
  await c.tick(1); assert.equal(button.childNodes[0].className, "tm-native-icon tm-icon-copy"); assert.equal(button.attrs["aria-label"], copy);
  assert.equal(button.attrs["data-copied"], "false"); assert.equal(note.textContent, "");
  assert.equal(redrawn.childNodes[0].childNodes[0].className, "tm-native-icon tm-icon-copy");
  assert.equal(copyValueControl(el, "app.agentshub.client.proto." + lang, c).childNodes[0].childNodes[0].className, "tm-native-icon tm-icon-copy");
  const refused = copyValueControl(el, "x", { copy: async () => { throw Error("denied"); }, ...c });
  await refused.childNodes[0].onclick();
  assert.equal(refused.childNodes[0].attrs["aria-label"], failed); assert.equal(refused.childNodes[0].childNodes[0].className, "tm-native-icon tm-icon-copy");
  assert.equal(refused.childNodes[1].textContent, failed);
}
hub.lang = "ru";

// Текст со значками: значок сразу за значением, до знака препинания; текст тот же; без значений — один узел.
const p = valueElement(el, "div", "tm-verdict", screen);
assert.equal(p.className, "tm-verdict"); assert.equal(p.textContent, screen);
assert.deepEqual(controls(p).map((at) => before(at).split(/\s/).at(-1)), ["app.agentshub.client.proto", "hub-proto"]);
assert.ok(p.childNodes[p.childNodes.indexOf(controls(p)[0].parentNode) + 1].textContent.startsWith(", SKU"));
// связка: последний сегмент значения и значок, без отдельного текста
assert.deepEqual(tree(p).filter((n) => n.className === "tm-copy-tie").map((t) => t.textContent), [".proto", "proto"]);
const path = valueElement(el, "div", null, "Лог ~/.claude/artifacts/hub/pinamar/smoke.log и 66cb2db0.");
assert.deepEqual(tree(path).filter((n) => n.className === "tm-copy-tie").map((t) => t.textContent), ["smoke.log", "66cb2db0"]);
assert.deepEqual(tieCases.map(([v]) => tieOf(v)), tieCases.map(([, t]) => t));
const plain = valueElement(el, "p", null, "Проверь результат и напиши.");
assert.equal(plain.childNodes.length, 1); assert.equal(controls(plain).length, 0);
assert.equal(valueElement(el, "p", null, undefined).textContent, "");

// Разметка replyText (ссылки, курсив): значок у значений по видимому тексту, внутри ссылок — нет, в курсиве — за значением.
const rich = el("div", "tm-draft-text tm-rich-text");
const link = el("a", null, "https://example.test/m800001"), em = el("em", null, "hub-proto");
rich.append("Bundle ID app.agentshub.client.proto, SKU ", em, " и ", link, " d837401");
decorateValues(el, rich);
assert.equal(rich.textContent, "Bundle ID app.agentshub.client.proto, SKU hub-proto и https://example.test/m800001 d837401");
assert.deepEqual(controls(rich).map((at) => before(at).split(/\s/).at(-1)), ["app.agentshub.client.proto", "hub-proto", "d837401"]);
assert.equal(em.childNodes.at(-1).className, "tm-copy-tie", "значок внутри курсива — сразу за значением");
assert.equal(controls(link).length, 0, "в ссылке значка нет: у неё своё меню");
// повторный проход не удваивает значки
decorateValues(el, rich); assert.equal(controls(rich).length, 3);

// Буфер: navigator.clipboard есть — им; нет (http tailnet) — скрытое поле и execCommand; ничего нет — отказ.
const got = [];
await copyText("a1", { navigator: { clipboard: { writeText: async (v) => got.push(v) } }, document: null });
const doc = { body: { append() {} }, activeElement: null, execCommand: (c) => { got.push(c + ":" + field.value); return true; },
  createElement: () => field };
const field = { setAttribute() {}, focus() {}, select() {}, remove() { got.push("removed"); } };
await copyText("b2", { navigator: {}, document: doc });
assert.deepEqual(got, ["a1", "copy:b2", "removed"]);
await assert.rejects(copyText("c3", { navigator: {}, document: {} }));

// main.js: значки в предложении, черновике, пояснении «Почему», ✨ над полем и строке разбора; лента реплик — без них.
assert.match(src, /import \{ decorateValues, valueElement \} from "\.\/copy-values\.js";/);
assert.match(src, /decorateValues\(el, replyText\(el,p\.text,"tm-proposed-text","p"\)\), valueElement\(el, "p", null, p\.context\), valueElement\(el, "p", null, p\.next_action\)/);
assert.match(src, /d\.append\(by, decorateValues\(el, replyText\(el,text\)\)\)/);
assert.match(src, /valueElement\(el, "div", "tm-draft-why"/);
assert.match(src, /valueElement\(el,"div",null,whyLine\(guidance\)\)/);
assert.match(src, /valueElement\(el, "div", "tm-verdict", analysed\)/);
assert.equal((src.match(/decorateValues\(|valueElement\(/g) || []).length, 7, "ровно 7 мест");
const css = readFileSync(new URL("../web/teams.css", import.meta.url), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
for (const [, selector] of css.matchAll(/([^{}]+)\{[^}]*user-select\s*:\s*none[^}]*\}/g))
  assert.equal(selector.trim(), ".tm-copy-at", "плагин выключает выделение только у самого значка");
assert.match(css, /\.tm-icon-check \{ --tm-icon: url\("\.\/icons\/check\.svg"\); \}/);
console.log("ALL OK");
