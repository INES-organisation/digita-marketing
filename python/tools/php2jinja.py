"""Convertit un template PHP (sous-ensemble utilisé par Digita) en template Jinja2.

Outil d'aide à la migration : le résultat est relu et corrigé à la main, puis validé
par tools/parity.py. Les instructions non reconnues sont laissées sous forme de
commentaire `{# FIXME php: … #}` pour être traitées manuellement.

Sémantique reproduite :
- PHP avale le saut de ligne qui suit immédiatement `?>` : le convertisseur le retire
  aussi du template Jinja (l'environnement est configuré sans trim_blocks).
- Les conditions sont évaluées avec la vérité PHP (`t()`), les concaténations avec
  `cat()` (null → ''), `??` avec `coalesce()`, etc. Voir digita/php.py.

    python tools/php2jinja.py fichier.php > fichier.html
"""
import re
import sys

JINJA_RESERVED = {
    "loop", "range", "self", "caller", "varargs", "kwargs", "class", "from", "in", "is",
    "not", "and", "or", "if", "else", "for", "def", "lambda", "none", "true", "false",
    "import", "with", "as", "pass", "return", "yield", "global", "del", "try", "while",
    "super", "namespace", "content",
    "h", "cat",  # helpers htmlspecialchars et concaténation : foreach ($x as $h) les masquerait
}

FUNC_MAP = {
    "htmlspecialchars": "h",
    "count": "count",
    "sizeof": "count",
}


def var_name(name):
    # Variables modifiées dans une boucle : en Jinja un {% set %} dans un {% for %} ne sort pas
    # de l'itération ; elles vivent donc dans un namespace (_ns) pour garder la portée PHP.
    if name in CURRENT.get("ns_vars", ()):
        return "_ns." + name
    return name + "_" if name.lower() in JINJA_RESERVED else name


class Tok:
    def __init__(self, kind, val):
        self.kind, self.val = kind, val

    def __repr__(self):
        return f"{self.kind}:{self.val}"


TOKEN_RX = re.compile(r"""
    (?P<ws>\s+)
  | (?P<var>\$[A-Za-z_]\w*)
  | (?P<num>\d+\.\d+|\d+)
  | (?P<sq>'(?:\\.|[^'\\])*')
  | (?P<dq>"(?:\\.|[^"\\])*")
  | (?P<cast>\((?:int|string|float|bool|array)\))
  | (?P<op>===|!==|<=>|\?\?|\?->|->|::|==|!=|<>|<=|>=|&&|\|\||\+\+|--|\+=|-=|\.=|\*=|=>|[-+*/%.!<>=?:,()\[\]{};&|])
  | (?P<name>[A-Za-z_\\][\w\\]*)
""", re.X)


def tokenize(src):
    toks, i = [], 0
    while i < len(src):
        m = TOKEN_RX.match(src, i)
        if not m:
            raise SyntaxError(f"token inconnu près de {src[i:i+30]!r}")
        i = m.end()
        if m.lastgroup == "ws":
            continue
        toks.append(Tok(m.lastgroup, m.group()))
    toks.append(Tok("eof", ""))
    return toks


def php_str(lit):
    """Littéral PHP → littéral Python (gère l'interpolation des chaînes "…")."""
    body = lit[1:-1]
    if lit[0] == "'":
        body = body.replace("\\'", "'").replace("\\\\", "\\")
        return repr(body)
    parts, buf, i = [], "", 0
    esc = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "$": "$"}
    while i < len(body):
        c = body[i]
        if c == "\\" and i + 1 < len(body) and body[i + 1] in esc:
            buf += esc[body[i + 1]]
            i += 2
        elif c == "{" and body[i + 1:i + 2] == "$":
            j = body.index("}", i)
            if buf:
                parts.append(repr(buf))
                buf = ""
            parts.append(Parser(tokenize(body[i + 1:j])).expr())
            i = j + 1
        elif c == "$" and i + 1 < len(body) and (body[i + 1].isalpha() or body[i + 1] == "_"):
            m = re.match(r"\$([A-Za-z_]\w*)(\[(?:'[^']*'|\w+)\]|->\w+)?", body[i:])
            if buf:
                parts.append(repr(buf))
                buf = ""
            expr = var_name(m.group(1))
            if m.group(2):
                g = m.group(2)
                if g.startswith("->"):
                    expr += "." + g[2:]
                else:
                    k = g[1:-1]
                    expr += f"[{k}]" if k.startswith("'") or k.isdigit() else f"['{k}']"
            parts.append(expr)
            i += m.end()
        else:
            buf += c
            i += 1
    if buf or not parts:
        parts.append(repr(buf))
    return parts[0] if len(parts) == 1 else "cat(" + ", ".join(parts) + ")"


