"""Coque commune des pages, formulaires de contact et de newsletter."""
import re

import pytest
from starlette.testclient import TestClient

from digita import db, sessions
from digita.realisations import REALISATIONS
from digita.main import PUBLIC, app
from digita.routes import leads
from digita.services import email, ines


@pytest.fixture(autouse=True)
def memory_sessions(monkeypatch):
    """Sessions en mémoire : ces tests n'ont pas besoin de PostgreSQL."""
    store = {}
    monkeypatch.setattr(sessions, "_load", lambda sid: store.get(sid))
    monkeypatch.setattr(sessions, "_save", lambda sid, data, touch: store.__setitem__(sid, data))


def _client():
    return TestClient(app, base_url="https://digita.buzz")


def _token(html):
    return re.search(r'name="_csrf_token" value="([^"]+)"', html).group(1)


def test_inner_pages_use_horizontal_menu_and_services_bar():
    c = _client()
    for path in ("/contact", "/connexion", "/inscription", "/page-qui-n-existe-pas"):
        r = c.get(path)
        assert "navbar-site fixed-top" in r.text and 'class="sidebar-onglet-sidebar"' in r.text, path
        assert 'id="sidebar-agence"' in r.text and 'class="footer-premium"' in r.text, path
        assert 'class="sidebar-premium"' not in r.text, path
        assert 'href="/#hero-premium"' in r.text, path
    r = c.get("/page-qui-n-existe-pas")
    assert r.status_code == 404 and "Page introuvable" in r.text and "noindex" in r.text and "/diagnostic#consultant" in r.text
    assert 'aria-current="page"' in c.get("/contact").text


def test_home_uses_vertical_menu_anchored_on_sections():
    r = _client().get("/")
    assert 'class="sidebar-premium"' in r.text and 'class="footer-premium"' in r.text
    assert "navbar-site" not in r.text and "sidebar-onglet-sidebar" not in r.text
    for anchor in ("#besoins", "#realisations", "#methode", "#engagements", "#faq", "#hero-premium"):
        assert f'href="{anchor}"' in r.text, anchor
    assert 'id="realisations"' in r.text and "https://lp48.digita.buzz" in r.text
    for category in ("Sites web et landing", "Réseaux sociaux", "Publicité", "Automatisation", "Agents IA"):
        assert category in r.text, category
    # Offres et tarifs par catégorie, projets livrés
    for text in ("990 €", "390 €/mois", "290 €/mois", "490 €", "49 €/mois", "Ce que nous réalisons", "À voir en ligne"):
        assert text in r.text, text
    # Les cartes ne montrent que des pages réelles, toutes liées.
    for client in ("Projets livrés", "Lurel", "TTC France", "TTC Sales", "TatooModel"):
        assert client not in r.text, client
    assert all(item["url"] for cat in REALISATIONS for item in cat["items"])
    assert "Connexion" in r.text and "data-theme-toggle" in r.text and "Diagnostic gratuit" in r.text


def test_contact_form_is_saved_and_sent_to_ines(monkeypatch):
    saved, leads_sent = [], []
    monkeypatch.setattr(db, "execute", lambda sql, p=None: saved.append(p))
    monkeypatch.setattr(ines, "push_lead", lambda *a, **k: leads_sent.append(a + (k,)))
    monkeypatch.setattr(leads, "MIN_FILL_SECONDS", 0)  # le test envoie aussitôt la page ouverte
    monkeypatch.setattr(email, "send_new_contact_notification", lambda *a: True)
    c = _client()
    token = _token(c.get("/contact").text)

    assert c.post("/contact", data={"nom": "Ana", "email": "ana@example.com"}).status_code == 403  # sans jeton
    r = c.post("/contact", data={"_csrf_token": token, "nom": "Ana", "email": "pas-un-email", "message": "x"},
               follow_redirects=False)
    assert r.status_code == 302 and saved == []
    assert "adresse e-mail valide" in c.get("/contact").text

    r = c.post("/contact", data={"_csrf_token": token, "nom": "Ana", "email": "ana@example.com",
                                 "service": "ia", "message": "Bonjour"}, follow_redirects=False)
    assert r.status_code == 302
    assert saved[0][:2] == ["Ana", "ana@example.com"] and "Intelligence Artificielle" in saved[0][3]
    assert leads_sent[0][:3] == ("Ana", "ana@example.com", "contact")
    assert leads_sent[0][-1] == {"outreach": True, "tags": ("Intelligence Artificielle",)}
    assert "bien été envoyé" in c.get("/contact").text


