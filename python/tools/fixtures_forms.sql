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
INSERT INTO promo_codes (id, code, discount_type, discount_value, max_uses, used_count, valid_from, valid_until, is_active) VALUES
  (9301, 'BIENVENUE20', 'percent', 20.00, NULL, 0, NULL, NULL, 1),
  (9302, 'FIXE50', 'fixed', 50.00, 10, 0, '2020-01-01 00:00:00', '2037-12-31 00:00:00', 1),
  (9303, 'OFFERT', 'percent', 100.00, 5, 0, NULL, NULL, 1),
  (9304, 'EXPIRE', 'percent', 10.00, NULL, 0, NULL, '2021-01-01 00:00:00', 1),
  (9305, 'INACTIF', 'fixed', 5.00, NULL, 0, NULL, NULL, 0),
  (9306, 'EPUISE', 'fixed', 5.00, 1, 1, NULL, NULL, 1);
-- Projets clients : un administrateur de test (mot de passe « adminpass1 ») et un projet complet
-- lié à Webox, qui n'appartient pas aux comptes créés pendant le parcours.
INSERT INTO users (id, username, email, password, role) VALUES
  (9501, 'Admin Test', 'admin-test@example.com', '$2y$10$B2nd82v8svuWAQDf6q7dgeMkbRzmMA7lwyrgbQONlFDYK3O5LkMAi', 'admin');
INSERT INTO client_projects (id, client_id, project_type, title, brief, brief_data, status, priority, webox_project_id,
                             price, estimated_days, created_at, updated_at) VALUES
  (9401, 9501, 'website', 'Site de test', 'Brief de test', '{"pages": 6, "colors": ["bleu"]}', 'generating', 'low',
   'wbx-9401', 550.00, 7, '2024-01-01 10:00:00', '2024-01-02 10:00:00');
INSERT INTO project_messages (id, project_id, user_id, message, is_admin, is_read, attachment, created_at) VALUES
  (9411, 9401, 9501, 'Bienvenue sur votre projet', 1, 0, NULL, '2024-01-01 11:00:00'),
  (9412, 9401, 9501, 'Pièce jointe', 0, 1, '/uploads/projects/9401/a.pdf', '2024-01-01 12:00:00');
INSERT INTO project_files (id, project_id, user_id, filename, filepath, filetype, filesize, created_at) VALUES
  (9421, 9401, 9501, 'a.pdf', '/uploads/projects/9401/a.pdf', 'pdf', 2048, '2024-01-01 12:00:00');
INSERT INTO project_tasks (id, project_id, title, description, status, sort_order) VALUES
  (9431, 9401, 'Maquette', 'Première version', 'done', 1), (9432, 9401, 'Intégration', NULL, 'todo', 2);
INSERT INTO project_status_history (id, project_id, old_status, new_status, changed_by, note, created_at) VALUES
  (9441, 9401, NULL, 'pending', 9501, 'Projet créé', '2024-01-01 10:00:00'),
  (9442, 9401, 'pending', 'generating', 9501, NULL, '2024-01-01 10:30:00');
INSERT INTO client_context (id, session_id, user_id, business_sector, business_goals, target_audience, lead_score,
                            created_at, updated_at) VALUES
  (9451, 'aucune', 9501, 'Restauration', 'Plus de réservations', 'Familles', 70, '2024-01-01 10:00:00', '2024-01-01 10:00:00');
-- Administration : messages de contact et abonnés newsletter (deux d'aujourd'hui, à la même seconde).
INSERT INTO contact_messages (id, name, email, phone, subject, message, status, created_at) VALUES
  (9601, 'Alice', 'alice@example.com', '0692000000', 'Devis site', 'Bonjour, un devis ?', 'new', '2024-03-01 09:00:00'),
  (9602, 'Bob', 'bob@example.com', NULL, 'Question', 'Une question', 'read', '2024-03-01 09:00:00'),
  (9603, 'Chloé', 'chloe@example.com', NULL, 'Merci', 'Merci <b>beaucoup</b>', 'replied', '2024-02-01 08:00:00');
INSERT INTO contact_messages (id, name, email, subject, message) VALUES
  (9604, 'Dan', 'dan@example.com', 'Aujourd''hui', 'Message du jour');
INSERT INTO newsletters (id, email, status, created_at) VALUES
  (9701, 'a@example.com', 'active', '2024-03-01 09:00:00'),
  (9702, 'b,c@example.com', 'active', '2024-03-01 09:00:00'),
  (9703, 'd@example.com', 'inactive', '2024-01-01 09:00:00');
INSERT INTO newsletters (id, email) VALUES (9704, 'today@example.com');
-- MySQL avance AUTO_INCREMENT après un id explicite, pas PostgreSQL : on aligne les séquences
-- pour que les lignes créées pendant le parcours reçoivent les mêmes id des deux côtés.
-- pg: DO $$ DECLARE t text; BEGIN FOREACH t IN ARRAY ARRAY['users', 'quizzes', 'quiz_questions', 'quiz_answers', 'promo_codes', 'client_projects', 'project_messages', 'project_files', 'project_tasks', 'project_status_history', 'client_context', 'contact_messages', 'newsletters'] LOOP EXECUTE 'SELECT setval(pg_get_serial_sequence(' || quote_literal(t) || ', ''id''), (SELECT max(id) FROM ' || quote_ident(t) || '))'; END LOOP; END $$;
