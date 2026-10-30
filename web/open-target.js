// Переход в Inbox по адресу #/x/inbox?plugin=<канал>&id=<сообщение> | &post=<pN> (Plugin API 1.28): какое сообщение открыть и
// в какой папке оно лежит. Колокол хаба зовёт с plugin плагина, чьё уведомление он показывает (например proactivity), а id у
// него — тот же id сообщения ленты teams, поэтому по id канал не проверяем; post — номер поста именно ленты teams.
export const OPEN_FOLDERS = ["new", "sent", "failed", "archive", "done"];   // done — «Разобранные»: отвеченное без отправки отсюда

export const POST_ID = /^p[0-9]{1,15}$/;
export const OLD_POST_FEATURE = "feed.post_by_id";   // ядро умеет отдать пост по номеру и из-за окна ленты (hub.feedPosts)

export function openTarget(params) {
  if (!params || typeof params !== "object") return null;
  // К id колокол кладёт post (пост сообщения в ленте teams) и state=answered (карточка уже отвечена: по старому посту
  // этого не видно — ответ лежит в более поздних постах, которых в загруженном куске нет)
  if (params.id) {
    const post = POST_ID.test(String(params.post || "")) ? String(params.post) : "";
    return { id: String(params.id), ...(post ? { post } : {}), ...(params.state === "answered" ? { state: "answered" } : {}) };
  }
  if (params.post && (!params.plugin || params.plugin === "teams")) return { post: String(params.post) };
  return null;
}

// Папка, где лежит сообщение; нет сообщения или ни одна папка его не держит — undefined.
export function openFolder(message, inFolder) {
  return message ? OPEN_FOLDERS.find((folder) => inFolder(message, folder)) : undefined;
}

// Сообщение из поста ленты. Ранние версии сборщика звали выбранный канал src "support" и постили и ответы внутри треда
// (в where — « · тред»): ответ без упоминания не показываем, только первое сообщение треда. Нет сообщения — null.
export function feedMessage(d, postId) {
  if (!d || d.kind !== "msg") return null;
  const reply = d.src === "support" && d.where?.includes(" · ");
  if (reply && !d.mention) return null;
  return { ...d, ...(reply ? { src: "mention" } : d.src === "support" ? { src: "channel" } : {}), post: postId };
}

// Старое сообщение, которого нет в загруженной ленте (окно — 500 постов): грузить его по номеру поста можно, только если
// ядро это умеет (features) и адрес назвал пост.
export const canLoadOld = (target, features) => !!target?.post && POST_ID.test(target.post) && Array.isArray(features) && features.includes(OLD_POST_FEATURE);

// Ответ ядра на запрос поста по номеру → сообщение для списка; пост должен быть именно тот, от процесса плагина, и
// сообщением того id, что назвал адрес (id уже есть — чужой пост под этим номером не подходит).
export function oldMessage(posts, target, author) {
  for (const p of Array.isArray(posts) ? posts : []) {
    if (!p || p.id !== target.post || p.by !== author) continue;
    let d = null;
    try { d = JSON.parse(p.text); } catch { continue; }
    if (typeof d?.id !== "string" || (target.id && d.id !== target.id)) continue;
    const message = feedMessage(d, p.id);
    if (message) return message;
  }
  return null;
}
