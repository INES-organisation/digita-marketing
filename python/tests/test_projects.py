from digita import config
from digita.models import project as Project
from digita.routes import projects


def test_upload_saved_with_sanitized_name(tmp_path, monkeypatch):
    saved = []
    monkeypatch.setattr(config, "PUBLIC_DIR", tmp_path)
    monkeypatch.setattr(Project, "add_file", lambda pid, uid, data: saved.append((pid, uid, data)))
    path = projects._store_upload("7", 3, "Mon devis (v2).PDF", b"%PDF")
    name = path.rsplit("/", 1)[1]
    assert path.startswith("/uploads/projects/7/") and name.endswith("_Mondevisv2.PDF")
    assert (tmp_path / "uploads" / "projects" / "7" / name).read_bytes() == b"%PDF"
    assert saved == [("7", 3, {"filename": "Mon devis (v2).PDF", "filepath": path, "filetype": "pdf", "filesize": 4})]


def test_upload_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "PUBLIC_DIR", tmp_path)
    monkeypatch.setattr(Project, "add_file", lambda *a: (_ for _ in ()).throw(AssertionError))
    assert projects._store_upload("7", 3, "shell.php", b"<?php") is None
    assert projects._store_upload("7", 3, "big.zip", b"0" * (10 * 1024 * 1024 + 1)) is None
    assert projects._store_upload("..", 3, "a.txt", b"x") is None
    assert not (tmp_path / "uploads").exists()


def test_colors_keep_php_keys():
    assert projects._colors("bleu,vert") == ["bleu", "vert"]
    assert projects._colors("vert,,marron,") == {"0": "vert", "2": "marron"}
    assert projects._colors("") == []


def test_quote():
    assert Project.calculate_quote("ecommerce", {"pages": 9, "urgent": True}) == 2100
    assert Project.calculate_quote("inconnu", {"pages": "abc", "multilingual": "on"}) == 650
