"""Équivalents PHP : comportements vérifiés contre PHP 8.3."""
from decimal import Decimal

from jinja2 import ChainableUndefined

from digita import php


def test_htmlspecialchars_comme_php():
    assert php.h("""<a href="x">l'été & co</a>""") == "&lt;a href=&quot;x&quot;&gt;l&#039;été &amp; co&lt;/a&gt;"
    assert php.h(None) == ""


def test_verite_php():
    assert not php.t("0") and not php.t("") and not php.t(0) and not php.t([]) and not php.t(None)
    assert php.t("0.00") and php.t(Decimal("0.00")) and php.t("a") and php.t([0])
    assert not php.t(ChainableUndefined())


def test_echo_php():
    assert php.finalize(None) == "" and php.finalize(True) == "1" and php.finalize(False) == ""
    assert php.finalize(3.0) == "3" and php.finalize(2.5) == "2.5"


def test_number_format_arrondi_commercial():
    assert php.number_format(1234.5) == "1,235"
    assert php.number_format(Decimal("49.00"), 2, ",", " ") == "49,00"
    assert php.number_format(1234567.891, 2, ",", " ") == "1 234 567,89"


def test_mb_strimwidth():
    assert php.mb_strimwidth("abcdefghij", 0, 5, "...") == "ab..."
    assert php.mb_strimwidth("abc", 0, 5, "...") == "abc"


def test_substr_coupe_en_octets():
    assert php.substr("éte", 0, 2) == "é"
    assert php.substr("été", 0, 1) == "�"


def test_str_word_count_ascii():
    assert php.str_word_count("Hello world") == 2
    assert php.str_word_count("été chaud") == 2  # comme PHP : « é » coupe le mot, reste « t »


def test_date_et_strtotime():
    ts = php.strtotime("2025-10-26 22:34:10")
    assert php.date("d/m/Y H:i", ts) == "26/10/2025 22:34"
    assert php.date("j F Y", ts) == "26 October 2025"


def test_preg_replace():
    assert php.preg_replace("/^## (.+)$/m", '<h2 id="$1">$1</h2>', "a\n## T\nb") == 'a\n<h2 id="T">T</h2>\nb'


def test_boucle_for_php_bornes_flottantes():
    assert php.php_upto(1, 3.0, True) == [1, 2, 3]
    assert php.php_upto(1, 3.5, False) == [1, 2, 3]
