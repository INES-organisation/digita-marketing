"""Génère la version PDF mise en page de chaque pack de master prompts (python/digita/boutique_files/*.md).

Le Markdown reste la source (et la « version texte » livrée avec le PDF, pratique pour copier-coller) ;
relancer ce script après chaque modification d'un pack, puis committer les PDF.

    pip install markdown playwright
    python tools/build_boutique_pdfs.py [chemin/vers/chrome]   # sinon le Chromium de Playwright
"""
import asyncio
import base64
import html
import re
import sys
from pathlib import Path

import markdown
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
FILES = ROOT / "python" / "digita" / "boutique_files"
LOGO = ROOT / "public" / "assets" / "images" / "logo-480.png"

CSS = """
@page { size: A4; margin: 22mm 18mm 20mm 18mm; }
@page :first { margin: 0; }
* { box-sizing: border-box; }
body { font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif; color: #1f2937; font-size: 10.5pt; line-height: 1.6; margin: 0; }
.cover { height: 297mm; width: 210mm; background: #0a0a0a; color: #f3f4f6; padding: 34mm 22mm 24mm; position: relative;
         display: flex; flex-direction: column; page-break-after: always; overflow: hidden; }
.cover::before { content: ""; position: absolute; inset: 0;
         background: radial-gradient(ellipse at 85% 15%, rgba(212,175,55,.28), transparent 55%),
                     radial-gradient(ellipse at 0% 100%, rgba(212,175,55,.12), transparent 50%); }
.cover > * { position: relative; }
.cover img { width: 62mm; margin-bottom: 38mm; }
.cover .kicker { display: inline-block; align-self: flex-start; padding: 2mm 5mm; border: 1px solid rgba(212,175,55,.5); border-radius: 20mm;
         color: #d4af37; font-size: 9pt; font-weight: 700; letter-spacing: 2.5px; text-transform: uppercase; margin-bottom: 9mm; }
.cover h1 { font-size: 34pt; line-height: 1.1; margin: 0 0 9mm; color: #fff; font-weight: 800; letter-spacing: -0.5px; }
.cover h1 span { color: #d4af37; }
.cover .promise { font-size: 12pt; line-height: 1.7; color: #d1d5db; max-width: 150mm; }
.cover .facts { display: flex; gap: 6mm; margin-top: 12mm; }
.cover .facts div { border: 1px solid rgba(255,255,255,.15); border-radius: 4mm; padding: 4mm 6mm; }
.cover .facts strong { display: block; font-size: 20pt; color: #d4af37; }
.cover .facts span { font-size: 9pt; color: #9ca3af; }
.cover .foot { margin-top: auto; font-size: 9pt; color: #9ca3af; border-top: 1px solid rgba(255,255,255,.12); padding-top: 5mm; }
.toc { page-break-after: always; }
.toc h2 { border: 0; }
.toc ol { padding-left: 0; list-style: none; counter-reset: t; }
.toc li { display: flex; gap: 4mm; padding: 2.6mm 0; border-bottom: 1px solid #e5e7eb; font-size: 11pt; }
.toc li b { color: #b8941f; min-width: 9mm; }
h2 { font-size: 17pt; color: #111827; margin: 0 0 5mm; padding-bottom: 3mm; border-bottom: 2px solid #d4af37; line-height: 1.25; }
h2.newpage { page-break-before: always; }
h3 { font-size: 11.5pt; color: #111827; margin: 6mm 0 2mm; }
h3::before { content: ""; display: inline-block; width: 2.2mm; height: 2.2mm; background: #d4af37; border-radius: 50%; margin-right: 2.5mm; vertical-align: middle; }
p { margin: 0 0 3mm; }
ul, ol { margin: 0 0 3mm; padding-left: 6mm; }
li { margin-bottom: 1.2mm; }
strong { color: #111827; }
a { color: #8a6d12; }
hr { border: 0; border-top: 1px solid #e5e7eb; margin: 6mm 0; }
blockquote { margin: 4mm 0; padding: 3mm 5mm; background: #faf6e8; border-left: 3px solid #d4af37; border-radius: 2mm; font-size: 9.5pt; }
blockquote p { margin: 0; }
.prompt { margin: 4mm 0 5mm; border: 1px solid #e5e7eb; border-left: 4px solid #d4af37; border-radius: 3mm; background: #f9fafb; break-inside: auto; }
.prompt .label { font-size: 7.5pt; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #8a6d12;
         padding: 2.5mm 5mm 0; }
.prompt pre { margin: 0; padding: 2.5mm 5mm 4mm; white-space: pre-wrap; word-wrap: break-word;
         font-family: 'JetBrains Mono', 'SFMono-Regular', Menlo, Consolas, monospace; font-size: 8.4pt; line-height: 1.55; color: #111827; }
.prompt pre .sec { color: #8a6d12; font-weight: 700; }
.prompt pre .var { background: #fdf3cf; color: #6b5310; border-radius: 1mm; padding: 0 .6mm; }
code { font-family: 'SFMono-Regular', Menlo, Consolas, monospace; font-size: 9pt; background: #f3f4f6; padding: 0 1mm; border-radius: 1mm; }
"""


