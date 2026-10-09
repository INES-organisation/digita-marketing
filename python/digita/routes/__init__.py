"""Table des routes, dans le même ordre que public/index.php.

Chaque entrée : (méthode, chemin PHP avec :param, fonction). Les routes que la
version Python ne gère pas encore pointent vers `not_ported` (voir le doc de suivi).
"""
from . import pages, blog, formations, tools, auth, leads, chatbot, analytics
from .common import not_ported

R = []


def get(path, fn):
    R.append(("GET", path, fn))


def post(path, fn):
    R.append(("POST", path, fn))


get("/", pages.home)

# ---------------------------------------------------------------- blog
get("/blog", blog.index)
get("/blog/search", blog.search)
get("/blog/categorie/:slug", blog.category)
get("/blog/:slug", blog.show)

# ---------------------------------------------------------------- formations
get("/formations", formations.index)
get("/formations/search", formations.search)
get("/mes-formations", not_ported)
get("/formations/categorie/:slug", formations.category)
post("/formations/:slug/inscription", not_ported)
get("/formations/:slug/learn", not_ported)
post("/formations/complete-lesson", not_ported)
get("/formations/quiz/:id", not_ported)
post("/formations/quiz/:id/submit", not_ported)
get("/formations/quiz/:id/results", not_ported)
post("/formations/:id/review", not_ported)
get("/formations/:id/certificate", not_ported)
get("/certificat/verifier", formations.verify_certificate)
get("/formations/:slug/landing", formations.landing)
get("/formations/checkout/:id", not_ported)
post("/formations/checkout/:id", not_ported)
get("/paiement/succes", not_ported)
get("/paiement/annulation", not_ported)
post("/webhook/stripe", not_ported)
post("/api/validate-promo", not_ported)
get("/mes-commandes", not_ported)
get("/mes-commandes/:id", not_ported)
get("/facture/:id", not_ported)

# ---------------------------------------------------------------- leads / projets
post("/api/audit-request", leads.submit_audit)
get("/projets/brief", not_ported)
post("/projets/brief", not_ported)
post("/api/project-quote", not_ported)
get("/espace-client", not_ported)
get("/espace-client/projet/:id", not_ported)
post("/espace-client/projet/:id/message", not_ported)
post("/webhook/webox", not_ported)

# ---------------------------------------------------------------- chatbot
post("/api/chatbot/message", chatbot.send_message)
get("/api/chatbot/history", chatbot.history)
post("/api/chatbot/qualify", chatbot.qualify)
post("/api/chatbot/appointment", chatbot.appointment)
get("/api/chatbot/slots", chatbot.slots)

# ---------------------------------------------------------------- outils gratuits
get("/outils", tools.index)  # redéclarée plus bas (OutilsController), comme en PHP
get("/outils/audit-seo", tools.seo_audit)
post("/outils/audit-seo", tools.seo_audit_post)
get("/outils/meta-generator", tools.meta_generator)
post("/outils/meta-generator", tools.meta_generator_post)
get("/outils/roi-calculator", tools.roi_calculator)
post("/outils/roi-calculator", tools.roi_calculator_post)
post("/api/roi-calculate", tools.roi_ajax)
get("/outils/calendrier-editorial", tools.editorial_calendar)
post("/outils/calendrier-editorial", tools.editorial_calendar_post)

# ---------------------------------------------------------------- analytics
post("/api/analytics/pageview", analytics.pageview)
post("/api/analytics/conversion", analytics.conversion)

get("/formations/:slug", formations.show)
get("/boutique", pages.boutique)
get("/solutions", pages.solutions)
get("/solution", pages.redirect_to("/solutions"))
get("/a-propos", pages.about)
get("/services", pages.services)
get("/catalogue", pages.catalogue)
get("/portfolio", pages.missing_template)
get("/equipe", pages.missing_template)
get("/contact", pages.contact)
get("/support", pages.support)
get("/tarifs", pages.tarifs)
get("/outils", pages.outils)
get("/formation", pages.redirect_to("/formations"))

# ---------------------------------------------------------------- pages légales
get("/mentions-legales", pages.legal("mentions-legales", "Mentions Légales - Digita Marketing"))
get("/politique-confidentialite", pages.legal("politique-confidentialite", "Politique de Confidentialité - Digita Marketing"))
get("/conditions-generales", pages.legal("conditions-generales", "Conditions Générales - Digita Marketing"))
get("/cookies", pages.legal("cookies", "Politique des Cookies - Digita Marketing"))

# ---------------------------------------------------------------- authentification
get("/connexion", auth.show_login)
post("/connexion", auth.login)
get("/inscription", auth.show_register)
post("/inscription", auth.register)

# ---------------------------------------------------------------- administration (phase 4)
for _p in ["/admin/dashboard", "/admin/contacts", "/admin/contacts/read", "/admin/contacts/replied",
           "/admin/newsletters", "/admin/newsletters/export", "/admin/logout", "/admin/webhooks",
           "/admin/articles", "/admin/articles/new", "/admin/articles/edit/:id", "/admin/formations",
           "/admin/formations/new", "/admin/formations/edit/:id", "/admin/media", "/admin/analytics",
           "/admin/projects", "/admin/projects/:id", "/admin/campaigns", "/admin/campaigns/new"]:
    get(_p, not_ported)
for _p in ["/admin/webhooks/save", "/admin/webhooks/test/:type", "/admin/articles/store",
           "/admin/articles/update/:id", "/admin/articles/delete/:id", "/admin/articles/upload-image",
           "/admin/formations/store", "/admin/formations/update/:id", "/admin/formations/delete/:id",
           "/admin/media/upload", "/admin/media/delete", "/admin/projects/:id/status",
           "/admin/projects/:id/message", "/admin/projects/:id/note", "/admin/projects/:id/generate",
           "/admin/projects/:id/task", "/admin/projects/task/update", "/admin/projects/:id/price",
           "/admin/campaigns/delete/:id"]:
    post(_p, not_ported)

ROUTES = R
