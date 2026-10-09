"""Quiz (équivalent de app/Models/Quiz.php, partie élève)."""
import json

from .. import db, php
from . import key


def get_by_id(quiz_id):
    return db.fetch("""SELECT q.*, fm.title as module_title, fm.formation_id
                       FROM quizzes q LEFT JOIN formation_modules fm ON q.module_id = fm.id
                       WHERE q.id = ?""", [key(quiz_id)])


def get_by_module_id(module_id):
    return db.fetch("SELECT * FROM quizzes WHERE module_id = ? AND is_active = 1 ORDER BY id LIMIT 1", [module_id])


def get_questions(quiz_id):
    questions = db.fetch_all("SELECT * FROM quiz_questions WHERE quiz_id = ? ORDER BY order_num NULLS FIRST, id",
                             [key(quiz_id)])
    for q in questions:
        q["answers"] = db.fetch_all("SELECT * FROM quiz_answers WHERE question_id = ? "
                                    "ORDER BY order_num NULLS FIRST, id", [q["id"]])
    return questions


def start_attempt(user_id, quiz_id):
    quiz = get_by_id(quiz_id)
    if not quiz:
        return None
    if quiz["max_attempts"] > 0 and get_attempt_count(user_id, quiz_id) >= quiz["max_attempts"]:
        return None
    row = db.fetch("INSERT INTO quiz_attempts (user_id, quiz_id) VALUES (?, ?) RETURNING id", [user_id, key(quiz_id)])
    return str(row["id"])  # lastInsertId() renvoie une chaîne


def submit_attempt(attempt_id, answers):
    attempt = db.fetch("SELECT * FROM quiz_attempts WHERE id = ?", [attempt_id])
    if not attempt:
        return None
    quiz = get_by_id(attempt["quiz_id"])
    score = max_score = 0
    results = []
    for question in get_questions(attempt["quiz_id"]):
        max_score += question["points"]
        user_answer = answers.get(question["id"])
        correct = False
        if question["question_type"] in ("single", "true_false"):
            correct = any(php.t(a["is_correct"]) and php.loose_eq(a["id"], user_answer) for a in question["answers"])
        elif question["question_type"] == "multiple":
            correct_ids = sorted(a["id"] for a in question["answers"] if php.t(a["is_correct"]))
            user_ids = sorted(user_answer, key=php.num) if isinstance(user_answer, list) else []
            correct = len(correct_ids) == len(user_ids) and all(php.loose_eq(a, b) for a, b in zip(correct_ids, user_ids))
        if correct:
            score += question["points"]
        results.append({"question_id": question["id"], "user_answer": user_answer,
                        "is_correct": correct, "explanation": question["explanation"]})
    percentage = php.php_round(score / max_score * 100, 2) if max_score > 0 else 0
    passed = percentage >= quiz["passing_score"]
    db.execute("""UPDATE quiz_attempts SET score = ?, max_score = ?, percentage = ?, passed = ?,
                  answers_json = ?, completed_at = LOCALTIMESTAMP(0) WHERE id = ?""",
               [score, max_score, percentage, 1 if passed else 0, php.json_encode(results), attempt_id])
    return {"score": score, "max_score": max_score, "percentage": percentage, "passed": passed, "results": results}


def get_attempt_count(user_id, quiz_id):
    return db.fetch("SELECT COUNT(*) as count FROM quiz_attempts WHERE user_id = ? AND quiz_id = ?",
                    [user_id, key(quiz_id)])["count"]


def get_best_attempt(user_id, quiz_id):
    return db.fetch("""SELECT * FROM quiz_attempts WHERE user_id = ? AND quiz_id = ? AND completed_at IS NOT NULL
                       ORDER BY percentage DESC NULLS LAST, id LIMIT 1""", [user_id, key(quiz_id)])


def has_passed(user_id, quiz_id):
    return bool(db.fetch("SELECT id FROM quiz_attempts WHERE user_id = ? AND quiz_id = ? AND passed = 1 LIMIT 1",
                         [user_id, quiz_id]))


def decode_results(text):
    try:
        return json.loads(text) if text else None
    except ValueError:
        return None
