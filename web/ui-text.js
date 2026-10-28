// Подписи плагина на языке владельца: T(ru, en[, es]). Свой модуль, а не /static/js/ui-text.js ядра — в ядре flagman его нет
// (там i18n.js и hub.lang), и импорт давал 404: плагин не грузился. Язык — как у прежнего ядерного T: owner.lang из
// снимка, затем язык страницы (hub.lang — flagman, Plugin API 1.25), затем <html lang>; "en" — английский, иначе русский.
let hub = null;

// register(h) плагина отдаёт сюда объект hub; до этого — язык страницы
export function bindHub(h) { hub = h; }

const lang = () => {
  let owner = null;
  try { owner = hub?.snapshot?.()?.owner?.lang; } catch { /* снимка ещё нет */ }
  return owner || hub?.lang || document.documentElement.lang;
};

// es — только там, где подпись уже переведена (как у натива); без неё испанский по-прежнему видит русскую
export const T = (ru, en, es) => { const l = lang(); return l === "en" ? en : l === "es" && es ? es : ru; };
