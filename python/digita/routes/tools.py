"""Outils gratuits (ToolsController.php) — affichage des formulaires."""
from ..render import render_view


def index(request):
    return render_view(request, "outils/index-content", {
        "title": "Outils Gratuits Marketing Digital — Digita Marketing",
        "metaDescription": "Outils gratuits pour booster votre marketing digital : audit SEO, générateur de meta descriptions, calculateur ROI, calendrier éditorial.",
    })


def seo_audit(request):
    return render_view(request, "outils/seo-audit-content", {
        "title": "Audit SEO Gratuit — Digita Marketing",
        "metaDescription": "Analysez gratuitement le SEO de votre site web. Score, recommandations et plan d'action personnalisé.",
        "result": None, "url": "",
    })


def meta_generator(request):
    return render_view(request, "outils/meta-generator-content", {
        "title": "Générateur de Meta Descriptions IA — Digita Marketing",
        "metaDescription": "Générez des meta descriptions SEO optimisées grâce à l'IA. Gratuit et instantané.",
        "result": None, "pageTitle": "", "pageContent": "",
    })


def roi_calculator(request):
    return render_view(request, "outils/roi-calculator-content", {
        "title": "Calculateur de ROI Marketing — Digita Marketing",
        "metaDescription": "Calculez le retour sur investissement de vos campagnes marketing. Outil gratuit et interactif.",
        "result": None, "params": [],
    })


def editorial_calendar(request):
    return render_view(request, "outils/editorial-calendar-content", {
        "title": "Générateur de Calendrier Éditorial IA — Digita Marketing",
        "metaDescription": "Générez un calendrier éditorial personnalisé pour votre blog grâce à l'IA. Gratuit.",
        "result": None, "niche": "", "duration": "1 mois", "frequency": "3 par semaine",
    })
