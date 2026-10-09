"""Fonctions utilitaires reproduisant le comportement PHP utilisé par les templates.

Le site d'origine est rendu par PHP ; pour garder un HTML identique, les templates
Jinja appellent ces équivalents (mêmes règles de vérité, d'échappement, d'arrondi…).
"""
import calendar
import datetime as dt
import math
import re
import time as _time
import urllib.parse
from decimal import ROUND_HALF_UP, Decimal

from jinja2 import Undefined


def is_undef(v):
    return isinstance(v, Undefined)


def isset(v):
    return not is_undef(v) and v is not None


def coalesce(*vals):
    for v in vals[:-1]:
        if isset(v):
            return v
    return vals[-1]


def t(v):
    """Vérité PHP : "0", "", 0, 0.0, null, [] sont faux ; "0.00" est vrai (chaîne)."""
    if is_undef(v) or v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, Decimal):
        return True  # PDO MySQL renvoie les DECIMAL sous forme de chaîne ("0.00" est vrai)
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v not in ("", "0")
    if isinstance(v, (list, tuple, dict)):
        return len(v) > 0
    return bool(v)


def empty(v):
    return not t(v)


def php_float(f):
    if math.isinf(f):
        return "INF" if f > 0 else "-INF"
    if math.isnan(f):
        return "NAN"
    if f == int(f) and abs(f) < 1e15:
        return str(int(f))
    r = repr(f)
    if "e" in r:
        mant, exp = r.split("e")
        r = f"{mant}E{'+' if not exp.startswith('-') else ''}{int(exp)}"
    return r


def strval(v):
    if is_undef(v) or v is None or v is False:
        return ""
    if v is True:
        return "1"
    if isinstance(v, float):
        return php_float(v)
    if isinstance(v, (list, dict)):
        return "Array"
    if isinstance(v, (dt.datetime,)):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    return str(v)


def finalize(v):
    """Conversion appliquée à chaque {{ … }} : identique à echo en PHP."""
    return strval(v)


def cat(*parts):
    return "".join(strval(p) for p in parts)


def h(s, flags=None, encoding=None, double_encode=True):
    """htmlspecialchars() avec les drapeaux par défaut de PHP 8.1+ (ENT_QUOTES)."""
    s = strval(s)
    if not double_encode:
        s = re.sub(r"&(?!(?:[A-Za-z][A-Za-z0-9]*|#\d+|#x[0-9A-Fa-f]+);)", "&amp;", s)
    else:
        s = s.replace("&", "&amp;")
    return s.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#039;")


def num(v):
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        return v
    if is_undef(v) or v is None or v is False:
        return 0
    if v is True:
        return 1
    m = re.match(r"\s*[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?", str(v))
    if not m:
        return 0
    s = m.group(0).strip()
    return float(s) if any(c in s for c in ".eE") else int(s)


def intval(v):
    n = num(v)
    return int(n)


def floatval(v):
    return float(num(v))


def count(v):
    if is_undef(v) or v is None:
        return 0
    return len(v)


def php_round(v, precision=0):
    d = Decimal(repr(float(num(v))))
    q = Decimal(1).scaleb(-precision)
    return float(d.quantize(q, rounding=ROUND_HALF_UP))


def number_format(v, decimals=0, dec_point=".", thousands_sep=","):
    d = Decimal(repr(float(num(v)))) if not isinstance(v, Decimal) else v
    q = Decimal(1).scaleb(-int(decimals))
    d = d.quantize(q, rounding=ROUND_HALF_UP)
    neg = d < 0
    s = f"{abs(d):f}"
    ent, _, frac = s.partition(".")
    groups = []
    while len(ent) > 3:
        groups.insert(0, ent[-3:])
        ent = ent[:-3]
    groups.insert(0, ent)
    out = thousands_sep.join(groups)
    if int(decimals) > 0:
        out += dec_point + frac
    if neg and d != 0:
        out = "-" + out
    return out


def ceil(v):
    return float(math.ceil(num(v)))


def floor(v):
    return float(math.floor(num(v)))


def php_min(*a):
    vals = a[0] if len(a) == 1 else a
    return min(vals, key=num)


def php_max(*a):
    vals = a[0] if len(a) == 1 else a
    return max(vals, key=num)


# ---------------------------------------------------------------- dates
TZ = dt.timezone.utc  # date.timezone par défaut du serveur PHP de référence

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"]


def time():
    return int(_time.time())


