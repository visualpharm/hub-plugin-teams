"""Другие каналы входящих рядом с Teams: WhatsApp, почта (владелец 10.10: «чтобы там были ещё WhatsApp и email, но
только то, что требует моего внимания; каналов будет больше»).

Канал — функция `read(cfg, now) -> (items, open_boxes)`, зарегистрированная `@source("имя")`. Включён, если в
`<состояние>/ext-teams/sources.json` есть ключ с его именем (`{"whatsapp": {...}, "email": {...}}`) — личные пути и
аккаунты лежат там, не в коде. items — те же dict, что у collect.py ({key, box, src, where, from, text, at, link,
mention}) плюс tier "A"|"B"; open_boxes — переписки, которые ждут владельца СЕЙЧАС: что было открыто и пропало из
списка — прочитано или отвечено, вкладка пометит «отвечено». Новый канал — ещё одна функция с `@source`, тип сообщения
src для вкладки — в SRC_LABELS страницы (web/main.js).

Что «требует внимания» — по правилам триажа Noe, в сокращении (`tier`): закрывающее «ок/спасибо» и рутинные
уведомления — C и во вкладку не попадают; срочное, штраф, блокировка, просрочка — A; живая переписка — B."""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone

SOURCES = {}
TIMEOUT = 90
OPEN = {}      # открытые пункты сборщика (ключ -> [box, at]): кладёт run_sources перед чтением каналов
GONE = set()   # ключи открытых пунктов, все ждущие сообщения которых собеседник удалил: сборщик их закрывает (d987429)


def source(name, every=120):
    def reg(fn):
        SOURCES[name] = {"fn": fn, "every": every}
        return fn
    return reg


# --- что требует внимания (правила Noe: server.py _compute_tier, в сокращении) ---------------------------------------
IMMEDIATE = re.compile(
    r"\b(?:urgent(?:e)?|urgente|asap|immediately|inmediato|inmediatamente|deadline|vence (?:hoy|ma[nñ]ana)|"
    r"antes de (?:hoy|ma[nñ]ana)|срочно|сегодня до|дедлайн)\b|"
    r"payment (?:has )?(?:failed|declined|rejected)|pago (?:fallid|rechazad|declinad)|card declined|past due|overdue|"
    r"en mora|(?:service|account) (?:has been |was |is )?(?:blocked|suspended|disabled)|"
    r"(?:servicio|cuenta) (?:fue |est[aá] |ha sido )?(?:bloquead|suspendid|inhabilitad)|"
    r"intimaci[oó]n|citaci[oó]n|embargo|multa|final notice|[uú]ltimo aviso|"
    r"action required|acci[oó]n requerida|pending confirmation|requires? your (?:action|attention|response)",
    re.IGNORECASE)
ROUTINE = re.compile(
    r"\b(?:newsletter|digest|unsubscribe|darse de baja|webinar|product announcement|marketing update|"
    r"order status|shipping update|delivery update|refund|receipt|recibo|comprobante)\b|"
    r"(?:payment|pago|transferencia) (?:was |is |has been |fue |es |ya )?(?:received|successful|completed|approved|"
    r"recibid[oa]|exitos[oa]|completad[oa]|aprobad[oa])|(?:subscription|suscripci[oó]n) (?:has been |was )?"
    r"(?:cancel|renew|cancelad|renovad)|auto[- ]?renewal|renovaci[oó]n autom[aá]tica|"
    r"terms of service|privacy policy|t[eé]rminos de servicio",
    re.IGNORECASE)
ACK_WORDS = {"ok", "oka", "okey", "okay", "dale", "listo", "gracias", "gracia", "gracias!", "perfecto", "genial",
             "buenisimo", "buenísimo", "bien", "vale", "si", "sí", "sii", "claro", "thanks", "thx", "thank", "you",
             "good", "great", "спасибо", "ок", "окей", "хорошо", "ладно", "понял", "отлично", "супер", "да", "👍", "🙏"}
AUTOMATED = re.compile(
    r"no[-_.]?reply|do[-_.]?not[-_.]?reply|donotreply|mailer-daemon|postmaster|notifications?@|notify@|"
    r"newsletter|updates?@|info@|news@|marketing@|billing@|invoice|support@|team@|hello@|bounce", re.IGNORECASE)


def closing_ack(text):
    t = (text or "").strip().lower()
    if not t or len(t) > 80 or "?" in t or "http" in t:
        return False
    words = re.findall(r"[\w'🙏👍]+", t)
    if not words:
        return bool(re.search(r"[👍🙏❤️💗💖🫶🤝👌✅]", t))
    return all(w in ACK_WORDS for w in words)


def tier(text, *, automated=False, updates=False):
    """A — срочное; B — живая переписка, подождёт; C — не требует внимания (во вкладку не идёт)."""
    if closing_ack(text):
        return "C"
    if IMMEDIATE.search(text or ""):
        return "A"
    if automated or updates or ROUTINE.search(text or ""):
        return "C"
    return "B"


def iso_utc(dt):
    if dt.tzinfo is None:
        dt = dt.astimezone()   # без пояса — местное время машины
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(cmd, timeout=TIMEOUT):
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
    if out.returncode:
        lines = [x for x in (out.stderr or out.stdout).splitlines() if x.strip()]
        e = OSError((lines[-1] if lines else f"код {out.returncode}")[:200])
        e.full = lines[-1] if lines else ""   # целиком: пометка «reconcile before retry» стоит в конце строки
        raise e
    return out.stdout


def expand(p):
    return os.path.expanduser(p)


# --- новый адресат в Контакты Mac (20.10, Иван m643740): send заводит карточку по --who «имя» и --about «дело» ------
_SEND_HELP = {}
CONTACT_KEYS = ("who", "about", "authors", "title")   # в ref — только для send: отпечаток адреса (target_of) их не учитывает


def send_knows(cmd, flag):
    """Понимает ли команда send флаг. Старая версия на незнакомом флаге откажет, а повторять отправку нельзя — поэтому
    сверяем заранее по её --help (ничего не отправляет); ответ помним до смены файла команды."""
    try:
        key = (cmd, os.stat(cmd).st_mtime)
    except OSError:
        key = (cmd, None)
    if key not in _SEND_HELP:
        try:
            out = subprocess.run([cmd, "--help"], capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL)
            _SEND_HELP[key] = (out.stdout or "") + (out.stderr or "")
        except (OSError, subprocess.SubprocessError):
            _SEND_HELP[key] = ""
    return bool(re.search(rf"(?<![\w-]){re.escape(flag)}(?![\w-])", _SEND_HELP[key]))


def one_line(s, limit=80):
    s = " ".join(str(s or "").split()).lstrip("…").strip()
    return s if len(s) <= limit else s[:limit - 1].rstrip() + "…"


def person(name):
    """Имя для карточки: пусто, если это только номер или id (такой карточки не заводим — send положит номер в ожидание)."""
    name = one_line(name)
    return name if re.search(r"[^\d\s+()\-@.]", name) and not re.fullmatch(r"@?\w+@(?:c|g)\.us", name) else ""


def contact_flags(cmd, who="", about=""):
    """--who/--about для send wa|tg: пустое не передаём; команда их не знает — не передаём ничего."""
    who, about = person(who), one_line(about)
    if not (who or about) or not send_knows(cmd, "--who") or not send_knows(cmd, "--about"):
        return []
    return [*(["--who", who] if who else []), *(["--about", about] if about else [])]


def contact_of(name, about, group=False, wait=()):
    """Поля ref для карточки контакта: у личной переписки — имя собеседника; в группе — автор последнего ждущего
    сообщения (и авторы по id — ответ на конкретное), иначе без имени."""
    authors = {str(m["id"]): person(m.get("from") or m.get("author")) for m in wait or ()
               if m.get("id") and person(m.get("from") or m.get("author"))} if group else {}
    who = (person((wait[-1] if wait else {}).get("from") or (wait[-1] if wait else {}).get("author")) if group
           else person(name))
    return {**({"who": who} if who else {}), **({"about": one_line(about)} if one_line(about) else {}),
            **({"authors": dict(list(authors.items())[-20:])} if authors else {})}


KIND_NAMES = {"ptt": ("голосовое", "голосовых"), "audio": ("аудио", "аудио"), "image": ("фото", "фото"),
              "video": ("видео", "видео"), "document": ("файл", "файлов"), "sticker": ("стикер", "стикеров"),
              "chat": ("текст", "текстовых"), "location": ("геопозиция", "геопозиций"),
              "call": ("звонок", "звонков"), "ptv": ("видеосообщение", "видеосообщений"), "gif": ("GIF", "GIF")}


SERVICE_TYPES = {"e2e_notification", "notification_template", "gp2", "protocol", "ciphertext", "revoked"}


def waiting(r):
    """Сообщения чата, которые ждут владельца: непрочитанные входящие ПОСЛЕ его последнего ответа (то, на что он уже
    ответил, заново не поднимаем), без служебных. Времени нет (старая команда wa) — последние по счётчику."""
    n = r.get("unread") or 0
    msgs = [m for m in (r.get("messages") or []) if m.get("type") not in SERVICE_TYPES]
    after = r.get("out_last_t") or 0
    if after:
        msgs = [m for m in msgs if (m.get("t") or after + 1) > after]
    return msgs[-n:] if n else []


def work_group(cfg, cid, name, group):
    """Рабочая группа владельца (14.10, слово владельца: «analizar los grupos … escalar al inbox»): группа из списка
    groups в sources.json (имя или id чата). Её ветка разбирается целиком — всё после его последнего ответа, а не только
    непрочитанное и не только срочное; остальные группы — как раньше, только срочное."""
    gs = cfg.get("groups") or []
    return bool(group) and bool(gs) and (cid in gs or (name or "") in gs)


