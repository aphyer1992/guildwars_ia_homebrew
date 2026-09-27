"""Render printable token and card sheets from data/ and art/.

Usage:
  python tools/render_print.py            # output/tokens.pdf and output/cards.pdf
  python tools/render_print.py --png      # also PNG previews of all pages
  python tools/render_print.py --prompts  # also output/art-prompts.md for making final art

Art for each figure comes from art/final/<key>.png, or art/final/<key>-icon.png for
the token if present. Until final art exists, the first reference image in
art/reference/<key>/ is used and the card is marked PLACEHOLDER ART. Sizes are in
tools/print_config.yaml; per-figure crops, badges and accents are in data/art.yaml.
Pages are built as HTML and printed to PDF with headless Chrome or Edge.
"""
import argparse
import html
import shutil
import subprocess
from pathlib import Path

import yaml
from PIL import Image

import card_layout

ROOT = Path(__file__).resolve().parent.parent
DATA, ART, OUT = ROOT / "data", ROOT / "art", ROOT / "output"
MM = 1 / 25.4  # inches per mm
BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "google-chrome", "chromium", "msedge"]
ART_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")  # whatever the image tool exports
DIE_COLOURS = {"red": "#c62828", "blue": "#1e5aa8", "green": "#2e7d32", "yellow": "#f2c230",
               "black": "#1b1b1b", "white": "#ffffff"}


def load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


CFG = load(Path(__file__).with_name("print_config.yaml"))
MANIFEST = load(DATA / "art.yaml")["figures"]


# ---------------------------------------------------------------- art lookup

def art_for(key, icon=False):
    """(path, is_placeholder) for a figure's card art or token art, or (None, True)."""
    final = ART / "final"
    stems = ([f"{key}-icon"] if icon else []) + [key]
    for stem in stems:
        for ext in ART_EXTENSIONS:
            if (final / f"{stem}{ext}").exists():
                return final / f"{stem}{ext}", False
    refs = sorted((ART / "reference" / key).glob("*")) if (ART / "reference" / key).exists() else []
    return (refs[0], True) if refs else (None, True)


def rel(path):
    return Path("..", path.relative_to(ROOT)).as_posix()


def crop_css(path, crop, box_in):
    """background-size/position placing (crop.x, crop.y) at the centre of a box."""
    w, h = Image.open(path).size
    width = crop.get("zoom", 1) * box_in
    height = width * h / w
    left = box_in / 2 - crop.get("x", 0.5) * width
    top = box_in / 2 - crop.get("y", 0.5) * height
    return (f"background-image:url('{rel(path)}');background-size:{width:.4f}in {height:.4f}in;"
            f"background-position:{left:.4f}in {top:.4f}in;")


def badge_html(key, size_in):
    fig = MANIFEST.get(key, {})
    if not fig.get("badge"):
        return ""
    svg = ART / "badges" / (fig["badge"].replace("/", "__") + ".svg")
    if not svg.exists():
        return ""
    # game-icons SVGs draw a black square behind a white glyph; drop the square so the
    # glyph sits on the group's accent colour.
    glyph = svg.read_text(encoding="utf-8").replace('<path d="M0 0h512v512H0z"/>', "")
    return (f'<div class="badge" style="width:{size_in}in;height:{size_in}in;'
            f'background:{fig.get("accent", "#444")}">{glyph}</div>')


# ---------------------------------------------------------------- figures

def enemies():
    out = []
    for f in sorted((DATA / "enemies").glob("*.yaml")):
        e = load(f)
        if e.get("status") == "stub":
            print(f"skipped {f.name}: status: stub (remove the status line once it's ready)")
        else:
            out.append((f.stem, e))
    return out


def heroes():
    return [(f.stem, load(f)) for f in sorted((DATA / "heroes").glob("*.yaml"))]


# ---------------------------------------------------------------- tokens

def token_html(key, rim, label):
    t = CFG["token"]
    inner = t["diameter_in"] - 2 * t["rim_mm"] * MM
    path, _ = art_for(key, icon=True)
    art = crop_css(path, MANIFEST.get(key, {}).get("icon_crop", {}), inner) if path else "background:#777;"
    return (f'<div class="cell"><div class="token" style="border-color:{rim}">'
            f'<div class="art" style="{art}"></div>{badge_html(key, 0.3)}</div>'
            f'<div class="label">{html.escape(label)}</div></div>')