def strtotime(s, base=None):
    if is_undef(s) or s is None or s == "":
        return False
    if isinstance(s, dt.datetime):
        d = s
    elif isinstance(s, dt.date):
        d = dt.datetime(s.year, s.month, s.day)
    else:
        s = str(s).strip()
        if s == "now":
            return time()
        d = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                d = dt.datetime.strptime(s, fmt)
                break
            except ValueError:
                pass
        if d is None:
            m = re.fullmatch(r"([+-]\d+)\s*(day|days|month|months|year|years|hour|hours)", s)
            if m:
                n, unit = int(m.group(1)), m.group(2).rstrip("s")
                now = dt.datetime.fromtimestamp(base if base is not None else time(), TZ).replace(tzinfo=None)
                if unit == "day":
                    d = now + dt.timedelta(days=n)
                elif unit == "hour":
                    d = now + dt.timedelta(hours=n)
                else:
                    months = n * (12 if unit == "year" else 1)
                    y, mo = divmod(now.month - 1 + months, 12)
                    d = now.replace(year=now.year + y, month=mo + 1)
            else:
                return False
    return int(calendar.timegm(d.timetuple()))


def date(fmt, ts=None):
    ts = time() if ts is None or is_undef(ts) else int(num(ts))
    d = dt.datetime.fromtimestamp(ts, TZ)
    out = []
    i = 0
    while i < len(fmt):
        c = fmt[i]
        if c == "\\" and i + 1 < len(fmt):
            out.append(fmt[i + 1])
            i += 2
            continue
        out.append({
            "d": f"{d.day:02d}", "j": str(d.day), "D": _DAYS[d.weekday()][:3], "l": _DAYS[d.weekday()],
            "N": str(d.isoweekday()), "w": str(d.isoweekday() % 7), "m": f"{d.month:02d}",
            "n": str(d.month), "F": _MONTHS[d.month - 1], "M": _MONTHS[d.month - 1][:3],
            "Y": str(d.year), "y": f"{d.year % 100:02d}", "H": f"{d.hour:02d}", "G": str(d.hour),
            "h": f"{(d.hour % 12) or 12:02d}", "g": str((d.hour % 12) or 12), "i": f"{d.minute:02d}",
            "s": f"{d.second:02d}", "A": "AM" if d.hour < 12 else "PM", "a": "am" if d.hour < 12 else "pm",
            "t": str(calendar.monthrange(d.year, d.month)[1]), "U": str(ts),
        }.get(c, c))
        i += 1
    return "".join(out)


# ---------------------------------------------------------------- chaînes
def strip_tags(s, allowed=None):
    s = strval(s)
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    return re.sub(r"<(?=\S)[^>]*(>|$)", "", s)


def mb_strimwidth(s, start, width, trim=""):
    s = strval(s)[int(start):]
    if len(s) <= width:
        return s
    return s[: max(0, width - len(trim))] + trim


def mb_substr(s, start, length=None):
    s = strval(s)
    return s[start:] if length is None or is_undef(length) else s[start:start + length] if length >= 0 else s[start:length]


def mb_strlen(s):
    return len(strval(s))


def substr(s, start, length=None):
    """substr() PHP travaille en octets : on reproduit la coupe UTF-8 octet par octet."""
    b = strval(s).encode("utf-8")
    start = int(start)
    if start < 0:
        start = max(0, len(b) + start)
    if length is None or is_undef(length):
        part = b[start:]
    else:
        length = int(length)
        part = b[start:start + length] if length >= 0 else b[start:len(b) + length]
    return part.decode("utf-8", errors="replace")


def strlen(s):
    return len(strval(s).encode("utf-8"))


def ucfirst(s):
    s = strval(s)
    return s[:1].upper() + s[1:] if s[:1].isascii() else s


def ucwords(s):
    return re.sub(r"(^|[ \t\r\n\f\v])([a-z])", lambda m: m.group(1) + m.group(2).upper(), strval(s))


def strtolower(s):
    return "".join(c.lower() if c.isascii() else c for c in strval(s))


def strtoupper(s):
    return "".join(c.upper() if c.isascii() else c for c in strval(s))


def mb_strtolower(s):
    return strval(s).lower()


def mb_strtoupper(s):
    return strval(s).upper()


def trim(s, chars=" \t\n\r\0\x0B"):
    return strval(s).strip(chars)


def urlencode(s):
    return urllib.parse.quote_plus(strval(s), safe="").replace("~", "%7E")


def rawurlencode(s):
    return urllib.parse.quote(strval(s), safe="-_.~")


def nl2br(s):
    return re.sub(r"(\r\n|\n\r|\n|\r)", r"<br />\1", strval(s))