def render_code(code):
    """Bloc de prompt : titres de section (« # RÔLE ») et variables [ENTRE_CROCHETS] mis en valeur."""
    out = []
    for line in html.escape(code).split("\n"):
        if re.match(r"^#{1,3} ", line):
            out.append(f'<span class="sec">{line.lstrip("# ")}</span>')
        else:
            out.append(re.sub(r"\[([^\]\n]{2,80})\]", r'<span class="var">[\1]</span>', line))
    return "\n".join(out)


def build_html(md_text, logo_uri):
    lines = md_text.split("\n")
    title = lines[0].lstrip("# ").strip()
    body = "\n".join(lines[1:])
    # Promesse : premier paragraphe après la signature
    body = re.sub(r"^\*\*Par DIGITA[^\n]*\n", "", body.lstrip("\n"), flags=re.M)
    promise, _, body = body.lstrip("\n").partition("\n\n")
    blocks = []

    def stash(match):
        blocks.append(match.group(1))
        return f"\n\nPROMPTBLOCK{len(blocks) - 1}\n\n"

    body = re.sub(r"```[a-z]*\n(.*?)```", stash, body, flags=re.S)
    content = markdown.markdown(body, extensions=["sane_lists"])
    for i, code in enumerate(blocks):
        content = content.replace(f"<p>PROMPTBLOCK{i}</p>",
                                  f'<div class="prompt"><div class="label">À copier dans votre IA</div><pre>{render_code(code)}</pre></div>')
    content = content.replace("<hr />", "")
    heads = re.findall(r"<h2>(.*?)</h2>", content)
    content = re.sub(r"<h2>", '<h2 class="newpage">', content)
    content = content.replace('<h2 class="newpage">', "<h2>", 1)  # « Comment utiliser » suit le sommaire
    toc = "".join(f"<li><b>{i:02d}</b><span>{h}</span></li>" for i, h in enumerate(heads, 1))
    name = title.split("—")[-1].strip()
    n_prompts = sum(1 for h in heads if h.startswith("Prompt"))
    cover = f"""<section class="cover">
<img src="{logo_uri}" alt="DIGITA">
<span class="kicker">Pack de master prompts</span>
<h1>{html.escape(name)}<br><span>{n_prompts} prompts prêts à l'emploi</span></h1>
<div class="promise">{markdown.markdown(promise)}</div>
<div class="facts"><div><strong>{n_prompts}</strong><span>master prompts</span></div><div><strong>1</strong><span>prompt de contexte</span></div><div><strong>4</strong><span>IA compatibles</span></div></div>
<div class="foot">DIGITA · digita.buzz · Licence personnelle : usage pour votre entreprise, revente et diffusion interdites.</div>
</section>"""
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>{CSS}</style></head>
<body>{cover}<section class="toc"><h2>Sommaire</h2><ol>{toc}</ol></section>{content}</body></html>""", title


async def main(executable=None):
    logo_uri = "data:image/png;base64," + base64.b64encode(LOGO.read_bytes()).decode()
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=executable) if executable else await p.chromium.launch()
        page = await browser.new_page()
        for md in sorted(FILES.glob("pack-*.md")):
            doc, title = build_html(md.read_text(encoding="utf-8"), logo_uri)
            await page.set_content(doc, wait_until="load")
            footer = (f'<div style="width:100%;font-size:7.5pt;color:#9ca3af;padding:0 18mm;display:flex;justify-content:space-between;'
                      f'font-family:Arial"><span>DIGITA · {html.escape(title)}</span>'
                      '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
            await page.pdf(path=str(md.with_suffix(".pdf")), format="A4", print_background=True, display_header_footer=True,
                           header_template="<div></div>", footer_template=footer, prefer_css_page_size=True)
            print("PDF :", md.with_suffix(".pdf").name)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
