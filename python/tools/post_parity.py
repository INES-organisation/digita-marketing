"""Compare les réponses des formulaires (audit, connexion, inscription) entre PHP et Python.

Usage : post_parity.py URL_PHP URL_PYTHON. Les deux sites doivent partir de la même base.
Code de sortie 1 si une réponse diffère.
"""
import re
import sys

import httpx

SERVERS = {"php": sys.argv[1], "py": sys.argv[2]}
TOK = re.compile(r'name="_csrf_token" value="([0-9a-f]+)"')

def run(base):
    out = []
    c = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity"})
    def tok(path):
        m = TOK.search(c.get(path).text); return m.group(1) if m else None
    def post(path, data, follow):
        r = c.post(path, data=data)
        line = [path, r.status_code, r.headers.get("location"), r.headers.get("content-type", "").split(";")[0] if r.status_code != 302 else "",
                r.text if r.status_code != 302 else ""]
        if follow and r.status_code == 302 and r.headers["location"] in ("/connexion", "/inscription"):
            page = c.get(r.headers["location"]).text
            m = re.search(r"Tous les champs[^<]*|Identifiants[^<]*|Adresse email[^<]*|Les mots de passe[^<]*|Le mot de passe doit[^<]*|Cet email[^<]*", page)
            line.append(m.group(0) if m else None)
        out.append(line)
    # audit
    post("/api/audit-request", {}, False)
    post("/api/audit-request", {"name": "0", "email": "a@b.c"}, False)
    post("/api/audit-request", {"name": "Jean Été", "email": "jean@example.com"}, False)
    post("/api/audit-request", {"name": "Zoé", "email": "z@example.com", "website": "https://z.fr/a"}, False)
    post("/api/audit-request", {"name": "x" * 150, "email": "long@example.com"}, False)
    # auth
    post("/connexion", {}, False)
    post("/connexion", {"_csrf_token": "bad", "email": "a", "password": "b"}, False)
    t = tok("/connexion")
    post("/connexion", {"_csrf_token": t, "email": " ", "password": "x"}, True)
    post("/connexion", {"_csrf_token": t, "email": "nobody@example.com", "password": "x"}, True)
    t = tok("/inscription")
    post("/inscription", {"_csrf_token": t, "email": "", "password": "a", "password2": "a"}, True)
    post("/inscription", {"_csrf_token": t, "email": "pas-un-mail", "password": "abcdefgh", "password2": "abcdefgh"}, True)
    post("/inscription", {"_csrf_token": t, "email": "n@example.com", "password": "abcdefgh", "password2": "abcdefgX"}, True)
    c2 = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity2"}); c = c2
    t = tok("/inscription")
    post("/inscription", {"_csrf_token": t, "email": "n@example.com", "password": "abc", "password2": "abc"}, True)
    post("/inscription", {"_csrf_token": t, "email": "Nouveau@Example.com", "password": "motdepasse1", "password2": "motdepasse1"}, True)
    out.append(["session after register -> /connexion", c.get("/connexion").status_code, c.get("/connexion").headers.get("location")])
    c3 = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity3"}); c = c3
    t = tok("/inscription")
    post("/inscription", {"_csrf_token": t, "email": "nouveau@example.com", "password": "motdepasse1", "password2": "motdepasse1"}, True)
    t = tok("/connexion")
    post("/connexion", {"_csrf_token": t, "email": "Nouveau@Example.com", "password": "mauvais"}, True)
    post("/connexion", {"_csrf_token": t, "email": "Nouveau@Example.com", "password": "motdepasse1"}, False)
    # rate limit: login 5 / 15 min
    c4 = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity4"}); c = c4
    t = tok("/connexion")
    for i in range(6):
        post("/connexion", {"_csrf_token": t, "email": "x@example.com", "password": "x"}, False)
    out[-1][-1] = re.sub(r'"retry_after":\d+', '"retry_after":N', out[-1][-1])
    return out


res = {k: run(v) for k, v in SERVERS.items()}
bad = 0
for a, b in zip(res["php"], res["py"]):
    print("OK  " if a == b else "DIFF", a if a == b else f"\n  php={a}\n  py ={b}")
    bad += a != b
print(f"formulaires : {len(res['php']) - bad} identiques, {bad} différentes")
sys.exit(1 if bad else 0)
