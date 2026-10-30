// Переход в Inbox по адресу #/x/inbox?plugin=<канал>&id=<сообщение> | &post=<pN> (Plugin API 1.28): какое сообщение открыть и
// в какой папке оно лежит. Колокол хаба зовёт с plugin плагина, чьё уведомление он показывает (например proactivity), а id у
// него — тот же id сообщения ленты teams, поэтому по id канал не проверяем; post — номер поста именно ленты teams.
export const OPEN_FOLDERS = ["new", "sent", "failed", "archive", "done"];   // done — «Разобранные»: отвеченное без отправки отсюда

export function openTarget(params) {
  if (!params || typeof params !== "object") return null;
  if (params.id) return { id: String(params.id) };
  if (params.post && (!params.plugin || params.plugin === "teams")) return { post: String(params.post) };
  return null;
}

// Папка, где лежит сообщение; нет сообщения или ни одна папка его не держит — undefined.
export function openFolder(message, inFolder) {
  return message ? OPEN_FOLDERS.find((folder) => inFolder(message, folder)) : undefined;
}