def test_contact_spam_is_flagged_without_auto_reply(monkeypatch):
    """Démarchage SEO du 02/11/2026 : il recevait le premier contact, une affaire et un devis brouillon."""
    saved, leads_sent = [], []
    monkeypatch.setattr(db, "execute", lambda sql, p=None: saved.append(p))
    monkeypatch.setattr(ines, "push_lead", lambda *a, **k: leads_sent.append(a + (k,)))
    monkeypatch.setattr(email, "send_new_contact_notification", lambda *a: True)
    clock = [1_000_000]
    monkeypatch.setattr(leads.php, "time", lambda: clock[0])
    c = _client()
    pitch = ("Hello http://www.digita.buzz/,\r\n\r\nI checked your website. You have an impressive site but "
             "ranking is not good on Google, Yahoo and Bing.\r\n\r\nCan I send?\r\n\r\nWarm regards,\r\nRadhika")
    form = {"nom": "Radhika", "email": "r@example.com", "service": "strategie", "message": pitch}

    token = _token(c.get("/contact").text)
    clock[0] += 60
    r = c.post("/contact", data={"_csrf_token": token, **form}, follow_redirects=False)
    assert r.status_code == 302 and "bien été envoyé" in c.get("/contact").text  # même réponse au visiteur
    assert saved[-1][3].startswith("[Spam ?]") and "démarchage" in saved[-1][4]
    assert leads_sent[-1][-1] == {"tags": ("spam?", "Conseil & Stratégie")}  # pas d'outreach : fiche simple

    token = _token(c.get("/contact").text)  # envoyé en 1 s : suspect même sans mot-clé
    clock[0] += 1
    c.post("/contact", data={"_csrf_token": token, **form, "message": "Bonjour, un site vitrine ?"})
    assert "après l'ouverture" in saved[-1][4]

    token = _token(c.get("/contact").text)  # piège rempli : enregistré, rien vers INES
    clock[0] += 60
    n = len(leads_sent)
    c.post("/contact", data={"_csrf_token": token, **form, "message": "Bonjour", "site_web": "http://x"})
    assert "robot" in saved[-1][4] and len(leads_sent) == n

    token = _token(c.get("/contact").text)  # vrai prospect
    clock[0] += 60
    c.post("/contact", data={"_csrf_token": token, **form, "message": "Bonjour, je voudrais un devis pour mon site."})
    assert not saved[-1][3].startswith("[Spam") and leads_sent[-1][-1]["outreach"] is True


def test_newsletter_subscription(monkeypatch):
    saved = []
    monkeypatch.setattr(leads.db, "execute", lambda sql, p=None: saved.append(p))
    monkeypatch.setattr(ines, "push_lead", lambda *a, **k: None)
    c = _client()
    token = _token(c.get("/contact").text)
    assert c.post("/newsletter/subscribe", data={"_csrf_token": token, "email": "x"}).json()["success"] is False
    r = c.post("/newsletter/subscribe", data={"_csrf_token": token, "email": "Abo@Example.com"})
    assert r.json()["success"] is True and saved == [["abo@example.com"]]


def test_empty_formation_cannot_be_bought(monkeypatch):
    """Formation sans contenu : « Bientôt disponible », pas de page de paiement."""
    from types import SimpleNamespace
    from digita.models import formation as Formation
    from digita.routes import payment
    f = {"id": 5, "slug": "seo", "title": "SEO", "price": "97.00"}
    monkeypatch.setattr(payment, "_find_formation", lambda fid: f)
    monkeypatch.setattr(Formation.db, "fetch", lambda sql, p=None: None)  # aucune leçon avec contenu
    request = SimpleNamespace(session={"user_id": 1}, query_params={})
    r = payment.checkout(request, "5")
    assert r.status_code == 302 and r.headers["location"] == "/formations/seo"
    assert "bientôt disponible" in request.session["info_message"]

    lesson = {"content": "", "video_url": None}
    assert not Formation._lesson_has_content(lesson)
    assert Formation._lesson_has_content({"content": "Leçon 1", "video_url": None})