BINARY = {
    # opérateur PHP: (priorité, jinja)
    "??": (2, None), "||": (3, "or"), "or": (3, "or"), "&&": (4, "and"), "and": (4, "and"),
    "==": (6, "=="), "!=": (6, "!="), "<>": (6, "!="), "===": (6, "=="), "!==": (6, "!="),
    "<": (7, "<"), ">": (7, ">"), "<=": (7, "<="), ">=": (7, ">="),
    ".": (8, None), "+": (8, "+"), "-": (8, "-"),
    "*": (9, "*"), "/": (9, "/"), "%": (9, "%"),
}
COMPARISONS = {"==", "!=", "<", ">", "<=", ">=", "<>", "===", "!=="}


class Node(str):
    """Expression Jinja produite, avec un indicateur « déjà booléen »."""
    boolean = False


def boolean(s):
    n = Node(s)
    n.boolean = True
    return n


def truthy(e):
    return e if getattr(e, "boolean", False) else Node(f"t({e})")


class Parser:
    def __init__(self, toks):
        self.toks, self.i = toks, 0

    @property
    def cur(self):
        return self.toks[self.i]

    def eat(self, val=None, kind=None):
        t = self.cur
        if (val is not None and t.val != val) or (kind is not None and t.kind != kind):
            raise SyntaxError(f"attendu {val or kind}, trouvé {t}")
        self.i += 1
        return t

    def at(self, *vals):
        return self.cur.val in vals

    def expr(self, min_prec=0):
        left = self.unary()
        while True:
            op = self.cur.val if self.cur.kind in ("op", "name") else None
            if op == "?" and min_prec <= 1:
                self.eat("?")
                if self.at(":"):
                    self.eat(":")
                    other = self.expr(1)
                    left = Node(f"({left} if {truthy(left)} else {other})")
                else:
                    a = self.expr(1)
                    self.eat(":")
                    b = self.expr(1)
                    left = Node(f"({a} if {truthy(left)} else {b})")
                continue
            if op not in BINARY:
                break
            prec, jop = BINARY[op]
            if prec < min_prec:
                break
            self.i += 1
            right = self.expr(prec if op == "??" else prec + 1)
            if op == "??":
                left = Node(f"coalesce({left}, {right})")
            elif op == ".":
                left = Node(f"cat({left}, {right})")
            elif op in ("&&", "||", "and", "or"):
                left = boolean(f"({truthy(left)} {jop} {truthy(right)})")
            elif op in ("===", "!==") and {str(left), str(right)} & {"true", "false"}:
                # 0 == false est vrai en Python : la comparaison stricte à un booléen garde son type.
                neg = "not " if op == "!==" else ""
                left = boolean(f"({neg}same({left}, {right}))")
            elif op in ("==", "!=", "<>"):
                # Comparaison souple PHP 8 : '3' == 3 est vrai.
                neg = "not " if op != "==" else ""
                left = boolean(f"({neg}loose_eq({left}, {right}))")
            elif op in COMPARISONS:
                left = boolean(f"({left} {jop} {right})")
            else:
                left = Node(f"({left} {jop} {right})")
        return left

    def unary(self):
        t = self.cur
        if t.val == "!":
            self.eat("!")
            return boolean(f"(not {truthy(self.unary())})")
        if t.val == "-":
            self.eat("-")
            return Node(f"(-{self.unary()})")
        if t.kind == "cast":
            self.i += 1
            fn = {"(int)": "intval", "(string)": "strval", "(float)": "floatval",
                  "(bool)": "t", "(array)": "to_array"}[t.val]
            return Node(f"{fn}({self.unary()})")
        if t.val == "@":
            self.eat("@")
        return self.postfix(self.primary())

    def args(self):
        self.eat("(")
        out = []
        while not self.at(")"):
            out.append(self.expr())
            if self.at(","):
                self.eat(",")
        self.eat(")")
        return out

    def primary(self):
        t = self.cur
        if t.kind == "var":
            self.i += 1
            return Node(var_name(t.val[1:]))
        if t.kind == "num":
            self.i += 1
            return Node(t.val)
        if t.kind in ("sq", "dq"):
            self.i += 1
            return Node(php_str(t.val))
        if t.val == "(":
            self.eat("(")
            e = self.expr()
            self.eat(")")
            return Node(f"({e})") if not getattr(e, "boolean", False) else boolean(f"({e})")
        if t.val == "[":
            return self.array_lit("[", "]")
        if t.kind == "name":
            name = t.val
            low = name.lower()
            self.i += 1
            if low in ("true", "false", "null"):
                return Node({"true": "true", "false": "false", "null": "none"}[low])
            if low == "array" and self.at("("):
                return self.array_lit("(", ")")
            if self.at("::"):
                self.eat("::")
                member = self.eat(kind="name").val
                if self.at("("):
                    a = self.args()
                    return Node(f"{name}_{member}({', '.join(a)})")
                return Node(f"{name}_{member}")
            if self.at("("):
                if low in ("isset", "empty"):
                    a = self.args()
                    if low == "isset":
                        return boolean("(" + " and ".join(f"isset({x})" for x in a) + ")")
                    return boolean(f"empty({a[0]})")
                a = self.args()
                return Node(f"{FUNC_MAP.get(low, low)}({', '.join(a)})")
            if re.fullmatch(r"[A-Z_][A-Z0-9_]*", name):
                return Node(f"const('{name}')")
            return Node(name)
        raise SyntaxError(f"expression inattendue : {t}")

    def array_lit(self, open_, close):
        self.eat(open_)
        items, keyed = [], False
        while not self.at(close):
            k = self.expr()
            if self.at("=>"):
                self.eat("=>")
                v = self.expr()
                items.append(f"{k}: {v}")
                keyed = True
            else:
                items.append(k)
            if self.at(","):
                self.eat(",")
        self.eat(close)
        return Node(("{" + ", ".join(items) + "}") if keyed else ("[" + ", ".join(items) + "]"))

    def postfix(self, e):
        while True:
            if self.at("["):
                self.eat("[")
                if self.at("]"):
                    self.eat("]")
                    e = Node(f"{e}[]")  # $a[] = … (append) — traité par l'appelant
                    continue
                k = self.expr()
                self.eat("]")
                e = Node(f"{e}[{k}]")
            elif self.at("->", "?->"):
                self.i += 1
                m = self.eat(kind="name").val
                if self.at("("):
                    e = Node(f"{e}.{m}({', '.join(self.args())})")
                else:
                    e = Node(f"{e}.{m}")
            else:
                return e


