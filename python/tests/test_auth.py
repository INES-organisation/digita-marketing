from digita.routes.auth import _hash, _verify

# Généré par PHP : password_hash('motdepasse1', PASSWORD_DEFAULT)
PHP_HASH = "$2y$10$ELIrjTmxGkY5wsYLw5d.nelB165saIJ/7IhCuniRLeD5v4HqRDA5y"


def test_verify_php_hash():
    assert _verify("motdepasse1", PHP_HASH)
    assert not _verify("motdepasse2", PHP_HASH)


def test_hash_keeps_php_prefix():
    h = _hash("motdepasse1")
    assert h.startswith("$2y$10$")
    assert _verify("motdepasse1", h)


def test_verify_invalid_hash():
    assert not _verify("x", "pas-un-hash")
