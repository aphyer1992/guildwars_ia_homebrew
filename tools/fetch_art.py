"""Download reference images and token badges listed in data/art.yaml.

Usage:  python tools/fetch_art.py [--force] [--wide]

Reference images come from wiki.guildwars.com (ArenaNet's art; home use only) and
go to art/reference/<figure>/. Badges come from game-icons.net (CC BY 3.0: credit
"game-icons.net" and the icon's author) and go to art/badges/<author>__<name>.svg.
Files already downloaded are skipped unless --force is given. art/ is gitignored.
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "art"
WIKI_API = "https://wiki.guildwars.com/api.php"
BADGE_URL = "https://raw.githubusercontent.com/game-icons/icons/master/{}.svg"
HEADERS = {"User-Agent": "gw-ia-homebrew/0.1 (personal tabletop project)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
        return r.read()


def wiki_file_urls(names):
    """{file name: download URL} for wiki files (missing files are left out)."""
    titles = "|".join("File:" + n for n in names)
    q = urllib.parse.urlencode({"action": "query", "titles": titles, "prop": "imageinfo",
                                "iiprop": "url", "format": "json"})
    pages = json.loads(get(f"{WIKI_API}?{q}"))["query"]["pages"].values()
    out = {}
    for p in pages:
        if "imageinfo" in p:
            out[p["title"].removeprefix("File:").replace(" ", "_")] = p["imageinfo"][0]["url"]
    return out


def figure_bbox(im, tolerance=45):
    """Bounding box of everything that differs clearly from the corner (background) colour."""
    from PIL import Image, ImageChops
    small = im.resize((max(1, im.width // 4), max(1, im.height // 4)))
    bg = small.getpixel((1, 1))
    diff = ImageChops.difference(small, Image.new("RGB", small.size, bg))
    mask = diff.convert("L").point(lambda v: 255 if v > tolerance else 0)
    box = mask.getbbox() or (0, 0, small.width, small.height)
    return tuple(v * 4 for v in box)


def wide_starts(manifest):
    """Write art/reference/<key>/wide-start.png: a 16:9 waist-up crop to feed image-to-image.

    Image-to-image copies the starting image's composition, so a tall full-length
    reference yields a tall full-length result even at 16:9. This crops a band from the
    figure's head (icon_crop y) downwards: from the figure's final art if it exists, else
    from its first reference image.
    """
    from PIL import Image
    for key, fig in manifest.items():
        finals = [p for p in (ART / "final").glob(f"{key}.*")] if (ART / "final").exists() else []
        refs = sorted((ART / "reference" / key).glob("*")) if (ART / "reference" / key).exists() else []
        src = next(iter(finals), None) or next((r for r in refs if not r.name.startswith("wide-start")), None)
        if not src:
            continue
        im = Image.open(src).convert("RGB")
        w, h = im.size
        x0, y0, x1, y1 = figure_bbox(im)
        fig_h = y1 - y0
        # waist-up band: from just above the head to ~55% down the figure, widened to 16:9
        band_h = fig_h * 0.62
        band_w = max(band_h * 16 / 9, (x1 - x0) * 1.05)
        band_h = band_w * 9 / 16
        cx = (x0 + x1) / 2
        left, top = cx - band_w / 2, y0 - fig_h * 0.05
        box = (int(left), int(top), int(left + band_w), int(top + band_h))
        bg = im.getpixel((2, 2))
        out = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), bg)  # pad past edges with background
        out.paste(im.crop((max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3]))),
                  (max(0, -box[0]), max(0, -box[1])))
        dest = ART / "reference" / key / "wide-start.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        out.save(dest)
        print(f"wide start {key}: from {src.name}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    ap.add_argument("--wide", action="store_true",
                    help="also write art/reference/<key>/wide-start.png (16:9 waist-up start images)")
    a = ap.parse_args()
    manifest = yaml.safe_load((ROOT / "data" / "art.yaml").read_text(encoding="utf-8"))["figures"]
    if a.wide:
        wide_starts(manifest)

    wanted = sorted({n for f in manifest.values() for n in f.get("reference") or []})
    urls = {}
    for i in range(0, len(wanted), 40):  # the API takes up to 50 titles per request
        urls.update(wiki_file_urls(wanted[i:i + 40]))

    problems = []
    for key, fig in manifest.items():
        for name in fig.get("reference") or []:
            dest = ART / "reference" / key / name
            if dest.exists() and not a.force:
                continue
            if name not in urls:
                problems.append(f"{key}: wiki file not found: {name}")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(get(urls[name]))
            print(f"reference  {key}/{name}")
            time.sleep(0.2)  # be polite to the wiki

    for badge in sorted({f["badge"] for f in manifest.values() if f.get("badge")}):
        dest = ART / "badges" / (badge.replace("/", "__") + ".svg")
        if dest.exists() and not a.force:
            continue
        try:
            svg = get(BADGE_URL.format(badge))
        except Exception as e:  # noqa: BLE001 - report and carry on
            problems.append(f"badge not found: {badge} ({e})")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(svg)
        print(f"badge      {badge}")

    for p in problems:
        print("PROBLEM:", p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
