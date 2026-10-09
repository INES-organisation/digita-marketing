-- Données de test pour tools/post_parity.py, appliquées à l'identique dans MySQL et PostgreSQL.
-- Toutes les formations de l'export sont payantes et aucun quiz n'existe : on rend la formation 2
-- gratuite et on lui ajoute un quiz sur son premier module.
UPDATE formations SET price = 0 WHERE id = 2;
INSERT INTO quizzes (id, module_id, title, description, passing_score, time_limit_minutes, max_attempts, is_active)
VALUES (9001, 6, 'Quiz de test', 'Vérification', 60, 0, 2, 1);
INSERT INTO quiz_questions (id, quiz_id, question, question_type, explanation, points, order_num) VALUES
  (9101, 9001, 'Question simple', 'single', 'Explication A', 1, 1),
  (9102, 9001, 'Question multiple', 'multiple', 'Explication B', 2, 2),
  (9103, 9001, 'Vrai ou faux', 'true_false', NULL, 1, 3);
INSERT INTO quiz_answers (id, question_id, answer_text, is_correct, order_num) VALUES
  (9201, 9101, 'Bonne', 1, 1), (9202, 9101, 'Mauvaise', 0, 2),
  (9203, 9102, 'Oui 1', 1, 1), (9204, 9102, 'Oui 2', 1, 2), (9205, 9102, 'Non', 0, 3),
  (9206, 9103, 'Vrai', 1, 1), (9207, 9103, 'Faux', 0, 2);
