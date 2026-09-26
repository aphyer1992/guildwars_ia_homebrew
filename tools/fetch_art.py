"""Download reference images and token badges listed in data/art.yaml.

Usage:  python tools/fetch_art.py [--force]

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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    a = ap.parse_args()
    manifest = yaml.safe_load((ROOT / "data" / "art.yaml").read_text(encoding="utf-8"))["figures"]

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
