from digita import config, php
from digita.models import article
from digita.routes import admin


def test_slug_matches_php_byte_classes():
    # Sans /u, [àáâãäå] remplace chaque octet UTF-8 : « é » (C3 A9) devient « ae » (valeur vérifiée avec php -r).
    assert article.php_slug(" Été à La Réunion : ça déçoit ? ") == "a-tae-aa-la-raeunion-aca-daeacoit"
    assert article.php_slug("SEO & Ads 2024") == "seo-ads-2024"


def test_fputcsv_quotes_like_php():
    assert admin.fputcsv(["Email", "Date"]) == "Email,Date\n"
    assert admin.fputcsv(["b,c@example.com", "2024-03-01 09:00:00"]) == '"b,c@example.com","2024-03-01 09:00:00"\n'
    assert admin.fputcsv(['a"b', None]) == '"a""b",\n'


def test_image_upload_checks_type_and_extension(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PUBLIC_DIR", tmp_path)
    path = admin._store_image(("photo.JPG", "image/jpeg", b"\xff\xd8"), "articles", "article_")
    assert path.startswith("/uploads/articles/article_") and path.endswith(".JPG")
    assert (tmp_path / path.lstrip("/")).read_bytes() == b"\xff\xd8"
    # Le PHP acceptait x.php envoyé avec le type image/png.
    assert admin._store_image(("x.php", "image/png", b"<?php"), "articles", "article_") is None
    assert admin._store_image(("x.png", "text/html", b"<b>"), "articles", "article_") is None
    assert admin._store_image(("big.png", "image/png", b"0" * (5 * 1024 * 1024 + 1)), "articles", "a_") is None


def test_strict_and_loose_comparisons():
    assert php.same(0, False) is False and php.same(False, False)
    assert php.loose_eq("3", 3) and not php.loose_eq("abc", 0)
    assert php.to_array(None) == [] and php.to_array("x") == ["x"] and php.to_array(["a"]) == ["a"]
