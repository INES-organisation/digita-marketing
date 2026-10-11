"""Outils gratuits (ToolsController.php)."""
import logging

from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import db, php, security
from ..render import render_view
from ..services import ai

log = logging.getLogger("digita.tools")


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


# ---------------------------------------------------------------- traitement (POST)
TITLES = {
    "outils/seo-audit-content": ("Audit SEO Gratuit — Digita Marketing",
                                 "Analysez gratuitement le SEO de votre site web. Score, recommandations et plan d'action personnalisé."),
    "outils/meta-generator-content": ("Générateur de Meta Descriptions IA — Digita Marketing",
                                      "Générez des meta descriptions SEO optimisées grâce à l'IA. Gratuit et instantané."),
    "outils/roi-calculator-content": ("Calculateur de ROI Marketing — Digita Marketing",
                                      "Calculez le retour sur investissement de vos campagnes marketing. Outil gratuit et interactif."),
    "outils/editorial-calendar-content": ("Générateur de Calendrier Éditorial IA — Digita Marketing",
                                          "Générez un calendrier éditorial personnalisé pour votre blog grâce à l'IA. Gratuit."),
}


def _render(request, view, **data):
    title, desc = TITLES[view]
    return render_view(request, view, {"title": title, "metaDescription": desc, **data})

def _track(request, tool, input_data, summary=None):
    """trackToolUsage() : silencieux en cas d'erreur."""
    try:
        db.execute("INSERT INTO tool_usage (tool_name, user_id, visitor_ip, input_data, result_summary) "
                   "VALUES (?, ?, ?, ?, ?)", [tool, request.session.get("user_id"), security.remote_addr(request),
                                              php.json_encode(input_data, 256), summary])
    except Exception as e:  # noqa: BLE001
        log.warning("tool_usage non enregistré : %s", e)


async def seo_audit_post(request):
    form = await request.form()
    url = php.trim(form.get("url", ""))
    return await run_in_threadpool(_seo_audit, request, url)


def _seo_audit(request, url):
    result = None
    if php.empty(url) or not ai.valid_url(url):
        request.session["error_message"] = "Veuillez entrer une URL valide (ex: https://example.com)"
    else:
        result = ai.audit_seo(url)
        _track(request, "seo_audit", {"url": url}, "Score: " + php.strval(result.get("score", 0)) + "/100")
    return _render(request, "outils/seo-audit-content", result=result, url=url)


async def meta_generator_post(request):
    form = await request.form()
    return await run_in_threadpool(_meta_generator, request, php.trim(form.get("page_title", "")),
                                   php.trim(form.get("page_content", "")))


def _meta_generator(request, page_title, page_content):
    result = None
    if php.empty(page_title):
        request.session["error_message"] = "Le titre de la page est requis."
    else:
        try:
            result = ai.generate_meta_description(page_title, page_content)
            _track(request, "meta_generator", {"title": page_title}, php.mb_strimwidth(result, 0, 100, "..."))
        except Exception:  # noqa: BLE001
            request.session["error_message"] = "Erreur lors de la génération. Vérifiez votre clé API OpenAI."
    return _render(request, "outils/meta-generator-content",
                 result=result, pageTitle=page_title, pageContent=page_content)


def _roi_params(form):
    return {
        "budget": form.get("budget", 1000), "cpc": form.get("cpc", 1.5),
        "conversion_rate": form.get("conversion_rate", 2), "avg_order_value": form.get("avg_order_value", 100),
        "margin": form.get("margin", 30),
    }


async def roi_calculator_post(request):
    params = _roi_params(await request.form())
    return await run_in_threadpool(_roi_calculator, request, params)


def _roi_calculator(request, params):
    result = ai.calculate_roi(params)
    _track(request, "roi_calculator", params, "ROI: " + php.strval(result.get("roi", 0)) + "%")
    return _render(request, "outils/roi-calculator-content", result=result, params=params)


async def roi_ajax(request):
    result = ai.calculate_roi(_roi_params(await request.form()))
    return Response(php.json_encode({"success": True, "result": result}), media_type="application/json")


async def editorial_calendar_post(request):
    form = await request.form()
    return await run_in_threadpool(_editorial_calendar, request, php.trim(form.get("niche", "")),
                                   form.get("duration", "1 mois"), form.get("frequency", "3 par semaine"))


def _editorial_calendar(request, niche, duration, frequency):
    result = None
    if php.empty(niche):
        request.session["error_message"] = "Veuillez indiquer votre niche / secteur d'activité."
    else:
        try:
            result = ai.generate_editorial_calendar(niche, duration, frequency)
            _track(request, "editorial_calendar", {"niche": niche, "duration": duration}, "Calendrier généré")
        except Exception:  # noqa: BLE001
            request.session["error_message"] = "Erreur lors de la génération. Vérifiez votre clé API OpenAI."
    return _render(request, "outils/editorial-calendar-content",
                 result=result, niche=niche, duration=duration, frequency=frequency)
