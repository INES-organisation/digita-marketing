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
    # heure des messages écrits pendant le parcours (« 09/10 14:13 ») : PHP et Python passent à des minutes différentes
    (re.compile(r"\b\d\d/\d\d \d\d:\d\d\b"), "JJ/MM HH:MM"),
    # en dernier : aussi appliqué seul aux réponses JSON
    (re.compile(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d"), "TIMESTAMP"),
]
GENERIC_500 = "Une erreur est survenue. Veuillez réessayer plus tard."


def same_failure(a, b):
    """Exception non gérée : le PHP affiche son gestionnaire d'erreur (200), le Python le message générique (500)."""
    return (a[3] == 200 and b[3] == 500 and isinstance(a[-1], list) and isinstance(b[-1], list)
            and "Exception non gérée" in "".join(a[-1]) and b[-1] == [GENERIC_500])


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

    def call(method, path, data=None, params=None, page=False, files=None, content=None):
        r = c.request(method, path, data=data, params=params, files=files, content=content)
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

    # paiement (sans clé Stripe des deux côtés ; codes promo de tools/fixtures_forms.sql)
    anon = c
    c = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity7"})
    call("GET", "/formations/checkout/1")
    call("GET", "/mes-commandes")
    c = anon
    call("GET", "/formations/checkout/1", page=True)
    for promo in ("BIENVENUE20", "fixe50", "bidon", "EXPIRE", "INACTIF", "EPUISE"):
        call("GET", "/formations/checkout/1", params={"promo": promo}, page=True)
    call("GET", "/formations/checkout/99999", page=True)
    call("GET", "/formations/checkout/2")
    for data in ({}, {"code": "bidon"}, {"code": "BIENVENUE20", "formation_id": "1"},
                 {"code": "FIXE50", "formation_id": "1"}, {"code": "FIXE50"}, {"code": "OFFERT", "formation_id": "3"}):
        call("POST", "/api/validate-promo", data)
    call("POST", "/api/validate-promo", params={"code": "BIENVENUE20", "formation_id": "1"})
    call("POST", "/formations/checkout/1", {"promo_code": "BIENVENUE20"})
    call("GET", paid, page=True)
    call("POST", "/formations/checkout/99999")
    call("POST", "/formations/checkout/1", {"promo_code": "OFFERT"})
    call("GET", paid + "/learn", page=True)
    call("GET", "/formations/checkout/1")
    call("GET", "/mes-commandes", page=True)
    for path in ("/mes-commandes/1", "/mes-commandes/2", "/mes-commandes/999", "/facture/1", "/facture/2"):
        call("GET", path, page=True)
    call("GET", "/paiement/annulation", params={"order_id": "1"}, page=True)
    call("GET", "/paiement/annulation", params={"order_id": "2"}, page=True)
    call("GET", "/paiement/annulation", page=True)
    call("GET", "/paiement/succes", params={"session_id": "cs_test"}, page=True)
    call("GET", "/mes-commandes", page=True)
    call("POST", "/webhook/stripe", {"x": "1"})

    # projets clients (projet 9401 et administrateur 9501 de tools/fixtures_forms.sql)
    c = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity8"})
    call("GET", "/projets/brief", page=True)
    for path in ("/espace-client", "/espace-client/projet/9401"):
        call("GET", path)
    call("POST", "/projets/brief", {"project_type": "website", "title": "x", "brief": "y"})
    call("POST", "/espace-client/projet/9401/message", {"message": "x"})
    call("POST", "/webhook/webox", content=b'{"event":"website.generated"}')
    for data, params in (({}, None), ({"project_type": "ecommerce", "pages": "12", "urgent": "1"}, None),
                         ({}, {"project_type": "landing", "pages": "8", "multilingual": "on"}),
                         ({"project_type": "inconnu", "pages": "abc"}, None),
                         ({"project_type": "app", "pages": "3", "multilingual": "1", "urgent": "1"}, None),
                         ({"pages": "0"}, {"pages": "20", "urgent": "0"})):
        call("POST", "/api/project-quote", data, params)
    t = tok("/inscription")
    c.post("/inscription", data={"_csrf_token": t, "email": "client@example.com", "password": "motdepasse1",
                                 "password2": "motdepasse1"})
    call("GET", "/espace-client", page=True)
    call("POST", "/projets/brief", {"project_type": "website", "title": " ", "brief": "Mon brief"})
    call("GET", "/projets/brief", page=True)
    call("POST", "/projets/brief", {
        "project_type": "ecommerce", "title": " Boutique bio ", "brief": "Vendre des légumes",
        "business_name": " Ferme ", "business_type": "Agriculture", "target_audience": "Locaux", "style": "nature",
        "colors": "vert,,marron,", "pages": "9", "features[]": ["panier", "blog"], "content_tone": "chaleureux",
        "existing_url": "https://exemple.fr", "competitors": "aucun", "deadline": "2025-06-01", "budget": "2000",
        "urgent": "1"})
    call("GET", "/espace-client/projet/1", page=True)
    call("GET", "/espace-client/projet/1", page=True)
    call("POST", "/projets/brief", {"project_type": "landing", "title": "Page", "brief": "Promo", "colors": ",rouge"})
    call("GET", "/espace-client/projet/2", page=True)
    call("GET", "/espace-client/projet/9401", page=True)
    call("GET", "/espace-client/projet/1abc", page=True)
    call("POST", "/espace-client/projet/9401/message", {"message": "intrus"})
    call("POST", "/espace-client/projet/1/message", {"message": "   "})
    call("POST", "/espace-client/projet/1/message", {"message": " Bonjour "})
    call("POST", "/espace-client/projet/1/message", {"message": "Fichier refusé"},
         files={"attachment": ("script.php", b"<?php echo 1;", "text/plain")})
    call("GET", "/espace-client/projet/1", page=True)
    call("GET", "/espace-client", page=True)
    call("POST", "/webhook/webox", content=b'{"event":"website.generated"}')
    c = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity9"})
    t = tok("/connexion")
    c.post("/connexion", data={"_csrf_token": t, "email": "admin-test@example.com", "password": "adminpass1"})
    for body in (b"", b"pas du json", b"[]", b'{"event":"autre"}', b'{"event":"website.generated","data":{}}',
                 b'{"event":"website.generated","data":{"project_id":"inconnu"}}',
                 b'{"event":"website.generated","data":{"project_id":"wbx-9401","preview_url":"https://p.example"}}',
                 b'{"event":"website.error","data":{"project_id":"wbx-9401"}}',
                 b'{"event":"website.deployed","data":{"project_id":"wbx-9401","production_url":"https://s.example"}}'):
        call("POST", "/webhook/webox", content=body)
    call("GET", "/espace-client", page=True)
    call("GET", "/espace-client/projet/9401", page=True)

    # administration (compte 9501 encore connecté ; contacts et abonnés de tools/fixtures_forms.sql)
    admin = c
    c = httpx.Client(base_url=base, follow_redirects=False, headers={"User-Agent": "parity10"})
    for path in ("/admin/dashboard", "/admin/contacts/read", "/admin/contacts/read?id=9601", "/admin/projects/9401"):
        call("GET", path)
    call("POST", "/admin/articles/store", {"title": "x"})
    t = tok("/connexion")
    c.post("/connexion", data={"_csrf_token": t, "email": "client@example.com", "password": "motdepasse1"})
    for path in ("/admin/dashboard", "/admin/media", "/admin/contacts/read?id=9601"):
        call("GET", path)
    call("POST", "/admin/projects/task/update", {"task_id": "9431", "status": "todo"})
    c = admin
    for path in ("/admin/dashboard", "/admin/contacts", "/admin/newsletters", "/admin/webhooks", "/admin/campaigns",
                 "/admin/articles", "/admin/formations", "/admin/media", "/admin/projects"):
        call("GET", path, page=True)
    call("GET", "/admin/contacts/read", params={"id": "0"})
    call("GET", "/admin/contacts/read", params={"id": "9601"})
    call("GET", "/admin/contacts/replied", params={"id": "9602"})
    call("GET", "/admin/contacts", page=True)
    call("GET", "/admin/newsletters/export")
    call("POST", "/admin/webhooks/save", {"contact_url": "https://x"})
    call("POST", "/admin/webhooks/test/contact")
    call("GET", "/admin/campaigns/new")
    call("POST", "/admin/campaigns/delete/3")
    for params in ({"page": "2"}, {"page": "0"}, {"status": "draft"}, {"category": "3"}, {"q": "SEO"},
                   {"q": "reseaux", "status": "published", "page": "abc"}, {"category": "abc"}):
        call("GET", "/admin/articles", params=params, page=True)
        call("GET", "/admin/formations", params=params, page=True)
    call("GET", "/admin/articles/new", page=True)
    call("POST", "/admin/articles/store", {"title": "  "})
    call("GET", "/admin/articles/new", page=True)
    call("POST", "/admin/articles/store", {"title": " Été à La Réunion : ça déçoit ? ", "content": "<p>Texte</p>",
                                           "category_id": "3", "status": "published", "meta_title": "",
                                           "featured_image_url": " /img/a.png "})
    call("POST", "/admin/articles/store", {"title": "Été à La Réunion : ça déçoit ?", "status": "draft",
                                           "category_id": ""})
    out.append(["articles", c.get("/admin/articles", params={"q": "Réunion : ça"}).status_code])
    call("GET", "/admin/articles", params={"q": "ça déçoit"}, page=True)
    call("GET", "/admin/articles/edit/999999")
    call("GET", "/admin/articles/edit/1", page=True)
    call("POST", "/admin/articles/update/1", {"title": ""})
    call("GET", "/admin/articles/edit/1", page=True)
    call("POST", "/admin/articles/update/999999", {"title": "x"})
    call("POST", "/admin/articles/delete/999999")
    call("POST", "/admin/articles/upload-image")
    call("POST", "/admin/articles/upload-image", files={"file": ("x.txt", b"x", "text/plain")})
    call("GET", "/admin/formations/new", page=True)
    call("POST", "/admin/formations/store", {"title": ""})
    call("POST", "/admin/formations/store", {"title": "Formation Admin ÉÀ", "price": "49,90", "level": "avance",
                                             "category_id": "2", "description": "<p>Desc</p>"})
    call("GET", "/admin/formations/edit/999999")
    call("GET", "/admin/formations/edit/2", page=True)
    call("POST", "/admin/formations/update/2", {"title": ""})
    call("POST", "/admin/formations/delete/999999")
    call("GET", "/admin/formations/edit/2", page=True)
    call("POST", "/admin/media/upload")
    call("POST", "/admin/media/upload", files={"files[]": ("a.exe", b"MZ", "application/octet-stream")})
    call("POST", "/admin/media/delete")
    call("POST", "/admin/media/delete", {"filename": "../../index.php"})
    call("GET", "/admin/analytics", page=True)
    call("GET", "/admin/analytics", params={"period": "7"}, page=True)
    for params in ({}, {"view": "list"}, {"view": "list", "status": "pending"}, {"view": "list", "type": "website"}):
        call("GET", "/admin/projects", params=params, page=True)
    call("GET", "/admin/projects/999999")
    call("GET", "/admin/projects", page=True)
    call("GET", "/admin/projects/9402", page=True)
    call("POST", "/admin/projects/9402/status", {"status": "bidon"})
    call("POST", "/admin/projects/9402/status", {"status": "review", "note": " Relecture "})
    call("POST", "/admin/projects/9402/message", {"message": " "})
    call("POST", "/admin/projects/9402/message", {"message": "Votre maquette est prête"})
    call("POST", "/admin/projects/9402/note", {"admin_notes": " Client pressé "})
    call("POST", "/admin/projects/9402/task", {"task_title": ""})
    call("POST", "/admin/projects/9402/task", {"task_title": "Logo", "task_description": "SVG"})
    call("POST", "/admin/projects/9402/task", {"task_title": "Textes"})
    for data in ({}, {"task_id": "9431", "status": "bidon"}, {"task_id": "9432", "status": "in_progress"}):
        call("POST", "/admin/projects/task/update", data)
    call("POST", "/admin/projects/9402/price", {"price": "1234.5"})
    call("POST", "/admin/projects/9402/generate")
    call("POST", "/admin/projects/999999/generate")
    call("GET", "/admin/projects/9402", page=True)
    call("GET", "/admin/projects", params={"view": "list"}, page=True)
    call("GET", "/admin/dashboard", page=True)
    call("GET", "/espace-client/projet/9402")
    call("POST", "/admin/articles/delete/1")
    call("GET", "/admin/articles", page=True)
    call("POST", "/admin/formations/delete/2")
    call("GET", "/admin/formations", page=True)
    call("GET", "/admin/logout")
    call("GET", "/admin/dashboard")
    return out


res = {k: run(v) for k, v in SERVERS.items()}
bad = 0
known = 0
for a, b in zip(res["php"], res["py"]):
    if a == b:
        print("OK  ", str(a)[:300])
    elif same_failure(a, b):
        print("OK* ", str(a[:3]), "erreur PHP (exception) = erreur 500 en Python")
        known += 1
        continue
    elif isinstance(a[-1], list) and isinstance(b[-1], list):
        print("DIFF", a[:-1], "\n  " + "\n  ".join(difflib.unified_diff(a[-1], b[-1], "php", "py", n=1, lineterm="")))
    else:
        print("DIFF", f"\n  php={a}\n  py ={b}")
    bad += a != b
print(f"formulaires : {len(res['php']) - bad - known} identiques, {known} en erreur des deux côtés, {bad} différentes")
sys.exit(1 if bad else 0)