def test_navigation_order_matches_footer():
    """Même ordre partout : Agence (menu horizontal + pied de page) et Ressources (menu agence + pied de page)."""
    html = _client().get("/contact").text

    def order(fragment, labels):
        """Chaque libellé apparaît après le précédent (une chaîne absente lève une erreur)."""
        pos = 0
        for label in labels:
            pos = fragment.index(label, pos) + len(label)
        return True

    nav = html[html.index('id="mainNavbar"'):html.index('id="sidebar-agence"')]
    agence = html[html.index('id="sidebar-agence"'):html.index('id="sidebar-overlay"')]
    footer = html[html.index('class="footer-premium"'):]
    assert order(nav, ["À propos<", "Services<", "Solutions<", "Tarifs<", "Contact<"])
    assert "Espace membre" not in nav and "nav-sep" not in nav
    assert order(agence, [">Blog<", ">Outils<", ">Aide<", "<hr>", ">Formations<", ">Boutique<", ">Diagnostic gratuit<"])
    assert order(footer, [">À propos<", ">Services<", ">Solutions<", ">Tarifs<", ">Contact<", "footer-sep", ">Diagnostic gratuit<", ">Mon espace<",
                          ">Blog<", ">Outils<", ">Aide<", ">Formations<", ">Boutique<"])
    # « Lancer un projet » menait au brief, qui exige un compte : remplacé par le diagnostic gratuit
    assert "/projets/brief" not in nav + agence + footer


def test_services_page_lists_every_category_in_order():
    """/services : sommaire, barre mobile et sections ouvertes dans le même ordre que la barre de droite."""
    from digita import services_catalog
    html = _client().get("/services").text
    ids = [c["id"] for c in services_catalog.categories()]
    assert len(ids) == 14 and "accordion-collapse" not in html and "data-services-search" in html
    toc = html[html.index('class="services-toc"'):html.index("data-services-search")]
    sections = html[html.index("data-services-search"):]
    bar = html[html.index('class="sidebar-onglet-sidebar"'):]

    def in_order(fragment, needles):
        pos = 0
        for n in needles:
            pos = fragment.index(n, pos) + len(n)
        return True

    assert in_order(toc, [f'href="#{i}"' for i in ids])
    assert in_order(sections, [f'<div id="{i}" class="services-category"' for i in ids])
    assert in_order(bar, [f"/services#{i}" for i in ids])


def test_home_hero_without_unsourced_figures():
    """Accroches §18 (docs/ACCROCHES_TAGLINES_SEO.md) : pas de chiffre de résultat non documenté."""
    html = _client().get("/").text
    assert "<title>Agence IA &amp; Automatisation à La Réunion | DIGITA</title>" in html
    assert "Plus de clients, moins de tâches." in html and "L'agence IA &amp; automatisation de La Réunion</span>" in html
    for figure in ("+250", "x2.5", "45%", "-70%", "+40%"):
        assert figure not in html, figure
    assert '"name": "DIGITA"' in html and '"alternateName": "Digita Marketing"' in html


def test_page_titles_use_digita_brand():
    c = _client()
    for path in ("/services", "/tarifs", "/contact", "/a-propos", "/outils", "/connexion", "/mentions-legales"):
        title = re.search(r"<title>(.*?)</title>", c.get(path).text, re.S).group(1).strip()
        assert title.endswith("| DIGITA") and len(title.replace("&amp;", "&")) <= 60, (path, title)


def test_diagnostic_page_offers_both_formats(monkeypatch):
    saved, leads_sent = [], []
    monkeypatch.setattr(leads.db, "execute", lambda sql, p=None: saved.append(p))
    monkeypatch.setattr(ines, "push_lead", lambda *a, **k: leads_sent.append(a))
    monkeypatch.setattr(email, "send_new_contact_notification", lambda *a: True)
    monkeypatch.setattr(email, "send_diagnostic_confirmation", lambda *a: True)
    monkeypatch.setattr(leads, "MIN_FILL_SECONDS", 0)  # le test envoie aussitôt la page ouverte
    c = _client()
    html = c.get("/diagnostic").text
    assert "<title>Diagnostic Digital Gratuit à La Réunion | DIGITA</title>" in html
    assert 'action="/outils/audit-seo"' in html and 'id="diagnosticForm"' in html
    assert '"@type": "FAQPage"' in html and '"@type": "BreadcrumbList"' in html
    assert 'href="/diagnostic"' in html  # lien du pied de page

    r = c.post("/api/audit-request", data={"name": "Ana", "email": "ana@example.com", "phone": "0693000000",
                                           "company": "Piscines Ana", "sector": "Artisan / BTP",
                                           "_csrf_token": _token(html)})
    assert r.json()["success"] is True
    assert saved[0][2] == "0693000000" and "Entreprise : Piscines Ana" in saved[0][4]
    assert "Secteur : Artisan / BTP" in leads_sent[0][3]


