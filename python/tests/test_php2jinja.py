import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from php2jinja import convert  # noqa: E402


def test_echo_et_echappement():
    assert convert("<?= htmlspecialchars($a['b']) ?>") == "{{ h(a['b']) }}"


def test_saut_de_ligne_avale_apres_balise():
    assert convert("<?= $x ?>\n</span>") == "{{ x }}</span>"


def test_conditions_et_boucles():
    out = convert("<?php if (!empty($items)): ?><?php foreach ($items as $i => $it): ?>x<?php endforeach; ?><?php endif; ?>")
    assert out == "{% if (not empty(items)) %}{% for i, it in php_items(items) %}x{% endfor %}{% endif %}"


def test_operateurs():
    assert convert("<?= $a ?? 'd' ?>") == "{{ coalesce(a, 'd') }}"
    assert convert("<?= $a . ' ' . $b ?>") == "{{ cat(cat(a, ' '), b) }}"
    assert convert("<?= $n > 1 ? 's' : '' ?>") == "{{ ('s' if (n > 1) else '') }}"


def test_texte_jinja_protege():
    assert convert("{{ vue }}") == "{% raw %}{{ vue }}{% endraw %}"