def conv_expr(src):
    p = Parser(tokenize(src))
    e = p.expr()
    if p.cur.kind != "eof":
        raise SyntaxError(f"reste non analysé : {p.toks[p.i:]}")
    return e


def split_statements(code):
    """Découpe un bloc PHP en instructions (séparateurs ; et : de la syntaxe alternative)."""
    out, buf, depth, i = [], "", 0, 0
    while i < len(code):
        c = code[i]
        if c in "'\"":
            j = i + 1
            while j < len(code) and code[j] != c:
                j += 2 if code[j] == "\\" else 1
            buf += code[i:j + 1]
            i = j + 1
            continue
        if code.startswith("//", i) or code[i] == "#":
            j = code.find("\n", i)
            i = len(code) if j < 0 else j
            continue
        if code.startswith("/*", i):
            i = code.index("*/", i) + 2
            continue
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        if depth == 0 and c == ";":
            out.append(buf.strip())
            buf = ""
        elif depth == 0 and c == ":" and re.match(r"\s*(if|elseif|else\s*if|foreach|for|while)\b.*\)\s*$|\s*else\s*$", buf, re.S) and not code.startswith("::", i):
            out.append(buf.strip() + ":")
            buf = ""
        elif depth == 0 and c == "{" and re.match(r"\s*(if|elseif|foreach|for|while)\b.*\)\s*$|\s*else\s*$", buf, re.S):
            out.append(buf.strip() + ":")
            buf = ""
        elif depth == 0 and c == "}":
            if buf.strip():
                out.append(buf.strip())
            out.append("}")
            buf = ""
        else:
            buf += c
        i += 1
    if buf.strip():
        out.append(buf.strip())
    out = [s for s in out if s]
    # « } elseif (…) { » / « } else { » : l'accolade ferme la branche, pas le if.
    return [s for k, s in enumerate(out)
            if not (s == "}" and k + 1 < len(out) and re.match(r"(elseif|else\s*if|else)\b", out[k + 1]))]


ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent.parent
CURRENT = {"rel": ""}


