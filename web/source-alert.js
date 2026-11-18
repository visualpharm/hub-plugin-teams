// A source that stopped reading is named in plain words: "Gmail disconnected — new mail is not coming in" with "Reconnect",
// never the provider's raw error with its sign-in address (the owner reads the list from a phone). The address is not
// usable anyway: the reader cuts the error to 160 characters, and the sign-in returns to the reading machine's own
// 127.0.0.1. "Reconnect" sends the hub a request to sign the source in again (main.js): the hub knows how.
import { T } from "./ui-text.js";

// a lost sign-in, read on the error's words without its addresses: "oauth2.googleapis.com" in a network error is no sign-in
const AUTH = /invalid_grant|unauthori[sz]ed|\b401\b|token (?:has )?(?:expired|been revoked)|re-?auth|log(?:ged)?[- ]?in (?:required|again)|not logged in|m365 login|sign[- ]?in required|AADSTS/i;
const LINK = /["'(<]?\bhttps?:\/\/[^\s"'<>]*["')>]?/gi;   // with the quotes or brackets around it

// the error's words without addresses, spaces and the trailing punctuation
export const plain = (error) => String(error || "").replace(LINK, "").replace(/\s+/g, " ").replace(/^[\s:;,.]+|[\s:;,."']+$/g, "").trim();

const isMail = (name) => name === "email" || name === "gmail";
const whoOf = (name, raw, names) => isMail(name) && /google|gmail/i.test(raw + name) ? "Gmail" : names[name] || name;

// name — the reading's source (status post), names — its display names; returns {text, reconnect: true for a lost sign-in}
export function sourceAlert(name, error, names = {}) {
  const raw = String(error || ""), words = plain(raw), mail = isMail(name), who = whoOf(name, raw, names);
  const off = mail ? T("новые письма сюда не приходят", "new mail is not coming in", "el correo nuevo no llega")
    : T("новые сообщения сюда не приходят", "new messages are not coming in", "los mensajes nuevos no llegan");
  if (AUTH.test(words)) {
    return { text: T(`${who} отключился — ${off}.`, `${who} disconnected — ${off}.`, `${who} se desconectó: ${off}.`), reconnect: true };
  }
  const why = words || T("ошибка", "error", "error"), Off = off[0].toUpperCase() + off.slice(1);
  // Teams reads through ms365: its failures are most often an expired sign-in there
  const maybe = name === "teams" ? " " + T("Возможно, истёк вход ms365.", "The ms365 sign-in may have expired.", "Quizás venció el inicio de sesión de ms365.") : "";
  return { text: T(`Не могу прочитать ${who}: ${why}. ${Off}.`, `Cannot read ${who}: ${why}. ${Off}.`, `No puedo leer ${who}: ${why}. ${Off}.`) + maybe, reconnect: false };
}

// what "Reconnect" sends the hub: the source and the plain error
export function reconnectAsk(name, error, names = {}) {
  const who = whoOf(name, String(error || ""), names);
  return T(`${who} отключился (источник ${name}): ${plain(error)}. Подключи заново.`,
           `${who} disconnected (source ${name}): ${plain(error)}. Sign it in again.`,
           `${who} se desconectó (fuente ${name}): ${plain(error)}. Conéctalo de nuevo.`);
}
