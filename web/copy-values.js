import { T } from "./ui-text.js";

// Значок «скопировать» у значений в тексте Inbox: разбор хаба (почему), пояснение черновика, черновик и предложение
// после личного указания. Правило — hub-ios design-plans/kit/copy-value.md, Sources/CopyValues.swift; перенос один в
// один, как web/copy-values.js модуля hubbahub-web-look 0.3.73 (плагин не импортирует /static/js ядра и модулей).
// Значения: идентификаторы вида app.agentshub.client.proto, значение после метки (Bundle ID, SKU, ID, токен, ключ,
// команда:), хеши, UUID, id хаба (m800001, d800001), пути. Внутри адреса http… и ссылок — нет: у ссылки своё меню.
const rx = (source, flags = "") => new RegExp(source, "gu" + flags);
const URL_RX = rx(String.raw`\b(?:https?|ftp|file)://\S+`, "i");
const REVERSE_DOMAIN = rx(String.raw`(?<![\p{L}\p{N}_.@/-])[A-Za-z][A-Za-z0-9-]*(?:\.[A-Za-z][A-Za-z0-9-]*){2,}(?![\p{L}\p{N}_-]|\.[A-Za-z0-9])`);
const LABEL = rx(String.raw`(?<![\p{L}\p{N}])(?:bundle id|sku|id|token|токен|key|ключ)(\s*:\s*|\s+)([A-Za-z0-9][A-Za-z0-9._:/@+=-]*[A-Za-z0-9/_])`, "id");
const COMMAND = rx(String.raw`(?<![\p{L}\p{N}])(?:команда|command)\s*:[ \t]*([^\n]+)`, "id");
const HASH = rx(String.raw`(?<![\p{L}\p{N}_-])[0-9a-f]{7,40}(?![\p{L}\p{N}_-])`);
const UUID = rx(String.raw`(?<![\p{L}\p{N}_-])[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?![\p{L}\p{N}_-])`, "i");
const HUB_ID = rx(String.raw`(?<![\p{L}\p{N}_-])[mdqp][0-9]{5,}(?![\p{L}\p{N}_-])`);
const ROOTS = "Users|tmp|private|var|opt|Applications|Library|etc|usr";
const PATH = rx(String.raw`(?<![\p{L}\p{N}_.:/~-])(?:~/[^\s,;«»"'()\[\]]+|/(?:${ROOTS})(?:/[^\s,;«»"'()\[\]]+)+)`);
// Путь с пробелами — только в кавычках ("…", «…», “…”): значение без кавычек.
const QUOTED_PATH = rx(String.raw`["«“]((?:~/|/(?:${ROOTS})/)[^"»”\n]+)["»”]`, "d");
const TRAILING = ".,:;!?";
const overlaps = (a, b) => Math.max(a.start, b.start) < Math.min(a.end, b.end);

/** Найденные значения по порядку, без пересечений: из пересекающихся — раннее, при равном начале — длинное. */
export function copyValues(text) {
  const s = String(text ?? ""), links = [...s.matchAll(URL_RX)].map((m) => ({ start: m.index, end: m.index + m[0].length })), found = [];
  function add(start, end) {
    // хвостовой знак препинания — не часть значения (путь и команда берут всё до пробела/конца строки)
    while (end > start && TRAILING.includes(s[end - 1])) end--;
    while (end > start && s[end - 1] === " ") end--;
    const r = { start, end };
    if (end - start >= 3 && !links.some((link) => overlaps(link, r))) found.push(r);
  }
  const whole = (m) => add(m.index, m.index + m[0].length), group = (m, n) => add(m.indices[n][0], m.indices[n][1]);
  for (const m of s.matchAll(REVERSE_DOMAIN)) whole(m);
  for (const m of s.matchAll(LABEL)) if (m[1].includes(":") || /[0-9\-_./]/.test(m[2])) group(m, 2);
  for (const m of s.matchAll(COMMAND)) group(m, 1);
  for (const m of s.matchAll(HASH)) if (/[0-9]/.test(m[0]) && /[a-f]/.test(m[0])) whole(m);
  for (const m of s.matchAll(UUID)) whole(m);
  for (const m of s.matchAll(HUB_ID)) whole(m);
  for (const m of s.matchAll(PATH)) whole(m);
  for (const m of s.matchAll(QUOTED_PATH)) group(m, 1);
  const taken = [];
  for (const r of found.sort((a, b) => a.start !== b.start ? a.start - b.start : (b.end - b.start) - (a.end - a.start)))
    if (!taken.some((t) => overlaps(t, r))) taken.push(r);
  return taken.map((r) => ({ ...r, value: s.slice(r.start, r.end) }));
}

// Буфер: на http-адресе tailnet navigator.clipboard нет (не secure context) — запасной путь через скрытое поле.
export async function copyText(text, { navigator = globalThis.navigator, document = globalThis.document } = {}) {
  if (navigator?.clipboard?.writeText) {
    try { await navigator.clipboard.writeText(text); return; } catch { /* запасной путь ниже */ }
  }
  if (!document?.body || !document.execCommand) throw Error("Copy unavailable");
  const field = document.createElement("textarea"), previous = document.activeElement;
  field.className = "tm-copy-field"; field.value = text; field.readOnly = true; field.tabIndex = -1;
  field.setAttribute("aria-hidden", "true");
  try {
    document.body.append(field); field.focus({ preventScroll: true }); field.select();
    if (!document.execCommand("copy")) throw Error("Copy unavailable");
  } finally { field.remove(); previous?.focus?.({ preventScroll: true }); }
}

