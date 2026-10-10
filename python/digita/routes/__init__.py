"""Table des routes, dans le même ordre que public/index.php.

Chaque entrée : (méthode, chemin PHP avec :param, fonction).
"""
from . import pages, blog, formations, tools, auth, leads, chatbot, analytics, learning, payment, projects, admin

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
get("/mes-formations", learning.my_formations)
get("/formations/categorie/:slug", formations.category)
post("/formations/:slug/inscription", learning.enroll)
get("/formations/:slug/learn", learning.learn)
post("/formations/complete-lesson", learning.complete_lesson)
get("/formations/quiz/:id", learning.quiz)
post("/formations/quiz/:id/submit", learning.submit_quiz)
get("/formations/quiz/:id/results", learning.quiz_results)
post("/formations/:id/review", learning.review)
get("/formations/:id/certificate", learning.certificate)
get("/certificat/verifier", formations.verify_certificate)
get("/formations/:slug/landing", formations.landing)
get("/formations/checkout/:id", payment.checkout)
post("/formations/checkout/:id", payment.process_checkout)
get("/paiement/succes", payment.success)
get("/paiement/annulation", payment.cancel)
post("/webhook/stripe", payment.webhook)
post("/api/validate-promo", payment.validate_promo)
get("/mes-commandes", payment.my_orders)
get("/mes-commandes/:id", payment.order_detail)
get("/facture/:id", payment.invoice)

# ---------------------------------------------------------------- leads / projets
post("/api/audit-request", leads.submit_audit)
get("/projets/brief", projects.brief_form)
post("/projets/brief", projects.submit_brief)
post("/api/project-quote", projects.ajax_quote)
get("/espace-client", projects.dashboard)
get("/espace-client/projet/:id", projects.show)
post("/espace-client/projet/:id/message", projects.send_message)
post("/webhook/webox", projects.webhook_webox)

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

# ---------------------------------------------------------------- administration
get("/admin/dashboard", admin.dashboard)
get("/admin/contacts", admin.contacts)
get("/admin/contacts/read", admin.contact_read)
get("/admin/contacts/replied", admin.contact_replied)
get("/admin/newsletters", admin.newsletters)
get("/admin/newsletters/export", admin.export_newsletters)
get("/admin/logout", admin.logout)
get("/admin/webhooks", admin.webhooks)
post("/admin/webhooks/save", admin.save_webhooks)
post("/admin/webhooks/test/:type", admin.test_webhook)
get("/admin/articles", admin.articles)
get("/admin/articles/new", admin.article_new)
post("/admin/articles/store", admin.article_store)
get("/admin/articles/edit/:id", admin.article_edit)
post("/admin/articles/update/:id", admin.article_update)
post("/admin/articles/delete/:id", admin.article_delete)
post("/admin/articles/upload-image", admin.article_upload_image)
get("/admin/formations", admin.formations)
get("/admin/formations/new", admin.formation_new)
post("/admin/formations/store", admin.formation_store)
get("/admin/formations/edit/:id", admin.formation_edit)
post("/admin/formations/update/:id", admin.formation_update)
post("/admin/formations/delete/:id", admin.formation_delete)
get("/admin/media", admin.media)
post("/admin/media/upload", admin.media_upload)
post("/admin/media/delete", admin.media_delete)
get("/admin/analytics", admin.analytics)
get("/admin/projects", admin.projects)
get("/admin/projects/:id", admin.project_show)
post("/admin/projects/:id/status", admin.project_status)
post("/admin/projects/:id/message", admin.project_message)
post("/admin/projects/:id/note", admin.project_note)
post("/admin/projects/:id/generate", admin.project_generate)
post("/admin/projects/:id/task", admin.project_task)
post("/admin/projects/task/update", admin.project_task_update)
post("/admin/projects/:id/price", admin.project_price)
get("/admin/campaigns", admin.campaigns)
get("/admin/campaigns/new", admin.new_campaign)
post("/admin/campaigns/delete/:id", admin.delete_campaign)

ROUTES = R
