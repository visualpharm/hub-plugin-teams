"""Простой Markdown → HTML тела сообщения Teams (contentType html).

Teams в html-сообщении маркеры Markdown не рисует: подпись «🤖 _…_» доходила с подчёркиваниями. Понимаем малое:
_курсив_ и *курсив*, **жирный**, `код`, ```блок кода```, [текст](https://…), списки «- »/«* »/«1. » и переводы
строк; остальной текст экранируется. Маркер курсива/жирного парный и стоит на границе слова:
snake_case, __init__, пути, адреса и 2*3*4 остаются как есть. Текст без Markdown даёт прежнее тело: экранированный
текст, перевод строки — <br>.
"""
import html
import re

_FENCE = re.compile(r"^```[^\n`]*\n(.*?)\n?```[ \t]*$", re.M | re.S)
_BULLET = re.compile(r"^[ \t]*[-*•][ \t]+(\S.*)$")
_NUMBER = re.compile(r"^[ \t]*(\d{1,3})[.)][ \t]+(\S.*)$")
_CODE = re.compile(r"`([^`\n]+)`")
_LINK = re.compile(r"\[([^\]\n]+)\]\(((?:https?://|mailto:)[^\s()<>]+)\)")
_URL = re.compile(r"(?:https?://|mailto:|www\.)[^\s<>]+")
# Маркер открывает, только если перед ним не буква/цифра и не знак пути или адреса, и закрывает, только если после
# него не буква/цифра; внутри — без переводов строки, у краёв не пробел.
_EDGE_L = r"(?<![\w/\\.@:=~*-])"
_EDGE_R = r"(?![\w/\\@=~*])"
_BOLD = re.compile(_EDGE_L + r"\*\*(?=[^\s*])([^\n]*?[^\s*])\*\*" + _EDGE_R)
_STAR = re.compile(_EDGE_L + r"\*(?=[^\s*])([^\n*]*?[^\s*])\*" + _EDGE_R)
_UNDER = re.compile(_EDGE_L + r"_(?=[^\s_])([^\n_]*?[^\s_])_" + _EDGE_R)
_SLOT = re.compile("\x00(\\d+)\x00")


def _esc(s):
    return html.escape(s, quote=False)


def inline(line):
    """Одна строка: код, ссылки и голые адреса — неприкосновенны, остальное экранируется, затем жирный и курсив."""
    keep = []

    def slot(markup):
        keep.append(markup)
        return f"\x00{len(keep) - 1}\x00"

    line = _CODE.sub(lambda m: slot(f"<code>{_esc(m.group(1))}</code>"), line)
    line = _LINK.sub(lambda m: slot(f'<a href="{html.escape(m.group(2))}">{_esc(m.group(1))}</a>'), line)
    line = _URL.sub(lambda m: slot(_esc(m.group(0))), line)
    line = _esc(line)
    line = _BOLD.sub(r"<b>\1</b>", line)
    line = _STAR.sub(r"<i>\1</i>", line)
    line = _UNDER.sub(r"<i>\1</i>", line)
    while _SLOT.search(line):
        line = _SLOT.sub(lambda m: keep[int(m.group(1))], line)
    return line


def to_html(text):
    """Весь текст → тело html: строки через <br>, пустая строка — <br><br>, списки и блоки кода — блоками."""
    text = (text or "").replace("\r\n", "\n")
    blocks = []

    def fence(m):
        blocks.append(f"<pre>{_esc(m.group(1))}</pre>")
        return f"\x01{len(blocks) - 1}\x01"

    text = _FENCE.sub(fence, text)
    parts = []                                  # (block?, html)
    items, tag = [], None

    def flush():
        nonlocal items, tag
        if items:
            start = ""
            if tag == "ol" and items[0][0] not in ("", "1"):
                start = f' start="{items[0][0]}"'
            parts.append((True, f"<{tag}{start}>" + "".join(f"<li>{inline(t)}</li>" for _, t in items) + f"</{tag}>"))
        items, tag = [], None

    for line in text.split("\n"):
        b, n = _BULLET.match(line), _NUMBER.match(line)
        kind = "ul" if b else "ol" if n else None
        if kind and tag not in (None, kind):
            flush()
        if b:
            tag = "ul"
            items.append(("", b.group(1)))
        elif n:
            tag = "ol"
            items.append((n.group(1), n.group(2)))
        else:
            flush()
            m = re.fullmatch("\x01(\\d+)\x01", line.strip())
            parts.append((True, blocks[int(m.group(1))]) if m else (False, inline(line)))
    flush()
    # пустые строки у блоков не нужны: список и <pre> сами отделяются
    keep = [p for i, p in enumerate(parts)
            if p[0] or p[1] or not ((i > 0 and parts[i - 1][0]) or (i + 1 < len(parts) and parts[i + 1][0]))]
    out = ""
    for i, (block, markup) in enumerate(keep):
        if i and not block and not keep[i - 1][0]:
            out += "<br>"
        out += markup
    return out


def has_blocks(markup):
    return bool(re.search(r"<(ul|ol|pre)\b", markup))


_TAG = re.compile(r"</?(?:b|i|u|s|em|strong|br|p|div|span|a|ul|ol|li|pre|code|blockquote|h[1-6]|at|emoji|img|table)"
                  r"(?:\s[^<>]*)?/?>", re.I)


def looks_html(text):
    """Вызывающий уже прислал html (раньше тело уходило как есть) — его не трогаем."""
    return bool(_TAG.search(text or ""))
