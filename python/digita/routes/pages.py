"""Pages de contenu fixe (contrôleurs About, Services, Catalogue, Contact…)."""
from starlette.responses import HTMLResponse

from ..render import render_page, render_view
from .common import redirect


def home(request):
    return render_page(request, "templates/home.html")


def _simple(view, title, css):
    def handler(request):
        return render_view(request, view, {"title": title, "extraCss": [css]})
    return handler


about = _simple("about/index-content", "À propos - Digita Marketing", "/assets/css/about.css")
services = _simple("services/index-content", "Services - Digita Marketing", "/assets/css/services.css")
catalogue = _simple("catalogue/index-content", "Catalogue Complet - Digita Marketing", "/assets/css/catalogue.css")
contact = _simple("contact/index-content", "Contact - Digita Marketing", "/assets/css/contact.css")
support = _simple("support/index-content", "Support - Digita Marketing", "/assets/css/support.css")
tarifs = _simple("tarifs/index-content", "Tarifs - Digita Marketing", "/assets/css/tarifs.css")
boutique = _simple("boutique/index-content", "Boutique - Produits & Services | Digita", "/assets/css/boutique.css")
solutions = _simple("solutions/index-content", "Solutions - Marketing Digital | Digita", "/assets/css/solutions.css")
outils = _simple("outils/index-content", "Outils - Marketing Digital | Digita", "/assets/css/outils.css")


def legal(view, title):
    return _simple(f"legal/{view}", title, "/assets/css/legal.css")


def redirect_to(url):
    return lambda request: redirect(url)


def missing_template(request):
    # /portfolio et /equipe incluent des templates absents du dépôt PHP : en production
    # le gestionnaire d'erreurs PHP affiche ce message générique.
    return HTMLResponse("Une erreur est survenue. Veuillez réessayer plus tard.")