def test_agent_landing_moved_to_its_page_builder_subdomain():
    """La page de vente Agent IA 24/7 vit dans le Page Builder INES (05/11/2026) : les anciennes adresses y mènent."""
    from digita.realisations import AGENT_URL

    for old in ("/agent24-7", "/accueil-v2"):
        r = _client().get(old, follow_redirects=False)
        assert (r.status_code, r.headers["location"]) == (301, AGENT_URL), old
    assert "/agent24-7" not in _client().get("/sitemap.xml").text
    # Son bouton « Écrire à INES maintenant » ouvre le chat de digita.buzz (…#discuter-avec-ines).
    assert "#discuter-avec-ines" in (PUBLIC / "assets/js/chatbot.js").read_text()
    assert 'id="essai-standardiste"' in _client().get("/conditions-generales").text


def test_agent_card_prices_are_synced_with_solutions():
    from digita import solutions
    from digita.realisations import AGENT_URL

    card = next(c for c in REALISATIONS if c["id"] == "agents-ia")
    standardiste = solutions.OFFERS[0]
    assert card["price"] == "149 €/mois" and standardiste["monthly"].startswith("149 €")
    assert standardiste["setup"] in card["price_note"] and standardiste["monthly"] in card["price_note"]
    assert "WhatsApp" not in " ".join(card["capabilities"]) + card["price_note"]
    assert card["items"][0]["url"] == AGENT_URL
    assert solutions.LANCEMENT["price"] == "499 €" and solutions.LANCEMENT["price"] in _client().get("/solutions").text


def test_ines_catalogue_publishes_the_site_prices():
    from digita import ines_feed, services_catalog, solutions

    response = _client().get("/api/catalogue")
    assert response.status_code == 200
    feed = {row["name"]: row for row in response.json()}
    assert ines_feed.parse_price("2 490 €") == (2490.0, "forfait")
    assert ines_feed.parse_price("0,08 €/mot") == (0.08, "mot")
    assert ines_feed.parse_price("Sur devis") == (0.0, "forfait")
    assert feed["Sites Vitrine"]["base_price"] == 990
    assert feed["Community Management"]["unit"] == "mois"
    assert feed["Chatbots & Assistants Virtuels"]["base_price"] == 490
    assert feed[solutions.LANCEMENT["title"]]["category"] == "Packs & Formules"
    # Un service présent dans deux catégories doit y avoir le même prix.
    for (category_id, name), ines_names in ines_feed.INES_NAMES.items():
        service = next(s for c in services_catalog.categories() if c["id"] == category_id
                       for s in c["services"] if s["name"] == name)
        assert all(feed[n]["base_price"] == ines_feed.parse_price(service["price"])[0] for n in ines_names)


def test_prices_are_coherent_across_pages():
    from digita import grille, services_catalog, solutions

    client = _client()
    tarifs, services = client.get("/tarifs").text, client.get("/services").text
    # /tarifs et la barre de droite viennent des données : plus d'offres fantômes ni de prix en dur
    assert solutions.LANCEMENT["title"] in tarifs and solutions.LP48["price"] in tarifs
    for gone in ("2990€", "1490€", "Le plus populaire", "24/7 support", "Support dédié 24/7", "2 à 4 fois"):
        assert gone not in tarifs, gone
    for offer in solutions.OFFERS:
        assert offer["title"] in tarifs and offer["monthly"] in tarifs
    assert "Essai gratuit 14 jours" in tarifs
    seo = next(c for c in services_catalog.categories() if c["id"] == "seo")
    on_page = next(s for s in seo["services"] if s["name"] == "SEO On-Page")
    assert on_page["price"] == grille.euros(next(r for r in grille.GRILLE if r["id"] == "seo")["levels"]["pro"]["price"]).replace("\u202f", " ").replace("\u00a0", " ")
    for cat in services_catalog.categories():
        for s in cat["services"]:
            assert s["name"] in services
    assert "149€/session" not in services and "text-success" not in services.split('aria-label="Nos services"')[1][:20000]
    sites, social = REALISATIONS[0], REALISATIONS[1]
    assert sites["price"] == "Dès 499 €" and sites["items"][0]["tag"] == solutions.LP48["price"]
    assert social["price"] == "Dès 390 €/mois"


