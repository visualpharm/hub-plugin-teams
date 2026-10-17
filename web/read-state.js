// Local reminders only. Opening a conversation never sends a provider read receipt.
export function localReadState(scope, identity, legacy = new Set(), storage) {
  const cache = new Map();
  const store = () => storage ?? globalThis.localStorage;
  const key = () => 'hub.inbox.read.v1:' + scope();
  function read() {
    const name = key(), raw = store().getItem(name) || '[]';
    if (cache.get(name)?.raw===raw) return cache.get(name).value;
    const value = JSON.parse(raw);
    if (!Array.isArray(value) || value.some(x => !Array.isArray(x) || x.length!==2 || typeof x[0]!=='string' || typeof x[1]!=='boolean')) throw Error('Invalid local read state');
    const parsed = new Map(value); cache.set(name,{raw,value:parsed}); return parsed;
  }
  return {
    isUnread(message) {
      try { const value = read().get(identity(message)); if (value!==undefined) return value; } catch {}
      return !legacy.has(message.id) && message.unread!==false && message.unread!==0;
    },
    set(messages, unread) {
      try {
        const next = new Map(read()); let changed = false;
        for (const message of messages) { const id = identity(message); if (next.get(id)!==unread) { next.set(id,unread); changed=true; } }
        if (changed) store().setItem(key(),JSON.stringify([...next]));
        return true;
      } catch { return false; }
    },
  };
}
