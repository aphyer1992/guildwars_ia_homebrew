"""IA-style deployment card layout (HTML/CSS) with game symbols.

The layout mirrors Imperial Assault deployment cards: cost / reinforcement boxes, name
banner and affiliation tab along the top; trait tab; group-size bars; art; surge
boxes; ability text over a faint affiliation watermark; Health / Speed / Defense /
Attack tabs along the bottom. It's designed on a 300 x 467 unit grid (Kensei's
export size) and scaled to the physical card size, so text and symbols stay vector.

Card text understands Kensei-style tags, e.g. <surge> <damage> <strain> <block>
<evade> <dodge> <power-block> <action> <ability>...</ability> <b> <i> <br>, drawn
from the ImperialAssaultSymbols font extracted by tools/extract_kensei_fonts.py.
"""
import html
import re

# ImperialAssaultSymbols glyphs (same letter code as the IA rules PDFs).
SYMBOLS = {
    "action": "A", "surge": "B", "strain": "C", "threat": "D", "dodge": "E", "evade": "F",
    "block": "G", "damage": "H", "tech": "I", "insight": "J", "strength": "K", "might": "K",
    "ranged": "O", "range": "O", "melee": "P", "attack-action": "Q", "armor": "R", "armour": "R",
    "equipment": "S", "empire": "U", "imperial": "U", "rebellion": "V", "rebel": "V",
    "mercenary": "W", "mercenaries": "W", "merc": "W", "scum": "W",
    "power-surge": "b", "power-any": "e", "power-evade": "f", "power-block": "g", "power-damage": "h",
    "core-set": "0", "core": "0", "twin-shadows": "1", "return-to-hoth": "2", "hoth": "2",
    "bespin-gambit": "3", "bespin": "3", "jabbas-realm": "4", "jabba": "4",
    "heart-of-the-empire": "5", "hote": "5", "tyrants-of-lothal": "6", "lothal": "6",
}
DIE_COLOURS = {"red": "#d7262b", "blue": "#1f9ad6", "green": "#3aa63f", "yellow": "#f5d000",
               "black": "#1d1d1d", "white": "#ffffff"}
FORMAT_TAGS = {"b": "b", "bold": "b", "i": "i", "italic": "i", "ability": "b class='ab'",
               "heroability": "b class='ab'", "skill": "b class='ab'", "trait": "i", "c": "span class='c'",
               "center": "span class='c'", "centre": "span class='c'"}


def sym(name):
    return f'<span class="sym">{SYMBOLS[name]}</span>'


def die(colour):
    return f'<span class="die" style="background:{DIE_COLOURS[colour]}"></span>'


def rich(text):
    """Escape card text and turn Kensei-style tags into symbols and formatting."""
    out = html.escape(" ".join((text or "").split()), quote=False)

    def tag(m):
        close, name = m.group(1), m.group(2).lower()
        if name in SYMBOLS and not close:
            return sym(name)
        if name.startswith("dice-") and name[5:] in DIE_COLOURS:
            return die(name[5:])
        if name in FORMAT_TAGS:
            el = FORMAT_TAGS[name]
            return f"</{el.split()[0]}>" if close else f"<{el}>"
        if name in ("br", "hr"):
            return "<br>" if name == "br" else '<span class="hr"></span>'
        if name == "nbsp":
            return "&nbsp;"
        return m.group(0)  # unknown: leave visible so it gets noticed
    return re.sub(r"&lt;(/?)([a-z*-]+)&gt;", tag, out)


def surge_rich(surge):
    """'2 surges: +1 damage, Cleave 2' -> surge icons and damage symbols."""
    cost, text = 1, surge.strip()
    if m := re.fullmatch(r"(\d+) surges?: (.*)", text, re.I):
        cost, text = int(m[1]), m[2]
    if "<" not in text:  # plain-text surge: add symbols the way IA cards print them
        text = re.sub(r"([+-]\d+) damage\b", r"\1<damage>", text, flags=re.I)
        text = re.sub(r"\b(Cleave|Blast|Recover) (\d+)\b", r"\1 \2<damage>", text)
    return sym("surge") * cost + ": " + rich(text)


