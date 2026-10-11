"""Espace élève (FormationController.php) : inscription, leçons, quiz, avis, certificats."""
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from .. import db, php
from ..forms import php_post
from ..models import certificate as Certificate
from ..models import formation as Formation
from ..models import quiz as Quiz
from ..render import render_view
from .common import not_found, redirect


def _uri(request):
    raw = request.scope.get("raw_path", b"").decode("latin-1")
    qs = request.scope.get("query_string", b"").decode("latin-1")
    return raw + ("?" + qs if qs else "")


def _json(payload):
    return Response(php.json_encode(payload), media_type="application/json")


def my_formations(request):
    if "user_id" not in request.session:
        return redirect("/connexion")
    user_id = request.session["user_id"]
    return render_view(request, "formations/my-formations-content", {
        "title": "Mes formations - Digita Marketing",
        "extraCss": ["/assets/css/formations.css"],
        "formations": Formation.get_user_formations(user_id),
        "certificates": Certificate.get_user_certificates(user_id),
    })


async def enroll(request, slug):
    if "user_id" not in request.session:
        request.session["redirect_after_login"] = _uri(request)
        return redirect("/connexion")
    return await run_in_threadpool(_enroll, request, slug)


def _enroll(request, slug):
    user_id = request.session["user_id"]
    f = Formation.get_by_slug(slug)
    if not f:
        return Response(b"", status_code=404, media_type="text/html")
    if Formation.is_enrolled(user_id, f["id"]):
        return redirect("/formations/" + f["slug"])
    if php.floatval(f.get("price") if f.get("price") is not None else 0) > 0:
        return redirect("/formations/checkout/" + php.strval(f["id"]))
    if Formation.enroll(user_id, f["id"]):
        request.session["success_message"] = "Vous êtes maintenant inscrit à cette formation !"
    else:
        request.session["error_message"] = "Erreur lors de l'inscription."
    return redirect("/formations/" + f["slug"])


def learn(request, slug):
    if "user_id" not in request.session:
        request.session["redirect_after_login"] = "/formations/" + slug + "/learn"
        return redirect("/connexion")
    user_id = request.session["user_id"]
    f = Formation.get_full_formation(slug)
    if not f:
        return redirect("/formations")
    if not Formation.is_enrolled(user_id, f["id"]):
        request.session["error_message"] = "Vous devez être inscrit à cette formation pour y accéder."
        return redirect("/formations/" + slug)

    progress = Formation.get_progress(user_id, f["id"])
    completed = Formation.get_completed_lessons(user_id, f["id"])
    lesson_id = php.intval(request.query_params["lesson"]) if "lesson" in request.query_params else None
    if not php.t(lesson_id) and f["modules"] and f["modules"][0]["lessons"]:
        lesson_id = f["modules"][0]["lessons"][0]["id"]

    all_lessons = [lesson for m in f["modules"] for lesson in m["lessons"]]
    current = previous = nxt = None
    for i, lesson in enumerate(all_lessons):
        if php.loose_eq(lesson["id"], lesson_id):
            current = lesson
            if i > 0:
                previous = all_lessons[i - 1]
            if i < len(all_lessons) - 1:
                nxt = all_lessons[i + 1]
            break

    module_quiz = None
    if current:
        module_quiz = Quiz.get_by_module_id(current["module_id"])
        if module_quiz:
            module_quiz["user_passed"] = Quiz.has_passed(user_id, module_quiz["id"])
            module_quiz["attempt_count"] = Quiz.get_attempt_count(user_id, module_quiz["id"])

    is_complete = bool(progress) and progress["percentage"] >= 100
    certificate = Certificate.get_by_user_and_formation(user_id, f["id"]) if is_complete else None
    return render_view(request, "formations/learn-content", {
        "title": php.strval(f["title"]) + " - Apprentissage",
        "formation": f, "currentLesson": current, "previousLesson": previous, "nextLesson": nxt,
        "allLessons": all_lessons, "progress": progress, "completedLessons": completed,
        "moduleQuiz": module_quiz, "isComplete": is_complete, "certificate": certificate,
    }, layout="learn")


async def complete_lesson(request):
    if "user_id" not in request.session:
        return _json({"success": False, "error": "Non connecté"})
    form = await request.form()
    lesson_id = php.intval(form.get("lesson_id", 0))
    formation_id = php.intval(form.get("formation_id", 0))
    if not lesson_id or not formation_id:
        return _json({"success": False, "error": "Paramètres manquants"})
    user_id = request.session["user_id"]

    def work():
        ok = Formation.complete_lesson(user_id, lesson_id, formation_id)
        return {"success": ok, "progress": Formation.get_progress(user_id, formation_id)}
    return _json(await run_in_threadpool(work))