def resolve_include(path):
    """Chemin PHP inclus → template Jinja (même arborescence, extension .html)."""
    import os
    here = os.path.dirname(CURRENT["rel"])
    for cand in (os.path.normpath(os.path.join(here, path.lstrip("/"))), os.path.normpath(path.lstrip("/"))):
        cand = cand.replace("\\", "/")
        while cand.startswith("../"):
            cand = cand[3:]
        if (ROOT / cand).exists():
            return cand[:-4] + ".html"
    return path


def conv_statement(st, stack):
    if "for" in stack:
        m = re.match(r"\$(\w+)\s*(?:=(?!=)|\.=|\+=|-=|\+\+|--)", st)
        if m:
            CURRENT.setdefault("loop_assigned", set()).add(m.group(1))
    m = re.fullmatch(r"unset\s*\(\s*\$_SESSION\[\s*'(\w+)'\s*\]\s*\)", st)
    if m:
        return f"{{% do _SESSION.pop('{m.group(1)}', none) %}}"
    m = re.fullmatch(r"if\s*\((.*)\)\s*(continue|break)", st, re.S)
    if m:
        return f"{{% if {truthy(conv_expr(m.group(1)))} %}}{{% {m.group(2)} %}}{{% endif %}}"
    m = re.fullmatch(r"(if|elseif|else\s*if)\s*\((.*)\)\s*:", st, re.S)
    if m:
        kw = "if" if m.group(1) == "if" else "elif"
        if kw == "if":
            stack.append("if")
        return f"{{% {kw} {truthy(conv_expr(m.group(2)))} %}}"
    if re.fullmatch(r"else\s*:", st):
        return "{% else %}"
    if st in ("endif", "endforeach", "endfor", "endwhile") or st == "}":
        kind = stack.pop() if stack else "if"
        return "{% end" + kind + " %}"
    m = re.fullmatch(r"foreach\s*\((.*)\s+as\s+(\$\w+)(?:\s*=>\s*(\$\w+))?\s*\)\s*:", st, re.S)
    if m:
        stack.append("for")
        src = conv_expr(m.group(1))
        if m.group(3):
            return f"{{% for {var_name(m.group(2)[1:])}, {var_name(m.group(3)[1:])} in php_items({src}) %}}"
        return f"{{% for {var_name(m.group(2)[1:])} in php_values({src}) %}}"
    m = re.fullmatch(r"for\s*\(\s*\$(\w+)\s*=\s*(.+?);\s*\$\w+\s*(<=|<)\s*(.+?);\s*\$\w+\+\+\s*\)\s*:", st, re.S)
    if m:
        stack.append("for")
        incl = "true" if m.group(3) == "<=" else "false"
        return f"{{% for {var_name(m.group(1))} in php_upto({conv_expr(m.group(2))}, {conv_expr(m.group(4))}, {incl}) %}}"
    m = re.fullmatch(r"echo\s+(.*)", st, re.S)
    if m:
        return "{{ " + conv_expr(m.group(1)) + " }}"
    m = re.fullmatch(r"(?:require|include)(_once)?\s*\(?\s*(.*?)\s*\)?", st, re.S)
    if m:
        path = re.findall(r"'([^']+\.php)'", m.group(2))
        if not path:
            return f"{{# FIXME php: {st} #}}"
        tpl = resolve_include(path[-1])
        if m.group(1):  # require_once : une seule inclusion par requête, comme en PHP
            return f"{{% if once({tpl!r}) %}}{{% include {tpl!r} %}}{{% endif %}}"
        return f"{{% include {tpl!r} %}}"
    m = re.fullmatch(r"(\$\w+(?:\[[^\]]*\])*)\s*(=|\.=|\+=|-=)\s*(.*)", st, re.S)
    if m and not m.group(3).startswith("="):
        target, op, val = m.groups()
        val = conv_expr(val)
        tgt = conv_expr(target) if not target.endswith("[]") else None
        if target.endswith("[]"):
            base = conv_expr(target[:-2])
            return f"{{% do {base}.append({val}) %}}"
        if op == ".=":
            val = f"cat({tgt}, {val})"
        elif op in ("+=", "-="):
            val = f"({tgt} {op[0]} {val})"
        if "[" in tgt:
            base, key = re.fullmatch(r"(.*)\[(.*)\]", tgt).groups()
            return f"{{% do {base}.__setitem__({key}, {val}) %}}"
        return f"{{% set {tgt} = {val} %}}"
    m = re.fullmatch(r"\$(\w+)(\+\+|--)", st)
    if m:
        v = var_name(m.group(1))
        return f"{{% set {v} = {v} {m.group(2)[0]} 1 %}}"
    return f"{{# FIXME php: {st} #}}"


