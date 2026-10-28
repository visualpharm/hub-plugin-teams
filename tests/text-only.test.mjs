import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
// Текстовое поле на ядре без composerFiles (flagman): hub.input не знает attachments:false — скрепку прячет плагин,
// вставленные и перетащенные файлы останавливает до поля; текст вставляется как обычно; на ядре с composerFiles
// и для поля с файлами плагин поле не трогает. Запуск: node tests/text-only.test.mjs web/main.js
const src = readFileSync(process.argv[2] || "web/main.js", "utf8");
const a = src.indexOf("const textInput = opts =>"), b = src.indexOf("\n};\n", a) + 3;
assert.ok(a > 0, "textInput в main.js");
const make = hub => new Function("hub", src.slice(a, b) + "; return textInput;")(hub);

function field() {
  const attach = { hidden: false }, listeners = [];
  const node = {
    querySelector: (q) => (q === ":scope > .attach" ? attach : null),
    addEventListener: (type, fn, capture) => listeners.push({ type, fn, capture }),
  };
  return { attach, listeners, node };
}
function fire(f, type, types) {
  const e = { type, stopped: false, prevented: false, preventDefault() { this.prevented = true; }, stopImmediatePropagation() { this.stopped = true; } };
  e[type === "paste" ? "clipboardData" : "dataTransfer"] = { types };
  for (const l of f.listeners.filter((l) => l.type === type)) { assert.equal(l.capture, true, type + " — в фазе перехвата"); l.fn(e); }
  return e;
}

// flagman: capabilities без composerFiles
let f = field();
const flagman = { capabilities: { composerTransport: 1 }, input: () => ({ node: f.node }) };
let box = make(flagman)({ attachments: false });
assert.equal(box.node, f.node);
assert.equal(f.attach.hidden, true, "скрепка спрятана");
for (const type of ["paste", "dragover", "drop"]) {
  const e = fire(f, type, ["Files"]);
  assert.ok(e.prevented && e.stopped, type + " с файлами не доходит до поля");
}
const text = fire(f, "paste", ["text/plain"]);
assert.ok(!text.prevented && !text.stopped, "текст вставляется");

// поле, где файлы разрешены, — без изменений
f = field(); make(flagman)({ attachments: true });
assert.equal(f.attach.hidden, false); assert.equal(f.listeners.length, 0);
f = field(); make(flagman)({});
assert.equal(f.attach.hidden, false); assert.equal(f.listeners.length, 0);

// ядро, которое само уважает attachments:false (composerFiles), — поле не трогаем
f = field();
make({ capabilities: { composerFiles: 1 }, input: () => ({ node: f.node }) })({ attachments: false });
assert.equal(f.attach.hidden, false); assert.equal(f.listeners.length, 0);

// начальный текст (черновик хаба в поле, web-parity m1053809): ядро flagman text в hub.input не берёт — плагин кладёт его set;
// ядро, что взяло текст само, и пустое поле set не получают
const stub = (initial) => { const calls = []; let value = initial; return { calls, box: { node: field().node, draft: () => ({ text: value, files: [] }), set: (n) => { calls.push(n); if (n.text !== undefined) value = n.text; } } }; };
let s = stub(""); make({ capabilities: {}, input: () => s.box })({ text: "Черновик хаба" });
assert.deepEqual(s.calls, [{ text: "Черновик хаба" }], "flagman: текст черновика через set");
s = stub("Черновик хаба"); make({ capabilities: {}, input: () => s.box })({ text: "Черновик хаба" });
assert.deepEqual(s.calls, [], "ядро взяло текст само — set не нужен");
s = stub(""); make({ capabilities: {}, input: () => s.box })({ text: "" });
assert.deepEqual(s.calls, [], "пустой текст — поле не трогаем");
make({ capabilities: {}, input: () => ({ node: field().node }) })({ text: "x" });   // старое ядро без set/draft — не падает

// все текстовые поля плагина идут через textInput
assert.ok(src.includes('st.box = textInput({ key: "reply:"'));
assert.ok(src.includes('st.instructBox = textInput({ key: "instruction:"'));
assert.ok(src.includes('const input = textInput({ key: "whole-inbox"'));
assert.ok(src.includes("newMessage(h, textInput)"));
const nm = readFileSync(new URL("../web/new-message.js", import.meta.url), "utf8");
assert.ok(nm.includes('const box = input({ key: "new:"'));
console.log("text-only ok");