def str_replace(search, replace, subject):
    subject = strval(subject)
    if isinstance(search, list):
        reps = replace if isinstance(replace, list) else [replace] * len(search)
        for i, s in enumerate(search):
            subject = subject.replace(strval(s), strval(reps[i] if i < len(reps) else ""))
        return subject
    return subject.replace(strval(search), strval(replace))


def explode(sep, s, limit=None):
    parts = strval(s).split(sep)
    if limit is not None and limit > 0 and len(parts) > limit:
        parts = parts[: limit - 1] + [sep.join(parts[limit - 1:])]
    return parts


def implode(sep, arr):
    if isinstance(sep, list):
        sep, arr = arr, sep
    return strval(sep).join(strval(x) for x in php_values(arr))


def strtok(s, tok):
    s = strval(s)
    for i, c in enumerate(s):
        if c not in tok:
            j = i
            while j < len(s) and s[j] not in tok:
                j += 1
            return s[i:j]
    return False


def str_word_count(s):
    s = strval(s)
    if s[:1] in ("'", "-"):  # même règle que PHP : 1er caractère ni ' ni -, dernier pas -
        s = s[1:]
    if s.endswith("-"):
        s = s[:-1]
    return len(re.findall(r"[A-Za-z'-]+", s))


def str_repeat(s, n):
    return strval(s) * int(n)


def sprintf(fmt, *args):
    return fmt % tuple(args)