CSS = """
@font-face { font-family:IASymbols; src:url('../art/fonts/ImperialAssaultSymbols.ttf'); }
@font-face { font-family:'Minion Pro'; src:url('../art/fonts/MinionPro-Regular.otf'); }
@font-face { font-family:'Minion Pro'; font-weight:bold; src:url('../art/fonts/MinionPro-Bold.otf'); }
@font-face { font-family:'Minion Pro'; font-style:italic; src:url('../art/fonts/MinionPro-It.otf'); }
.cardbox { overflow:hidden; }
.ia { position:relative; width:300px; height:467px; transform-origin:0 0; overflow:hidden;
      background:#2d2d2f; font-family:'Minion Pro','Palatino Linotype',Georgia,serif; color:#1b1b1b;
      --dark:#353537; --mid:#5d5e61; --light:#d9d9d9; }
.ia.elite { --dark:#6e1215; --mid:#a82226; --light:#e8c9c9; }
.ia .sym { font-family:IASymbols; font-style:normal; font-weight:normal; }
.ia .ttl { font-family:'Agency FB','Arial Narrow',sans-serif; }
.ia .art { position:absolute; left:0; top:28px; width:300px; height:156px; background-size:cover;
           background-repeat:no-repeat; background-color:#555; }
.ia .ph { position:absolute; left:40px; top:150px; font:bold 9px sans-serif; color:#fff;
          background:rgba(0,0,0,.55); padding:1px 4px; }
/* header */
.ia .cost { position:absolute; left:0; top:0; width:60px; height:44px; background:var(--dark);
            clip-path:polygon(0 0,100% 0,82% 100%,0 100%); }
.ia .cost span { position:absolute; left:6px; top:1px; width:38px; height:40px; background:#fff;
                 color:var(--dark); font-size:40px; line-height:42px; text-align:center; font-weight:bold;
                 clip-path:polygon(0 0,100% 0,100% 100%,0 100%); }
.ia .reinf { position:absolute; left:55px; top:0; width:36px; height:44px; background:var(--mid);
             clip-path:polygon(22% 0,100% 0,78% 100%,0 100%); color:#fff; font-size:22px;
             line-height:44px; text-align:center; font-weight:bold; }
.ia .name { position:absolute; left:84px; top:0; width:176px; height:44px;
            background:linear-gradient(#fff,#e4e4e4); clip-path:polygon(9% 0,100% 0,100% 100%,0 100%);
            display:flex; align-items:center; justify-content:center; padding-left:10px; box-sizing:border-box;
            font-size:26px; font-weight:bold; line-height:1; text-align:center; color:#151515; }
.ia .name.long { font-size:21px; }
.ia .name.xlong { font-size:17px; }
.ia .affil { position:absolute; right:0; top:0; width:44px; height:42px; background:#f4f4f4;
             border-bottom-left-radius:14px; display:flex; align-items:center; justify-content:center; }
.ia .affil img { max-width:34px; max-height:34px; }
.ia .affil .sym { font-size:30px; color:#1a1a1a; }
.ia .traits { position:absolute; right:0; top:47px; height:20px; padding:0 8px 0 18px;
              background:var(--light); clip-path:polygon(10px 0,100% 0,100% 100%,0 100%);
              font-size:14px; line-height:20px; color:#222; }
.ia .bars { position:absolute; left:0; top:48px; display:flex; flex-direction:column; gap:4px; }
.ia .bars i { display:block; width:34px; height:9px; background:var(--dark);
              clip-path:polygon(0 0,100% 0,80% 100%,0 100%); }
/* surge boxes + text */
.ia .surges { position:absolute; left:0; top:184px; width:300px; display:flex; flex-wrap:wrap;
              background:var(--dark); padding:4px 0 0; box-sizing:border-box; }
.ia .surge { flex:1 1 50%; box-sizing:border-box; min-height:24px; margin:0 0 3px;
             background:linear-gradient(#fbfbfb,#dcdcdc); border-left:2px solid var(--dark);
             border-right:2px solid var(--dark); display:flex; align-items:center; justify-content:center;
             font-size:12.5px; line-height:1.05; text-align:center; padding:2px 4px; }
.ia .surge .sym { font-size:13px; }
.ia .textbox { position:absolute; left:8px; right:8px; bottom:84px; background:linear-gradient(#f3f3f3,#d6d6d6);
               border:2px solid var(--dark); border-bottom:none; overflow:hidden; padding:6px 8px;
               font-size:13px; line-height:1.18; }
.ia .wm { position:absolute; left:50%; top:52%; width:170px; height:170px; transform:translate(-50%,-50%);
          opacity:.13; filter:grayscale(1); mix-blend-mode:multiply; object-fit:contain; }
.ia .wm.sym { font-size:150px; line-height:170px; text-align:center; opacity:.08; color:#000;
              filter:none; mix-blend-mode:normal; }
.ia .ability { position:relative; margin-bottom:5px; text-indent:-10px; padding-left:10px; }
.ia .ab { font-family:'Agency FB','Arial Narrow',sans-serif; font-size:15px; }
.ia .ability .sym { font-size:13px; }
/* stat tabs */
.ia .stats { position:absolute; left:0; bottom:0; width:300px; height:84px; background:#1e1e20;
             display:flex; justify-content:space-around; align-items:flex-start; padding-top:6px;
             box-sizing:border-box; }
.ia .stat { width:62px; height:74px; border-radius:30px 30px 10px 10px; overflow:hidden;
            background:linear-gradient(#c9c9c9,#8d8d8d); text-align:center; }
.ia .stat.wide { width:78px; }
.ia .stat b { display:block; height:24px; line-height:26px; font-size:15px; color:#111;
              background:linear-gradient(#fdfdfd,#d4d4d4); font-family:'Agency FB','Arial Narrow',sans-serif; }
.ia .stat .val { display:flex; height:48px; align-items:center; justify-content:center; gap:2px;
                 font-size:38px; font-weight:bold; color:#fff; font-family:'Agency FB','Arial Narrow',sans-serif;
                 text-shadow:0 1px 1px #000; }
.ia .die { display:inline-block; width:13px; height:13px; border:1.5px solid #222; box-sizing:border-box; }
.ia .stat .sym { font-size:26px; color:#fff; margin-right:2px; }
"""


