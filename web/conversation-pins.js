// Browser preferences only; provider read state and message delivery are separate.
export function conversationPins(scope, storage) {
  const cache = new Map();
  const store = () => storage ?? globalThis.localStorage;
  const key = () => 'hub.inbox.pinned.v1:' + scope();
  function current() {
    const name = key();
    if (!cache.has(name)) {
      let values = [];
      try { const value = JSON.parse(store().getItem(name) || '[]'); if (Array.isArray(value)) values = value.filter(v => typeof v === 'string'); } catch {}
      cache.set(name, new Set(values));
    }
    return cache.get(name);
  }
  return {
    has(id) { return current().has(id); },
    toggle(id) {
      const next = new Set(current());
      next.has(id) ? next.delete(id) : next.add(id);
      try { store().setItem(key(), JSON.stringify([...next])); } catch { return false; }
      cache.set(key(), next);
      return true;
    },
  };
}
