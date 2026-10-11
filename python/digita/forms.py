"""$_POST à la manière de PHP : « nom[] » devient une liste, « nom[cle] » un dictionnaire."""
import re

_KEY = re.compile(r"^([^\[\]]+)((?:\[[^\[\]]*\])*)$")


def php_post(form):
    out = {}
    for raw, value in form.multi_items():
        if not isinstance(value, str):
            continue  # fichiers : $_FILES, traités à part
        m = _KEY.match(raw)
        if not m or not m.group(2):
            out[raw] = value  # la dernière valeur l'emporte, comme en PHP
            continue
        keys = re.findall(r"\[([^\[\]]*)\]", m.group(2))
        node, name = out, m.group(1)
        for k in keys:
            child = node.get(name)
            if not isinstance(child, (dict, list)):
                child = [] if k == "" else {}
                node[name] = child
            if isinstance(child, list) and k != "":
                child = node[name] = dict(enumerate(child))
            node, name = child, k
        if isinstance(node, list):
            node.append(value)
        else:
            node[name] = value
    return out