def quiz(request, quiz_id):
    if "user_id" not in request.session:
        return redirect("/connexion")
    q = Quiz.get_by_id(quiz_id)
    if not q:
        return not_found(request, quizId=quiz_id, quiz=q)
    user_id = request.session["user_id"]
    if not Formation.is_enrolled(user_id, q["formation_id"]):
        return redirect("/formations")
    attempts = Quiz.get_attempt_count(user_id, quiz_id)
    return render_view(request, "formations/quiz-content", {
        "title": php.strval(q["title"]) + " - Quiz",
        "quiz": q,
        "questions": Quiz.get_questions(quiz_id),
        "attemptCount": attempts,
        "bestAttempt": Quiz.get_best_attempt(user_id, quiz_id),
        "canAttempt": php.loose_eq(q["max_attempts"], 0) or attempts < q["max_attempts"],
        "formation": Formation.get_by_id(q["formation_id"]),
    })


async def submit_quiz(request, quiz_id):
    if "user_id" not in request.session:
        return redirect("/connexion")
    post = php_post(await request.form())
    return await run_in_threadpool(_submit_quiz, request, quiz_id, post)


def _submit_quiz(request, quiz_id, post):
    user_id = request.session["user_id"]
    q = Quiz.get_by_id(quiz_id)
    if not q:
        return redirect("/formations")
    attempt_id = Quiz.start_attempt(user_id, quiz_id)
    if not attempt_id:
        request.session["error_message"] = "Nombre maximum de tentatives atteint."
        return redirect(f"/formations/quiz/{quiz_id}")
    answers = {}
    for k, v in post.items():
        if k.startswith("question_"):
            answers[php.intval(k.replace("question_", ""))] = v
    results = Quiz.submit_attempt(attempt_id, answers)
    request.session["quiz_results"] = {**(results or {}), "quiz": q}
    return redirect(f"/formations/quiz/{quiz_id}/results")


def quiz_results(request, quiz_id):
    if "user_id" not in request.session:
        return redirect("/connexion")
    results = request.session.pop("quiz_results", None)
    q = Quiz.get_by_id(quiz_id)
    user_id = request.session["user_id"]
    if not results:
        best = Quiz.get_best_attempt(user_id, quiz_id)
        results = {
            "score": best["score"], "max_score": best["max_score"], "percentage": best["percentage"],
            "passed": best["passed"], "results": Quiz.decode_results(best["answers_json"]),
        } if best else None
    if not q:
        # $quiz['formation_id'] sur false : avertissement PHP, donc message d'erreur générique en production.
        raise LookupError(f"quiz {quiz_id} introuvable")
    formation = Formation.get_by_id(q["formation_id"])
    return render_view(request, "formations/quiz-results-content", {
        "title": "Résultats - " + php.strval(q["title"]),
        "quiz": q, "results": results, "formation": formation,
    })


async def review(request, formation_id):
    if "user_id" not in request.session:
        return redirect("/connexion")
    form = await request.form()
    return await run_in_threadpool(_review, request, formation_id, form)


def _review(request, formation_id, form):
    user_id = request.session["user_id"]
    f = Formation.get_by_id(formation_id)
    if not f:
        return redirect("/formations")
    if not Formation.is_enrolled(user_id, f["id"]):
        request.session["error_message"] = "Vous devez être inscrit pour laisser un avis."
        return redirect("/formations/" + f["slug"])
    data = {
        "rating": max(1, min(5, php.intval(form.get("rating", 5)))),
        "title": php.trim(form.get("title", "")),
        "comment": php.trim(form.get("comment", "")),
    }
    if Formation.add_review(user_id, f["id"], data):
        request.session["success_message"] = "Merci pour votre avis ! Il sera publié après modération."
    else:
        request.session["error_message"] = "Erreur lors de l'envoi de votre avis."
    return redirect("/formations/" + f["slug"])


def certificate(request, formation_id):
    if "user_id" not in request.session:
        return redirect("/connexion")
    user_id = request.session["user_id"]
    f = Formation.get_by_id(formation_id)
    if not f:
        return redirect("/formations")
    progress = Formation.get_progress(user_id, f["id"])
    if not progress or progress["percentage"] < 100:
        request.session["error_message"] = "Vous devez terminer la formation pour obtenir votre certificat."
        return redirect("/formations/" + f["slug"] + "/learn")
    return render_view(request, "formations/certificate-content", {
        "title": "Certificat - " + php.strval(f["title"]),
        "certificate": Certificate.generate(user_id, f["id"]),
        "formation": f,
        "user": db.fetch("SELECT * FROM users WHERE id = ?", [user_id]),
    })
