"""Certificats (équivalent de app/Models/Certificate.php)."""
import hashlib
import random
import time as _time

from .. import db, php


def get_by_user_and_formation(user_id, formation_id):
    return db.fetch("""SELECT c.*, f.title as formation_title, f.slug as formation_slug
                       FROM certificates c JOIN formations f ON c.formation_id = f.id
                       WHERE c.user_id = ? AND c.formation_id = ?""", [user_id, formation_id])


def get_user_certificates(user_id):
    return db.fetch_all("""SELECT c.*, f.title as formation_title, f.slug as formation_slug,
                                  f.image_url as formation_image
                           FROM certificates c JOIN formations f ON c.formation_id = f.id
                           WHERE c.user_id = ? ORDER BY c.issued_at DESC NULLS LAST, c.id DESC""", [user_id])


def generate(user_id, formation_id):
    existing = get_by_user_and_formation(user_id, formation_id)
    if existing:
        return existing
    row = db.fetch("INSERT INTO certificates (user_id, formation_id, certificate_number) VALUES (?, ?, ?) "
                   "RETURNING id", [user_id, formation_id, _number()])
    db.execute("UPDATE formation_enrollments SET completed = 1, completed_at = NOW() "
               "WHERE user_id = ? AND formation_id = ?", [user_id, formation_id])
    return db.fetch("SELECT * FROM certificates WHERE id = ?", [row["id"]])


def _number():
    # 'DM-' . date('Y') . '-' . strtoupper(substr(md5(uniqid(mt_rand(), true)), 0, 8))
    seed = f"{random.getrandbits(31)}{_time.time_ns()}{random.random()}"
    return "DM-" + php.date("Y") + "-" + hashlib.md5(seed.encode()).hexdigest()[:8].upper()