def test_tarifs_show_three_levels():
    from digita import grille

    tarifs = _client().get("/tarifs").text
    assert "Trois niveaux pour chaque prestation" in tarifs and "Essentiel" in tarifs and "Premium" in tarifs
    landing = next(r for r in grille.GRILLE if r["id"] == "landing-page")
    assert [landing["levels"][k]["price"] for k in grille.LEVELS] == [499, 790, 1190]
    assert "499\u00a0€" in tarifs and "1\u202f190\u00a0€" in tarifs
    assert grille.price_label(next(r for r in grille.GRILLE if r["id"] == "agent-ia-24-7")["levels"]["essentiel"]) \
        == "490\u00a0€ + 149\u00a0€/mois"
    assert '"@type": "FAQPage"' in tarifs


def test_catalogue_is_merged_into_services():
    r = _client().get("/catalogue", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (301, "/services")


def test_old_shop_and_solution_addresses_are_moved_permanently():
    # 404 relevées par la Search Console (24/10/2026) : liens de l'ancienne boutique PHP.
    c = _client()
    for old, new in [("/solutions/categorie/mobile", "/solutions"), ("/solutions/site-web", "/solutions"),
                     ("/boutique/categorie/outils", "/outils"), ("/boutique/categorie/services", "/services"),
                     ("/boutique/categorie/templates", "/solutions"), ("/boutique/pack-formation-marketing", "/formations"),
                     ("/boutique/template-ecommerce", "/solutions"), ("/boutique/search?q=seo", "/formations/search?q=seo"),
                     ("/favicon.ico", "/assets/images/digita.png")]:
        r = c.get(old, follow_redirects=False)
        assert (r.status_code, r.headers["location"]) == (301, new), old
    from digita import boutique

    html = c.get("/boutique").text
    # Liens de la boutique : seulement vers les vrais produits (fiche ou commande) et la liste d'attente
    for target in re.findall(r'(?:href|action)="/boutique/([^"#?]+)', html):
        slug = target.removeprefix("commander/")
        assert target == "prevenir" or boutique.product(slug), target


def test_boutique_sells_real_products_without_fake_ones():
    from digita import boutique

    c = _client()
    html = c.get("/boutique").text
    assert boutique.OPEN and len(boutique.WORKFLOWS) == 10 and len(boutique.PROMPT_PACKS) == 4
    for gone in ("197.00", "349.00", "Populaire", "🛒"):
        assert gone not in html
    for item in [*boutique.WORKFLOWS, *boutique.PROMPT_PACKS]:
        assert item["title"] in html and boutique.euros(item["price"]) in html
        assert f'href="/boutique/commander/{item["slug"]}"' in html
    for group in boutique.WORKFLOW_GROUPS:
        assert group in html
    page = c.get("/boutique/devis-ia")
    assert page.status_code == 200 and "Acheter" in page.text and "Installé et paramétré pour vous" in page.text
    for pack in boutique.PROMPT_PACKS:  # chaque pack vendu a bien son fichier
        assert (__import__("pathlib").Path(__file__).parent.parent / "digita" / "boutique_files" / pack["file"]).is_file(), pack["file"]


def test_boutique_checkout_requires_login_and_both_consents(monkeypatch):
    from digita.routes import shop

    c = _client()
    r = c.get("/boutique/commander/pack-immobilier", follow_redirects=False)
    assert (r.status_code, r.headers["location"]) == (302, "/connexion")
    monkeypatch.setattr(shop.stripe, "is_configured", lambda: True)
    created = []
    monkeypatch.setattr(shop.Shop, "create_order", lambda *a: created.append(a) or "12")
    monkeypatch.setattr(shop.stripe, "create_checkout", lambda *a: {"url": "https://checkout.stripe.test/cs"})
    from digita import sessions as sess

    sid = "a" * 64
    store = {sid: {"user_id": 3, "user_email": "a@b.fr"}}
    monkeypatch.setattr(sess, "_load", lambda k: store.get(k))
    monkeypatch.setattr(sess, "_save", lambda k, data, touch: store.__setitem__(k, data))
    c.cookies.set(sess.COOKIE, sid)
    page = c.get("/boutique/commander/pack-immobilier")
    assert page.status_code == 200 and "perdre ainsi mon droit de rétractation" in page.text
    token = _token(page.text)
    billing = {"billing_name": "Marie Hoarau", "billing_address": "1 rue de Paris, 97400 Saint-Denis"}
    r = c.post("/boutique/commander/pack-immobilier", data={"_csrf_token": token, "cgv": "1", **billing}, follow_redirects=False)
    assert r.headers["location"] == "/boutique/commander/pack-immobilier" and not created
    r = c.post("/boutique/commander/pack-immobilier", data={"_csrf_token": token, "cgv": "1", "consent": "1"},
               follow_redirects=False)
    assert r.headers["location"] == "/boutique/commander/pack-immobilier" and not created  # nom et adresse obligatoires
    r = c.post("/boutique/commander/pack-immobilier", data={"_csrf_token": token, "cgv": "1", "consent": "1", **billing},
               follow_redirects=False)
    assert r.headers["location"] == "https://checkout.stripe.test/cs"
    assert created and "L221-28" in created[0][3] and created[0][5]["name"] == "Marie Hoarau"
    page = c.get("/boutique/commander/devis-ia")  # service : exécution anticipée, pas de renonciation
    assert "L221-25" in page.text and "perdre ainsi" not in page.text


def test_expired_download_link_is_refused(monkeypatch):
    from digita.routes import shop

    monkeypatch.setattr(shop.Shop, "use_link", lambda token: None)
    r = _client().get("/telecharger/inconnu")
    assert r.status_code == 410 and "plus valable" in r.text
    monkeypatch.setattr(shop.Shop, "use_link", lambda token: {"file_name": "../config.py"})
    assert _client().get("/telecharger/x").status_code == 410  # pas de sortie du dossier des fichiers


def test_home_seo_is_clean_and_preview_redirects():
    """Accueil publié : indexable, H1 en premier titre, données structurées valides ; l'ancien aperçu redirige."""
    import json
    c = _client()
    assert c.get("/apercu-accueil", follow_redirects=False).headers["location"] == "/"
    r = c.get("/")
    assert r.status_code == 200
    html = r.text
    assert 'name="robots" content="index, follow"' in html
    titles = re.findall(r"<h([1-6])[^>]*>", html)
    assert titles[0] == "1" and titles.count("1") == 1
    blocks = [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]
    types = [g["@type"] for b in blocks for g in b.get("@graph", [b])]
    assert types == ["ProfessionalService", "WebSite", "FAQPage"]
    # Pas d'image lourde, pas de fond animé en canvas, pas de barre de services de droite
    assert "logo.png" not in html and "<canvas" not in html and "sidebar-onglet" not in html
    for anchor in ("#besoins", "#realisations", "#methode", "#engagements", "#faq"):
        assert f'href="{anchor}"' in html, anchor


def test_server_error_page_matches_the_site():
    from digita import main

    assert "Un souci technique momentané" in main.ERROR_500 and "wa.me/262693487817" in main.ERROR_500


def test_ines_formation_fiches_are_hidden_until_ready_then_link_to_ines(monkeypatch):
    """Fiches INES (Google 149 €, DGT 197 €) : masquées tant que « visible » est faux ; sinon prix de la grille,
    achat sur INES et carte au catalogue."""
    from digita import grille
    from digita.models import formation as Formation
    assert grille.FORMATIONS_INES_BY_ID["etre-trouve-sur-google"]["price"] == 149
    for name, value in (("count", 0), ("available_ids", set()), ("get_all_published", []), ("get_popular", []),
                        ("get_categories", [])):
        monkeypatch.setattr(Formation, name, lambda *a, v=value: v)
    for f in grille.FORMATIONS_INES:
        path = "/formations/" + f["id"]
        r = _client().get(path, follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"].endswith("/formations")
        assert f'href="{path}"' not in _client().get("/formations").text

        monkeypatch.setitem(f, "visible", True)
        html = _client().get(path).text
        assert grille.euros(f["price"]) in html and f'href="{f["url"]}"' in html
        assert f["notice"].split(":")[0] in html and "certifiante" not in html.lower()
        assert len(f["meta"]) <= 160
        html = _client().get("/formations").text
        assert f'href="{path}"' in html and "Les premières formations arrivent" in html


def test_seo_audit_unescapes_entities_and_home_description_fits(monkeypatch):
    """L'audit affiche « & » (pas « &amp; ») et compte les vrais caractères ; la page d'accueil passe l'audit."""
    from digita.services import ai
    page = ('<html><head><title>Agence IA &amp; Automatisation à La Réunion | DIGITA</title>'
            '<meta name="description" content="' + "x" * 130 + '"></head><body><h1>A &amp; B</h1></body></html>')
    monkeypatch.setattr(ai, "_fetch", lambda url: (page, 200, 0.1))
    checks = {c["name"]: c for c in ai.audit_seo("https://exemple.test")["checks"]}
    assert checks["Balise Title"]["detail"] == "Agence IA & Automatisation à La Réunion | DIGITA (48 car.)"
    assert checks["Balise H1"]["detail"] == "A & B"

    import html as html_mod
    home = _client().get("/").text
    desc = html_mod.unescape(re.search(r'<meta\s+name="description"\s+content="(.*?)"', home, re.S).group(1))
    assert 120 <= len(desc) <= 160


def test_meta_descriptions_fit_google_snippet():
    """Pages fixes : meta description de 120 à 160 caractères (au-delà, Google la coupe)."""
    import html as html_mod
    from digita.routes.blog import category_meta
    client = _client()
    for path in ("/", "/a-propos", "/outils/audit-seo", "/outils/meta-generator", "/outils/roi-calculator",
                 "/outils/calendrier-editorial", "/boutique"):
        page = client.get(path).text
        desc = html_mod.unescape(re.search(r'<meta\s+name="description"\s+content="(.*?)"', page, re.S).group(1))
        assert 120 <= len(desc) <= 160, (path, len(desc))
    for kind in ("Articles", "Formations"):
        for name, desc in (("CRM", "Relation client et CRM"), ("Publicité en Ligne", "Google Ads et publicité display"),
                           ("Réseaux Sociaux", "Community management et publicité sur les réseaux sociaux")):
            meta = category_meta(kind, {"name": name, "description": desc})
            assert 120 <= len(meta) <= 160 and "google Ads" not in meta, meta


def test_diagnostic_refuses_scripts_and_bots(monkeypatch):
    """11/11/2026 : la route n'avait ni CSRF ni contrôle ; un robot y créait affaire + devis dans INES."""
    leads_sent, mails = [], []
    monkeypatch.setattr(leads.db, "execute", lambda sql, p=None: None)
    monkeypatch.setattr(ines, "push_lead", lambda *a, **k: leads_sent.append(a))
    monkeypatch.setattr(email, "send_new_contact_notification", lambda *a: True)
    monkeypatch.setattr(email, "send_diagnostic_confirmation", lambda *a: mails.append(a) or True)
    c = _client()
    base = {"name": "Ana", "email": "ana@example.com", "phone": "0693000000"}
    assert c.post("/api/audit-request", data=base).json()["success"] is False  # sans jeton : refusé
    token = _token(c.get("/diagnostic").text)
    # Envoyé aussitôt la page affichée : réponse « réussie », mais rien n'est fait.
    assert c.post("/api/audit-request", data={**base, "_csrf_token": token}).json()["success"] is True
    monkeypatch.setattr(leads, "MIN_FILL_SECONDS", 0)
    assert c.post("/api/audit-request", data={**base, "_csrf_token": token, "site_web": "x"}).json()["success"] is True
    assert c.post("/api/audit-request", data={**base, "name": "TVuEYaKiNfTagVdYfjrOQRiI", "_csrf_token": token}).json()["success"] is True
    assert c.post("/api/audit-request", data={**base, "email": "ni.g.e.l...da@gmail.com", "_csrf_token": token}).json()["success"] is False
    assert leads_sent == [] and mails == []
    assert c.post("/api/audit-request", data={**base, "_csrf_token": token}).json()["success"] is True
    assert len(leads_sent) == 1 and len(mails) == 1
