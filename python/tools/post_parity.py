"""Compare les réponses des formulaires et API publiques entre PHP et Python.

Couvre : demande d'audit, connexion, inscription, chatbot (sans clé OpenAI : réponses de
secours), rendez-vous, outils gratuits (audit SEO sur une page locale, ROI, générateurs IA
sans clé) et suivi analytics. L'audit SEO analyse une page servie par ce script ; le site
Python doit donc tourner avec DIGITA_AUDIT_ALLOW_PRIVATE=1 (adresse locale).

Usage : post_parity.py URL_PHP URL_PYTHON. Les deux sites doivent partir de la même base.
Code de sortie 1 si une réponse diffère.
"""
import re
import sys

import difflib
import http.server
import os
import threading

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parity import normalize  # noqa: E402

LOAD_TIME = [
    (re.compile(r"&mdash; [\d.]+s"), "&mdash; Ns"),
    (re.compile(r"\d+(\.\d+)?s( \(idéal &lt; 2s\)| \(trop lent\))?</"), "Ns</"),
    (re.compile(r'"load_time":[\d.]+'), '"load_time":N'),
    (re.compile(r"https?://(127\.0\.0\.1|localhost)(:\d+)?"), "http://HOST"),
    (re.compile(r"DM-\d{4}-[0-9A-F]{8}"), "DM-NUMERO"),
    (re.compile(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d"), "TIMESTAMP"),
]


SAMPLE = ("<html><head><title>Agence de marketing digital à La Réunion</title>"
          '<meta name="description" content="Courte description">'
          '<meta name="viewport" content="width=device-width"></head><body>'
          "<h1>Titre <em>principal</em></h1><h1>Second</h1>"
          '<img src="a.png" alt="A"><img src="b.png"><img src="c.png" alt="">'
          '<a href="/x">x</a><a href="https://ailleurs.fr">y</a><a href="http://127.0.0.1/z">z</a>'
          "</body></html>").encode()


class SampleHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/redirect":
            self.send_response(301)
            self.send_header("Location", "/page")
            self.end_headers()
            return
        ok = self.path == "/page"
        self.send_response(200 if ok else 404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(SAMPLE if ok else b"not found")

    def log_message(self, *a):
        pass


SAMPLE_SERVER = http.server.ThreadingHTTPServer(("127.0.0.1", 0), SampleHandler)
threading.Thread(target=SAMPLE_SERVER.serve_forever, daemon=True).start()
SAMPLE_URL = f"http://127.0.0.1:{SAMPLE_SERVER.server_port}"


def clean(text):
    for rx, rep in LOAD_TIME:
        text = rx.sub(rep, text)
    return normalize(text)

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

    # chatbot, sans clé OpenAI des deux côtés
    c = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity5"})

    def call(method, path, data=None, params=None, page=False):
        r = c.request(method, path, data=data, params=params)
        body = clean(r.text) if page else re.sub(r'"conversation_id":"?\d+"?', '"conversation_id":N',
                                                  LOAD_TIME[-1][0].sub("TIMESTAMP", r.text))
        loc = r.headers.get("location")
        if loc:
            loc = re.sub(r"^https?://[^/]+", "", loc)
        out.append([method, path, data, r.status_code, loc, r.headers.get("content-type", "").split(";")[0]
                    if r.status_code != 302 else "", body if r.status_code != 302 else ""])

    call("POST", "/api/chatbot/message", {"message": "  "})
    for msg in ("Bonjour", "Quel est votre TARIF ?", "Je veux une formation", "audit seo", "mon site web",
                "un rdv svp", "autre chose", "Coût d'un projet"):
        call("POST", "/api/chatbot/message", {"message": msg, "session_id": "parity-chat", "page": "/"})
    call("GET", "/api/chatbot/history", params={"session_id": "inconnue"})
    out.append(["history", len(c.get("/api/chatbot/history", params={"session_id": "parity-chat"}).json()["messages"])])
    call("POST", "/api/chatbot/qualify", {})
    call("POST", "/api/chatbot/qualify", {"conversation_id": "abc"})
    call("POST", "/api/chatbot/appointment", {"name": "A"})
    call("POST", "/api/chatbot/appointment", {"name": "A", "email": "pas-un-mail", "date": "2026-11-02", "time_slot": "09:00"})
    call("POST", "/api/chatbot/appointment", {"name": " Anne ", "email": "anne@example.com", "date": "2026-11-02",
                                              "time_slot": "09:00", "subject": "Site"})
    call("POST", "/api/chatbot/appointment", {"name": "Bob", "email": "bob@example.com", "date": "2026-11-02", "time_slot": "09:00"})
    call("GET", "/api/chatbot/slots", params={"date": "2026-11-02"})
    call("GET", "/api/chatbot/slots", params={"date": "2026-11-03"})

    # outils
    call("POST", "/outils/audit-seo", {"url": "pas une url"}, page=True)
    call("POST", "/outils/audit-seo", {"url": SAMPLE_URL + "/page"}, page=True)
    call("POST", "/outils/audit-seo", {"url": SAMPLE_URL + "/redirect"}, page=True)
    call("POST", "/outils/audit-seo", {"url": SAMPLE_URL + "/absente"}, page=True)
    call("POST", "/outils/meta-generator", {"page_title": ""}, page=True)
    call("POST", "/outils/meta-generator", {"page_title": "Mon titre", "page_content": "Texte"}, page=True)
    call("POST", "/outils/calendrier-editorial", {"niche": " "}, page=True)
    call("POST", "/outils/calendrier-editorial", {"niche": "Immobilier", "duration": "2 mois"}, page=True)
    call("POST", "/outils/roi-calculator", {}, page=True)
    call("POST", "/outils/roi-calculator", {"budget": "2500", "cpc": "0,8", "conversion_rate": "3.5",
                                            "avg_order_value": "120", "margin": "40"}, page=True)
    call("POST", "/outils/roi-calculator", {"budget": "0"}, page=True)
    call("POST", "/api/roi-calculate", {"budget": "1000", "cpc": "1.3"})
    call("POST", "/api/roi-calculate", {"budget": "50", "cpc": "7"})
    call("POST", "/api/roi-calculate", {"cpc": "-1"})

    # analytics : réservé aux administrateurs
    call("POST", "/api/analytics/pageview", {"page_url": "/"})
    call("POST", "/api/analytics/conversion", {"event_type": "contact"})
    c = c3  # connecté avec un compte « user »
    call("POST", "/api/analytics/pageview", {"page_url": "/"})

    # espace élève (données de tools/fixtures_forms.sql : formation 2 gratuite, quiz 9001)
    free = "/formations/formation-cration-et-planification-de-contenu"
    paid = "/formations/formation-community-management"
    c = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity6"})
    for path in ("/mes-formations", free + "/learn", "/formations/quiz/9001", "/formations/2/certificate"):
        call("GET", path)
    call("POST", free + "/inscription")
    call("POST", "/formations/complete-lesson", {"lesson_id": "21", "formation_id": "2"})
    t = tok("/inscription")
    c.post("/inscription", data={"_csrf_token": t, "email": "eleve@example.com", "password": "motdepasse1",
                                 "password2": "motdepasse1"})
    call("GET", "/mes-formations", page=True)
    call("POST", paid + "/inscription")
    call("POST", "/formations/inexistante/inscription")
    call("GET", free + "/learn")
    call("GET", free, page=True)
    call("POST", "/formations/2/review", {"rating": "4"})
    call("POST", free + "/inscription")
    call("GET", free, page=True)
    call("POST", free + "/inscription")
    call("GET", free + "/learn", page=True)
    call("GET", free + "/learn", params={"lesson": "23"}, page=True)
    call("GET", free + "/learn", params={"lesson": "abc"}, page=True)
    call("GET", "/formations/2/certificate")
    call("GET", free + "/learn", page=True)
    call("POST", "/formations/complete-lesson", {"lesson_id": "21"})
    for lesson in (21, 22, 22, 23):
        call("POST", "/formations/complete-lesson", {"lesson_id": str(lesson), "formation_id": "2"})
    call("GET", free + "/learn", params={"lesson": "24"}, page=True)
    call("GET", "/formations/quiz/9001", page=True)
    call("GET", "/formations/quiz/424242", page=True)
    call("POST", "/formations/quiz/9001/submit", {"question_9101": "9201", "question_9102[]": ["9204", "9203"],
                                                 "question_9103": "9207"})
    call("GET", "/formations/quiz/9001/results", page=True)
    call("GET", "/formations/quiz/9001/results", page=True)
    call("POST", "/formations/quiz/9001/submit", {"question_9101": "9202"})
    call("POST", "/formations/quiz/9001/submit", {"question_9101": "9201"})
    call("GET", "/formations/quiz/9001", page=True)
    call("POST", "/formations/2/review", {"rating": "9", "title": " Super ", "comment": "Très bien"})
    call("POST", "/formations/2/review", {"rating": "0", "title": "Bof"})
    call("GET", free, page=True)
    for lesson in range(24, 41):
        call("POST", "/formations/complete-lesson", {"lesson_id": str(lesson), "formation_id": "2"})
    call("GET", free + "/learn", params={"lesson": "40"}, page=True)
    call("GET", "/formations/2/certificate", page=True)
    call("GET", "/formations/2abc/certificate", page=True)
    call("GET", "/mes-formations", page=True)
    return out


res = {k: run(v) for k, v in SERVERS.items()}
bad = 0
for a, b in zip(res["php"], res["py"]):
    if a == b:
        print("OK  ", str(a)[:300])
    elif isinstance(a[-1], list) and isinstance(b[-1], list):
        print("DIFF", a[:-1], "\n  " + "\n  ".join(difflib.unified_diff(a[-1], b[-1], "php", "py", n=1, lineterm="")))
    else:
        print("DIFF", f"\n  php={a}\n  py ={b}")
    bad += a != b
print(f"formulaires : {len(res['php']) - bad} identiques, {bad} différentes")
sys.exit(1 if bad else 0)