BLOCK_RX = re.compile(r"<\?(?:php\b|=)(.*?)(\?>\n?|$)", re.S)


def raw_text(txt):
    if re.search(r"\{[{%#]", txt):
        return "{% raw %}" + txt + "{% endraw %}"
    return txt


def convert(src, rel=""):
    CURRENT["rel"] = rel
    CURRENT["ns_vars"] = set()
    CURRENT["loop_assigned"] = set()
    _convert(src)
    if not CURRENT["loop_assigned"]:
        return _convert(src)
    CURRENT["ns_vars"] = set(CURRENT["loop_assigned"])
    print(f"  {rel} : variables de boucle en namespace : {sorted(CURRENT['ns_vars'])}", file=sys.stderr)
    return "{% set _ns = namespace() %}" + _convert(src)


def _convert(src):
    out, pos, stack = [], 0, []
    for m in BLOCK_RX.finditer(src):
        out.append(raw_text(src[pos:m.start()]))
        pos = m.end()
        code = m.group(1)
        if m.group(0).startswith("<?="):
            try:
                out.append("{{ " + conv_expr(code.strip().rstrip(";")) + " }}")
            except SyntaxError as e:
                out.append(f"{{# FIXME php ({e}): {code.strip()} #}}")
            continue
        for st in split_statements(code):
            try:
                out.append(conv_statement(st, stack))
            except (SyntaxError, ValueError, IndexError) as e:
                out.append(f"{{# FIXME php ({e}): {st} #}}")
    out.append(raw_text(src[pos:]))
    return "".join(out)


if __name__ == "__main__":
    # python tools/php2jinja.py <fichier.php relatif à la racine du dépôt>…  → digita/templates/…html
    import pathlib
    for rel in sys.argv[1:]:
        dst = pathlib.Path(__file__).resolve().parent.parent / "digita" / "templates" / (rel[:-4] + ".html")
        dst.parent.mkdir(parents=True, exist_ok=True)
        out = convert((ROOT / rel).read_text(encoding="utf-8"), rel)
        dst.write_text(out, encoding="utf-8")
        print(f"{rel} → {dst.relative_to(ROOT)}  ({out.count('FIXME')} FIXME)")
