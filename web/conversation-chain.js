// Пункт Inbox — пост сообщения. Собеседник дописал — сборщик закрывает прежний пост (answered с `newer`, у старых
// сборщиков — соседним постом перед новым сообщением той же переписки) и открывает новый. Черновик хаба, ✨ и «Хаб
// готовит черновик», положенные у прежнего поста, идут за перепиской к новому пункту (как Inbox+Chain.swift натива,
// d653040). Ответ владельца (своя отправка, реакция) и закрытие без соседнего нового сообщения заменой не считаются.

// Пометку proactivity «Перенесён из pN: …» под «---» разбирает splitDraft (main.js).

export function conversationChain() {
  const replacedFrom = new Map();   // новое сообщение → закрытое, которое оно заменило
  let lastClosed = null;            // закрытие без newer: {id, seq} — ждём соседний пост с новым сообщением
  return {
    // Сборщик закрыл сообщение. `newer` — замена новым сообщением.
    closed(id, newer, seq) {
      if (typeof newer === "string" && newer && newer !== id) { replacedFrom.set(newer, id); lastClosed = null; }
      else lastClosed = { id, seq };
    },
    // Новое сообщение сразу за закрытием (тот же тик сборщика, следующий пост) — замена, если переписка та же и
    // закрытое не было ответом владельца. `same(oldId)` решает вызывающий: он знает переписку и отправки.
    opened(id, seq, same) {
      const c = lastClosed; lastClosed = null;
      if (c && seq === c.seq + 1 && c.id !== id && !replacedFrom.has(id) && same(c.id)) replacedFrom.set(id, c.id);
    },
    // Сообщения, которые это заменило, ближайшее первым.
    predecessors(id) {
      const out = []; let cur = id;
      while (replacedFrom.has(cur) && out.length < 32) {
        const p = replacedFrom.get(cur);
        if (p === id || out.includes(p)) break;
        out.push(p); cur = p;
      }
      return out;
    },
  };
}

// Черновики строки: свой пост главнее; нет своих — ближайшего заменённого сообщения переписки (перенесён).
// `postOf(id)` — пост сообщения, `repliesOf(post)` — черновики сессий под постом.
export function chainReplies(chain, m, postOf, repliesOf) {
  const own = repliesOf(m.post) || [];
  if (own.length) return { list: own, carried: false };
  for (const id of chain.predecessors(m.id)) {
    const list = repliesOf(postOf(id)) || [];
    if (list.length) return { list, carried: true };
  }
  return { list: [], carried: false };
}

// ✨ нажата у этого сообщения или у заменённого им прежнего — время просьбы.
export function chainAsked(chain, m, askedOf) {
  const own = askedOf(m.id);
  if (own !== undefined) return own;
  for (const id of chain.predecessors(m.id)) { const t = askedOf(id); if (t !== undefined) return t; }
  return undefined;
}
