"""Corrections manuelles appliquées après php2jinja (constructions PHP non converties)."""
import re
from pathlib import Path

T = Path(__file__).resolve().parent.parent / "digita" / "templates"


def edit(rel, fn):
    p = T / rel
    s = p.read_text(encoding="utf-8")
    new = fn(s)
    if new == s:
        raise SystemExit(f"fixup sans effet : {rel}")
    p.write_text(new, encoding="utf-8")


def unset_session(s):
    return re.sub(r"\{# FIXME php: unset\(\$_SESSION\['(\w+)'\]\) #\}", r"{% do _SESSION.pop('\1', none) %}", s)


for rel in ["app/Views/outils/meta-generator-content.html", "app/Views/outils/editorial-calendar-content.html",
            "app/Views/outils/seo-audit-content.html", "app/Views/formations/show-content.html"]:
    edit(rel, unset_session)

edit("app/Views/layouts/main.html", lambda s: s.replace(
    "{# FIXME php: if (isset($canonical)) $canonicalUrl = $canonical #}",
    "{% if isset(canonical) %}{% set canonicalUrl = canonical %}{% endif %}"))


def layout(s):
    s = re.sub(r"\{# FIXME php \(reste non analysé[^#]*?if \(isset\(\$(extraCss|extraJs)\)\) foreach \(\$\w+ as \$(\w+)\): #\}(.*?)\{% endif %\}",
               lambda m: "{%% if isset(%s) %%}{%% for %s in php_values(%s) %%}%s{%% endfor %%}{%% endif %%}"
               % (m.group(1), m.group(2), m.group(1), m.group(3)), s, flags=re.S)
    return s


edit("templates/layout.html", layout)


def capture(s):
    s = s.replace("{# FIXME php: ob_start() #}", "{% set content_ %}")
    return re.sub(r"(\{% set extraJs = [^%]*%\})\{% set content_ = ob_get_clean\(\) %\}", r"{% endset %}\1", s)


edit("templates/home.html", capture)

for rel in ["app/Views/auth/login.html", "app/Views/auth/register.html"]:
    edit(rel, lambda s: re.sub(r"\{% if once\('app/Middleware/CsrfMiddleware.html'\) %\}\{% include [^%]*%\}\{% endif %\}", "", s))

left = [str(p.relative_to(T)) for p in T.rglob("*.html") if "FIXME" in p.read_text(encoding="utf-8")]
print("FIXME restants :", left or "aucun")


edit("app/Views/layouts/main.html", lambda s: re.sub(r"\{% set projectRoot = [^%]*%\}", "", s))
