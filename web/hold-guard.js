// A web editor hold must never outlive the page that took it. The collector never releases a hold by itself
// (navigation, time and restart leave it), and another client cannot take it over, so a closed tab, a reload or an
// abandoned draft used to lock the conversation for every other client (Android, iPhone, Mac).
// This module owns the page-side bookkeeping; main.js does the transport. No DOM, no network.
const HOLDS = "hub.teams.holds";   // editor identity → { message id → time the hold was acknowledged }
const ALIVE = "hub.teams.alive";   // editor identity → last heartbeat of the page that owns it
export const BEAT_MS = 5000;
export const STALE_MS = 30000;      // a page silent this long is gone (closed, crashed, frozen)
export const RETRY_MS = 30000;      // one release attempt per conversation this often
export const MAX_TRIES = 5;
const KEEP_MS = 7 * 24 * 3600 * 1000;

const read = (store, key) => {
  try { const v = JSON.parse(store?.getItem(key) || "{}"); return v && typeof v === "object" && !Array.isArray(v) ? v : {}; }
  catch { return {}; }
};
const write = (store, key, value) => { try { store?.setItem(key, JSON.stringify(value)); } catch { /* blocked storage: the live checks still run */ } };

// Facts about holds this browser took: only these may be released by a later page (never a hold of another device).
export function remember(store, editor, id, now = Date.now()) {
  const all = read(store, HOLDS); (all[editor] ||= {})[id] = now; write(store, HOLDS, all);
}
export function forget(store, editor, id) {
  const all = read(store, HOLDS);
  if (!all[editor] || !(id in all[editor])) return;
  delete all[editor][id]; if (!Object.keys(all[editor]).length) delete all[editor];
  write(store, HOLDS, all);
}
export const beat = (store, editor, now = Date.now()) => { const a = read(store, ALIVE); a[editor] = now; write(store, ALIVE, a); };
export function leave(store, editor) { const a = read(store, ALIVE); delete a[editor]; write(store, ALIVE, a); }

export const heldBy = (m, editor) => m?.inbox?.v === 1 && m.inbox.held === true && m.inbox.holder === editor;

// What to release now. msgs: id → message with the collector's token; inUse: ids whose editor is on screen right now;
// idle: ids whose editor is not on screen (the caller counts two quiet checks before it lists them).
// Returns { own: [ids held by this page and not in use], orphans: [{ id, editor }], gone: cleanup of the registry }.
export function plan(store, me, msgs, { inUse = new Set(), now = Date.now() } = {}) {
  const holds = read(store, HOLDS), alive = read(store, ALIVE);
  const own = [], orphans = [];
  for (const [id, m] of msgs) if (heldBy(m, me) && !inUse.has(id)) own.push(id);
  for (const [editor, ids] of Object.entries(holds)) {
    for (const [id, at] of Object.entries(ids)) {
      const m = msgs.get(id);
      if (m && !heldBy(m, editor)) forget(store, editor, id);       // released, sent or taken: nothing left to do
      else if (!m && now - at > KEEP_MS) forget(store, editor, id);  // the conversation left the list a long time ago
      else if (m && editor !== me && !(now - (alive[editor] || 0) < STALE_MS)) orphans.push({ id, editor });
    }
  }
  return { own, orphans };
}

// The collector's own draft_control request (docs/inbox-management.md): current token, stable editor, explicit action.
export const releaseRequest = (m, editor, rid) => ({ kind: "draft_control", id: m.id, rid, inbox: m.inbox, editor, action: "release" });

// Per-conversation throttle of release attempts, so a refused one (stale token) is not repeated every beat.
export function attempts() {
  const seen = new Map();
  return {
    due(key, now = Date.now()) { const r = seen.get(key); return !r || (r.n < MAX_TRIES && now - r.at >= RETRY_MS); },
    mark(key, now = Date.now()) { const r = seen.get(key) || { n: 0, at: 0 }; seen.set(key, { n: r.n + 1, at: now }); },
    clear(key) { seen.delete(key); },
  };
}
