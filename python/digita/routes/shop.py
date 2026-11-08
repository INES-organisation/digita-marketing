"""Boutique : fiches produits, commande et paiement (Stripe via INES), téléchargements.

Produits et prix : digita/boutique.py. Commandes : models/shop.py. La commande est validée au retour
sur /paiement/succes (et par le rattrapage nocturne des commandes) comme pour les formations.
"""
from starlette.concurrency import run_in_threadpool
from starlette.responses import FileResponse

from .. import boutique, config, php, security
from ..models import order as Order
from ..models import shop as Shop
from ..render import base_context, render_view
from ..services import stripe
from .common import moved, not_found, redirect

FILES = config.ROOT / "python" / "digita" / "boutique_files"
CSS = ["/assets/css/boutique.css"]

CGV_TEXT = "J'ai lu et j'accepte les conditions générales de vente."
CONSENT = {
    "download": ("Je demande à recevoir le contenu numérique immédiatement après le paiement et je reconnais perdre "
                 "ainsi mon droit de rétractation (article L221-28, 13° du Code de la consommation)."),
    "service": ("Je demande que l'installation commence avant la fin du délai de rétractation de 14 jours ; si je me "
                "rétracte après son début, je paierai la part déjà réalisée (article L221-25 du Code de la consommation)."),
}


def product_page(request, slug):
    product = boutique.product(slug)
    if not product:  # anciennes fiches de la boutique PHP encore connues de Google
        return moved("/solutions")
    base = base_context(request)["base_url"]
    return render_view(request, "boutique/product-content", {
        "title": f"{product['title']} | Boutique DIGITA",
        "metaDescription": php.mb_strimwidth(product["summary"], 0, 155, "…"),
        "metaRobots": "index, follow" if boutique.OPEN else "noindex, follow",
        "extraCss": CSS, "product": product, "shop": boutique, "open": boutique.OPEN,
        "breadcrumbs": [{"name": "Accueil", "url": base + "/"}, {"name": "Boutique", "url": base + "/boutique"},
                        {"name": product["title"], "url": f"{base}/boutique/{slug}"}],
    })


def _guard(request, slug):
    """Produit vendable et visiteur connecté ; sinon la réponse de redirection."""
    product = boutique.product(slug)
    if not product or not boutique.OPEN:
        return None, redirect("/boutique")
    if "user_id" not in request.session:
        request.session["redirect_after_login"] = f"/boutique/commander/{slug}"
        return None, redirect("/connexion")
    return product, None


def checkout(request, slug):
    product, stop = _guard(request, slug)
    if stop:
        return stop
    return render_view(request, "boutique/checkout-content", {
        "title": f"Commander : {product['title']} | DIGITA", "metaRobots": "noindex, nofollow", "extraCss": CSS,
        "product": product, "shop": boutique, "cgvText": CGV_TEXT, "consentText": CONSENT[product["kind"]],
        "checkoutError": request.session.pop("checkout_error", None), "billing": request.session.get("billing"),
        "stripeConfigured": stripe.is_configured(),
    })


async def process(request, slug):
    form = await request.form()
    security.check_csrf(request, form)
    return await run_in_threadpool(_process, request, slug, form)


def _process(request, slug, form):
    product, stop = _guard(request, slug)
    if stop:
        return stop
    session = request.session
    billing = Order.billing_from_form(form)
    if not billing:
        session["checkout_error"] = "Merci d'indiquer votre nom et votre adresse : ils figurent sur la facture."
        return redirect(f"/boutique/commander/{slug}")
    session["billing"] = billing  # pré-remplissage des prochaines commandes
    if not form.get("cgv") or not form.get("consent"):
        session["checkout_error"] = "Merci de cocher les deux cases pour valider la commande."
        return redirect(f"/boutique/commander/{slug}")
    if not stripe.is_configured():
        session["checkout_error"] = "Le paiement en ligne est momentanément indisponible. Écrivez-nous sur WhatsApp ou par e-mail."
        return redirect(f"/boutique/commander/{slug}")
    consent = f"{CGV_TEXT}\n{CONSENT[product['kind']]}"
    ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "")
    order_id = Shop.create_order(session["user_id"], product, session.get("user_email"), consent, ip, billing)
    base = base_context(request)["base_url"]
    try:
        checkout_session = stripe.create_checkout(
            product["title"], product["summary"], None, order_id, product["price"], base + "/paiement/succes",
            base + "/paiement/annulation?order_id=" + order_id, session.get("user_email"),
            {"product": product["slug"], "user_id": session.get("user_id")})
    except stripe.StripeError:
        Order.update_status(order_id, "cancelled")
        session["checkout_error"] = "Le paiement n'a pas pu démarrer. Merci de réessayer dans un instant."
        return redirect(f"/boutique/commander/{slug}")
    return redirect(checkout_session["url"])


def download(request, token):
    """Lien personnel envoyé par e-mail et affiché dans « Mes commandes » (pas besoin d'être connecté)."""
    row = Shop.use_link(token) if len(token) <= 64 else None
    path = (FILES / row["file_name"]).resolve() if row else None
    if not row or not path or path.parent != FILES.resolve() or not path.is_file():
        return render_view(request, "boutique/link-expired-content", {
            "title": "Lien de téléchargement expiré | DIGITA", "metaRobots": "noindex, nofollow", "extraCss": CSS,
        }, status=410)
    return FileResponse(path, filename=row["file_name"], media_type=boutique.MEDIA_TYPES.get(path.suffix, "application/octet-stream"),
                        headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex"})


async def renew(request, order_id):
    form = await request.form()
    security.check_csrf(request, form)
    if "user_id" not in request.session:
        return redirect("/connexion")
    return await run_in_threadpool(_renew, request, order_id)


def _renew(request, order_id):
    order = Order.find(order_id)
    if not order or not php.loose_eq(order["user_id"], request.session["user_id"]) or order["status"] != "paid":
        return not_found(request)
    Shop.renew_links(order_id, request.session["user_id"])
    request.session["success_message"] = "Vos nouveaux liens de téléchargement sont prêts."
    return redirect(f"/mes-commandes/{order_id}")