const textNode = (el, value) => globalThis.document?.createTextNode ? globalThis.document.createTextNode(value) : el("span", null, value);
const glyph = (el, name) => { const i = el("span", "tm-native-icon tm-icon-" + name); i.setAttribute("aria-hidden", "true"); return i; };
const COPIED_FOR = 1500;
// Перерисовка Inbox пересобирает строки разбора и черновика: только что скопированное значение рисуется галочкой до конца
// своих 1,5 с и в новой разметке.
const copiedAt = new Map();

/**
 * Значок «скопировать» сразу за значением: span.tm-copy-at (его ::before — word joiner, значок не уходит на строку
 * один; в выделение не попадает: user-select:none) с кнопкой. Нажатие — значение в буфер, значок ~1,5 с сменяется
 * галочкой того же размера; подтверждение — имя кнопки и невидимый статус, без видимой строки.
 */
export function copyValueControl(el, value, { copy = copyText, setTimer = setTimeout, clearTimer = clearTimeout, now = Date.now } = {}) {
  const label = T("Копировать", "Copy", "Copiar"), copied = T("Скопировано", "Copied", "Copiado");
  const at = el("span", "tm-copy-at"), button = el("button", "tm-copy-value"), note = el("span", "tm-sr-only");
  button.type = "button"; note.setAttribute("role", "status"); note.setAttribute("aria-live", "polite");
  let timer;
  const show = (icon, name, said, done) => {
    button.replaceChildren(glyph(el, icon)); button.title = name; button.setAttribute("aria-label", name);
    button.setAttribute("data-copied", String(done)); note.textContent = said;
  };
  const reset = () => show("copy", label, "", false);
  button.onclick = async (e) => {
    e?.stopPropagation?.(); clearTimer(timer);
    try { await copy(value); copiedAt.set(value, now()); show("check", copied, copied, true); timer = setTimer(reset, COPIED_FOR); }
    catch { const failed = T("Не удалось скопировать", "Could not copy", "No se pudo copiar"); show("copy", failed, failed, false); timer = setTimer(reset, COPIED_FOR); }
  };
  const left = COPIED_FOR - (now() - (copiedAt.get(value) ?? -Infinity));
  if (left > 0) { show("check", copied, "", true); timer = setTimer(reset, left); } else { copiedAt.delete(value); reset(); }
  at.append(button, note); return at;
}

/**
 * Значки в уже собранном тексте (replyText: текст, ссылки, курсив): значения ищутся по видимому тексту блока, как в
 * нативе (PieceText); внутри ссылок — нет. Ходит только по своим узлам блока, не по документу.
 */
export function decorateValues(el, block, options) {
  const pieces = []; let plain = "", done = false;
  (function walk(node, link) {
    for (const child of [...(node.childNodes || [])]) {
      if (child.nodeType === 3) { pieces.push({ node: child, start: plain.length, link }); plain += child.data; continue; }
      const tag = String(child.tagName || "").toLowerCase();
      if (child.classList?.contains("tm-copy-at")) { done = true; continue; }
      if (tag === "button") continue;
      walk(child, link || tag === "a");
    }
  })(block, false);
  if (done) return block;   // уже со значками: второй проход их не удваивает
  const links = pieces.filter((p) => p.link).map((p) => ({ start: p.start, end: p.start + p.node.data.length }));
  const ranges = copyValues(plain).filter((v) => !links.some((l) => overlaps(l, v)));
  // С конца: вставка за значением не сдвигает начала ещё не обработанных.
  for (const r of ranges.sort((a, b) => b.end - a.end)) {
    const piece = pieces.find((p) => r.end > p.start && r.end <= p.start + p.node.data.length);
    if (!piece) continue;
    const cut = r.end - piece.start, tail = piece.node.data.slice(cut);
    // Последний кусок значения (после / - _ :, до 12 знаков) и значок — одной неразрывной связкой: длинный путь
    // переносится по сегментам, значок не уходит на строку один и при overflow-wrap:anywhere. Текст остаётся текстом.
    const end = piece.node.data.slice(0, cut), last = tieOf(r.value), keep = Math.min(last.length, end.length);
    piece.node.data = end.slice(0, end.length - keep);
    const tie = el("span", "tm-copy-tie");
    tie.append(textNode(el, end.slice(end.length - keep)), copyValueControl(el, r.value, options));
    if (tail) piece.node.after(textNode(el, tail));
    piece.node.after(tie);
  }
  return block;
}

// Хвост значения, что держится вместе со значком: последний сегмент пути/имени, не длиннее 12 знаков.
export function tieOf(value) {
  const last = String(value).split(/(?<=[\/\-_:\s])/).at(-1) || "";
  return last.length > 12 ? last.slice(-6) : last;
}

/** Элемент tag с текстом и значками у найденных значений; без значений — как прежде el(tag, cls, text). */
export function valueElement(el, tag, cls, text, options) {
  const s = String(text ?? ""), node = el(tag, cls, s);
  return copyValues(s).length ? decorateValues(el, node, options) : node;
}
