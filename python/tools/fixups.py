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

def preg_match_capture(s):
    return re.sub(r"\{# FIXME php: preg_match\(('[^']*'), \$(\w+), \$matches\) #\}",
                  r"{% set matches = preg_matches(\1, \2) %}", s)


edit("app/Views/formations/learn-content.html", preg_match_capture)


def count_completed(s):
    for neg, flt in (("!", "rejectattr"), ("", "selectattr")):
        s = s.replace("{# FIXME php (expression inattendue : op:{): count(array_filter($formations, function($f) "
                      "{ return %s$f['completed']; })) #}" % neg,
                      "{{ count(php_values(formations)|%s('completed')|list) }}" % flt)
    return s


edit("app/Views/formations/my-formations-content.html", count_completed)

left = [str(p.relative_to(T)) for p in T.rglob("*.html") if "FIXME" in p.read_text(encoding="utf-8")]
print("FIXME restants :", left or "aucun")


edit("app/Views/layouts/main.html", lambda s: re.sub(r"\{% set projectRoot = [^%]*%\}", "", s))

edit("app/Views/layouts/admin.html", lambda s: s.replace(
    "{# FIXME php: require __DIR__ . '/../' . $contentView . '.php' #}",
    "{% include 'app/Views/' ~ contentView ~ '.html' %}"))


def dashboard_date(s):
    # $date = new DateTime() puis $date->format(…) : même chose avec date() du jour.
    s = re.sub(r"\{# FIXME php \(reste non analysé[^#]*\$date = new DateTime\(\) #\}", "", s)
    s = s.replace("jours[date.format('w')]", "jours[intval(date('w'))]").replace("date.format('d')", "date('d')")
    s = s.replace("mois[intval(date.format('n'))]", "mois[intval(date('n'))]").replace("date.format('Y')", "date('Y')")
    return s


edit("app/Views/admin/dashboard.html", dashboard_date)