def deployment_card(*, name, elite, cost, reinforce, group, traits, surges, abilities, health,
                    speed, defense, attack_type, attack_dice, attack_bonus, art_style, placeholder,
                    sigil_html, watermark_html, scale):
    size_class = " xlong" if len(name) > 20 else " long" if len(name) > 14 else ""
    bars = "".join("<i></i>" for _ in range(group or 1))
    surge_html = "".join(f'<div class="surge">{surge_rich(s)}</div>' for s in surges if s)
    ability_html = "".join(
        f'<div class="ability"><b class="ab">{html.escape(a.get("name", ""))}:</b> {rich(a.get("text"))}</div>'
        for a in abilities)
    bonus = f' <span style="font-size:12px">{rich(attack_bonus)}</span>' if attack_bonus else ""
    attack_icon = sym("melee" if attack_type == "melee" else "ranged") if attack_type else ""
    return f"""
<div class="cardbox" style="width:{300 * scale:.3f}px;height:{467 * scale:.3f}px">
<div class="ia{' elite' if elite else ''}" style="transform:scale({scale:.5f})">
  <div class="art" style="{art_style}"></div>
  {'<div class="ph">PLACEHOLDER ART</div>' if placeholder else ''}
  <div class="cost"><span class="ttl">{cost}</span></div>
  {f'<div class="reinf ttl">{reinforce}</div>' if reinforce else ''}
  <div class="name ttl{size_class}">{html.escape(name)}</div>
  <div class="affil">{sigil_html}</div>
  {f'<div class="traits ttl">{" - ".join(html.escape(t) for t in traits)}</div>' if traits else ''}
  <div class="bars">{bars}</div>
  <div class="surges">{surge_html}</div>
  <div class="textbox" style="top:{184 + 4 + 27 * ((len([s for s in surges if s]) + 1) // 2)}px">
    {watermark_html}{ability_html}</div>
  <div class="stats">
    <div class="stat"><b>Health</b><div class="val">{health}</div></div>
    <div class="stat"><b>Speed</b><div class="val">{speed}</div></div>
    <div class="stat wide"><b>Defense</b><div class="val">{''.join(die(d) for d in defense or [])}</div></div>
    <div class="stat wide"><b>Attack</b><div class="val">{attack_icon}{''.join(die(d) for d in attack_dice or [])}{bonus}</div></div>
  </div>
</div></div>"""
