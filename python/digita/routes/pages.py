"""Pages de contenu fixe (contrôleurs About, Services, Catalogue, Contact…)."""
from .. import services_catalog
from .. import solutions as solutions_catalog
from ..realisations import REALISATIONS
from ..render import base_context, render_page, render_view
from .common import redirect


def home(request):
    return render_page(request, "templates/home.html", {"realisations": REALISATIONS})


def _simple(view, title, css, description=None):
    def handler(request):
        return render_view(request, view, {"title": title, "metaDescription": description, "extraCss": [css]})
    return handler


about = _simple("about/index-content", "À propos : Agence IA et Digitale à La Réunion | DIGITA", "/assets/css/about.css",
                "DIGITA, agence IA et digitale à La Réunion : conseil stratégique, création de sites et automatisation "
                "pour les dirigeants de TPE/PME. Notre méthode.")
def services(request):
    return render_view(request, "services/index-content", {
        "title": "Sites Web, Automatisation & IA à La Réunion | DIGITA",
        "metaDescription": "Sites web, réseaux sociaux, publicité, automatisation et agents IA : les services DIGITA "
                           "pour les TPE/PME de La Réunion. Offres claires, prix affichés.",
        "extraCss": ["/assets/css/services.css"],
        "poles": services_catalog.POLES, "categories": services_catalog.categories(),
    })
catalogue = _simple("catalogue/index-content", "Catalogue des Services Digitaux | DIGITA", "/assets/css/catalogue.css",
                    "Le catalogue complet des services DIGITA : création de sites, marketing digital, automatisation, "
                    "IA et formations. Trouvez l'offre adaptée à votre projet.")
support = _simple("support/index-content", "Support Client | DIGITA", "/assets/css/support.css",
                  "Support client DIGITA : aide sur votre site, vos automatisations, vos formations et votre espace "
                  "client. Une équipe joignable à La Réunion.")
tarifs = _simple("tarifs/index-content", "Tarifs Sites Web, Automatisation & IA | DIGITA", "/assets/css/tarifs.css",
                 "Tarifs DIGITA : sites vitrines, e-commerce, automatisation et IA pour TPE/PME à La Réunion. "
                 "Prix affichés, sans surprise. Diagnostic gratuit offert.")
boutique = _simple("boutique/index-content", "Boutique : Packs et Services Digitaux | DIGITA", "/assets/css/boutique.css",
                   "Packs et services digitaux DIGITA prêts à commander : sites, visibilité, automatisation et "
                   "formations pour faire grandir votre entreprise.")
def solutions(request):
    return render_view(request, "solutions/index-content", {
        "title": "Packs Clés en Main : Acquisition, E-commerce, RDV | DIGITA",
        "metaDescription": "Packs clés en main pour TPE/PME : système d'acquisition automatique, boutique "
                           "e-commerce prête à vendre, prise de RDV, devis automatiques. Diagnostic offert.",
        "extraCss": ["/assets/css/solutions.css"], "packs": solutions_catalog.PACKS,
    })
outils = _simple("outils/index-content", "Outils Marketing Gratuits : Audit SEO, ROI | DIGITA", "/assets/css/outils.css",
                 "Outils gratuits pour booster votre marketing digital : audit SEO, générateur de meta descriptions, "
                 "calculateur ROI, calendrier éditorial.")


# Questions de /diagnostic : affichées sur la page et reprises dans les données structurées FAQPage.
DIAGNOSTIC_FAQ = [
    {"question": "Le diagnostic est-il vraiment gratuit ?",
     "answer": "Oui. L'audit SEO automatique comme le diagnostic de 30 minutes avec un consultant sont gratuits et "
               "sans engagement. Aucune carte bancaire n'est demandée."},
    {"question": "Quelle différence entre l'audit SEO et le diagnostic de 30 minutes ?",
     "answer": "L'audit SEO analyse automatiquement votre site en quelques secondes : score, points bloquants et "
               "recommandations. Le diagnostic de 30 minutes est un échange avec un consultant sur toute votre activité : "
               "visibilité, suivi des prospects, devis, rendez-vous et tâches à automatiser."},
    {"question": "À qui s'adresse le diagnostic ?",
     "answer": "Aux dirigeants de TPE et PME, artisans, cabinets, instituts, agences et indépendants, à La Réunion ou "
               "à distance, qui veulent trouver plus de clients et gagner du temps."},
    {"question": "Faut-il déjà avoir un site internet ?",
     "answer": "Non. Le diagnostic de 30 minutes porte aussi sur votre page Facebook, votre fiche Google, la façon dont "
               "vous suivez vos prospects et vos devis."},
    {"question": "Que se passe-t-il après le diagnostic ?",
     "answer": "Vous repartez avec un plan d'action concret et priorisé. Vous êtes libre de le mettre en œuvre seul ou "
               "avec nous ; nos offres et nos prix sont affichés sur la page Tarifs."},
]


def diagnostic(request):
    base = base_context(request)["base_url"]
    return render_view(request, "diagnostic/index-content", {
        "title": "Diagnostic Digital Gratuit à La Réunion | DIGITA",
        "metaDescription": "Diagnostic digital gratuit : audit SEO automatique de votre site en quelques secondes, ou "
                           "30 min avec un consultant DIGITA à La Réunion. Sans engagement.",
        "extraCss": ["/assets/css/diagnostic.css"],
        "faqSchema": DIAGNOSTIC_FAQ,
        # Venu d'un pack de /solutions (« Parler de ce pack ») : rappelé dans le formulaire et la demande.
        "pack": next((p for p in solutions_catalog.PACKS if p["id"] == request.query_params.get("pack")), None),
        "breadcrumbs": [{"name": "Accueil", "url": base + "/"}, {"name": "Diagnostic gratuit", "url": base + "/diagnostic"}],
    })


def contact(request):
    return render_view(request, "contact/index-content", {
        "title": "Contact : Agence Digitale à La Réunion | DIGITA",
        "metaDescription": "Contactez DIGITA, agence IA et digitale à La Réunion : un projet de site, d'automatisation "
                           "ou d'IA ? Réponse rapide et diagnostic gratuit de 30 min.",
        "extraCss": ["/assets/css/contact.css"],
        "contactFlash": request.session.pop("contact_flash", None),
    })


def legal(view, title):
    return _simple(f"legal/{view}", title, "/assets/css/legal.css")


def redirect_to(url):
    return lambda request: redirect(url)