def _json_floats(v):
    # json_encode(1000.0) donne 1000 en PHP (pas de « .0 » pour un flottant entier).
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        return int(v)
    if isinstance(v, Decimal):
        return format(v, "f")  # PDO renvoie les DECIMAL sous forme de chaîne
    if isinstance(v, dict):
        return {k: _json_floats(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_json_floats(x) for x in v]
    return v


def json_encode(v, flags=0):
    import json
    return json.dumps(_json_floats(v), ensure_ascii=not (flags & 256),
                      separators=(",", ":")).replace("/", "\\/")


# ---------------------------------------------------------------- tableaux
def php_values(v):
    if is_undef(v) or v is None:
        return []
    if isinstance(v, dict):
        return list(v.values())
    return v


def php_items(v):
    if is_undef(v) or v is None:
        return []
    if isinstance(v, dict):
        return list(v.items())
    return list(enumerate(v))


def array_slice(arr, offset, length=None):
    arr = list(php_values(arr))
    return arr[offset:] if length is None else arr[offset:offset + length]


def array_filter(arr, fn=None):
    if isinstance(arr, dict):
        return {k: v for k, v in arr.items() if (fn(v) if fn else t(v))}
    return [v for v in arr if (fn(v) if fn else t(v))]


def array_column(arr, col):
    return [r[col] for r in php_values(arr) if col in r]


def array_keys(arr):
    return list(arr.keys()) if isinstance(arr, dict) else list(range(len(arr)))


def array_sum(arr):
    return sum(num(x) for x in php_values(arr))


def array_map(fn, arr):
    return [fn(x) for x in php_values(arr)]


def in_array(needle, arr, strict=False):
    vals = php_values(arr)
    return needle in vals if strict else any(strval(needle) == strval(v) for v in vals)


def array_merge(*arrs):
    if all(isinstance(a, dict) for a in arrs):
        out = {}
        for a in arrs:
            out.update(a)
        return out
    out = []
    for a in arrs:
        out.extend(php_values(a))
    return out


def is_array(v):
    return isinstance(v, (list, dict))


def is_numeric(v):
    if isinstance(v, (int, float, Decimal)) and not isinstance(v, bool):
        return True
    return bool(re.fullmatch(r"\s*[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?\s*", strval(v)))


def rtrim(s, chars=" \t\n\r\0\x0B"):
    return strval(s).rstrip(chars)


def ltrim(s, chars=" \t\n\r\0\x0B"):
    return strval(s).lstrip(chars)


def parse_url(url, component=None):
    p = urllib.parse.urlsplit(strval(url))
    parts = {"scheme": p.scheme, "host": p.hostname, "port": p.port, "path": p.path,
             "query": p.query, "fragment": p.fragment}
    parts = {k: v for k, v in parts.items() if v not in (None, "")}
    if component is None:
        return parts
    key = {"PHP_URL_PATH": "path", "PHP_URL_QUERY": "query", "PHP_URL_HOST": "host",
           "PHP_URL_SCHEME": "scheme", "PHP_URL_FRAGMENT": "fragment"}.get(component, component)
    return parts.get(key)


def _pcre(pattern):
    delim = pattern[0]
    end = {"(": ")", "{": "}", "[": "]", "<": ">"}.get(delim, delim)
    body, flags_s = pattern[1:pattern.rindex(end)], pattern[pattern.rindex(end) + 1:]
    flags = 0
    for f in flags_s:
        flags |= {"i": re.I, "m": re.M, "s": re.S, "x": re.X, "u": 0, "U": 0, "D": 0}[f]
    return re.compile(body, flags)


def _pcre_repl(rep):
    return re.sub(r"\$(\d+)|\$\{(\d+)\}|\\(\d+)", lambda m: "\\g<" + (m.group(1) or m.group(2) or m.group(3)) + ">",
                  rep.replace("\\", "\\\\"))


def preg_replace(pattern, replacement, subject, limit=-1):
    return _pcre(pattern).sub(_pcre_repl(replacement), strval(subject), count=0 if limit < 0 else limit)


def preg_match(pattern, subject):
    return 1 if _pcre(pattern).search(strval(subject)) else 0


def loose_eq(a, b):
    """Comparaison == de PHP 8 (scalaires et tableaux)."""
    if is_undef(a):
        a = None
    if is_undef(b):
        b = None
    if a is None and b is None:
        return True
    if a is None or b is None:
        other = b if a is None else a
        return other == "" if isinstance(other, str) else not t(other)
    if isinstance(a, bool) or isinstance(b, bool):
        return t(a) == t(b)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(loose_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, (int, float, Decimal)) and isinstance(b, str):
        return float(a) == float(b) if is_numeric(b) else strval(a) == b
    if isinstance(b, (int, float, Decimal)) and isinstance(a, str):
        return loose_eq(b, a)
    if isinstance(a, str) and isinstance(b, str) and is_numeric(a) and is_numeric(b):
        return float(a) == float(b)
    return a == b


def preg_matches(pattern, subject):
    """Tableau $matches rempli par preg_match($pattern, $subject, $matches)."""
    m = _pcre(pattern).search(strval(subject))
    if not m:
        return []
    groups = list(m.groups())
    while groups and groups[-1] is None:
        groups.pop()  # PHP omet les groupes finaux non capturés
    return [m.group(0)] + ["" if g is None else g for g in groups]


def json_decode(s, assoc=False):
    import json
    try:
        return json.loads(strval(s))
    except ValueError:
        return None


def dirname(p):
    import posixpath
    return posixpath.dirname(strval(p)) or "."


def php_upto(start, end, inclusive):
    """for ($i = start; $i <= end; $i++) — accepte des bornes flottantes comme PHP."""
    i, end = num(start), num(end)
    out = []
    while (i <= end) if inclusive else (i < end):
        out.append(i)
        i += 1
    return out


GLOBALS = {
    "isset": isset, "empty": empty, "coalesce": coalesce, "t": t, "cat": cat, "h": h,
    "htmlspecialchars": h, "strval": strval, "intval": intval, "floatval": floatval,
    "count": count, "round": php_round, "number_format": number_format, "ceil": ceil,
    "floor": floor, "min": php_min, "max": php_max, "time": time, "strtotime": strtotime,
    "date": date, "strip_tags": strip_tags, "mb_strimwidth": mb_strimwidth,
    "mb_substr": mb_substr, "mb_strlen": mb_strlen, "substr": substr, "strlen": strlen,
    "ucfirst": ucfirst, "ucwords": ucwords, "strtolower": strtolower, "strtoupper": strtoupper,
    "mb_strtolower": mb_strtolower, "mb_strtoupper": mb_strtoupper, "trim": trim,
    "urlencode": urlencode, "rawurlencode": rawurlencode, "nl2br": nl2br,
    "str_replace": str_replace, "explode": explode, "implode": implode, "strtok": strtok,
    "str_word_count": str_word_count, "str_repeat": str_repeat, "sprintf": sprintf,
    "json_encode": json_encode, "php_values": php_values, "php_items": php_items,
    "array_slice": array_slice, "array_filter": array_filter, "array_column": array_column,
    "array_keys": array_keys, "array_sum": array_sum, "array_map": array_map,
    "in_array": in_array, "array_merge": array_merge, "is_array": is_array,
    "is_numeric": is_numeric, "abs": abs, "rtrim": rtrim, "ltrim": ltrim, "parse_url": parse_url,
    "preg_replace": preg_replace, "preg_match": preg_match, "preg_matches": preg_matches, "json_decode": json_decode,
    "dirname": dirname, "php_upto": php_upto,
}
