"""Coque commune des pages, formulaires de contact et de newsletter."""
import re

import pytest
from starlette.testclient import TestClient

from digita import db, sessions
from digita.realisations import REALISATIONS
from digita.main import app
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
    assert r.status_code == 404 and "Page non trouvée" in r.text and "noindex" in r.text
    assert 'aria-current="page"' in c.get("/contact").text


def test_home_uses_vertical_menu_anchored_on_sections():
    r = _client().get("/")
    assert 'class="sidebar-premium"' in r.text and 'class="footer-premium"' in r.text
    assert "navbar-site" not in r.text and "sidebar-onglet-sidebar" not in r.text
    for anchor in ("#enjeux", "#ecosysteme", "#collaboration", "#methode", "#realisations", "#hero-premium"):
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
    monkeypatch.setattr(ines, "push_lead", lambda *a, **k: leads_sent.append(a))
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
    assert "bien été envoyé" in c.get("/contact").text


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
    assert order(nav, ["À propos<", "Services<", "Contact<", "Solutions<", "Tarifs<"])
    assert "Espace membre" not in nav and "nav-sep" not in nav
    assert order(agence, [">Blog<", ">Outils<", ">Support<", "<hr>", ">Formations<", ">Boutique<", ">Lancer un projet<"])
    assert order(footer, [">À propos<", ">Services<", ">Contact<", ">Solutions<", ">Tarifs<", "footer-sep", ">Diagnostic gratuit<", ">Espace membre<",
                          ">Blog<", ">Outils<", ">Support<", ">Formations<", ">Boutique<", "footer-sep", ">Lancer un projet<"])


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
    assert "Votre Temps, Retrouvé." in html and "La Réunion</span>" in html
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
    c = _client()
    html = c.get("/diagnostic").text
    assert "<title>Diagnostic Digital Gratuit à La Réunion | DIGITA</title>" in html
    assert 'action="/outils/audit-seo"' in html and 'id="diagnosticForm"' in html
    assert '"@type": "FAQPage"' in html and '"@type": "BreadcrumbList"' in html
    assert 'href="/diagnostic"' in html  # lien du pied de page

    r = c.post("/api/audit-request", data={"name": "Ana", "email": "ana@example.com", "phone": "0693000000",
                                           "company": "Piscines Ana", "sector": "Artisan / BTP"})
    assert r.json()["success"] is True
    assert saved[0][2] == "0693000000" and "Entreprise : Piscines Ana" in saved[0][4]
    assert "Secteur : Artisan / BTP" in leads_sent[0][3]


def test_agent_landing_is_noindex_and_uses_real_offers():
    """Page de vente Agent IA 24/7 (docs/SUIVI_REFONTE_ACCUEIL.md) : hors index, offres et FAQ réelles, légère."""
    from digita import solutions
    from digita.routes.pages import AGENT_FAQ

    r = _client().get("/agent24-7")
    assert r.status_code == 200
    html = r.text
    assert '<meta name="robots" content="noindex, nofollow">' in html
    assert html.count("<h1") == 1 and "Même à 23 h." in html
    for offer in solutions.OFFERS:
        assert offer["title"] in html and offer["monthly"] in html, offer["id"]
    for dependency in ("bootstrap", "data-aos", "fonts.googleapis.com", "glass-card"):
        assert dependency not in html, dependency
    for figure in ("+250", "x2.5", "45%", "-70%", "+40%"):
        assert figure not in html, figure
    assert html.count("<details>") == len(AGENT_FAQ)
    assert "/agent24-7" not in _client().get("/sitemap.xml").text
    # Agent nommé INES, prix nets (art. 293 B), WhatsApp par offre, chatbot présent, marque DIGITA.buzz.
    assert "INES, notre agent IA" in html and 'id="chatbot-container"' in html and "/assets/js/chatbot.js" in html
    assert " HT" not in html and "293 B" in html
    assert html.count("https://wa.me/262693487817") == 1 + len(solutions.OFFERS)
    assert 'DIGITA<span>.buzz</span>' in html
    assert solutions.LANCEMENT["price"] in html
    # L'ancienne adresse d'aperçu mène à la page.
    old = _client().get("/accueil-v2", follow_redirects=False)
    assert old.status_code == 302 and old.headers["location"] == "/agent24-7"
    assert 'id="essai-standardiste"' in _client().get("/conditions-generales").text


def test_agent_subdomain_serves_landing_and_sends_other_links_to_main_site():
    host = {"host": "agent24-7.digita.buzz"}
    client = _client()
    assert "Même à 23 h." in client.get("/", headers=host).text
    assert client.get("/assets/css/agent247.css", headers=host).status_code == 200
    link = client.get("/diagnostic?pack=standardiste", headers=host, follow_redirects=False)
    assert link.status_code == 302 and link.headers["location"] == "https://digita.buzz/diagnostic?pack=standardiste"
    # Le chatbot répond sur le sous-domaine (pas de redirection, un POST la perdrait).
    assert client.get("/api/chatbot/slots", headers=host, follow_redirects=False).status_code != 302


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
    from digita import solutions

    client = _client()
    tarifs, catalogue = client.get("/tarifs").text, client.get("/catalogue").text
    assert solutions.LANCEMENT["title"] in tarifs and "Choisir Starter" not in tarifs
    assert "Révisions illimitées" not in tarifs.split("Business")[0]
    assert "2 séries de révisions" in tarifs
    assert "À partir de 499€" in catalogue and "149€/session" not in catalogue
    chatbots = catalogue[catalogue.rindex("Chatbots Intelligents"):][:900]
    assert "À partir de 490€" in chatbots
    sites, social = REALISATIONS[0], REALISATIONS[1]
    assert sites["price"] == "Dès 499 €" and sites["items"][0]["tag"] == solutions.LP48["price"]
    assert social["price"] == "Dès 390 €/mois"


def test_tarifs_show_three_levels():
    from digita import grille

    tarifs = _client().get("/tarifs").text
    assert "Prix par Niveau" in tarifs and "Essentiel" in tarifs and "Premium" in tarifs
    landing = next(r for r in grille.GRILLE if r["id"] == "landing-page")
    assert [landing["levels"][k]["price"] for k in grille.LEVELS] == [499, 790, 1190]
    assert "499\u00a0€" in tarifs and "1\u202f190\u00a0€" in tarifs
    assert grille.price_label(next(r for r in grille.GRILLE if r["id"] == "agent-ia-24-7")["levels"]["essentiel"]) \
        == "490\u00a0€ + 149\u00a0€/mois"
