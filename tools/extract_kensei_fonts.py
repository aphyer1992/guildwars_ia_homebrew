"""Extract the fonts embedded in the Kensei Imperial Assault Tools Suite.

Usage:  python tools/extract_kensei_fonts.py [path-to-ImpAss.Resources.dll]

Writes art/fonts/ (gitignored: these fonts aren't ours to redistribute):
  ImperialAssaultSymbols.ttf   IA game symbols (fan font by "a1bert"), used for
                               <surge>, <damage>, <strain>, ... in card text
  MinionPro-*.otf              IA's body font
Agency FB (IA's title font) ships with Windows/Office, so it isn't needed here.
"""
import struct
import sys
from pathlib import Path

DEFAULT = Path(r"C:\Program Files\Kensei\Kensei Imperial Assault Tools Suite\ImpAss.Resources.dll")
OUT = Path(__file__).resolve().parent.parent / "art" / "fonts"
WANTED = {"ImperialAssaultSymbols": "ImperialAssaultSymbols.ttf",
          "MinionPro-Regular": "MinionPro-Regular.otf", "MinionPro-Bold": "MinionPro-Bold.otf",
          "MinionPro-It": "MinionPro-It.otf", "MinionPro-BoldIt": "MinionPro-BoldIt.otf"}


def fonts_in(blob):
    """Yield (postscript-or-family name, font bytes) for each embedded sfnt font."""
    for sig in (b"\x00\x01\x00\x00", b"OTTO"):
        i = 0
        while (i := blob.find(sig, i)) >= 0:
            try:
                num = struct.unpack(">H", blob[i + 4:i + 6])[0]
                if not 4 <= num <= 40:
                    raise ValueError
                tables, end = {}, 0
                for k in range(num):
                    rec = blob[i + 12 + 16 * k:i + 28 + 16 * k]
                    if not all(32 <= c < 127 for c in rec[:4]):
                        raise ValueError
                    off, ln = struct.unpack(">II", rec[8:16])
                    tables[rec[:4].decode()] = off
                    end = max(end, off + ln)
                if "name" not in tables or end > 5_000_000:
                    raise ValueError
                data = blob[i:i + end]
                nt = data[tables["name"]:]
                count, strings = struct.unpack(">HH", nt[2:6])
                names = {}
                for r in range(count):
                    pid, _, _, nid, ln, off = struct.unpack(">HHHHHH", nt[6 + 12 * r:18 + 12 * r])
                    raw = nt[strings + off:strings + off + ln]
                    names[nid] = raw.decode("utf-16-be", "ignore") if pid in (0, 3) else raw.decode("latin1")
                yield names.get(6) or names.get(1, ""), data
                i += end
            except (ValueError, struct.error):
                i += 4


def main():
    dll = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    OUT.mkdir(parents=True, exist_ok=True)
    got = set()
    for name, data in fonts_in(dll.read_bytes()):
        if name in WANTED and name not in got:
            (OUT / WANTED[name]).write_bytes(data)
            got.add(name)
            print("wrote", OUT / WANTED[name])
    missing = set(WANTED) - got
    if missing:
        sys.exit(f"not found: {sorted(missing)}")


if __name__ == "__main__":
    main()