def whole_group(cfg, cid, name, group):
    """Группа, ветка которой идёт в Inbox целиком (как у рабочей): рабочая (groups) или — при all_groups: true в
    sources.json (20.10) — любая, кроме skip_groups (имя или id; спам и рассылки). Признак team (он открывает автоответ
    proactivity) остаётся только у рабочих: новые группы показываются, но отвечает на них владелец или черновик."""
    if work_group(cfg, cid, name, group):
        return True
    skip = cfg.get("skip_groups") or []
    return bool(group) and cfg.get("all_groups") is True and cid not in skip and (name or "") not in skip


def team_wait(r):
    """Сколько сообщений рабочей группы ждут разбора: все входящие после его последнего ответа (прочитал — не значит
    ответил)."""
    after = r.get("out_last_t") or 0
    return len([m for m in r.get("messages") or [] if m.get("type") not in SERVICE_TYPES
                and not m.get("out") and (m.get("t") or after + 1) > after])


def revoked(r):
    """Сообщения, которые собеседник удалил после последнего ответа владельца (26.10, d987429): в хранилище вкладки
    у удалённого своя запись type=revoked, а `wa new` кладёт в неё id исходного (revokes). [(id исходного, t)]."""
    after = r.get("out_last_t") or 0
    return [(m["revokes"], m.get("t") or 0) for m in r.get("messages") or [] if m.get("type") == "revoked"
            and m.get("revokes") and (m.get("t") or after + 1) > after]


def unread_digest(messages, n, limit=600, preview="", authors=False):
    """Резюме непрочитанного: тексты последних n входящих по порядку, медиа без подписи — словом («голосовое»,
    «фото»). Текст есть только у сообщений из сохранённой копии треда; у самого свежего без копии — строка из
    списка чатов (preview); текстовые без текста пропускаются (сборщик дочитывает чат сам и без текста пункт не шлёт).
    Длинное обрезается с конца. Ничего не известно — пусто."""
    msgs = [m for m in (messages or []) if m.get("type") not in SERVICE_TYPES][-n:] if n else []
    parts, blind, last_who = [], 0, ""
    for i, m in enumerate(msgs):
        txt = " ".join((m.get("text") or "").split())
        if not txt and i == len(msgs) - 1 and not m.get("cached"):
            txt = " ".join((preview or "").split())
        if txt:
            who = (m.get("from") or m.get("author") or "").strip() if authors else ""
            if who and who != last_who:   # в группе — кто пишет, у первой реплики подряд
                txt = f"{who}: {txt}"
            last_who = who or last_who
            parts.append(txt)
            continue
        one = KIND_NAMES.get(m.get("type") or "", (m.get("type") or "", ""))[0]
        if one and one != "текст":
            parts.append(f"[{one}]")
        else:
            blind += 1
    if not parts:
        return ""
    out = " · ".join(parts)
    return out if len(out) <= limit else "…" + out[-(limit - 1):]


ICON_WORDS = (("keyboard-voice|mic|ptt", "голосовое"), ("videocam|video", "видео"), ("photo|image|camera", "фото"),
              ("description|document|file|insert-drive", "файл"), ("audio|music|headphones", "аудио"))


def clean_preview(text):
    """Строка превью из списка чатов WhatsApp для медиа приходит именем иконки с длительностью
    («ic-keyboard-voice-filled0:32», 14.10) — переводим в слово: «[голосовое 0:32]»; неизвестную иконку убираем."""
    text = (text or "").strip()

    def word(m):
        name = m.group(1).lower()
        for pat, w in ICON_WORDS:
            if re.search(pat, name):
                return f"[{w}]"
        return ""
    out = re.sub(r"(?:wds-)?ic-([a-z-]+?)(?:-(?:filled|outline|rounded|sharp))*(?![a-z-])", word, text, flags=re.I)
    out = re.sub(r"(\])\s*(\d{1,2}:\d{2})\b", r"\1 \2", out)   # «[голосовое]0:32» → «[голосовое 0:32]»
    out = re.sub(r"\]\s(\d{1,2}:\d{2})\b", r" \1]", out)
    return " ".join(out.split())


def media_summary(kinds, n):
    """Что пришло, когда у последнего нет текста: «4 голосовых, 2 фото» вместо счётчика (11.10, Иван: «мне надо не
    число, а про что он писал»). Без типов от `wa` — число и общие слова. Содержимое без открытия чата недоступно."""
    parts = []
    for k, c in sorted((kinds or {}).items(), key=lambda kv: -kv[1]):
        if k in SERVICE_TYPES:
            continue
        one, many = KIND_NAMES.get(k, (k, k))
        if k == "chat":   # 12.10: «1 текст» читалось как содержимое; чат читаем сами (wa_read) — сюда доходит, если не вышло
            one, many = "сообщение", "сообщения"
        parts.append(f"{c} {one if c == 1 else many}")
    return ", ".join(parts) if parts else f"Непрочитанных: {n} (фото, голосовое или файл)"


# --- WhatsApp: `wa new` — читает только список чатов открытой вкладки, ничего не открывает и не отмечает прочитанным ---
@source("whatsapp", every=120)
def whatsapp(cfg, now):
    """Чаты с непрочитанным входящим за сутки. Своя вкладка у каждого номера (channels в sources.json); номер без
    вкладки/входа — ошибка в плашке, остальные читаются. Группы — только срочное: иначе это шум; рабочие (groups) и —
    при all_groups — все, кроме skip_groups, целиком (whole_group)."""
    cmd = expand(cfg.get("cmd") or "~/.claude/bin/wa")
    labels = cfg.get("labels") or {}
    items, boxes, errors, ok = [], set(), [], 0
    for ch in cfg.get("channels") or ["whatsapp"]:
        try:
            rows = json.loads(run([cmd, "new", "--channel", ch, "--hours", "24", "--json"]) or "[]")
        except (OSError, ValueError, subprocess.TimeoutExpired) as e:
            msg = re.sub(r"^(?:WhatsApp(?: Web)?:\s*)+", "", str(e))
            if "no open WhatsApp Web tab" in msg and "logged in as" in msg:
                msg = "в Chrome нет вкладки WhatsApp Web, залогиненной на этот номер"
            elif "no open WhatsApp Web tab" in msg:
                msg += " — открыта ли вкладка WhatsApp Web и включено ли View → Developer → Allow JavaScript from Apple Events"
            errors.append(f"{labels.get(ch, ch)}: {msg}")
            continue
        ok += 1
        for r in rows:
            cid, text = r.get("chat_id") or "", clean_preview(r.get("preview") or "")
            n = r.get("unread") or 0
            gone = revoked(r)
            if gone:   # удалённое снимает счётчик непрочитанных; что из ждущего осталось — по его последнему ответу
                n = max(n, team_wait(r))
            box = f"wa:{ch}:{cid}"
            dead = [f"{box}:{x}" for x, _t in gone]   # пункт удалённого: ничего не осталось — закрыть
            if not n and cid in _WA_OPENED and (r.get("out_last_t") or 0) < max(
                    [m.get("t") or 0 for m in r.get("messages") or []] or [0]):
                n = _WA_OPENED[cid]   # прочитали мы сами (текст, картинки), а не он — сообщение всё ещё ждёт ответа
            team = work_group(cfg, cid, r.get("name"), cid.endswith("@g.us"))
            whole = whole_group(cfg, cid, r.get("name"), cid.endswith("@g.us"))
            if whole:
                n = max(n, team_wait(r))
            if not cid or not n:
                GONE.update(k for k in dead if k in OPEN)
                continue   # всё прочитано или отвечено — внимания не требует
            wait = waiting({**r, "unread": n})
            def blind(ms):   # текстовые без текста; у последнего хватает строки из списка чатов
                out = [m for k, m in enumerate(ms) if not (m.get("text") or "").strip()
                       and (m.get("type") or "chat") == "chat" and not (k == len(ms) - 1 and text and not m.get("cached"))]
                if len(out) < len(ms) and any((m.get("text") or "").strip() for m in ms):
                    # 20.10: реплика, которую прочитанный чат отдал пустой, не держит остальные (Pampa Salta — сутки)
                    out = [m for m in out if (cid, m.get("id")) not in _WA_BLANK]
                return out
            wait = [{**m, "text": _WA_TEXT[(cid, m.get("id"))], "cached": True,
                     **({"from": _WA_WHO[(cid, m["id"])]} if (cid, m.get("id")) in _WA_WHO else {})}
                    if not (m.get("text") or "").strip() and (cid, m.get("id")) in _WA_TEXT else m for m in wait]
            if blind(wait):
                wait = wa_read(cfg, ch, cmd, r, wait, n)   # текста нет в копии — дочитываем чат сами, владельца не просим
            if blind(wait):
                # 14.10, владелец: «не говорить мне, что они непрочитаны» — без текста пункт не выходит; чат перечитаем
                # в плашку не идёт: это не поломка, которую чинит владелец, — в лог плагина
                print(f"whatsapp: {labels.get(ch, ch)}: чат {r.get('name') or cid} не прочитан — повторю", file=sys.stderr,
                      flush=True)
                continue
            if r.get("messages") and not wait:
                GONE.update(k for k in dead if k in OPEN)
                continue   # после его ответа нового нет (или только служебное) — отвеченное не поднимаем
            latest = max(r.get("messages") or [{}], key=lambda m: m.get("t") or 0)
            if gone and latest.get("type") == "revoked":
                text = ""   # строка списка чатов — «This message was deleted», не текст ждущего
            voice = wa_voice(cfg, ch, cid, f"{ch}:{cid}:{(wait[-1].get('id') if wait else '') or r.get('last')}", wait)
            if voice:   # 14.10: расшифровка голосового — текст сообщения (по ней и срочность, и резюме); 24.10: «🎤 …»,
                # не скачалось — так и пишем (а не «[голосовое]»: владелец решил бы, что расшифровки просто нет)
                wait = [{**m, "text": "🎤 " + voice[m["id"]]["text"], "cached": True}
                        if m.get("id") in voice and voice[m["id"]].get("text") else
                        {**m, "text": VOICE_FAILED, "cached": True}
                        if m.get("id") in voice and voice[m["id"]].get("failed") else m for m in wait]
            digest = unread_digest(wait, len(wait), preview=text, **({"limit": 1200, "authors": True} if whole else {}))
            if digest:
                text = digest
            elif not text:   # текста нет ни в копии, ни в списке чатов: что пришло — словами
                kinds = {}
                for m in wait:
                    kinds[m.get("type") or ""] = kinds.get(m.get("type") or "", 0) + 1
                text = media_summary(kinds or r.get("kinds"), len(wait) or n)
            group = cid.endswith("@g.us")
            t = tier(text)
            if t == "C" or (group and t != "A" and not whole):
                GONE.update(k for k in dead if k in OPEN)
                continue
            last = datetime.fromisoformat(r["last"]) if r.get("last") else now
            digits = re.sub(r"\D", "", cid.split("@")[0])
            boxes.add(box)
            # ключ — последнее ждущее сообщение: то же сообщение второй раз карточкой не станет
            mark = (wait[-1].get("id") if wait else "") or r.get("last")
            # удалено последнее из ждущих, а его пункт открыт — пункт тот же, остальное уходит в него (не новый ключ)
            kept = [x for x, at in gone if f"{box}:{x}" in OPEN and at >= max([m.get("t") or 0 for m in wait] or [0])]
            if kept:
                mark = kept[-1]
            kinds = {m.get("type") for m in wait} | set((r.get("kinds") or {}) if not wait else ())
            # 26.10 (d985909): фото, видео, видео-заметки, документы — из хранилища вкладки, чат не открывается;
            # чего там нет — фото и стикеры, как раньше, из открытого чата
            files, notes, missed = wa_files(cfg, ch, cid, wait)
            pics = wa_media(cfg, ch, cid, f"{box}:{mark}") if (missed & {"image", "sticker"} or (
                not wait and kinds & {"image", "sticker"})) else []
            if pics:
                _WA_OPENED.setdefault(cid, n)   # wamedia открывал чат — счётчик непрочитанных обнулится
            if any(v.get("opened") for v in voice.values()):
                _WA_OPENED.setdefault(cid, n)
            media = files + pics + [v["media"] for v in voice.values() if v.get("media")]
            if (media or notes) and not any(m.get("body") or m.get("text") for m in wait):
                text = ""   # у картинки без подписи заглушек нет — клиент рисует вложение
            elif any(v.get("media") for v in voice.values()) and not digest:
                text = "[голосовое]"
            if notes:   # не скачалось или больше потолка — владелец и разборщик видят почему
                text = "\n".join([text] + notes).strip()
            links = youtube_links(" ".join([text] + [m.get("text") or "" for m in wait]))
            ref = {"wa": ch, "to": cid, "cmd": cmd, "send": expand(cfg.get("send") or "~/.claude/bin/send"),
                   **contact_of(r.get("name"), text, group, wait),
                   **({"title": r["name"]} if r.get("name") and wa_named(cid) else {}),
                   **({"account": cfg["accounts"][ch]} if isinstance(cfg.get("accounts"), dict)
                      and isinstance(cfg["accounts"].get(ch), str) else {}),
                   **({"react": expand(cfg["react"]), "msg": (r.get("messages") or [{}])[-1].get("id")}
                      if cfg.get("react") and (r.get("messages") or [{}])[-1].get("id") else {})}
            context = wa_context(ref, wait, f"{box}:{mark}")
            items.append({"key": f"{box}:{mark}", "box": box, "src": "whatsapp", "tier": t, "unread": n,
                          **({"media": media} if media else {}), **({"context": context} if context else {}),
                          **({"links": links} if links else {}),
                          "where": labels.get(ch, "WhatsApp") + (" · группа" if group else ""),
                          "from": r.get("name") or digits, "text": text[:1200], "at": iso_utc(last),
                          "link": f"https://wa.me/{digits}" if digits and not group and len(digits) <= 15 else "",
                          "mention": False, **({"team": True} if team else {}), **({"revoked": True} if gone else {}),
                          "ref": ref})
    if errors and not ok:
        raise OSError("; ".join(errors))
    return items, boxes, errors


