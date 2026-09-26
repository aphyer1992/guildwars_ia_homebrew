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

ROOT = Path(__file__).resolve().parent.parent
DATA, ART, OUT = ROOT / "data", ROOT / "art", ROOT / "output"
MM = 1 / 25.4  # inches per mm
BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "google-chrome", "chromium", "msedge"]
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
    for name in ([f"{key}-icon.png"] if icon else []) + [f"{key}.png", f"{key}.jpg"]:
        if (final / name).exists():
            return final / name, False
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
        if e.get("status") != "stub":
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

def dice_html(dice):
    return "".join(f'<span class="die" style="background:{DIE_COLOURS[d]}"></span>' for d in dice or [])


def surge_html(s):
    text = s
    icons = "&#9889;"  # lightning: surge
    if s.lower().startswith("2 surges:"):
        icons, text = "&#9889;&#9889;", s.split(":", 1)[1].strip()
    return f'<div class="surge"><span class="si">{icons}</span> {html.escape(text)}</div>'


def ability_html(a):
    return (f'<div class="ability"><b>{html.escape(a.get("name", ""))}:</b> '
            f'{html.escape(" ".join((a.get("text") or "").split()))}</div>')


def enemy_card(key, e, vname, v):
    c = CFG["card"]
    border = CFG["card_borders"]["elite" if vname == "elite" else "regular"]
    path, placeholder = art_for(key)
    crop = MANIFEST.get(key, {}).get("icon_crop", {})
    art = (f"background-image:url('{rel(path)}');background-size:cover;"
           f"background-position:{crop.get('x', 0.5) * 100:.0f}% {crop.get('y', 0.3) * 100:.0f}%;"
           if path else "background:#666;")
    attack = e.get("attack") or {}
    dice = v.get("dice") or attack.get("dice")
    abilities = (v.get("abilities") or []) + (e.get("abilities") or [])
    group = e.get("group_size") or 1
    cost = f'{v.get("cost", "?")}' + (f'<small>/{v["reinforce"]}</small>' if v.get("reinforce") else "")
    bonus = attack.get("bonus")
    return f"""
      <div class="card" style="width:{c['width_in']}in;height:{c['height_in']}in;border-color:{border}">
        <div class="head" style="background:{border}">
          <div class="name">{html.escape(v.get('name', e['name']))}</div>
          <div class="cost">{cost}</div>
        </div>
        <div class="sub">{html.escape((e.get('affiliation') or '').title())}
          {"".join('<span class="pip"></span>' for _ in range(group))}</div>
        <div class="cart" style="{art}">{'<div class="ph">PLACEHOLDER ART</div>' if placeholder else ''}
          {badge_html(key, 0.28)}</div>
        <div class="stats">
          <span>&#10084; {v.get('health', '?')}</span><span>&#10140; {e.get('speed', '?')}</span>
          <span>DEF {dice_html(e.get('defense'))}</span>
        </div>
        <div class="attack"><b>{html.escape((attack.get('type') or '?').title())}</b> {dice_html(dice)}
          {f'<span class="bonus">{html.escape(bonus)}</span>' if bonus else ''}</div>
        <div class="text">
          {"".join(surge_html(s) for s in v.get('surges') or [] if s)}
          {"".join(ability_html(a) for a in abilities)}
        </div>
      </div>"""


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
      .card { box-sizing:border-box; border:0.1in solid; background:#f4efe4; position:relative;
              display:flex; flex-direction:column; overflow:hidden; font-family:Georgia,serif; }
      .head { display:flex; justify-content:space-between; align-items:center; color:#fff;
              padding:0 0.03in 0.02in; }
      .name { font-weight:bold; font-size:8.5pt; line-height:1.05; }
      .cost { font-weight:bold; font-size:11pt; }
      .cost small { font-size:7pt; }
      .sub { font-size:5.5pt; color:#555; padding:0.01in 0.04in; display:flex; gap:0.03in; align-items:center; }
      .pip { width:0.06in; height:0.06in; background:#555; display:inline-block; }
      .cart { position:relative; height:1.55in; background-repeat:no-repeat; background-color:#333; }
      .ph { position:absolute; top:0.03in; left:0.03in; font:bold 4.5pt sans-serif; color:#fff;
            background:rgba(0,0,0,.55); padding:0.01in 0.03in; }
      .cart .badge { position:absolute; right:0.04in; bottom:0.04in; border-radius:50%;
                     border:0.6pt solid #fff; display:flex; align-items:center; justify-content:center; }
      .cart .badge svg { width:72%; height:72%; }
      .stats, .attack { display:flex; gap:0.08in; align-items:center; font-size:7pt;
                        padding:0.025in 0.05in; border-bottom:0.4pt solid #cbbfa6; }
      .die { display:inline-block; width:0.13in; height:0.13in; border-radius:0.02in;
             border:0.4pt solid #333; margin-right:0.015in; vertical-align:middle; }
      .bonus { font-size:6pt; font-style:italic; }
      .text { font-size:6.4pt; line-height:1.2; padding:0.03in 0.05in; }
      .surge { margin-bottom:0.01in; }
      .si { color:#b8860b; }
      .ability { margin-top:0.025in; }
    """
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
             "palette). Card art is shown about 2.05 x 1.55 in (4:3 landscape): generate at "
             "least 1200 x 900 px. Save as `art/final/<key>.png`. If the token crop of the card "
             "art doesn't work, also make a square close-up portrait as `art/final/<key>-icon.png`.",
             "", f"**Shared style:** {style}", ""]
    for key, fig in MANIFEST.items():
        refs = ", ".join(f"`art/reference/{key}/{r}`" for r in fig.get("reference") or [])
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