def token_sheet():
    rims = CFG["rims"]
    cells = []
    for key, e in enemies():
        n = e.get("group_size") or 1
        for vname, v in e["variants"].items():
            name = v.get("name", e["name"])
            cells += [token_html(key, rims["elite" if vname == "elite" else "regular"], name)] * n
    for key, h in heroes():
        cells.append(token_html(key, rims["hero"], h["name"]))
    t, p = CFG["token"], CFG["page"]
    cell_w, cell_h = t["diameter_in"] + t["gap_in"], t["diameter_in"] + t["gap_in"] + 0.12
    cols = int((p["width_in"] - 0.5) // cell_w)
    rows = int((p["height_in"] - 0.5) // cell_h)
    pages = [cells[i:i + cols * rows] for i in range(0, len(cells), cols * rows)]
    css = f"""
      .sheet {{ display:grid; grid-template-columns:repeat({cols},{cell_w}in);
               grid-auto-rows:{cell_h}in; justify-content:center; padding-top:0.25in; }}
      .cell {{ display:flex; flex-direction:column; align-items:center; }}
      .token {{ position:relative; width:{t['diameter_in']}in; height:{t['diameter_in']}in;
               box-sizing:border-box; border:{t['rim_mm']}mm solid; border-radius:50%;
               overflow:hidden; box-shadow:0 0 0 0.35pt #999; background:#555; }}
      .art {{ position:absolute; inset:0; background-repeat:no-repeat; }}
      .badge {{ position:absolute; left:50%; bottom:0.015in; transform:translateX(-50%);
               border-radius:50%; border:0.6pt solid #fff; display:flex;
               align-items:center; justify-content:center; }}
      .badge svg {{ width:72%; height:72%; }}
      .label {{ font:4.5pt sans-serif; color:#666; margin-top:0.02in; white-space:nowrap; }}
    """
    body = "".join(f'<div class="page"><div class="sheet">{"".join(pg)}</div></div>' for pg in pages)
    return page_doc("Tokens", css, body)


# ---------------------------------------------------------------- cards

def sigil_parts(affiliation):
    """(corner-tab html, watermark html) for an affiliation's sigil image."""
    rel_path = (CFG.get("affiliation_sigils") or {}).get(affiliation or "")
    path = ROOT / rel_path if rel_path else None
    if path and path.exists():
        return (f'<img src="{rel(path)}">', f'<img class="wm" src="{rel(path)}">')
    glyph = card_layout.SYMBOLS["empire" if affiliation == "adversary" else "mercenary"]
    return (f'<span class="sym">{glyph}</span>', f'<div class="wm sym">{glyph}</div>')


def enemy_card(key, e, vname, v):
    path, placeholder = art_for(key)
    fig = MANIFEST.get(key, {})
    crop = fig.get("card_crop") or fig.get("icon_crop") or {}
    art = ""
    if path:
        art = (f"background-image:url('{rel(path)}');"
               f"background-position:{crop.get('x', 0.5) * 100:.0f}% {crop.get('y', 0.35) * 100:.0f}%;")
        if crop.get("fit") == "contain":  # whole image, scaled to the window height, over a plain colour
            art += (f"background-size:auto {crop.get('scale', 0.9) * 100:.0f}%;"
                    f"background-color:{crop.get('bg', '#000')};")
    attack = e.get("attack") or {}
    tab, watermark = sigil_parts(e.get("affiliation"))
    scale = CFG["card"]["width_in"] * 96 / 300  # 300-unit design grid -> CSS px at 96/in
    return card_layout.deployment_card(
        name=v.get("name", e["name"]), elite=vname == "elite", cost=v.get("cost", "?"),
        reinforce=v.get("reinforce"), group=e.get("group_size") or 1, traits=e.get("traits") or [],
        surges=v.get("surges") or [], abilities=(v.get("abilities") or []) + (e.get("abilities") or []),
        health=v.get("health", "?"), speed=e.get("speed") or 4, defense=e.get("defense"),
        attack_type=attack.get("type"), attack_dice=v.get("dice") or attack.get("dice"),
        attack_bonus=v.get("bonus") or attack.get("bonus"), art_style=art, placeholder=placeholder,
        sigil_html=tab, watermark_html=watermark, scale=scale)


def card_sheet():
    c, p = CFG["card"], CFG["page"]
    cards = [enemy_card(key, e, vn, v) for key, e in enemies() for vn, v in e["variants"].items()]
    cols = int(p["width_in"] // c["width_in"])
    rows = int(p["height_in"] // c["height_in"])
    grid_w, grid_h = cols * c["width_in"], rows * c["height_in"]
    mx, my = (p["width_in"] - grid_w) / 2, (p["height_in"] - grid_h) / 2
    marks = "".join(
        f'<div class="mark" style="left:{mx + i * c["width_in"]:.4f}in;top:0;height:{my - 0.05:.4f}in"></div>'
        f'<div class="mark" style="left:{mx + i * c["width_in"]:.4f}in;bottom:0;height:{my - 0.05:.4f}in"></div>'
        for i in range(cols + 1)) + "".join(
        f'<div class="mark h" style="top:{my + j * c["height_in"]:.4f}in;left:0;width:{mx - 0.05:.4f}in"></div>'
        f'<div class="mark h" style="top:{my + j * c["height_in"]:.4f}in;right:0;width:{mx - 0.05:.4f}in"></div>'
        for j in range(rows + 1))
    per = cols * rows
    body = "".join(
        f'<div class="page">{marks}<div class="grid" style="left:{mx}in;top:{my}in;'
        f'grid-template-columns:repeat({cols},{c["width_in"]}in)">{"".join(cards[i:i + per])}</div></div>'
        for i in range(0, len(cards), per))
    css = """
      .grid { position:absolute; display:grid; }
      .mark { position:absolute; width:0; border-left:0.4pt solid #000; }
      .mark.h { height:0; width:auto; border-left:none; border-top:0.4pt solid #000; }
    """ + card_layout.CSS
    return page_doc("Cards", css, body)


# ---------------------------------------------------------------- output

def page_doc(title, css, body):
    p = CFG["page"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{title}</title><style>
      @page {{ size:{p['width_in']}in {p['height_in']}in; margin:0; }}
      html, body {{ margin:0; padding:0; }}
      * {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
      .page {{ position:relative; width:{p['width_in']}in; height:{p['height_in']}in;
               page-break-after:always; overflow:hidden; }}
      {css}</style></head><body>{body}</body></html>"""


def browser():
    for b in BROWSERS:
        if Path(b).exists() or shutil.which(b):
            return b
    raise SystemExit("no Chrome/Edge found to print PDFs")


def to_pdf(html_path, pdf_path):
    subprocess.run([browser(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", f"--print-to-pdf={pdf_path}",
                    html_path.resolve().as_uri()], check=True, capture_output=True)


def prompt_sheet():
    """Markdown prompt sheet for making final art (e.g. in OpenArt)."""
    style = " ".join(load(DATA / "art.yaml")["style"].split())
    lines = ["# Art prompts", "",
             "For each figure, use the reference image as the image-to-image / reference input "
             "(medium strength keeps the silhouette; the prompt supplies weapons, pose and "
             "palette). Save as `art/final/<key>.<png|jpg|jpeg|webp>`.",
             "",
             "**Aspect ratio and composition.** The card's art window is wide and short "
             "(about 1.9:1), and the name bar covers its top fifth. Generate **16:9** (or 2:1 if "
             "offered), at least 1920 x 1080. Frame the figure **from the knees or waist up**, "
             "centred, with a little empty space above the head. A full-length figure in 4:3 "
             "gets cropped to its chest. For art you already have, `card_crop: {fit: contain}` "
             "in data/art.yaml shows the whole image on a plain background instead.",
             "",
             "**Image-to-image copies the starting image's framing,** so a tall full-length "
             "reference gives a tall full-length result even at 16:9 (the tool just pads the "
             "sides). Run `python tools/fetch_art.py --wide` and start from "
             "`art/reference/<key>/wide-start.png` instead: a 16:9 waist-up crop around the "
             "figure, taken from your existing art if there is some (so the character stays "
             "the same), otherwise from the wiki reference.",
             "",
             "**Fixing a result.** Adding emphasis (\"MORE BESTIAL\") helps. It works better "
             "to remove words that pull the other way, and to list unwanted traits under "
             "Avoid (or in a negative prompt field, if the tool has one). Lower image-to-image "
             "strength lets the prompt override the reference more.",
             "",
             "If the token crop of the card art doesn't work, also make a square close-up "
             "portrait as `art/final/<key>-icon.<ext>`.",
             "", f"**Shared style:** {style}", ""]
    for key, fig in MANIFEST.items():
        refs = ", ".join([f"`art/reference/{key}/wide-start.png` (preferred)"]
                         + [f"`art/reference/{key}/{r}`" for r in fig.get("reference") or []])
        badge = f" Token badge: {fig['badge']} on {fig['accent']}." if fig.get("badge") else ""
        lines += [f"## {key}", "", f"Reference: {refs}.{badge}", "",
                  f"> {' '.join(fig.get('prompt', '').split())}. {style}", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--png", action="store_true", help="also write PNG previews of each page")
    ap.add_argument("--prompts", action="store_true", help="also write output/art-prompts.md")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    if a.prompts:
        (OUT / "art-prompts.md").write_text(prompt_sheet(), encoding="utf-8")
        print("wrote output/art-prompts.md")
    for name, doc in (("tokens", token_sheet()), ("cards", card_sheet())):
        h = OUT / f"{name}.html"
        h.write_text(doc, encoding="utf-8")
        to_pdf(h, OUT / f"{name}.pdf")
        print(f"wrote output/{name}.pdf")
        if a.png:
            pages = doc.count('<div class="page"')
            p = CFG["page"]
            subprocess.run([browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--allow-file-access-from-files", "--force-device-scale-factor=1.5",
                            f"--window-size={int(p['width_in'] * 96)},{int(p['height_in'] * 96 * pages)}",
                            f"--screenshot={OUT / f'{name}-preview.png'}", h.resolve().as_uri()],
                           check=True, capture_output=True)
            print(f"wrote output/{name}-preview.png ({pages} page(s))")


if __name__ == "__main__":
    main()