_WA_OPENED = {}   # чат WhatsApp -> сколько ждало, когда мы его открыли сами: обнулённый нами счётчик — не «прочитал владелец»
_WA_READ = {}     # сообщение, ради текста которого чат открывали -> когда: не вышло — снова не раньше WA_READ_AGAIN
WA_READ_AGAIN = 10 * 60
_WA_TEXT = {}     # (чат, сообщение) -> текст, дочитанный из чата: копия треда может отстать от списка чатов
_WA_WHO = {}      # (чат, сообщение) -> автор (группы: кто пишет)
_WA_BLANK = {}    # (чат, сообщение) -> когда: чат прочитан, а реплика пришла без текста — читать её снова бесполезно


_WA_CTX = {}      # ключ поста -> (когда, context): копию треда читаем раз на сообщение; пусто — снова через WA_READ_AGAIN
WA_KINDS = {"voice": "ptt", "image": "image", "video": "video", "document": "document", "sticker": "sticker"}


def wa_context(ref, wait, key):
    """Реплики до ждущих (20.10, d665535, как tg_context): разборщику нужно, на что отвечает собеседник, — обычно это
    ответы владельца, а `wa new` отдаёт только входящие. Берём сохранённую копию треда (`wa thread --cached`: чат не
    открывается, синих галочек нет) и только строки, прошедшие verified_wa_history (source v1, номер аккаунта канала
    из sources.json); без номера аккаунта или с непроверенной копией — пусто. Копия может отставать от чата (его ответ
    с телефона попадёт в неё со следующим чтением чата) — context лишь подсказка разборщику, ни отправка, ни защиты
    (inbox_guard, сверка источника) на него не опираются: они читают историю сами."""
    if not isinstance(ref.get("account"), str):
        return []
    got = _WA_CTX.get(key)
    if got and (got[1] or time.time() - got[0] < WA_READ_AGAIN):
        return got[1]
    who = ref["to"] if ref["to"].endswith("@g.us") else re.sub(r"\D", "", ref["to"].split("@")[0])
    try:
        data = json.loads(run([ref.get("cmd") or expand("~/.claude/bin/wa"), "thread", who, "--cached", "--json",
                               "--limit", "40", "--channel", ref["wa"]], timeout=60) or "{}")
        rows = verified_wa_history(ref, data)
    except (OSError, ValueError, subprocess.SubprocessError):
        rows = []
    ids = [m.get("id") for m in rows]
    first = min([ids.index(m.get("id")) for m in wait if m.get("id") in ids] or [len(rows)])

    def at(m):
        try:
            return iso_utc(datetime.strptime(m.get("when") or "", "%I:%M %p, %m/%d/%Y"))
        except ValueError:
            return ""
    out = fit_context({"at": at(m), "from": "" if m.get("out") else (m.get("author") or ""), "me": bool(m.get("out")),
                       "text": m.get("body"), "kind": WA_KINDS.get(m.get("kind") or "", "")}
                      for m in rows[:first] if m.get("kind") != "system")
    _WA_CTX[key] = (time.time(), out)
    while len(_WA_CTX) > 500:
        _WA_CTX.pop(next(iter(_WA_CTX)))
    return out


def wa_read(cfg, ch, cmd, r, wait, n):
    """Текста сообщения нет в сохранённой копии — читаем чат сами: `wa thread` (открывает чат во вкладке WhatsApp Web,
    синие галочки — слово 14.10: «Чё, я тебе должен чаты, что ли, открывать?»). Один раз на последнее ждущее сообщение;
    не вышло (нет вкладки) — как было, без текста."""
    cid = r.get("chat_id") or ""
    key = f"{ch}:{cid}:{(wait[-1].get('id') if wait else '') or r.get('last')}"
    if time.time() - _WA_READ.get(key, 0) < WA_READ_AGAIN or cfg.get("read") is False:
        return wait
    _WA_READ[key] = time.time()
    who = re.sub(r"\D", "", cid.split("@")[0]) if cid.endswith("@c.us") else (r.get("name") or "")
    try:
        got = json.loads(run([cmd, "thread", who, "--channel", ch, "--json", "--limit", "40"], timeout=120) or "{}")
    except (OSError, ValueError, subprocess.SubprocessError):
        return wait
    _WA_OPENED.setdefault(cid, n)
    body = {m.get("id"): (m.get("body") or "").strip() for m in got.get("messages") or [] if not m.get("out")}
    who = {m.get("id"): (m.get("author") or "").strip() for m in got.get("messages") or [] if m.get("author")}
    for mid, b in body.items():
        if b:
            _WA_TEXT[(cid, mid)] = b
            _WA_BLANK.pop((cid, mid), None)
            if who.get(mid):
                _WA_WHO[(cid, mid)] = who[mid]
        elif not any(m.get("id") == mid and m.get("media") for m in got.get("messages") or []):
            _WA_BLANK[(cid, mid)] = time.time()
    while len(_WA_BLANK) > 2000:
        _WA_BLANK.pop(next(iter(_WA_BLANK)))
    while len(_WA_TEXT) > 2000:
        _WA_WHO.pop(next(iter(_WA_TEXT)), None)
        _WA_TEXT.pop(next(iter(_WA_TEXT)))
    return [{**m, "text": body.get(m.get("id")) or m.get("text") or "", "cached": True,
             **({"from": who[m["id"]]} if who.get(m.get("id")) else {})} if body.get(m.get("id")) else m
            for m in wait]


# --- вложения сообщений (12.10, «фото, видео, файлы, голосовые — как в мессенджере») -----------------------------------
MEDIA_KEEP = 6
_WA_MEDIA = {}   # ключ поста -> вложения: чат ради картинок открываем один раз на сообщение (синие галочки — слово 13.10)   # у скольких последних сообщений с вложениями тянем файл; у остальных — только описание


