"""Outil de parité PHP ↔ Python.

Liste toutes les URL publiques (pages fixes + chaque article, catégorie et formation
en base), télécharge le HTML depuis deux serveurs et compare le rendu normalisé.

    python tools/parity.py urls --db mysql+pymysql://root:root@127.0.0.1/digita > urls.txt
    python tools/parity.py snap http://127.0.0.1:8081 urls.txt snaps/php
    python tools/parity.py snap http://127.0.0.1:8000 urls.txt snaps/py
    python tools/parity.py diff snaps/php snaps/py
"""
import argparse
import datetime
import difflib
import hashlib
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

STATIC_PAGES = [
    "/", "/blog", "/blog/search?q=seo", "/formations", "/formations/search?q=seo",
    "/boutique", "/solutions", "/solution", "/a-propos", "/services", "/catalogue",
    "/portfolio", "/equipe", "/contact", "/support", "/tarifs", "/outils", "/formation",
    "/mentions-legales", "/politique-confidentialite", "/conditions-generales", "/cookies",
    "/connexion", "/inscription", "/outils/audit-seo", "/outils/meta-generator",
    "/outils/roi-calculator", "/outils/calendrier-editorial", "/certificat/verifier",
    "/page-qui-n-existe-pas",
]


def list_urls(db_url):
    from sqlalchemy import create_engine, text

    eng = create_engine(db_url)
    urls = list(STATIC_PAGES)
    with eng.connect() as c:
        for (slug,) in c.execute(text("SELECT slug FROM service_categories ORDER BY id")):
            urls += [f"/blog/categorie/{slug}", f"/formations/categorie/{slug}"]
        for (slug,) in c.execute(text("SELECT slug FROM blog_articles WHERE status='published' ORDER BY id")):
            urls.append(f"/blog/{slug}")
        for (slug,) in c.execute(text("SELECT slug FROM formations WHERE status='published' ORDER BY id")):
            urls += [f"/formations/{slug}", f"/formations/{slug}/landing"]
    return urls


def fname(url):
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", url.strip("/")) or "_home"
    return safe[:120] + "-" + hashlib.md5(url.encode()).hexdigest()[:6] + ".html"


def fetch(base, url):
    try:
        with urllib.request.urlopen(base + url, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:  # noqa: BLE001
        return 0, str(e).encode()


def snap(base, urls_file, out, workers=1):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    urls = [u.strip() for u in Path(urls_file).read_text().splitlines() if u.strip()]

    def one(u):
        status, body = fetch(base.rstrip("/"), u)
        (out / fname(u)).write_bytes(f"<!-- STATUS {status} {u} -->\n".encode() + body)
        return status

    # Séquentiel par défaut : les compteurs de vues dépendent de l'ordre de visite.
    with ThreadPoolExecutor(workers) as ex:
        statuses = list(ex.map(one, urls))
    print(f"{len(urls)} pages, statuts: { {s: statuses.count(s) for s in set(statuses)} }")


# Parties du HTML qui changent d'une requête à l'autre (jetons, compteurs, dates du jour).
VOLATILE = [
    (re.compile(r"\?v=\d+"), "?v="),
    (re.compile(r"https?://(127\.0\.0\.1|localhost)(:\d+)?"), "http://HOST"),
    # updated_at est réécrit à chaque vue d'article : seule la date du jour est masquée.
    (re.compile(r'"dateModified": "%s \d\d:\d\d:\d\d"' % datetime.date.today()), '"dateModified": "TODAY"'),
    (re.compile(r'name="_?csrf_token" value="[^"]*"'), 'name="csrf_token" value=""'),
    (re.compile(r'(<meta name="csrf-token" content=")[^"]*'), r"\1"),
]


def normalize(text):
    for rx, rep in VOLATILE:
        text = rx.sub(rep, text)
    lines = [ln.strip() for ln in text.splitlines()]
    return [ln for ln in lines if ln]


def diff(a_dir, b_dir, show=3):
    a_dir, b_dir = Path(a_dir), Path(b_dir)
    same, different, missing = 0, [], []
    for fa in sorted(a_dir.glob("*.html")):
        fb = b_dir / fa.name
        if not fb.exists():
            missing.append(fa.name)
            continue
        la = normalize(fa.read_text(errors="replace"))
        lb = normalize(fb.read_text(errors="replace"))
        if la == lb:
            same += 1
        else:
            different.append((fa.name, la, lb))
    print(f"identiques: {same}  différentes: {len(different)}  manquantes: {len(missing)}")
    # Regroupe les pages par première ligne divergente pour traiter les écarts par famille.
    groups = {}
    for name, la, lb in different:
        d = [ln for ln in difflib.unified_diff(la, lb, n=0, lineterm="")
             if ln[:1] in "+-" and not ln.startswith(("+++", "---"))]
        groups.setdefault(d[0][:120] if d else "?", []).append((name, d))
    for key, items in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:show]:
        print(f"\n===== {len(items)} page(s), ex. {items[0][0]}")
        for ln in items[0][1][:12]:
            print("   ", ln[:220])
    return not different and not missing


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("urls")
    u.add_argument("--db", required=True)
    s = sub.add_parser("snap")
    s.add_argument("base")
    s.add_argument("urls_file")
    s.add_argument("out")
    s.add_argument("--workers", type=int, default=1)
    d = sub.add_parser("diff")
    d.add_argument("a")
    d.add_argument("b")
    d.add_argument("--show", type=int, default=10)
    a = p.parse_args()
    if a.cmd == "urls":
        print("\n".join(list_urls(a.db)))
    elif a.cmd == "snap":
        snap(a.base, a.urls_file, a.out, a.workers)
    else:
        sys.exit(0 if diff(a.a, a.b, a.show) else 1)


if __name__ == "__main__":
    main()
