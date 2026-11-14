// One rule of the native lists (hub-ios ListAdvance.swift, the owner: "standard interactions are the same in Notes, To-do,
// Inbox, everywhere"): the open conversation left the list by the owner's action here (Archive, Send and Archive, back to
// Inbox from Archive) — the next row below opens; none below — the nearest above; the list is empty — nothing. A departure
// that is not the owner's here (the hub closed it, a reply from another device) opens nothing: opening marks a conversation
// read, and a chain of hub closures would read the list without the owner.

export const OWN_WINDOW = 60;     // seconds an "acted here" mark lives: the row leaves at once or with the collector's receipt
export const GRACE_WINDOW = 1;    // after the first step on a mark: the same departure seen again stays own, later ones do not
export const UNDO_SECONDS = 10;   // the "Archived · Undo" strip

// The row that stood below the departed one and is still there; else the nearest above; none — null.
export function nextAfter(key, was, now) {
  const at = was.indexOf(key);
  if (at < 0) return null;
  const left = new Set(now);
  for (let i = at + 1; i < was.length; i++) if (left.has(was[i])) return was[i];
  for (let i = at - 1; i >= 0; i--) if (left.has(was[i])) return was[i];
  return null;
}

export function listAdvance() {
  const own = new Map();   // key -> until (ms)
  return {
    acted(keys, at = Date.now()) {
      for (const [k, until] of own) if (until <= at) own.delete(k);
      for (const k of keys) own.set(k, at + OWN_WINDOW * 1000);
    },
    // Did the owner remove any of these keys here? The first step shortens the mark to the grace second.
    mine(keys, at = Date.now()) {
      const hit = keys.some((k) => (own.get(k) ?? 0) > at);
      for (const k of keys) {
        if (!own.has(k)) continue;
        if (hit) own.set(k, Math.min(own.get(k), at + GRACE_WINDOW * 1000)); else own.delete(k);
      }
      return hit;
    },
    kept(keys) { for (const k of keys) own.delete(k); },
  };
}