def _state_dir():
    d = os.environ.get("HUB_STATE_DIR")
    if d:
        return d
    from core.daemon import default_state_dir
    return default_state_dir()


def wa_media(cfg, ch, cid, key):
    """Фото и стикеры WhatsApp: `wamedia` открывает чат (владелец 13.10: «синие галочки допустимы») и снимает blob-картинки
    отрисованной страницы. Видео и голосовые вне прокрутки не отдаются — их тут нет. Нет скрипта/вкладки — без вложений."""
    from urllib.parse import quote
    if cfg.get("media") is False:
        return []
    if key in _WA_MEDIA:
        return _WA_MEDIA[key]
    cmd = expand(cfg.get("media_cmd") or "~/.claude/bin/wamedia")
    got = []
    try:
        rows = json.loads(run([cmd, cid, "--dir", media_dir("wa"), "--channel", ch], timeout=120) or "[]")
        for m in rows:
            got.append({"id": f"wa:{cid}:{m['id']}", "kind": m.get("kind") or "image", "name": os.path.basename(m["path"]),
                        "mime": m.get("mime"), "w": m.get("w"), "h": m.get("h"),
                        "url": "/api/file?path=" + quote(m["path"], safe="")})
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        got = []
    _WA_MEDIA[key] = got
    return got


WA_FILE_TYPES = {"image", "sticker", "video", "ptv", "gif", "document"}
MEDIA_MAX_MB = 50   # больше — не качаем: вложение без url и строка-причина
_WA_FILES = {}   # (чат, id сообщения) -> {"media": вложение} | {"big": вложение без url}: второй раз не качаем
_WA_FILE_TRIES = {}   # (чат, id сообщения) -> (сколько раз не скачалось, когда последний раз, почему)
WA_KIND_WORD = {"image": "фото", "sticker": "стикер", "video": "видео", "ptv": "видеосообщение", "gif": "GIF",
                "document": "файл"}


def wa_files(cfg, ch, cid, wait, keep=MEDIA_KEEP):
    """Вложения WhatsApp среди ждущих (26.10, d985909): `wamedia --store --only` берёт фото, стикеры, видео,
    видео-заметки (ptv), гифки и документы из хранилища вкладки и CDN WhatsApp — чат не открывается, синих галочек нет.
    Файл — в attachments хаба; у видео кадр-превью (thumb) и длительность (dur, секунды, ffprobe). Больше потолка
    (`media_max_mb`, по умолчанию 50 МБ) — вложение без url и строка-причина. Не скачалось — строка-причина, повтор
    на следующих тактах до WA_VOICE_TRIES раз. -> (media, notes, типы, которых в хранилище не нашлось)."""
    msgs = [m for m in wait if m.get("id") and m.get("type") in WA_FILE_TYPES][-keep:]
    if not msgs or cfg.get("media") is False:
        return [], [], set()
    now = time.time()
    want = [m["id"] for m in msgs if (cid, m["id"]) not in _WA_FILES
            and _WA_FILE_TRIES.get((cid, m["id"]), (0, 0, ""))[0] < WA_VOICE_TRIES
            and now - _WA_FILE_TRIES.get((cid, m["id"]), (0, 0, ""))[1] >= WA_VOICE_AGAIN]
    if want:
        cap = cfg.get("media_max_mb") or MEDIA_MAX_MB
        cmd = expand(cfg.get("media_cmd") or "~/.claude/bin/wamedia")
        why = {}
        try:
            rows = json.loads(run([cmd, cid, "--dir", media_dir("wa"), "--channel", ch, "--store", "--only", ",".join(want),
                                   "--max-mb", f"{cap:g}"], timeout=300) or "[]")
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            rows, why = [], {i: str(e) for i in want}
        for m in rows if isinstance(rows, list) else []:
            if not isinstance(m, dict) or m.get("id") not in want:
                continue
            if m.get("error") and (m.get("size") or 0) > cap * 1e6:
                _WA_FILES[(cid, m["id"])] = {"big": _wa_file_item(cid, m, None), "type": m.get("type") or m.get("kind")}
            elif m.get("error") or not m.get("path"):
                why[m["id"]] = m.get("error") or "wamedia не вернул файл"
            else:
                _WA_FILES[(cid, m["id"])] = {"media": _wa_file_item(cid, m, m["path"])}
        for i in want:
            if (cid, i) not in _WA_FILES:
                n = _WA_FILE_TRIES.get((cid, i), (0, 0, ""))[0] + 1
                _WA_FILE_TRIES[(cid, i)] = (n, now, why.get(i) or "wamedia его не вернул")
                print(f"whatsapp: вложение {cid} {i} не скачалось (попытка {n} из {WA_VOICE_TRIES}): "
                      f"{_WA_FILE_TRIES[(cid, i)][2]}", file=sys.stderr, flush=True)
        while len(_WA_FILES) > 500:
            _WA_FILES.pop(next(iter(_WA_FILES)))
        while len(_WA_FILE_TRIES) > 500:
            _WA_FILE_TRIES.pop(next(iter(_WA_FILE_TRIES)))
    media, notes, missed = [], [], set()
    for m in msgs:
        got = _WA_FILES.get((cid, m["id"])) or {}
        word = WA_KIND_WORD.get(m["type"], "файл")
        if got.get("media"):
            media.append(got["media"])
        elif got.get("big"):
            media.append(got["big"])
            cap = cfg.get("media_max_mb") or MEDIA_MAX_MB
            notes.append(f"📎 {word} {got['big'].get('size', 0) / 1e6:.0f} МБ — больше {cap:g} МБ, не скачано")
        else:
            missed.add(m["type"])
            if m["type"] not in ("image", "sticker"):   # фото и стикеры ещё попробуем из открытого чата
                notes.append(f"📎 {word} — не скачалось: {_WA_FILE_TRIES.get((cid, m['id']), (0, 0, 'нет файла'))[2]}")
    return media, notes, missed


def _wa_file_item(cid, m, path):
    """Строка wamedia --store -> вложение поста: {id, kind, name, mime, size, w, h, dur, url, thumb}. path None —
    файл не качали (больше потолка): без url, только описание."""
    from urllib.parse import quote
    kind = {"doc": "file", "voice": "voice"}.get(m.get("kind"), m.get("kind") or "file")
    item = {"id": f"wa:{cid}:{m['id']}", "kind": kind,
            "name": m.get("name") or (os.path.basename(path) if path else ""), "mime": m.get("mime") or ""}
    if path:
        item["url"] = "/api/file?path=" + quote(path, safe="")
        try:
            item["size"] = os.path.getsize(path)
        except OSError:
            pass
    elif m.get("size"):
        item["size"] = m["size"]
    if m.get("w") and m.get("h"):
        item["w"], item["h"] = m["w"], m["h"]
    dur = _duration(path) if path and kind in ("video", "voice", "audio") else 0
    dur = dur or (m.get("dur") if isinstance(m.get("dur"), (int, float)) else 0)
    if dur:
        item["dur"] = dur
    if path and kind == "video":
        poster = _poster(path, dur)
        if poster:
            item["thumb"] = "/api/file?path=" + quote(poster, safe="")
    return item


def _clock(v):
    """«1:05», «32» или число -> секунды числом; не разобрать — 0."""
    if isinstance(v, (int, float)):
        return v
    parts = str(v or "").strip().split(":")
    try:
        return sum(int(x) * 60 ** k for k, x in enumerate(reversed(parts))) if all(parts) else 0
    except ValueError:
        return 0


def _duration(path):
    """Длительность файла в секундах (ffprobe), с точностью до десятых; нет ffprobe или не вышло — 0."""
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True, timeout=30)
        return round(float(out.stdout.strip()), 1)
    except (OSError, ValueError, subprocess.SubprocessError):
        return 0


def _poster(path, dur=0):
    """Кадр-превью видео рядом с файлом (`<имя>-poster.jpg`, кадр на 1-й секунде, у коротких — первый): клиенты
    показывают его до загрузки видео. Нет ffmpeg или не вышло — None."""
    out = os.path.splitext(path)[0] + "-poster.jpg"
    if os.path.exists(out) and os.path.getsize(out):
        return out
    try:
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-ss", "1" if not dur or dur > 1.5 else "0",
                        "-i", path, "-frames:v", "1", "-vf", "scale='min(640,iw)':-2", "-q:v", "4", out],
                       timeout=60, check=True, capture_output=True)
    except (OSError, subprocess.SubprocessError):
        return None
    return out if os.path.exists(out) and os.path.getsize(out) else None


# --- ссылки YouTube (26.10, d985909): название и обложка из oEmbed (без ключа), обложка — в attachments хаба --------
YOUTUBE = re.compile(r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com/(?:watch\?(?:[^\s<>\"']*?&)?v=|shorts/|live/|embed/)"
                     r"|youtu\.be/)([A-Za-z0-9_-]{11})[^\s<>\"')\]]*")
_YT = {}   # id видео -> (когда, {title, image} | None): oEmbed спрашиваем раз; не вышло — снова через WA_READ_AGAIN


def youtube_links(text, keep=3):
    """Ссылки YouTube в тексте -> [{url, title, site: "YouTube", image}] (поля превью ссылки, как у почты и Telegram:
    клиенты рисуют карточку сами, не ходя на YouTube). Видео без названия (удалено, приватное, нет сети) — без карточки."""
    from urllib.parse import quote
    out, ids = [], set()
    for m in YOUTUBE.finditer(text or ""):
        vid, url = m.group(1), m.group(0).rstrip(".,;:!?")
        if vid in ids or len(out) >= keep:
            continue
        ids.add(vid)
        got = _YT.get(vid)
        if not got or (got[1] is None and time.time() - got[0] >= WA_READ_AGAIN):
            info = None
            try:
                data = json.loads(run(["curl", "-4", "-sS", "--fail", "--max-time", "10",
                                       "https://www.youtube.com/oembed?format=json&url="
                                       + quote(f"https://www.youtube.com/watch?v={vid}", safe="")], timeout=15) or "{}")
                if isinstance(data, dict) and str(data.get("title") or "").strip():
                    info = {"title": str(data["title"]).strip()[:200]}
                    thumb = data.get("thumbnail_url") or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
                    path = os.path.join(media_dir("links"), f"youtube-{vid}.jpg")
                    if not os.path.exists(path) and str(thumb).startswith("https://"):
                        try:
                            run(["curl", "-4", "-sS", "--fail", "--max-time", "15", "-o", path, thumb], timeout=20)
                        except (OSError, subprocess.SubprocessError):
                            pass
                    if os.path.exists(path) and os.path.getsize(path):
                        info["image"] = "/api/file?path=" + quote(path, safe="")
            except (OSError, ValueError, subprocess.SubprocessError):
                info = None
            got = _YT[vid] = (time.time(), info)
            while len(_YT) > 500:
                _YT.pop(next(iter(_YT)))
        if got[1]:
            out.append({"url": url, "site": "YouTube", **got[1]})
    return out


_WA_VOICE = {}   # (чат, id сообщения) -> {text, media, opened}: скачанное голосовое второй раз не качаем
_WA_VOICE_TRIES = {}   # (чат, id сообщения) -> (сколько раз не скачалось, когда последний раз)
WA_VOICE_TRIES = 3   # 24.10 (d841958): не скачалось — пробуем на следующих тактах, всего до трёх раз
WA_VOICE_AGAIN = 2 * 60
VOICE_FAILED = "голосовое не скачалось"


def wa_voice(cfg, ch, cid, key, wait):
    """Голосовые WhatsApp среди ждущих: `wamedia --voice --only` берёт файл из хранилища вкладки (ключ и путь файла
    там открыты, чат не открывается; 24.10, d841958: чаты бизнеса «secure service from Meta» и не отрисованные фоновой
    вкладкой голосовые меню «Download» не отдавали), иначе через меню «Download» открытого чата (владелец 13.10: синие
    галочки для медиа допустимы); расшифровка — `--transcribe` (fal wizper, язык `voice_lang`, по умолчанию es), рядом
    `.txt`. {id: {text, media, opened}} — скачанное; {id: {failed: True}} — не скачалось (причина в логе, повтор на
    следующих тактах до WA_VOICE_TRIES раз). Голос выключен или голосовых нет — пусто."""
    from urllib.parse import quote
    ids = [m["id"] for m in wait if m.get("id") and m.get("type") in ("ptt", "audio")]
    if not ids or cfg.get("media") is False or cfg.get("voice") is False:
        return {}
    now = time.time()
    want = [i for i in ids if (cid, i) not in _WA_VOICE
            and _WA_VOICE_TRIES.get((cid, i), (0, 0))[0] < WA_VOICE_TRIES
            and now - _WA_VOICE_TRIES.get((cid, i), (0, 0))[1] >= WA_VOICE_AGAIN]
    why = {}
    if want:
        cmd = expand(cfg.get("media_cmd") or "~/.claude/bin/wamedia")
        try:
            rows = json.loads(run([cmd, cid, "--dir", media_dir("wa"), "--channel", ch, "--voice", "--only", ",".join(want),
                                   "--transcribe", "--lang", cfg.get("voice_lang") or "es"], timeout=240) or "[]")
        except (OSError, ValueError, subprocess.SubprocessError) as e:
            rows, why = [], {i: str(e) for i in want}
        for m in rows:
            try:
                if m.get("error"):
                    why[m["id"]] = m["error"]
                    continue
                path = m["path"]
                play = _playable(path)
                item = {"id": f"wa:{cid}:{m['id']}", "kind": "voice", "name": os.path.basename(play),
                        "mime": m.get("mime"), "url": "/api/file?path=" + quote(play, safe="")}
                if play != path:
                    item["mime"] = "audio/mp4"
                dur = _clock(m.get("dur"))   # 26.10: секунды числом — клиенты читают dur как число («0:32» не видели)
                if dur:
                    item["dur"] = dur
                text = (m.get("transcript") or "").strip() or _transcript(path).strip()
                _WA_VOICE[(cid, m["id"])] = {"text": text, "media": item, "opened": m.get("via") not in ("store", "disk")}
            except (KeyError, TypeError, OSError):
                continue
        for i in want:
            if (cid, i) not in _WA_VOICE:
                n = _WA_VOICE_TRIES.get((cid, i), (0, 0))[0] + 1
                _WA_VOICE_TRIES[(cid, i)] = (n, now)
                print(f"whatsapp: голосовое {cid} {i} не скачалось (попытка {n} из {WA_VOICE_TRIES}): "
                      f"{why.get(i) or 'wamedia его не вернул'}", file=sys.stderr, flush=True)
        while len(_WA_VOICE) > 500:
            _WA_VOICE.pop(next(iter(_WA_VOICE)))
        while len(_WA_VOICE_TRIES) > 500:
            _WA_VOICE_TRIES.pop(next(iter(_WA_VOICE_TRIES)))
    out = {i: _WA_VOICE.get((cid, i)) or {"failed": True} for i in ids}
    if any(v.get("opened") for v in out.values()):
        _WA_OPENED.setdefault(cid, len(ids))   # wamedia открывал чат — счётчик непрочитанных обнулится
    return out


def media_dir(src):
    """Куда класть: под attachments хаба — страница и клиенты отдают такие файлы сами (/api/file), чужие пути — нет."""
    d = os.path.join(_state_dir(), "attachments", "inbox", src)
    os.makedirs(d, exist_ok=True)
    return d


def _playable(path):
    """Голосовые Telegram приходят в ogg/opus — системный плеер iOS/macOS его не играет. Рядом кладём m4a (AAC),
    клиентам отдаём его; нет ffmpeg или не вышло — как есть."""
    if not path.lower().endswith((".ogg", ".oga", ".opus")):
        return path
    out = os.path.splitext(path)[0] + ".m4a"
    if os.path.exists(out):
        return out
    try:
        subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-i", path, "-vn", "-c:a", "aac", "-b:a", "48k", out],
                       timeout=60, check=True, capture_output=True)
    except (OSError, subprocess.SubprocessError):
        return path
    return out


def _transcript(path):
    """Расшифровка голосового сразу (Whisper / ChatGPT по настройкам хаба); рядом `.txt` — второй раз не гоняем.
    Пусто — голос не настроен или не вышло: клиент покажет один плеер."""
    side = path + ".txt"
    try:
        with open(side, encoding="utf-8") as f:
            return f.read()
    except OSError:
        pass
    try:
        from core import catalog
        from modules.voice import transcribe
        cfg = catalog.load_config(_state_dir())
        if not transcribe.enabled(cfg):
            return ""
        with open(path, "rb") as f:
            text = transcribe.transcribe(f.read(), cfg, suffix=os.path.splitext(path)[1] or ".ogg")
    except Exception as e:   # нет голоса, нет ffmpeg, лимит — расшифровки нет, переписка живёт
        print(f"teams: расшифровка {os.path.basename(path)}: {e}", flush=True)
        return ""
    with open(side, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def tg_media(cmd, chat, msgs, keep=MEDIA_KEEP):
    """Вложения сообщений Telegram → список для клиентов: {id, kind, name, mime, size, dur, w, h, url, thumb, text}.
    Файл — в attachments хаба (`url` — /api/file); тяжёлый (>40 МБ) — миниатюра с thumb:true; не скачался — без url."""
    from urllib.parse import quote
    out, d = [], None
    with_media = [m for m in msgs if m.get("media")]
    for m in with_media[-keep:]:
        meta = dict(m["media"])
        item = {"id": f"tg:{chat}:{m.get('id')}", **meta}
        d = d or media_dir("tg")
        base = f"{abs(int(chat)) if str(chat).lstrip('-').isdigit() else chat}-{m.get('id')}"
        have = next((f for f in os.listdir(d) if f.startswith(base + ".") or f.startswith(base + "-thumb.")), None)
        if have is None:
            try:
                got = json.loads(run([cmd, "media", str(chat), str(m["id"]), "--dir", d], timeout=120) or "{}")
                have = os.path.basename(got.get("path") or "") or None
            except (OSError, ValueError, subprocess.TimeoutExpired):
                have = None
        if have:
            path = os.path.join(d, have)
            item["url"] = "/api/file?path=" + quote(path, safe="")
            item["thumb"] = "-thumb." in have
            if meta.get("kind") in ("voice", "audio") and not item["thumb"]:
                t = _transcript(path)
                if t:
                    item["text"] = t
                play = _playable(path)
                if play != path:
                    item["url"] = "/api/file?path=" + quote(play, safe="")
                    item["mime"] = "audio/mp4"
        out.append(item)
    return out


def tg_reply_text(m, by_id):
    """Цитата в ответе: текст и автор сообщения, на которое отвечают (если оно в окне)."""
    r = m.get("reply") or {}
    src = by_id.get(str(r.get("id")))
    if not src:
        return r or None
    return {"id": r.get("id"), "from": src.get("from") or ("вы" if src.get("out") else ""),
            "text": (src.get("text") or "")[:160]}


CONTEXT_MAX = 700   # знаков JSON на предыдущие реплики в посте msg: текст сообщения важнее, пост — до 2000


def tg_context(r, wait):
    """Реплики до ждущих (20.10, d664989): разборщику нужно, на что отвечает собеседник, а ветка kind:thread выходит
    только по просьбе владельца. `tgnew new` и так отдаёт пару сообщений перед непрочитанным — обычно его ответы;
    раньше они отбрасывались. [{at, from, me, text}] по порядку, новые важнее: не влезло — без старых."""
    msgs = [m for m in r.get("messages") or [] if m.get("type") not in SERVICE_TYPES]
    ids = [m.get("id") for m in msgs]
    first = ids.index(wait[0].get("id")) if wait and wait[0].get("id") in ids else len(msgs)
    return fit_context({"at": iso_utc(datetime.fromtimestamp(m["t"], timezone.utc)) if m.get("t") else "",
                        "from": "" if m.get("out") else (m.get("from") or ""), "me": bool(m.get("out")),
                        "text": m.get("text"), "kind": m.get("type")} for m in msgs[:first])


def fit_context(rows):
    """Реплики по порядку -> context поста: текст в одну строку до 240 знаков, медиа без подписи — словом, пустые
    пропускаются; всего до CONTEXT_MAX знаков JSON, новые важнее — не влезло, без старых."""
    out, size = [], 0
    for m in reversed(list(rows)):
        text = " ".join((m.get("text") or "").split())[:240]
        if not text:
            one = KIND_NAMES.get(m.get("kind") or "", ("", ""))[0]
            text = f"[{one}]" if one and one != "текст" else ""
        if not text:
            continue
        e = {"at": m.get("at") or "", "from": m.get("from") or "", "me": bool(m.get("me")), "text": text}
        size += len(json.dumps(e, ensure_ascii=False)) + 2
        if size > CONTEXT_MAX:
            break
        out.append(e)
    return out[::-1]


# --- Telegram: личный аккаунт, только чтение (`tgnew new` — копия сессии Telethon, прочитанным ничего не отмечает) --
@source("telegram", every=120)
def telegram(cfg, now):
    """Чаты с непрочитанным входящим за сутки; та же логика, что у WhatsApp. Группы — только срочное (рабочие и при
    all_groups все, кроме skip_groups, — целиком); заглушённые,
    каналы-рассылки и боты командой не отдаются. Ответ — `send tg` (ночной запрет и выходные действуют там)."""
    cmd = expand(cfg.get("cmd") or "~/.claude/bin/tgnew")
    try:
        rows = json.loads(run([cmd, "new", "--hours", "24", "--json"]) or "[]")
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        raise OSError(f"Telegram: {e}")
    items, boxes = [], set()
    for r in rows:
        cid, n = r.get("chat_id") or "", r.get("unread") or 0
        team = work_group(cfg, cid, r.get("name"), r.get("group"))
        whole = whole_group(cfg, cid, r.get("name"), r.get("group"))
        if whole:
            n = max(n, team_wait(r))
        if not cid or not n:
            continue
        wait = waiting({**r, "unread": n})
        if r.get("messages") and not wait:
            continue
        text = unread_digest(wait, len(wait), preview=r.get("preview") or "",
                             **({"limit": 1200, "authors": True} if whole else {}))
        if not text:
            kinds = {}
            for m in wait:
                kinds[m.get("type") or ""] = kinds.get(m.get("type") or "", 0) + 1
            text = (r.get("preview") or "").strip() or media_summary(kinds, len(wait) or n)
        group = bool(r.get("group"))
        if group and wait and not whole:   # в группе — кто написал (у рабочей — у каждой реплики)
            last = wait[-1]
            if last.get("from"):
                text = f"{last['from']}: {text}" if " · " not in text else text
        t = tier(text)
        if t == "C" or (group and t != "A" and not whole):
            continue
        at = datetime.fromisoformat(r["last"]) if r.get("last") else now
        box = f"tg:{cid}"
        boxes.add(box)
        mark = (wait[-1].get("id") if wait else "") or r.get("last")
        user = r.get("username") or ""
        media = tg_media(cmd, cid, wait)
        if media and not any((m.get("text") or "").strip() for m in wait):
            text = ""   # 12.10: у медиа без подписи заглушки («[фото]», «1 сообщение без текста») не кладём — клиент рисует само вложение
        links = [m["link"] for m in wait if m.get("link")][-3:] \
            or youtube_links(" ".join(m.get("text") or "" for m in wait))   # превью Telegram нет — YouTube сами
        context = tg_context(r, wait)
        items.append({"key": f"{box}:{mark}", "box": box, "src": "telegram", "tier": t, "unread": n,
                      **({"context": context} if context else {}),
                      "where": "Telegram" + (" · группа" if group else ""), "from": r.get("name") or cid,
                      "text": text[:1200], "at": iso_utc(at), "mention": False, **({"team": True} if team else {}),
                      **({"media": media} if media else {}), **({"links": links} if links else {}),
                      "link": f"https://t.me/{user}" if user else (f"tg://user?id={cid}" if not group else ""),
                      "ref": {"tg": cid, "cmd": cmd, "send": expand(cfg.get("send") or "~/.claude/bin/send"),
                              **contact_of(r.get("name"), text, group, wait)}})
    tg_gone(cmd, boxes)
    return items, boxes, []


_TG_GONE = {}   # ключ открытого пункта -> когда проверяли, не удалено ли его сообщение


def tg_gone(cmd, boxes):
    """26.10 (d987429): собеседник удалил ждущее сообщение — в Telegram оно пропадает целиком, непрочитанное снимается,
    и чат уходит из `tgnew new`; пункт висел бы, пока владелец не ответит. Открытый пункт, чей чат больше не ждёт:
    его сообщения нет (`tgnew gone`) и после ответа владельца не осталось ни одного входящего — пункт в GONE. Осталось
    что-то — пункт не трогаем. Раз в WA_READ_AGAIN на пункт: каждый вызов — вход в Telegram."""
    for k, (box, _at) in list(OPEN.items()):
        if not str(box).startswith("tg:") or box in boxes or not k.startswith(box + ":"):
            continue
        mark = k[len(box) + 1:]
        if not mark.isdigit() or time.time() - _TG_GONE.get(k, 0) < WA_READ_AGAIN:
            continue
        _TG_GONE[k] = time.time()
        try:
            got = json.loads(run([cmd, "gone", box[3:], mark], timeout=60) or "{}")
        except (OSError, ValueError, subprocess.SubprocessError):
            continue
        if mark in (got.get("missing") or []) and not got.get("waiting"):
            GONE.add(k)
    for k in [k for k in _TG_GONE if k not in OPEN]:
        del _TG_GONE[k]


# --- тело письма (12.10: «показана только тема — нет тела письма»), без цитат предыдущих писем --------------------
_QUOTE = re.compile(r"(?im)^(?:>.*|(?:on|el|em|am|le) .{3,200}(?:wrote|escribi[oó]|escreveu|schrieb|a [eé]crit).{0,60}:?\s*|"
                    r".{0,160}(?:написал[аи]?|писал[аи]?):\s*|"
                    r"-{2,}\s*(?:original|forwarded|mensaje reenviado|пересланное).*|_{5,}\s*)$")
_BODIES = {}


def _decode(data):
    import base64
    try:
        return base64.urlsafe_b64decode(str(data) + "=" * (-len(str(data)) % 4)).decode("utf-8", "replace")
    except (ValueError, TypeError):
        return ""


def message_text(payload):
    """Текст письма из payload Gmail: text/plain, иначе text/html без разметки; цитаты и подписи-хвосты обрезаны."""
    plain, html_ = [], []

    def walk(p):
        mt = (p.get("mimeType") or "").lower()
        data = (p.get("body") or {}).get("data")
        if data and mt == "text/plain":
            plain.append(_decode(data))
        elif data and mt == "text/html":
            html_.append(_decode(data))
        for c in p.get("parts") or []:
            walk(c)
    walk(payload or {})
    text = "\n".join(plain)
    if not text.strip() and html_:
        import html as H
        h = re.sub(r"(?is)<(script|style).*?</\1>", " ", "\n".join(html_))
        h = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</li>", "\n", h)
        text = H.unescape(re.sub(r"<[^>]+>", " ", h))
    lines = []
    for ln in text.replace("\r", "").split("\n"):
        if _QUOTE.match(ln.strip()):
            if ln.strip().startswith(">"):
                continue
            if re.match(r"(?i)(?:-{2,}\s*(?:forwarded|mensaje reenviado|пересланное|original)|_{5,})", ln.strip()) \
                    and len(re.sub(r"(?i)obtener outlook.*|sent from.*|enviado desde.*", "", " ".join(lines)).strip()) < 40:
                continue   # «Fw:» без своих слов — само пересланное и есть содержание письма
            break   # «El … escribió:» — дальше только цитата
        lines.append(" ".join(ln.split()))
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return out


def mail_thread(cmd, acct, thread_id, count):
    """Письма цепочки [{from, at, me, text}] с телом; кеш на (цепочка, число писем)."""
    key = (acct, thread_id, count)
    if key in _BODIES:
        return _BODIES[key]
    data = json.loads(run([cmd, "gmail", "thread", "get", thread_id, "-a", acct, "-j"]))
    out = []
    for m in (data.get("thread") or {}).get("messages") or []:
        heads = {h.get("name", "").lower(): h.get("value", "") for h in (m.get("payload") or {}).get("headers") or []}
        try:
            at = iso_utc(datetime.fromtimestamp(int(m.get("internalDate") or 0) / 1000, timezone.utc))
        except (ValueError, OSError):
            at = ""
        out.append({"at": at, "from": re.sub(r"\s*<[^>]*>\s*$", "", heads.get("from", "")).strip().strip('"'),
                    "me": "SENT" in (m.get("labelIds") or []), "text": message_text(m.get("payload")) or (m.get("snippet") or "").strip(),
                    "subject": heads.get("subject", ""), "id": m.get("id"), "files": mail_files(m.get("payload"))})
    if len(_BODIES) > 200:
        _BODIES.clear()
    _BODIES[key] = out
    return out


def mail_files(payload):
    """Вложения письма [{name, mime, size, att}]: файлы и картинки в теле; мелкие картинки-подписи (логотипы,
    трекеры — inline до 30 КБ) не считаем."""
    out = []

    def walk(p):
        body = p.get("body") or {}
        name, att = p.get("filename") or "", body.get("attachmentId")
        if att and (name or (p.get("mimeType") or "").startswith("image/")):
            heads = {h.get("name", "").lower(): h.get("value", "") for h in p.get("headers") or []}
            size = int(body.get("size") or 0)
            if not (heads.get("content-id") and size < 30000 and (p.get("mimeType") or "").startswith("image/")):
                out.append({"name": name or f"image-{abs(hash(att)) % 10**6}", "mime": p.get("mimeType") or "", "size": size, "att": att})
        for c in p.get("parts") or []:
            walk(c)
    walk(payload or {})
    return out


def mail_media(cmd, acct, msg, keep=MEDIA_KEEP, limit=40 << 20):
    """Вложения письма — файлами в attachments хаба (`url` — /api/file), как у Telegram; тяжёлое и лишнее — без файла."""
    from urllib.parse import quote
    d = media_dir("mail")
    out = []
    for f in (msg.get("files") or [])[:keep]:
        name = re.sub(r"[^\w.\- ]+", "_", f["name"])[:80] or "file"
        path = os.path.join(d, f"{msg['id']}-{name}")
        item = {"id": f"mail:{msg['id']}:{__import__('hashlib').md5(f['att'].encode()).hexdigest()[:10]}", "kind": ("image" if f["mime"].startswith("image/") else
                "video" if f["mime"].startswith("video/") else "audio" if f["mime"].startswith("audio/") else "file"),
                "name": f["name"], "mime": f["mime"], "size": f["size"]}
        if f["size"] <= limit:
            if not os.path.exists(path):
                try:
                    run([cmd, "gmail", "attachment", msg["id"], f["att"], "-a", acct, "--out", path], timeout=120)
                except (OSError, subprocess.SubprocessError):
                    pass
            if os.path.exists(path) and os.path.getsize(path):
                item["url"] = "/api/file?path=" + quote(path, safe="")
        out.append(item)
    return out


URL = re.compile(r"https?://[^\s<>\"')\]]+")


# --- Почта: Gmail через gogx — непрочитанные входящие вне рассылок; тема и отправитель ----------------------------
@source("email", every=120)
def email(cfg, now):
    cmd = expand(cfg.get("cmd") or "~/.claude/bin/gogx")
    query = cfg.get("query") or ("is:unread in:inbox newer_than:7d -category:promotions -category:social "
                                 "-category:forums")
    items, boxes, errors, ok, fetched = [], set(), [], 0, 0
    for acct in cfg.get("accounts") or []:
        try:
            data = json.loads(run([cmd, "gmail", "search", query, "--max", "40", "-a", acct, "-j"]))
        except (OSError, ValueError, subprocess.TimeoutExpired) as e:
            errors.append(f"{acct}: {e}")
            continue
        ok += 1
        for th in data.get("threads") or []:
            labels = th.get("labels") or []
            if "SENT" in labels and "UNREAD" not in labels:
                continue
            sender, subject = th.get("from") or "", (th.get("subject") or "").strip()
            addr = re.search(r"<([^>]+)>", sender)
            t = tier(subject, automated=bool(AUTOMATED.search(addr.group(1) if addr else sender)),
                     updates="CATEGORY_UPDATES" in labels)
            if t == "C" or not subject and not sender:
                continue
            try:
                at = iso_utc(datetime.strptime(th["date"], "%Y-%m-%d %H:%M"))
            except (KeyError, ValueError):
                at = iso_utc(now)
            box = f"mail:{acct}:{th['id']}"
            boxes.add(box)
            name = re.sub(r"\s*<[^>]*>\s*$", "", sender).strip().strip('"') or (addr.group(1) if addr else "")
            body, media = "", []
            if fetched < 15:   # тело нового письма — не только тема (владелец 12.10); цепочки без нового кешируются
                fetched += 1
                try:
                    msgs = [m for m in mail_thread(cmd, acct, th["id"], th.get("messageCount")) if not m["me"]]
                    body = (msgs[-1]["text"] if msgs else "")[:1000]
                    if msgs and msgs[-1].get("files"):
                        media = mail_media(cmd, acct, msgs[-1])
                except (OSError, ValueError, subprocess.TimeoutExpired):
                    body = ""
            links = [{"url": u.rstrip(".,;")} for u in dict.fromkeys(URL.findall(body))
                     if not re.search(r"(?i)\.(png|gif|jpe?g)(\?|$)|gstatic\.com|aka\.ms/", u)][:3]
            items.append({"key": f"{box}:{th.get('date')}:{th.get('messageCount')}", "box": box, "src": "email",
                          "tier": t, "unread": "UNREAD" in labels, "where": "Почта" + (f" · {acct}" if len(cfg.get("accounts") or []) > 1 else ""),
                          "from": name or "—", "text": (subject or "(без темы)") + (f"\n\n{body}" if body else ""),
                          "at": at, **({"links": links} if links else {}), **({"media": media} if media else {}),
                          "link": f"https://mail.google.com/mail/u/0/?authuser={acct}#inbox/{th['id']}", "mention": False,
                          "contact": f"mail:{(addr.group(1) if addr else sender).lower()}",
                          "ref": {"mail": acct, "thread": th["id"], "subject": subject, "cmd": cmd}})
    if errors and not ok:
        raise OSError("; ".join(errors))
    return items, boxes, errors


# --- Ответ владельца из вкладки в WhatsApp и почту: теми же командами машины, что читают -----------------------------
# Отказы команды send — человеческим текстом, не именами переменных (владелец 12.10: «показывать ошибку понятно»)
HUMAN = [
    (re.compile(r"TELEGRAM_API_(ID|HASH)|api_id|api_hash", re.I), "Telegram не подключён на этом компьютере (нет ключей входа) — отправить не вышло"),
    (re.compile(r"Telethon session|session not found|not authorized|AuthKey", re.I), "Telegram не авторизован на этом компьютере — отправить не вышло"),
    (re.compile(r"between 2[23]:00 and 08:00|quiet hours|night", re.I), "С 23:00 до 08:00 по Аргентине WhatsApp и Telegram не отправляются — повтори после 08:00"),
    (re.compile(r"weekend|Saturday|Sunday|held", re.I), "В выходные это сообщение не отправляется — повтори в понедельник"),
    (re.compile(r"FloodWait|flood", re.I), "Telegram просит подождать — повтори через несколько минут"),
    (re.compile(r"timed? ?out|timeout", re.I), "Не дождались ответа от сервиса — повтори"),
]


def human(message):
    msg = str(message or "")
    for rx, text in HUMAN:
        if rx.search(msg):
            return text
    return re.sub(r"^(?:send failed|Blocked|Not sent):\s*", "", msg).strip() or "не отправлено"


class NotSent(OSError):
    """Команда отправки отказала до транспорта — доказанно ничего не ушло (группа без названия, чат не открылся,
    текст не совпал). Не «итог неизвестен»: main отвечает send_blocked, разбор кладёт черновик с причиной."""


def wa_named(chat_id):
    """Группа или @lid: send wa открывает их только по названию в списке чатов (по номеру — нельзя)."""
    return str(chat_id or "").strip().endswith(("@g.us", "@lid"))


def wa_title(ref):
    """Название чата в списке WhatsApp Web — для группы и @lid: send wa открывает их только по нему (--title).
    Адрес пункта, опубликованного до 21.10, названия не несёт — берём из списка чатов (`wa chats`, без открытия
    чата). Не нашлось однозначно — NotSent: отправлять некуда, ничего не ушло."""
    to = ref.get("to") or ""
    if not wa_named(to):
        return ""
    if ref.get("title"):
        return ref["title"]
    digits = re.sub(r"\D", "", to.split("@")[0])
    try:
        rows = json.loads(run([ref.get("cmd") or expand("~/.claude/bin/wa"), "chats", digits, "--json",
                               "--channel", ref["wa"]], timeout=60) or "[]")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        rows = []
    rows = [x for x in rows if isinstance(x, dict) and x.get("name")]
    exact = [x for x in rows if x.get("chat_id") == to]
    names = {x["name"] for x in (exact or (rows if to.endswith("@lid") else []))}
    if len(names) != 1:
        raise NotSent("Не нашёл этот чат WhatsApp в списке чатов по названию — ничего не отправлено")
    return names.pop()


def wa_send(cmd, files):
    """send wa: отказ команды до отправки (send failed: WhatsApp Web: … без «reconcile before retry» — драйвер
    не нажал «отправить») — NotSent; итог неизвестен (пометка reconcile, сбой процесса, таймаут) — OSError как был.
    Несколько файлов: первый мог уйти, отказ — о следующем, итог неизвестен."""
    try:
        return run(cmd, timeout=180)
    except OSError as e:
        line = getattr(e, "full", "") or str(e)
        if len(files) <= 1 and re.match(r"send failed: WhatsApp Web: ", line) and not re.search(r"(?i)reconcile", line):
            raise NotSent(str(e)) from None
        raise


class Held(OSError):
    """Команда отправки отказала, ничего не отправив: ночь или выходной. Не ошибка — плагин перенесёт (main.hold)."""

    def __init__(self, why, text):
        super().__init__(text)
        self.why = why


def held(message):
    """Отказ гейта команды send → «night» / «weekend»; любая другая ошибка → None."""
    msg = str(message or "")
    if HUMAN[2][0].search(msg):
        return "night"
    return "weekend" if HUMAN[3][0].search(msg) else None


def reply(ref, text, files=None, reply_to=None, quote=None):
    try:
        return _reply(ref, text, files or [], reply_to, quote)
    except NotSent as e:
        raise NotSent(human(e)) from None
    except OSError as e:
        why = held(e)
        if why:
            raise Held(why, human(e)) from None
        raise OSError(human(e)) from None


def _reply(ref, text, files=(), reply_to=None, quote=None):
    """WhatsApp — сообщением в тот же чат (команда send из sources.json: её ночные и прочие запреты действуют — отказ
    вернётся ошибкой во вкладку); почта — ответом всем в ту же цепочку; файлы — вложениями (--file). Ответ на
    конкретное сообщение: Telegram — настоящим ответом (--reply-to), WhatsApp — цитатой текстом."""
    fl = [x for f in files for x in ("--file", f)]
    who = (ref.get("authors") or {}).get(str(reply_to)) if reply_to else None
    who = who or ref.get("who") or ""   # ответ на конкретное сообщение группы — его автор
    if ref.get("wa"):
        if reply_to and quote:
            text = f"> {' '.join(quote.split())[:300]}\n{text}"
        title = wa_title(ref)   # группа и @lid открываются только по названию в списке чатов
        return wa_send([ref["send"], "wa", "--to", ref["to"], "--channel", ref["wa"], *(["--title", title] if title else []),
                        "--text", text, *fl, *contact_flags(ref["send"], who, ref.get("about"))], files)
    if ref.get("tg"):
        rt = ["--reply-to", reply_to] if reply_to and str(reply_to).isdigit() else []
        return run([ref["send"], "tg", "--to", ref["tg"], "--text", text, *fl, *rt,
                    *contact_flags(ref["send"], who, ref.get("about"))], timeout=180)
    if ref.get("mail"):
        subject = ref.get("subject") or ""
        if not re.match(r"(?i)re:", subject):
            subject = "Re: " + subject
        return run([ref["cmd"], "gmail", "send", "--thread-id", ref["thread"], "--reply-all", "--subject", subject,
                    "--body", text, "-a", ref["mail"], *[x for f in files for x in ("--attach", f)]], timeout=180)
    raise OSError("не знаю, куда отвечать на это сообщение")


def react(ref, emoji, msg=None):
    """Реакция в WhatsApp — командой из sources.json (`"react": "<путь>"`): <команда> react <чат> --id <сообщение>
    --emoji <эмодзи> --channel <номер>; Telegram — tgnew react. msg — id конкретного сообщения переписки (иначе то,
    на которое пришёл пост)."""
    if ref.get("wa") and ref.get("react") and (msg or ref.get("msg")):
        return run([ref["react"], "react", ref["to"], "--id", msg or ref["msg"], "--emoji", emoji, "--channel", ref["wa"]],
                   timeout=120)
    if ref.get("tg") and (msg or ref.get("msg")) and str(msg or ref.get("msg")).isdigit():
        return run([ref.get("cmd") or expand("~/.claude/bin/tgnew"), "react", ref["tg"], str(msg or ref["msg"]),
                    "--emoji", emoji], timeout=60)
    raise OSError("на это сообщение реакцию поставить нельзя")


def page(items, top, before=None, search=None):
    """Страница переписки из полного списка по времени: старше сообщения `before` (id), с текстом `search`; последние top."""
    if before:
        ids = [str(i.get("id")) for i in items]
        if str(before) in ids:
            items = items[:ids.index(str(before))]
    if search:
        q = search.casefold()
        items = [i for i in items if q in (i.get("text") or "").casefold() or q in (i.get("from") or "").casefold()]
    return items[-top:]


def amend(ref, msg, text=None):
    """Правка (text) или удаление (text=None) своего отправленного. Telegram — Telethon (только свои сообщения);
    WhatsApp и почта — нельзя: у WhatsApp нет такого канала, письмо не вернуть."""
    if ref.get("tg") and str(msg).isdigit():
        cmd = ref.get("cmd") or expand("~/.claude/bin/tgnew")
        if text is None:
            return run([cmd, "delete", ref["tg"], str(msg)], timeout=60)
        return run([cmd, "edit", ref["tg"], str(msg), "--text", text], timeout=60)
    if ref.get("wa"):
        raise OSError("в WhatsApp отправленное отсюда не поправить")
    if ref.get("mail"):
        raise OSError("отправленное письмо не вернуть")
    raise OSError("это сообщение изменить нельзя")


def mark_read(ref):
    """Пометить прочитанным в источнике — только по явной кнопке владельца. Telegram — прочитано до конца чата; почта —
    снимается метка UNREAD с цепочки; WhatsApp — чат открывается (отправитель увидит синие галочки: слово Ивана 13.10)."""
    if ref.get("tg"):
        return run([ref.get("cmd") or expand("~/.claude/bin/tgnew"), "read", ref["tg"]], timeout=60)
    if ref.get("mail"):
        return run([ref["cmd"], "gmail", "thread", "modify", ref["thread"], "--remove", "UNREAD", "-a", ref["mail"]],
                   timeout=60)
    if ref.get("wa"):
        who = ref["to"] if ref["to"].endswith("@g.us") else re.sub(r"\D", "", ref["to"].split("@")[0])
        return run([ref.get("cmd") or expand("~/.claude/bin/wa"), "thread", who, "--limit", "1", "--channel", ref["wa"]],
                   timeout=120)
    raise OSError("в Teams прочитанным пометить нельзя: Graph этого не даёт")


def verified_wa_history(ref, data):
    """Validate the source-v1 cache contract before publishing any row.

    Expected account comes from the collector's channel configuration, never from
    returned data. Legacy rows remain on disk but cannot be used as thread context.
    """
    def peer(value):
        return str(value or "").replace("@s.whatsapp.net", "@c.us")
    want, account = peer(ref.get("to")), ref.get("account")
    rows = data.get("messages") if isinstance(data, dict) else None
    if (not re.fullmatch(r"\d+@(c\.us|g\.us|lid)", want)
            or not isinstance(account, str) or not re.fullmatch(r"\d+", account)
            or not isinstance(rows, list) or peer(data.get("chat_id")) != want):
        raise OSError("Unverified WhatsApp history identity")
    ids = set()
    for row in rows:
        source = (row.get("source") or {}) if isinstance(row, dict) else {}
        if not isinstance(source, dict):
            raise OSError("Unverified WhatsApp history identity")
        raw = str(source.get("raw_id") or "").split("_")
        if (not isinstance(row, dict) or source.get("version") != 1
                or source.get("channel") != ref["wa"] or source.get("account") != account
                or peer(source.get("peer")) != want or len(raw) not in (3, 4)
                or raw[0] not in ("true", "false") or peer(raw[1]) != want
                or not raw[2] or raw[2] != row.get("id") or row.get("id") in ids
                or (raw[0] == "true") != row.get("out")):
            raise OSError("Unverified WhatsApp history identity")
        try:
            stamp = datetime.fromisoformat(source.get("captured_at") or "")
            if stamp.utcoffset() is None:
                raise ValueError("timezone required")
        except (ValueError, TypeError):
            raise OSError("Unverified WhatsApp history identity") from None
        ids.add(row["id"])
    return rows


def history(ref, top=20, before=None, search=None):
    """Переписка для «всей переписки» во вкладке. WhatsApp — только сохранённая копия треда (`--cached`): живое чтение
    открыло бы чат и поставило синие галочки. Почта — письма цепочки: от кого, когда, начало текста."""
    if ref.get("wa"):
        who = ref["to"] if ref["to"].endswith("@g.us") else re.sub(r"\D", "", ref["to"].split("@")[0])
        data = json.loads(run([ref.get("cmd") or expand("~/.claude/bin/wa"), "thread", who, "--cached", "--json",
                               "--limit", str(500 if before or search else top), "--channel", ref["wa"]]))
        out = []
        for m in verified_wa_history(ref, data):
            try:
                at = iso_utc(datetime.strptime(m.get("when") or "", "%I:%M %p, %m/%d/%Y"))
            except ValueError:
                at = ""
            text = (m.get("body") or "").strip() or ("[медиа]" if m.get("media") else "")
            if text:
                out.append({"at": at, "from": m.get("author") or "", "me": bool(m.get("out")), "text": text,
                            "source": m["source"],
                            **({"id": str(m["id"])} if m.get("id") else {})})
        return page(out, top, before, search)   # копия треда целиком: листание и поиск — по ней
    if ref.get("tg"):
        extra = (["--before", str(before)] if before and str(before).isdigit() else []) + \
                (["--search", search] if search else [])
        try:
            data = json.loads(run([ref.get("cmd") or expand("~/.claude/bin/tgnew"), "thread", ref["tg"], "--limit",
                                   str(top), "--json", *extra]))
        except (OSError, ValueError):
            return []
        msgs = data.get("messages") or []
        by_id = {str(m.get("id")): m for m in msgs}
        got = {}
        for it in tg_media(ref.get("cmd") or expand("~/.claude/bin/tgnew"), ref["tg"], msgs):
            got[it["id"].rsplit(":", 1)[-1]] = it
        out = []
        for m in msgs:
            e = {"at": iso_utc(datetime.fromtimestamp(m["t"], timezone.utc)), "from": m.get("from") or "",
                 "me": bool(m.get("out")), "text": m.get("text") or "", **({"id": str(m["id"])} if m.get("id") else {})}
            if str(m.get("id")) in got:
                e["media"] = [got[str(m["id"])]]
            elif m.get("media"):
                e["media"] = [{**m["media"], "id": f"tg:{ref['tg']}:{m.get('id')}"}]   # без файла: описание
            if not e["text"] and not e.get("media"):
                e["text"] = f"[{KIND_NAMES.get(m.get('type'), ('медиа',))[0]}]"
            if m.get("link"):
                e["links"] = [m["link"]]
            for k in ("reactions", "fwd", "edited"):
                if m.get(k):
                    e[k] = m[k]
            if m.get("reply"):
                e["reply"] = tg_reply_text(m, by_id)
            out.append(e)
        return out
    if ref.get("mail"):
        out = [{"at": m["at"], "from": m["from"], "me": m["me"], "text": m["text"] or m.get("subject", "")}
               for m in mail_thread(ref["cmd"], ref["mail"], ref["thread"], None)]
        return page(out, top, None, search)
    return []
