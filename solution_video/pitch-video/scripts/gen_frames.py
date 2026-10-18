"""Writes compositions/frames/s01…s12-*.html (the animated scenes) and build/cues.json.

The scene HTML is generated: edit this file, then run `python3 scripts/gen_frames.py`.
Motion cues are keyed to words in the narration. Word times come from
build/vo_words.json (real clip word timestamps, written by scripts/vo_timing.py once the
ElevenLabs clips exist) or, before that, from a reading-speed estimate.

v2 (see revision_notes.md): S01–S04 are one connected vector story whose scene seams are matched
frames (no fade); every browser has one camera parent (`.cam`) that is the only moving part.
"""
import json, math, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "compositions", "frames")
CAP = "../../capture/v2/"
BRAND = "../../assets/brand/"
VO_OFFSET = 0.3  # each clip starts 0.3 s into its scene
FC = json.load(open(os.path.join(ROOT, "capture", "v2", "forecast_SKU008.json")))  # engine output for the S06 chart

# ---- scenes: id, start, duration, narration (must match voiceover_script.md) -------------------
SCENES = [
    ("s01-hook", 0, 14, "VO_01_HOOK", "Every retailer faces the same balancing act. Order too little, and customers find empty shelves. Order too much, and cash gets trapped in stock that may never sell."),
    ("s02-problem", 14, 15, "VO_02_PROBLEM", "The problem? The information needed to make better decisions is scattered. Sales sit in the POS, while supplier updates arrive through spreadsheets, PDFs, and emails. Critical changes can easily go unnoticed."),
    ("s03-stakes", 29, 11, "VO_03_STAKES", "A delayed delivery or an overlooked price increase can change what a retailer should order. Without connecting these signals, purchasing becomes a costly guessing game."),
    ("s04-intro", 40, 10, "VO_04_INTRO", "StockPulse turns scattered supplier updates, demand forecasts, and stock risks into precise, budget-aware purchasing decisions."),
    ("s05-intake", 50, 19, "VO_05_INTAKE", "Let's follow one purchasing scenario. A supplier changes Cola's delivery time from five days to eight, while increasing its price. StockPulse extracts these changes into structured data, ready for human review before they affect purchasing decisions."),
    ("s06-forecast", 69, 19, "VO_06_FORECAST", "Next, dedicated time-series models forecast future demand. StockPulse compares their predictions with a baseline, helping retailers understand what they may need in the coming weeks. The goal is to act before a shortage becomes urgent."),
    ("s07-risk", 88, 18, "VO_07_RISK", "But demand is only half the picture. With delivery taking longer, current stock may run out before the next shipment arrives. StockPulse combines inventory and lead-time information to flag products that need attention."),
    ("s08-optimize", 106, 23, "VO_08_OPTIMIZE", "Now comes the key decision: what should the retailer order? StockPulse calculates replenishment using expected demand, lead time, safety stock, and incoming orders. When the budget is limited, it prioritizes critical products and explains the trade-offs, so every recommendation has a reason behind it."),
    ("s09-agent", 129, 17, "VO_09_AGENT", "The procurement agent turns those calculations into a clear explanation and a purchase order draft. The logic remains auditable, and the agent cannot approve the order. The retailer makes the final decision."),
    ("s10-features", 146, 20, "VO_10_FEATURES", "From supplier documents to forecasts, risk detection, and replenishment, StockPulse brings the purchasing workflow together. It is designed for independent retailers, specialty grocers, and small wholesalers working with POS data and spreadsheets."),
    ("s11-architecture", 166, 23, "VO_11_TECH", "Our approach combines AI with dependable business logic. Language models interpret documents and explain recommendations, while deterministic code calculates risk and order quantities. AMD infrastructure, Instinct GPUs, and ROCm support our AI workload, with privacy and access controls built into the deployment."),
    ("s12-close", 189, 14, "VO_12_CLOSE", "Fewer empty shelves. Less cash tied up in excess stock. Smarter purchasing, with decisions retailers can understand. This is StockPulse."),
]
TOTAL = SCENES[-1][1] + SCENES[-1][2]

def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())

def estimate_words(text):
    """Scene-local onset of each word at a conversational pace (~2.7 words/s plus pauses)."""
    t, out = VO_OFFSET, []
    for w in text.split():
        out.append(round(t, 3))
        t += 0.37 + (0.38 if w[-1] in ".?" else 0.16 if w[-1] in ",:;" else 0)
    return out

_real = {}
_rp = os.path.join(ROOT, "build", "vo_words.json")
if os.path.exists(_rp):
    _real = json.load(open(_rp))  # {"VO_01_HOOK": [onset_in_clip, ...] per script word}

class Cues:
    def __init__(self, sid, vo, text):
        self.words = text.split()
        self.keys = [norm(w) for w in self.words]
        real = _real.get(vo)
        self.times = [round(VO_OFFSET + x, 3) for x in real] if real and len(real) == len(self.words) else estimate_words(text)
        self.end = self.times[-1] + 0.5

    def at(self, phrase, offset=0.0):
        p = [norm(w) for w in phrase.split()]
        for i in range(len(self.keys) - len(p) + 1):
            if self.keys[i:i + len(p)] == p:
                return round(self.times[i] + offset, 3)
        raise KeyError(f"cue phrase not in narration: {phrase!r}")

# ---- page scaffolding ---------------------------------------------------------------------------
HELPERS = r"""
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));
const fadeIn = (sel, t, d = 0.5) => tl.fromTo(sel, { opacity: 0 }, { opacity: 1, duration: d, ease: "power1.out" }, t);
const fadeOut = (sel, t, d = 0.4) => tl.fromTo(sel, { opacity: 1 }, { opacity: 0, duration: d, ease: "power1.in", immediateRender: false }, t);
// force3D keeps moved elements composited for their whole life: no end-of-move re-raster or pixel snap
const rise = (sel, t, o = {}) => tl.fromTo(sel, { opacity: 0, y: o.y ?? 18 }, { opacity: 1, y: 0, duration: o.d ?? 0.6, ease: "power3.out", stagger: o.s ?? 0, force3D: true }, t);
const pop = (sel, t, d = 0.45) => tl.fromTo(sel, { opacity: 0, scale: 0.86 }, { opacity: 1, scale: 1, duration: d, ease: "back.out(1.7)", force3D: true }, t);
const count = (el, from, to, t, d, fmt) => {
  const o = { v: from };
  el.textContent = fmt(from);
  tl.fromTo(o, { v: from }, { v: to, duration: d, ease: "power2.out", onUpdate: () => { el.textContent = fmt(o.v); } }, t);
};
// SVG path reveal: draws `frac` of each matching path
const draw = (sel, t, d = 0.8, frac = 1, ease = "power2.inOut") => $$(sel).forEach((p) => {
  const L = p.getTotalLength();
  p.style.strokeDasharray = L + " " + L;
  tl.fromTo(p, { opacity: 0 }, { opacity: 1, duration: 0.01 }, t);
  tl.fromTo(p, { strokeDashoffset: L }, { strokeDashoffset: L * (1 - frac), duration: d, ease }, t);
});
// the one camera move: a single scale-and-position tween, then a complete hold
const camTo = (sel, v, t, d = 1.3) => tl.to(sel, { ...v, duration: d, ease: "power2.inOut", force3D: true }, t);
// Scripted cursor: travel to (x, y), press at t, optional ripple.
const click = (cur, rip, x0, y0, x, y, t) => {
  tl.fromTo(cur, { opacity: 0, x: x0, y: y0 }, { opacity: 1, duration: 0.25 }, t - 1.2);
  tl.to(cur, { x, y, duration: 0.9, ease: "power2.inOut" }, t - 1.0);
  tl.to(cur, { scale: 0.86, duration: 0.08, ease: "power1.in" }, t);
  tl.to(cur, { scale: 1, duration: 0.18, ease: "power2.out" }, t + 0.08);
  if (rip) tl.fromTo(rip, { opacity: 0.5, scale: 0.2, x: x - 30, y: y - 30 }, { opacity: 0, scale: 1.4, duration: 0.6, ease: "power2.out" }, t);
};
"""

def page(sid, dur, css, body, js, T, fade=(True, True)):
    fi = f'fadeIn("#{sid}-scene", 0, 0.5);' if fade[0] else ""
    fo = f'fadeOut("#{sid}-scene", DUR - 0.4, 0.4);' if fade[1] else ""
    return f"""<!doctype html>
<html><head><meta charset="UTF-8" /></head><body><template>
<style>
#root {{ position: absolute; inset: 0; }}
{css}
</style>
<div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
<div class="scene" id="{sid}-scene">
{body}
</div>
</div>
<script>
(() => {{
const tl = gsap.timeline({{ paused: true }});
const T = {json.dumps(T)};
const DUR = {dur};
{HELPERS}
{fi}
{fo}
{js}
window.__timelines["{sid}"] = tl;
}})();
</script>
</template></body></html>
"""

def words(text, cls="w"):
    return " ".join(f'<span class="{cls}">{w}</span>' for w in text.split())

def browser(id_, x, y, w, h, url, layers, k, inner=""):
    """A browser frame around full-width page stills (1600 CSS px at 2x), laid out at k display px per CSS px.
    layers: [(img, layer_id)], first visible. Only the camera (`#{id_}-cam`) ever moves; see camv()."""
    imgs = "".join(f'<img id="{lid}" src="{CAP}{img}" style="width:{1600 * k:.1f}px;opacity:{1 if i == 0 else 0}" alt="">'
                   for i, (img, lid) in enumerate(layers))
    return f"""<div class="browser" id="{id_}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">
  <div class="bar"><i></i><i></i><i></i><span class="url">stockpulse.app/#/{url}</span></div>
  <div class="view"><div class="cam" id="{id_}-cam">{imgs}{inner}</div></div>
</div>"""

def camv(k, cx, cy, s=1.0):
    """Camera state: page CSS point (cx, cy) at the view's top-left, zoom s (always <= 1, so the layout is the sharpest framing)."""
    return f"{{ x: {-cx * k * s:.2f}, y: {-cy * k * s:.2f}, scale: {s:.4f} }}"

def scr(bx, by, k, cx, cy, px, py, s=1.0):
    """Scene px of page point (px, py) under camera (cx, cy, s) in a browser at (bx, by)."""
    return round(bx + (px - cx) * k * s), round(by + 40 + (py - cy) * k * s)

def box(k, x0, y0, x1, y1, pad=6):
    """Inline style placing an overlay over the page rect (x0, y0)–(x1, y1), in camera coordinates."""
    return f"left:{x0 * k - pad:.0f}px;top:{y0 * k - pad:.0f}px;width:{(x1 - x0) * k + 2 * pad:.0f}px;height:{(y1 - y0) * k + 2 * pad:.0f}px"

CURSOR = lambda sid: f'''<div id="{sid}-rip" class="ripple"></div><svg id="{sid}-cur" class="cursor" width="30" height="36" viewBox="0 0 30 36"><path d="M2 2 L2 28 L9 22 L14 33 L19 31 L14 20 L24 20 Z" fill="#202A3B" stroke="#FFFFFF" stroke-width="2" stroke-linejoin="round"/></svg>'''
LEGEND = lambda sid: f'<div class="legend" id="{sid}-legend"><span class="l-calc">Calculated</span><span class="l-ai">AI</span></div>'

# ================================================================================================
# The opening world: a shelf (left) and a stockroom (right), shared by S01, S02 and S12.
SHELF_O, ROOM_O, FLOOR_Y = (200, 300), (1080, 300), 786
ROWS = [150, 310, 470]                                          # top of each shelf board, shelf-local
SOLD = [9, 2, 13, 20, 5, 16, 11, 0, 22, 7, 18, 14, 3, 23, 10]   # facings that sell off on "too little", in order
KEEP = [(0, 0), (0, 1)]                                         # cartons already in the stockroom (row, col)
DROP = [(0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 0), (3, 1), (3, 2), (3, 3)]

def product(r, cx, by):
    if r == 0:  # can
        return (f'<rect x="{cx-25}" y="{by-96}" width="50" height="96" rx="7" fill="#4F67E8"/>'
                f'<rect x="{cx-25}" y="{by-66}" width="50" height="30" fill="#C9D2FA"/>'
                f'<rect x="{cx-21}" y="{by-101}" width="42" height="7" rx="3" fill="#3B4FC4"/>')
    if r == 1:  # bottle
        return (f'<rect x="{cx-9}" y="{by-118}" width="18" height="30" rx="4" fill="#3478F6"/>'
                f'<rect x="{cx-10}" y="{by-126}" width="20" height="10" rx="3" fill="#202A3B"/>'
                f'<rect x="{cx-22}" y="{by-96}" width="44" height="96" rx="12" fill="#3478F6"/>'
                f'<rect x="{cx-22}" y="{by-62}" width="44" height="26" fill="#CFE0FD"/>')
    return (f'<rect x="{cx-30}" y="{by-112}" width="60" height="112" rx="4" fill="#2E3A55"/>'  # box
            f'<rect x="{cx-30}" y="{by-78}" width="60" height="30" fill="#4F67E8"/>'
            f'<circle cx="{cx}" cy="{by-28}" r="7" fill="#F7F9FC"/>')

def shelf_svg(p, sold=False):
    s = ['<rect x="0" y="0" width="640" height="486" rx="6" fill="#E8ECF6"/>']
    s += [f'<rect x="0" y="{by-12}" width="640" height="12" fill="#DCE1EF"/>' for by in ROWS]
    items = []
    for i in range(24):
        r, c = divmod(i, 8)
        cx, by, h = 40 + c * 80, ROWS[r], [104, 130, 116][r]
        gone = sold and i in SOLD
        s.append(f'<rect id="{p}-g{i}" x="{cx-29}" y="{by-h}" width="58" height="{h-6}" rx="6" fill="none" stroke="#B4BDCF" stroke-width="2" stroke-dasharray="6 6" opacity="{1 if gone else 0}"/>')
        items.append(f'<g class="it" id="{p}-p{i}" opacity="{0 if gone else 1}">{product(r, cx, by)}</g>')
    s += items
    for by in ROWS:
        s.append(f'<rect x="-8" y="{by}" width="656" height="16" rx="3" fill="#202A3B"/><rect x="-8" y="{by}" width="656" height="4" fill="#3A4766"/>')
        s += [f'<rect x="{40 + c*80 - 14}" y="{by+6}" width="28" height="7" rx="1" fill="#F7F9FC"/>' for c in range(8)]
    s.append('<rect x="-22" y="-14" width="684" height="14" rx="3" fill="#202A3B"/>'
             '<rect x="-22" y="-14" width="16" height="500" rx="3" fill="#202A3B"/><rect x="646" y="-14" width="16" height="500" rx="3" fill="#202A3B"/>')
    return "".join(s)

def carton(x, b):
    return (f'<rect x="{x}" y="{b-88}" width="124" height="88" fill="#D5DCF6" stroke="#9FACE4" stroke-width="2"/>'
            f'<polygon points="{x},{b-88} {x+14},{b-102} {x+138},{b-102} {x+124},{b-88}" fill="#EEF1FD"/>'
            f'<polygon points="{x+124},{b-88} {x+138},{b-102} {x+138},{b-14} {x+124},{b}" fill="#AFBAEC"/>'
            f'<rect x="{x+54}" y="{b-87}" width="16" height="30" fill="#B9C3F0"/>'
            f'<rect x="{x+12}" y="{b-30}" width="30" height="16" rx="2" fill="#FFFFFF"/>')

def room_svg(p):
    s = ['<rect x="0" y="0" width="640" height="486" rx="6" fill="#EDF0F6"/>',
         '<rect x="0" y="0" width="640" height="64" rx="6" fill="#D9DFEA"/>',
         ''.join(f'<line x1="0" y1="{y}" x2="640" y2="{y}" stroke="#C5CDDB" stroke-width="2"/>' for y in (16, 32, 48)),
         f'<clipPath id="{p}-clip"><rect x="0" y="64" width="640" height="422"/></clipPath><g clip-path="url(#{p}-clip)">']
    for r, c in sorted(KEEP + DROP):  # bottom row first so upper cartons overlap the top faces below
        s.append(f'<g id="{p}-c{r}{c}">{carton(40 + c * 142, 456 - r * 88)}</g>')
    s.append('</g><rect x="30" y="456" width="580" height="12" rx="2" fill="#202A3B"/>'
             + ''.join(f'<rect x="{x}" y="468" width="40" height="18" fill="#202A3B"/>' for x in (40, 300, 560)))
    return "".join(s)

def world(p, end=False):
    """SVG world + its HTML overlays. end=True renders S01's final state statically (S02/S12 start from it)."""
    knob = 118 if end else 0
    return f"""
<svg id="{p}-art" class="full" viewBox="0 0 1920 1080" width="1920" height="1080">
  <path id="{p}-floor" d="M140,{FLOOR_Y} L1780,{FLOOR_Y}" stroke="#CDD5E0" stroke-width="3" fill="none"/>
  <g id="{p}-shelfw"><g transform="translate({SHELF_O[0]},{SHELF_O[1]})">{shelf_svg(p, end)}</g></g>
  <g id="{p}-roomw"><g transform="translate({ROOM_O[0]},{ROOM_O[1]})">{room_svg(p)}</g></g>
</svg>
<div class="eyebrow" id="{p}-eyl" style="position:absolute;left:186px;top:252px">Shelf</div>
<div class="eyebrow" id="{p}-eyr" style="position:absolute;left:1066px;top:252px">Stockroom</div>
<div id="{p}-cl" class="co-l"><div class="callout c-red">Too little</div><div class="sub">Empty shelves</div></div>
<div id="{p}-cr" class="co-r"><div class="callout c-indigo">Too much</div><div class="sub">Cash in the stockroom</div></div>
<div id="{p}-slip" class="card slip"><div class="eyebrow">This week’s order</div>
  <div class="track"><div class="knob" id="{p}-knob" data-x="{knob}"></div></div>
  <div class="ends"><span id="{p}-less" style="color:{'var(--red-ink)' if end else 'var(--ink-2)'}">Less</span><span id="{p}-more" style="color:{'var(--indigo)' if end else 'var(--ink-2)'}">More</span></div></div>
<div id="{p}-tag" class="pill red-pill"><i></i>Out of stock</div>
<div id="{p}-cash" class="pill cash-pill"><b>$</b>Cash tied up</div>
"""

WORLD_CSS = lambda p: f"""
#{p}-scene .full {{ position:absolute; inset:0; }}
#{p}-scene .co-l {{ position:absolute; left:186px; top:120px; }}
#{p}-scene .co-r {{ position:absolute; right:186px; top:120px; text-align:right; }}
#{p}-scene .callout {{ font-size:56px; }}
#{p}-scene .sub {{ font-size:28px; color: var(--ink-2); margin-top:6px; }}
#{p}-scene .slip {{ position:absolute; left:790px; top:104px; width:340px; height:136px; padding:20px 26px; }}
#{p}-scene .slip .eyebrow {{ font-size:16px; }}
#{p}-scene .slip .track {{ position:relative; margin-top:26px; height:6px; border-radius:3px; background: var(--line); }}
#{p}-scene .slip .knob {{ position:absolute; left:130px; top:-11px; width:28px; height:28px; border-radius:50%; background: var(--ink); border:4px solid #fff; box-shadow: 0 2px 6px rgba(32,42,59,.3); }}
#{p}-scene .slip .ends {{ display:flex; justify-content:space-between; margin-top:16px; font-size:20px; font-weight:500; }}
#{p}-scene .pill {{ position:absolute; display:flex; align-items:center; gap:12px; border-radius:999px; font-size:26px; font-weight:600; padding:10px 22px; box-shadow: var(--shadow); }}
#{p}-scene .red-pill {{ left:420px; top:500px; background:#fff; color: var(--red-ink); border:2px solid var(--red); }}
#{p}-scene .red-pill i {{ width:12px; height:12px; border-radius:50%; background: var(--red); display:block; }}
#{p}-scene .cash-pill {{ left:1250px; top:500px; background:#2B3A99; color:#fff; }}
#{p}-scene .cash-pill b {{ width:34px; height:34px; border-radius:50%; background:#fff; color:#2B3A99; display:grid; place-items:center; font-size:22px; }}
"""

# ================================================================================================
def s01(sid, dur, C):
    T = {"bet": C.at("same balancing act"), "little": C.at("Order too little"), "empty": C.at("empty shelves"),
         "much": C.at("Order too much"), "cash": C.at("cash gets trapped")}
    T["swing"] = min(T["bet"] - 1.2, T["little"] - 1.7)
    T["drop"] = T["much"] + 0.35
    T["cashpop"] = max(T["cash"] + 0.3, T["drop"] + (len(DROP) - 1) * 0.11 + 0.5)
    p = sid
    body = world(p)
    css = WORLD_CSS(p)
    js = f"""
draw("#{p}-floor", 0, 0.7, 1, "power2.out");
tl.fromTo("#{p}-shelfw", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, 0.05);
tl.fromTo("#{p}-shelfw .it", {{ opacity: 0, y: -10 }}, {{ opacity: 1, y: 0, duration: 0.22, stagger: 0.022, ease: "power2.out" }}, 0.35);
tl.fromTo("#{p}-roomw", {{ opacity: 0, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.55, ease: "power3.out" }}, 0.2);
fadeIn(["#{p}-eyl", "#{p}-eyr"], 0.7);
rise("#{p}-slip", 0.8, {{ y: -16 }});
// the bet: the order slider swings, then commits each way
tl.to("#{p}-knob", {{ x: -70, duration: 0.45, ease: "sine.inOut" }}, T.swing);
tl.to("#{p}-knob", {{ x: 70, duration: 0.6, ease: "sine.inOut" }}, T.swing + 0.45);
tl.to("#{p}-knob", {{ x: 0, duration: 0.45, ease: "sine.inOut" }}, T.swing + 1.05);
tl.to("#{p}-knob", {{ x: -118, duration: 0.5, ease: "power2.inOut" }}, T.little);
tl.to("#{p}-less", {{ color: "#B3344A", duration: 0.3 }}, T.little + 0.2);
rise("#{p}-cl", T.little - 0.15);
// too little: facings sell off and leave gaps
{json.dumps(SOLD)}.forEach((i, j) => {{
  const t = T.little + 0.55 + j * 0.09;
  tl.to("#{p}-p" + i, {{ opacity: 0, y: 14, duration: 0.26, ease: "power1.in" }}, t);
  tl.fromTo("#{p}-g" + i, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, t + 0.12);
}});
pop("#{p}-tag", T.empty + 0.35);
// too much: cartons drop into the stockroom one at a time
tl.to("#{p}-knob", {{ x: 118, duration: 0.7, ease: "power2.inOut" }}, T.much);
tl.to("#{p}-more", {{ color: "#4F67E8", duration: 0.3 }}, T.much + 0.3);
rise("#{p}-cr", T.much - 0.15);
{json.dumps([f"#{p}-c{r}{c}" for r, c in DROP])}.forEach((s, j) => {{
  const t = T.drop + j * 0.11;
  tl.fromTo(s, {{ y: -380 }}, {{ y: 0, duration: 0.42, ease: "power2.in" }}, t);
  tl.to(s, {{ y: -5, duration: 0.07, ease: "power1.out" }}, t + 0.42);
  tl.to(s, {{ y: 0, duration: 0.09, ease: "power1.in" }}, t + 0.49);
}});
pop("#{p}-cash", T.cashpop);
"""
    return css, body, js, T

# ================================================================================================
TL_X0, TL_PX, TL_Y = 380, 110, 740   # S02 delivery timeline: day 0 at x 380, 110 px a day
TRUCK = ('<rect x="-40" y="-40" width="54" height="34" rx="3" fill="#4F67E8"/><rect x="12" y="-32" width="26" height="26" rx="5" fill="#202A3B"/>'
         '<rect x="20" y="-28" width="12" height="9" rx="2" fill="#CFE0FD"/><circle cx="-26" cy="-5" r="7" fill="#202A3B"/><circle cx="-26" cy="-5" r="2.5" fill="#F7F9FC"/>'
         '<circle cx="26" cy="-5" r="7" fill="#202A3B"/><circle cx="26" cy="-5" r="2.5" fill="#F7F9FC"/>')

def timeline(p, end=False):
    d5, d8 = TL_X0 + 5 * TL_PX, TL_X0 + 8 * TL_PX
    ticks = "".join(f'<line x1="{TL_X0+d*TL_PX}" y1="{TL_Y}" x2="{TL_X0+d*TL_PX}" y2="{TL_Y+12}" stroke="#98A2B3" stroke-width="2"/>'
                    f'<text x="{TL_X0+d*TL_PX}" y="{TL_Y+38}" font-family="Geist Mono" font-size="19" fill="#667085" text-anchor="middle">{d}d</text>' for d in range(11))
    return f"""
<svg id="{p}-tl" class="full" viewBox="0 0 1920 1080" width="1920" height="1080">
  <rect id="{p}-tint" x="{d5}" y="626" width="{d8-d5}" height="{TL_Y-626}" fill="#FCEDEF"/>
  <rect id="{p}-redseg" x="{d5}" y="{TL_Y-4}" width="{d8-d5}" height="8" fill="#D94F61"/>
  <path id="{p}-axis" d="M{TL_X0},{TL_Y} L{TL_X0+10*TL_PX},{TL_Y}" stroke="#CDD5E0" stroke-width="3" fill="none"/>
  <g id="{p}-ticks">{ticks}</g>
  <g id="{p}-truck" transform="translate({d8 if end else d5},{TL_Y-6}) scale(1.25)">{TRUCK}</g>
</svg>
<div class="eyebrow" id="{p}-tleb" style="position:absolute;left:{TL_X0}px;top:600px">Supplier delivery</div>
<div id="{p}-tlab" class="tlab" style="left:{(d8 if end else d5) - 120}px"><span id="{p}-tl5">Delivery · day 5</span><span id="{p}-tl8">Delivery · day 8</span></div>
<div id="{p}-plus" class="plus3" style="left:{d5 + 14}px">+3 days</div>
"""

TL_CSS = lambda p: f"""
#{p}-scene .tlab {{ position:absolute; top:796px; width:240px; text-align:center; font-size:24px; font-weight:600; }}
#{p}-scene .tlab span {{ position:absolute; left:0; right:0; }}
#{p}-scene .plus3 {{ position:absolute; top:640px; font-size:26px; font-weight:600; color: var(--red-ink); }}
"""

def pdf_card(p, cls=""):
    return f"""<div id="{p}-pdf" class="card paper {cls}"><div class="eyebrow">PDF · Angkor Beverage Co</div><div class="t">Revised terms</div>
  <div class="q">“Standard delivery is <span class="hl" id="{p}-hl1">8 days</span> from order.”</div>
  <table><tr><td>Mineral Water 1.5L</td><td class="r">$0.57</td></tr>
  <tr id="{p}-row"><td>Cola 330ml, tray of 24<div class="mini">MOQ 48</div></td><td class="r"><span class="hl" id="{p}-hl2">$1.36</span></td></tr>
  <tr><td>Green Tea 500ml</td><td class="r">$0.92</td></tr></table></div>"""

PDF_CSS = lambda p: f"""
#{p}-scene .paper {{ position:absolute; width:400px; padding:26px 30px; }}
#{p}-scene .paper::after {{ content:""; position:absolute; right:-1px; top:-1px; width:34px; height:34px; background: linear-gradient(225deg, var(--bg) 50%, #E3E8EF 50%); border-bottom-left-radius:6px; }}
#{p}-scene .paper .eyebrow {{ font-size:15px; }}
#{p}-scene .paper .t {{ font-size:28px; font-weight:600; margin:10px 0 14px; }}
#{p}-scene .paper .q {{ font-size:21px; line-height:1.45; }}
#{p}-scene .paper table {{ width:100%; font-family: var(--mono); font-size:18px; border-collapse:collapse; margin-top:18px; }}
#{p}-scene .paper td {{ padding:9px 0; border-top:1px solid var(--line); vertical-align:top; }} #{p}-scene .paper td.r {{ text-align:right; }}
#{p}-scene .paper .mini {{ font-size:15px; color: var(--ink-2); margin-top:3px; }}
#{p}-scene .paper .hl {{ padding:0 4px; border-radius:4px; }}
"""

def s02(sid, dur, C):
    T = {"exists": C.at("The information needed"), "scattered": C.at("is scattered"), "sales": C.at("Sales sit"), "pdfs": C.at("PDFs"),
         "emails": C.at("emails"), "three": C.at("Critical changes"), "rarely": C.at("easily go"), "sheet": C.at("unnoticed")}
    T["tl"] = T["pdfs"] + 0.3
    T["move"] = max(T["three"], T["tl"] + 1.0)
    T["out"] = dur - 0.75
    p = sid
    hist = FC["history"][-7:]
    bars = "".join(f'<rect class="bar" x="{216 + i*42}" y="{330 - v*1.2:.0f}" width="30" height="{v*1.2:.0f}" rx="3" fill="#3478F6"/>' for i, v in enumerate(hist))
    body = world(p, end=True) + f"""
<svg id="{p}-net" class="full" viewBox="0 0 1920 1080" width="1920" height="1080">
  <g id="{p}-pos">
    <rect x="180" y="150" width="350" height="226" rx="16" fill="#202A3B"/><rect x="196" y="166" width="318" height="182" rx="8" fill="#F7F9FC"/>
    <text x="214" y="196" font-family="Geist" font-size="17" font-weight="500" fill="#667085">Cola 330ml · last 7 days</text>{bars}
    <rect x="335" y="376" width="40" height="40" fill="#2E3A55"/><rect x="250" y="414" width="210" height="22" rx="8" fill="#202A3B"/>
  </g>
  <g fill="none" stroke="#98A2B3" stroke-width="3" stroke-linecap="round">
    <path class="cn" d="M540,262 C620,262 660,268 742,272"/><path class="cn" d="M1370,250 C1290,250 1250,262 1176,266"/><path class="cn" d="M1330,470 C1250,470 1240,380 1176,368"/>
  </g>
</svg>
<div id="{p}-poslab" class="lab" style="left:180px;top:452px">POS · daily sales</div>
<div id="{p}-sheet" class="card"><div class="eyebrow">Reorder sheet</div><div class="t">Cola 330ml</div>
  <div class="row" id="{p}-ltrow"><span>Lead time</span><b id="{p}-lt">5 d</b></div><div class="row"><span>Unit cost</span><b>$1.28</b></div>
  <div id="{p}-stale" class="stale">Not updated</div></div>
{pdf_card(p)}
<div id="{p}-mail" class="card" data-layout-allow-overlap><div class="from">✉ Siam Snacks Import</div><div class="subj">Re: port congestion, revised delivery</div></div>
<div id="{p}-new1" class="new" style="left:1720px;top:96px">New</div><div id="{p}-new2" class="new" style="left:1660px;top:462px">New</div>
<div id="{p}-doclab" class="lab" style="left:1340px;top:590px">Supplier documents</div>
{timeline(p)}
<div id="{p}-token" class="token">+3 days</div>
"""
    css = WORLD_CSS(p) + TL_CSS(p) + PDF_CSS(p) + f"""
#{p}-scene .lab {{ position:absolute; font-size:26px; font-weight:500; color: var(--ink-2); }}
#{p}-sheet {{ position:absolute; left:760px; top:150px; width:400px; padding:26px 30px; }}
#{p}-sheet .t {{ font-size:32px; font-weight:600; margin:8px 0 12px; }}
#{p}-sheet .row {{ display:flex; justify-content:space-between; font-size:28px; padding:12px 8px; border-top:1px solid var(--line); border-radius:8px; }}
#{p}-sheet .row b {{ font-family: var(--mono); font-weight:500; }}
#{p}-sheet .stale {{ position:absolute; right:22px; top:22px; font-size:18px; font-weight:600; color: var(--red-ink); background: var(--red-tint); border-radius:999px; padding:4px 12px; }}
#{p}-pdf {{ left:1380px; top:110px; }}
#{p}-mail {{ position:absolute; left:1340px; top:476px; width:380px; padding:18px 24px; }}
#{p}-mail .from {{ font-size:20px; font-weight:600; }} #{p}-mail .subj {{ font-size:19px; color: var(--ink-2); margin-top:6px; }}
#{p}-scene .new {{ position:absolute; font-size:17px; font-weight:600; color:#fff; background: var(--indigo); border-radius:999px; padding:3px 12px; }}
#{p}-token {{ position:absolute; left:{TL_X0 + 5 * TL_PX + 14}px; top:640px; font-size:26px; font-weight:600; color: var(--red-ink); }}
"""
    d5, d8 = TL_X0 + 5 * TL_PX, TL_X0 + 8 * TL_PX
    js = f"""
gsap.set("#{p}-knob", {{ x: 118 }});
// S01's last frame morphs: shelf → POS, stockroom → supplier documents, order slip → reorder sheet
tl.to(["#{p}-cl", "#{p}-cr", "#{p}-tag", "#{p}-cash", "#{p}-eyl", "#{p}-eyr", "#{p}-floor"], {{ opacity: 0, duration: 0.35 }}, 0);
tl.to("#{p}-shelfw", {{ scale: 0.45, x: -165, y: -233, opacity: 0, duration: 0.9, ease: "power2.inOut", svgOrigin: "520 543" }}, 0.1);
tl.to("#{p}-roomw", {{ scale: 0.45, x: 160, y: -243, opacity: 0, duration: 0.9, ease: "power2.inOut", svgOrigin: "1400 543" }}, 0.1);
tl.to("#{p}-slip", {{ y: 90, opacity: 0, duration: 0.6, ease: "power2.inOut" }}, 0.1);
tl.fromTo("#{p}-pos", {{ opacity: 0, scale: 0.85, svgOrigin: "355 300" }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "power2.out", svgOrigin: "355 300" }}, 0.55);
tl.fromTo("#{p}-pos .bar", {{ scaleY: 0.15, svgOrigin: "0 330" }}, {{ scaleY: 1, duration: 0.6, ease: "power2.out", svgOrigin: "0 330", stagger: 0.05 }}, T.sales);
fadeIn("#{p}-poslab", 0.9);
tl.fromTo("#{p}-sheet", {{ opacity: 0, y: -50 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power2.out" }}, 0.35);
gsap.set("#{p}-stale", {{ opacity: 0 }});
rise(["#{p}-pdf", "#{p}-mail"], 0.6, {{ y: 24, s: 0.12 }});
fadeIn("#{p}-doclab", 1.0);
// scattered: every connection stops short of the sheet
draw("#{p}-net .cn", T.scattered, 0.9, 0.62);
// supplier changes arrive
pop("#{p}-new1", T.pdfs - 0.1);
tl.fromTo("#{p}-hl1", {{ backgroundColor: "rgba(252,237,239,0)", boxShadow: "inset 0 -2px 0 rgba(217,79,97,0)" }}, {{ backgroundColor: "rgba(252,237,239,1)", boxShadow: "inset 0 -2px 0 rgba(217,79,97,1)", duration: 0.35 }}, T.pdfs + 0.1);
tl.fromTo("#{p}-hl2", {{ backgroundColor: "rgba(252,237,239,0)" }}, {{ backgroundColor: "rgba(252,237,239,1)", duration: 0.35 }}, T.pdfs + 0.4);
pop("#{p}-new2", T.emails - 0.1);
// the delivery timeline: the truck slips three days
fadeIn("#{p}-tleb", T.tl);
draw("#{p}-axis", T.tl, 0.6, 1, "power2.out");
fadeIn("#{p}-ticks", T.tl + 0.2, 0.4);
tl.fromTo("#{p}-truck", {{ opacity: 0, x: {d5}, y: {TL_Y - 26} }}, {{ opacity: 1, y: {TL_Y - 6}, duration: 0.4, ease: "power2.out" }}, T.tl + 0.3);
tl.fromTo("#{p}-tlab", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, T.tl + 0.5);
gsap.set("#{p}-tl8", {{ opacity: 0 }});
tl.to("#{p}-truck", {{ x: {d8}, duration: 1.0, ease: "power2.inOut" }}, T.move);
tl.to("#{p}-tlab", {{ x: {d8 - d5}, duration: 1.0, ease: "power2.inOut" }}, T.move);
tl.to("#{p}-tl5", {{ opacity: 0, duration: 0.2 }}, T.move + 0.8);
tl.to("#{p}-tl8", {{ opacity: 1, duration: 0.2 }}, T.move + 0.8);
tl.fromTo(["#{p}-tint", "#{p}-redseg"], {{ scaleX: 0, svgOrigin: "{d5} 700" }}, {{ scaleX: 1, duration: 1.0, ease: "power2.inOut", svgOrigin: "{d5} 700" }}, T.move);
pop("#{p}-plus", T.move + 0.9);
// the news heads for the reorder sheet and never arrives
tl.fromTo("#{p}-token", {{ opacity: 0, x: 0, y: 0 }}, {{ opacity: 1, duration: 0.25 }}, T.rarely - 0.2);
tl.to("#{p}-token", {{ x: 40, y: -170, duration: 0.9, ease: "power1.inOut" }}, T.rarely);
tl.to("#{p}-token", {{ opacity: 0, duration: 0.4 }}, T.rarely + 0.6);
tl.to("#{p}-ltrow", {{ boxShadow: "inset 0 0 0 2.5px #D94F61", backgroundColor: "#FCEDEF", duration: 0.35 }}, T.sheet);
tl.to("#{p}-stale", {{ opacity: 1, duration: 0.3 }}, T.sheet + 0.2);
// clear the stage: only the delivery timeline carries into S03
tl.to(["#{p}-pos", "#{p}-net", "#{p}-poslab", "#{p}-sheet", "#{p}-pdf", "#{p}-mail", "#{p}-new1", "#{p}-new2", "#{p}-doclab"], {{ opacity: 0, duration: 0.45, ease: "power1.in" }}, T.out);
"""
    T["sfx_select"] = T["pdfs"] - 0.1  # the "New" badge lands on the supplier PDF
    return css, body, js, T

# ================================================================================================
P1, P2, P3 = 120, 720, 1320   # S03 panel columns, 480 px wide
P_AX, P_DAY = 140, 44         # panel 1 mini timeline: day 0 at x 140

def s03(sid, dur, C):
    T = {"head": 0.35, "stock": C.at("A delayed delivery"), "over": C.at("price increase"), "price": C.at("Without connecting"), "erodes": C.at("costly guessing game")}
    T["out"] = dur - 0.8
    p = sid
    stack = "".join(f'<g class="ct">{carton(40 + c * 142, 456 - r * 88)}</g>' for r in range(3) for c in range(3))
    ticks = "".join(f'<line x1="{P_AX+d*P_DAY}" y1="520" x2="{P_AX+d*P_DAY}" y2="530" stroke="#98A2B3" stroke-width="2"/><text x="{P_AX+d*P_DAY}" y="554" font-family="Geist Mono" font-size="17" fill="#667085" text-anchor="middle">{d}d</text>' for d in range(0, 11, 2))
    g0, g1 = P_AX + 5.7 * P_DAY, P_AX + 8 * P_DAY
    body = timeline(p, end=True) + f"""
<div id="{p}-head" class="headline">That gap is costly.</div>
<div id="{p}-sample" class="chip">Sample store data</div>
<svg id="{p}-art" class="full" viewBox="0 0 1920 1080" width="1920" height="1080">
  <g id="{p}-v1">
    <rect id="{p}-gap" x="{g0:.0f}" y="422" width="{g1-g0:.0f}" height="98" fill="#FCEDEF" stroke="#D94F61" stroke-width="2"/>
    <rect id="{p}-cov" x="{P_AX}" y="446" width="{5.7*P_DAY:.0f}" height="34" rx="6" fill="#3478F6"/>
    <text id="{p}-covt" x="{P_AX+14}" y="470" font-family="Geist" font-size="18" font-weight="600" fill="#fff">stock lasts 5.7 d</text>
    <path d="M{P_AX},520 L{P_AX+10*P_DAY},520" stroke="#CDD5E0" stroke-width="3"/>{ticks}
  </g>
  <g id="{p}-v2" transform="translate({P2+40},230) scale(0.75)">{stack}</g>
</svg>
<div class="col" id="{p}-c1" style="left:{P1}px"><div class="eyebrow">Stockout</div><div class="fig c-red">2.3 days</div><div class="desc">Cola sells out before the delayed truck arrives</div></div>
<div class="col" id="{p}-c2" style="left:{P2}px"><div class="eyebrow">Trapped capital</div><div class="fig c-blue" id="{p}-n2">$42,775</div><div class="desc">in stock beyond 90 days of cover</div></div>
<div class="col" id="{p}-c3" style="left:{P3}px"><div class="eyebrow">Margin erosion</div><div class="fig c-blue">$1.22 → <span id="{p}-n3">$1.14</span></div><div class="desc">margin per can of Cola</div></div>
<div id="{p}-lock" class="pill cash-pill" style="left:{P2+110}px;top:380px"><b>$</b>Cash tied up</div>
<div id="{p}-v3">
  <div class="price"><span class="k">Unit cost</span><span class="v" data-layout-allow-overlap><span id="{p}-c128">$1.28</span><span id="{p}-c136">$1.36</span></span><span id="{p}-up" class="up">+6.3%</span></div>
  <div class="mbar"><i id="{p}-cost" style="width:{1.28/2.5*440:.1f}px"></i><i id="{p}-marg" style="width:{1.22/2.5*440:.1f}px"></i></div>
  <div class="mlab"><span>cost</span><span>margin</span><span class="r">shelf price $2.50</span></div>
</div>
<div id="{p}-chips">
  <div class="chip dchip" id="{p}-k1" style="left:{P1+240}px"><i class="dot-ink"></i>Sales history</div>
  <div class="chip dchip" id="{p}-k2" style="left:{P2+240}px"><i class="dot-ink"></i>Stock &amp; orders</div>
  <div class="chip dchip" id="{p}-k3" style="left:{P3+240}px"><i class="dot-ink"></i>Supplier terms</div>
</div>
"""
    css = WORLD_CSS(p) + TL_CSS(p) + DCHIP_CSS(p) + f"""
#{p}-head {{ position:absolute; left:120px; top:96px; }}
#{p}-sample {{ position:absolute; right:120px; top:104px; font-size:18px; color: var(--ink-2); border-color: var(--line-strong); background:#fff; }}
#{p}-scene .col {{ position:absolute; top:262px; width:480px; }}
#{p}-scene .col .fig {{ font-size:64px; font-weight:600; letter-spacing:-0.02em; margin-top:336px; font-variant-numeric: tabular-nums; }}
#{p}-scene .col .desc {{ font-size:26px; color: var(--ink-2); margin-top:8px; line-height:1.35; }}
#{p}-v3 {{ position:absolute; left:{P3}px; top:330px; width:440px; }}
#{p}-v3 .price {{ display:flex; align-items:baseline; gap:16px; padding:14px 20px; background:#fff; border:1px solid var(--line); border-radius:12px; box-shadow: var(--shadow); width:max-content; }}
#{p}-v3 .price .k {{ font-size:22px; color: var(--ink-2); }}
#{p}-v3 .price .v {{ position:relative; display:inline-block; width:100px; height:40px; font-family: var(--mono); font-size:34px; font-weight:500; }}
#{p}-v3 .price .v span {{ position:absolute; left:0; top:0; }}
#{p}-v3 .price .up {{ font-size:20px; font-weight:600; color: var(--red-ink); }}
#{p}-v3 .mbar {{ display:flex; margin-top:44px; height:40px; border-radius:8px; overflow:hidden; background: var(--line); }}
#{p}-v3 .mbar i {{ display:block; height:100%; }}
#{p}-cost {{ background: var(--ink); }} #{p}-marg {{ background: var(--blue); }}
#{p}-v3 .mlab {{ display:flex; gap:18px; margin-top:10px; font-size:20px; color: var(--ink-2); }} #{p}-v3 .mlab .r {{ margin-left:auto; }}
"""
    d8 = TL_X0 + 8 * TL_PX
    js = f"""
// S02's timeline clears; its truck travels into the stockout panel
tl.to(["#{p}-tint", "#{p}-redseg", "#{p}-axis", "#{p}-ticks", "#{p}-tleb", "#{p}-tlab", "#{p}-plus"], {{ opacity: 0, duration: 0.4 }}, 0);
tl.fromTo("#{p}-truck", {{ x: {d8}, y: {TL_Y - 6}, scale: 1.25 }}, {{ x: {g1:.0f}, y: 514, scale: 1, duration: 1.0, ease: "power2.inOut" }}, 0.15);
rise("#{p}-head", T.head);
fadeIn("#{p}-sample", 0.8);
// panel 1: coverage runs out before the truck
fadeIn(["#{p}-c1 .eyebrow", "#{p}-c2 .eyebrow", "#{p}-c3 .eyebrow"], 0.5, 0.4);
fadeIn(["#{p}-v1 path", "#{p}-v1 line", "#{p}-v1 text:not(#{p}-covt)"], 0.7, 0.5);
tl.fromTo("#{p}-cov", {{ scaleX: 0, svgOrigin: "{P_AX} 463" }}, {{ scaleX: 1, duration: 0.8, ease: "power2.out", svgOrigin: "{P_AX} 463" }}, T.stock - 0.3);
fadeIn("#{p}-covt", T.stock + 0.3, 0.3);
tl.fromTo("#{p}-gap", {{ opacity: 0, scaleX: 0, svgOrigin: "{g0:.0f} 470" }}, {{ opacity: 1, scaleX: 1, duration: 0.5, ease: "power2.out", svgOrigin: "{g0:.0f} 470" }}, T.stock + 0.4);
rise(["#{p}-c1 .fig", "#{p}-c1 .desc"], T.stock + 0.5, {{ s: 0.1 }});
// panel 2: cartons stack up and lock the cash
tl.fromTo("#{p}-v2 .ct", {{ opacity: 0, y: -40 }}, {{ opacity: 1, y: 0, duration: 0.3, stagger: 0.05, ease: "power2.out" }}, T.over - 0.4);
pop("#{p}-lock", T.over + 0.3);
rise(["#{p}-c2 .fig", "#{p}-c2 .desc"], T.over + 0.3, {{ s: 0.1 }});
count($("#{p}-n2"), 0, 42775, T.over + 0.3, 1.0, (v) => "$" + Math.round(v).toLocaleString("en-US"));
// panel 3: the cost tag moves and the margin bar pays for it
rise("#{p}-v3", T.price - 0.4);
gsap.set("#{p}-c136", {{ opacity: 0, y: 14 }});
gsap.set("#{p}-up", {{ opacity: 0 }});
tl.to("#{p}-c128", {{ opacity: 0, y: -14, duration: 0.3 }}, T.price + 0.5);
tl.to("#{p}-c136", {{ opacity: 1, y: 0, duration: 0.3 }}, T.price + 0.6);
tl.to("#{p}-up", {{ opacity: 1, duration: 0.3 }}, T.price + 0.8);
tl.to("#{p}-cost", {{ width: {1.36/2.5*440:.1f}, duration: 0.8, ease: "power2.inOut" }}, T.price + 0.7);
tl.to("#{p}-marg", {{ width: {1.14/2.5*440:.1f}, duration: 0.8, ease: "power2.inOut" }}, T.price + 0.7);
rise(["#{p}-c3 .fig", "#{p}-c3 .desc"], T.price + 0.6, {{ s: 0.1 }});
count($("#{p}-n3"), 1.22, 1.14, T.erodes, 0.8, (v) => "$" + v.toFixed(2));
// collapse into the three data inputs StockPulse reads (S04 picks them up)
tl.to(["#{p}-head", "#{p}-sample", "#{p}-art", "#{p}-truck", "#{p}-c1", "#{p}-c2", "#{p}-c3", "#{p}-lock", "#{p}-v3"], {{ opacity: 0, duration: 0.4, ease: "power1.in" }}, T.out);
tl.fromTo("#{p}-chips .dchip", {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "back.out(1.6)", stagger: 0.06 }}, T.out + 0.2);
gsap.set("#{p}-chips .dchip", {{ xPercent: -50, yPercent: -50 }});
"""
    return css, body, js, T

DCHIP_CSS = lambda p: f"""
#{p}-scene .dchip {{ position:absolute; top:430px; font-size:28px; padding:12px 26px; color: var(--ink); border-color: var(--line-strong); background:#fff; box-shadow: var(--shadow); white-space:nowrap; }}
#{p}-scene .dot-ink {{ width:12px; height:12px; border-radius:3px; background: var(--indigo); display:block; }}
"""

# ================================================================================================
def s04(sid, dur, C):
    T = {"logo": 0.9, "promise": C.at("budget-aware"), "without": C.at("purchasing decisions")}
    T["push"] = max(T["without"] + 1.4, 5.0)
    T["move"] = T["push"] + 1.6
    p = sid
    k, BX, BY, BW, BH = 1.29, 160, 130, 1600, 780
    wide, kpi = camv(k, 0, 0, 1600 / 1600 / k), camv(k, 300, 88)
    body = f"""
<svg id="{p}-paths" class="full" viewBox="0 0 1920 1080" width="1920" height="1080" fill="none" stroke="#4F67E8" stroke-width="3" stroke-linecap="round" opacity="0.55">
  <path d="M{P1+240},430 C{P1+240},330 700,360 905,340"/><path d="M{P2+240},430 L960,350"/><path d="M{P3+240},430 C{P3+240},330 1220,360 1015,340"/>
</svg>
<div id="{p}-chips">
  <div class="chip dchip" id="{p}-k1" style="left:{P1+240}px"><i class="dot-ink"></i>Sales history</div>
  <div class="chip dchip" id="{p}-k2" style="left:{P2+240}px"><i class="dot-ink"></i>Stock &amp; orders</div>
  <div class="chip dchip" id="{p}-k3" style="left:{P3+240}px"><i class="dot-ink"></i>Supplier terms</div>
</div>
<div id="{p}-ring"></div>
<img id="{p}-logo" src="{BRAND}logo.png" alt="StockPulse">
<div id="{p}-promise" class="headline">{words("Explainable, budget-aware")} <span class="c-indigo">{words("purchasing decisions.")}</span></div>
<div id="{p}-sub">Works with your existing systems</div>
{browser(f"{p}-br", BX, BY, BW, BH, "overview", [("c01-overview.png", f"{p}-img")], k)}
"""
    css = DCHIP_CSS(p) + f"""
#{p}-scene .full {{ position:absolute; inset:0; }}
#{p}-logo {{ position:absolute; left:690px; top:262px; width:540px; transform-origin: 0 0; }}
#{p}-ring {{ position:absolute; left:810px; top:190px; width:300px; height:300px; border-radius:50%; border:3px solid var(--indigo); opacity:0; }}
#{p}-promise {{ position:absolute; left:0; right:0; top:470px; text-align:center; }}
#{p}-promise .w {{ display:inline-block; }}
#{p}-sub {{ position:absolute; left:0; right:0; top:560px; text-align:center; font-size:30px; color: var(--ink-2); }}
"""
    js = f"""
gsap.set("#{p}-chips .dchip", {{ xPercent: -50, yPercent: -50 }});
// the three inputs converge into StockPulse
draw("#{p}-paths path", 0.05, 0.8, 1, "power2.out");
tl.to("#{p}-k1", {{ x: {905 - P1 - 240}, duration: 0.95, ease: "power1.in" }}, 0.2);
tl.to("#{p}-k1", {{ y: -90, duration: 0.95, ease: "power2.out" }}, 0.2);
tl.to("#{p}-k2", {{ y: -80, duration: 0.95, ease: "power2.inOut" }}, 0.2);
tl.to("#{p}-k3", {{ x: {1015 - P3 - 240}, duration: 0.95, ease: "power1.in" }}, 0.2);
tl.to("#{p}-k3", {{ y: -90, duration: 0.95, ease: "power2.out" }}, 0.2);
tl.to("#{p}-chips .dchip", {{ opacity: 0, scale: 0.5, duration: 0.3, ease: "power1.in" }}, 0.85);
tl.to("#{p}-paths", {{ opacity: 0, duration: 0.4 }}, 1.0);
tl.fromTo("#{p}-logo", {{ opacity: 0, scale: 0.92, x: 22, y: 6 }}, {{ opacity: 1, scale: 1, x: 0, y: 0, duration: 0.8, ease: "power3.out" }}, T.logo);
tl.fromTo("#{p}-ring", {{ opacity: 0.6, scale: 0.4 }}, {{ opacity: 0, scale: 1.6, duration: 1.0, ease: "power2.out", immediateRender: false }}, T.logo);
rise("#{p}-promise .w", T.promise - 0.1, {{ s: 0.1, y: 20 }});
rise("#{p}-sub", T.without - 0.1);
// into the real product: the logo docks, the dashboard rises wide, one camera move to the KPIs, hold
tl.to("#{p}-logo", {{ x: {160 - 690}, y: {44 - 262}, scale: 0.3, duration: 0.8, ease: "power2.inOut" }}, T.push);
tl.to(["#{p}-promise", "#{p}-sub"], {{ opacity: 0, y: -24, duration: 0.35, ease: "power2.in" }}, T.push - 0.1);
tl.fromTo("#{p}-br", {{ opacity: 0, y: 60 }}, {{ opacity: 1, y: 0, duration: 0.8, ease: "power3.out" }}, T.push + 0.3);
gsap.set("#{p}-br-cam", {wide});
camTo("#{p}-br-cam", {kpi}, T.move, 1.4);
"""
    return css, body, js, T

# ================================================================================================
def s05(sid, dur, C):
    T = {"pdf": C.at("A supplier changes", -0.2), "eight": C.at("five days to eight"), "cola": C.at("increasing its price"),
         "fields": C.at("StockPulse extracts"), "nothing": C.at("ready for human review"), "confirm": C.at("purchasing decisions", 0.3)}
    T["pan"] = max(T["nothing"] - 0.2, T["fields"] + 3 * 0.22 + 1.6)
    T["verified"] = T["confirm"] + 0.3
    p = sid
    k, BX, BY, BW, BH = 1.12, 600, 110, 1200, 760
    A, B, Cv = (310, 215), (440, 640), (310, 60)
    # extracted fields: label, value, conf, page rect of the real input it fills
    F = [("lead time", "8", "90%", (720, 361, 907, 392), (330, 318)),
         ("unit cost", "1.36", "97%", (720, 483, 907, 515), (470, 430)),
         ("MOQ", "48", "95%", (920, 483, 1107, 515), (300, 455)),
         ("case pack", "24", "99%", (1120, 483, 1305, 515), (390, 400))]
    chips, rings = "", ""
    for i, (n, v, c, (x0, y0, x1, y1), _) in enumerate(F):
        tx, ty = scr(BX, BY, k, *A, (x0 + x1) / 2, (y0 + y1) / 2)
        chips += f'<div class="chip ember fld" data-layout-allow-overlap id="{p}-f{i}" style="left:{tx}px;top:{ty}px"><span>{n}</span><b class="mono">{v}</b><span class="conf">{c}</span></div>'
        rings += f'<div class="ring ember-ring" id="{p}-r{i}" style="{box(k, x0, y0, x1, y1, 5)}"></div>'
    rings += f'<div class="ring" id="{p}-rc" style="{box(k, 1366, 1097, 1506, 1129, 6)}"></div>'
    rings += f'<div class="ring" id="{p}-rv" style="{box(k, 333, 288, 640, 350, 8)}"></div>'
    cx, cy = scr(BX, BY, k, *B, 1436, 1113)
    body = f"""
{pdf_card(p)}
<div id="{p}-calls">
  <div class="cl" id="{p}-q1"><i class="ember"></i>AI reads the document</div>
  <div class="cl" id="{p}-q2"><i class="ink"></i>Nothing changes until confirmed</div>
  <div class="cl" id="{p}-q3"><i class="blue"></i>Confirmed: trusted data updated</div>
</div>
{browser(f"{p}-br", BX, BY, BW, BH, "inbox", [("c02b-review-full.png", f"{p}-i1"), ("c02d-review-ready-full.png", f"{p}-i2"), ("c02e-verified-full.png", f"{p}-i3")], k, rings)}
<div id="{p}-blank"></div>
{chips}
{LEGEND(p)}
{CURSOR(p)}
"""
    css = PDF_CSS(p) + f"""
#{p}-pdf {{ left:120px; top:150px; }}
#{p}-calls {{ position:absolute; left:120px; top:640px; width:440px; height:120px; }}
#{p}-calls .cl {{ position:absolute; left:0; top:0; display:flex; align-items:center; gap:14px; font-size:34px; font-weight:600; line-height:1.15; letter-spacing:-0.01em; }}
#{p}-calls .cl i {{ width:14px; height:14px; border-radius:4px; display:block; flex:none; }}
#{p}-calls .ember {{ background: var(--ember); }} #{p}-calls .ink {{ background: var(--ink); }} #{p}-calls .blue {{ background: var(--blue); }}
#{p}-scene .fld {{ position:absolute; font-size:21px; padding:8px 16px; background:#fff; box-shadow: var(--shadow); white-space:nowrap; }}
#{p}-scene .fld .conf {{ opacity:.75; font-size:18px; }}
#{p}-scene .ember-ring {{ border-color: var(--ember); }}
#{p}-blank {{ position:absolute; left:{BX+1}px; top:{BY+41}px; width:{BW-2}px; height:{BH-42}px; background:#F7F9FC; opacity:0; border-radius:0 0 15px 15px; }}
"""
    js = f"""
rise("#{p}-pdf", T.pdf, {{ y: 30 }});
tl.fromTo("#{p}-br", {{ opacity: 0, x: 40 }}, {{ opacity: 1, x: 0, duration: 0.7, ease: "power3.out" }}, T.pdf + 0.3);
gsap.set("#{p}-br-cam", {camv(k, *A)});
tl.fromTo("#{p}-hl1", {{ backgroundColor: "rgba(253,240,236,0)", boxShadow: "inset 0 -2px 0 rgba(232,106,74,0)" }}, {{ backgroundColor: "rgba(253,240,236,1)", boxShadow: "inset 0 -2px 0 rgba(232,106,74,1)", duration: 0.4 }}, T.eight);
tl.fromTo("#{p}-hl2", {{ backgroundColor: "rgba(253,240,236,0)", boxShadow: "inset 0 -2px 0 rgba(232,106,74,0)" }}, {{ backgroundColor: "rgba(253,240,236,1)", boxShadow: "inset 0 -2px 0 rgba(232,106,74,1)", duration: 0.4 }}, T.cola);
// AI extraction: each value lifts off the PDF and lands on the real field it fills
rise("#{p}-q1", T.fields - 0.3);
{json.dumps([[sx - scr(BX, BY, k, *A, (f[3][0] + f[3][2]) / 2, (f[3][1] + f[3][3]) / 2)[0], sy - scr(BX, BY, k, *A, (f[3][0] + f[3][2]) / 2, (f[3][1] + f[3][3]) / 2)[1]] for f in F for sx, sy in [f[4]]])}.forEach(([dx, dy], i) => {{
  const t = T.fields + i * 0.22, s = "#{p}-f" + i;
  gsap.set(s, {{ xPercent: -50, yPercent: -50 }});
  tl.fromTo(s, {{ opacity: 0, x: dx, y: dy, scale: 0.9 }}, {{ opacity: 1, duration: 0.2 }}, t);
  tl.to(s, {{ x: 0, y: 0, scale: 1, duration: 0.9, ease: "power3.inOut" }}, t);
  tl.to(s, {{ opacity: 0, scale: 0.85, duration: 0.3, ease: "power1.in" }}, t + 1.0);
  tl.fromTo("#{p}-r" + i, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.25 }}, t + 0.95);
}});
// the person reviews: guardrail lines excluded, one pan down to Confirm, the click
tl.to("#{p}-q1", {{ opacity: 0, duration: 0.3 }}, T.nothing - 0.5);
rise("#{p}-q2", T.nothing - 0.2);
tl.fromTo("#{p}-i2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, T.pan - 0.2);
tl.to("#{p}-scene .ember-ring", {{ opacity: 0, duration: 0.3 }}, T.pan - 0.2);
camTo("#{p}-br-cam", {camv(k, *B)}, T.pan, 1.2);
tl.fromTo("#{p}-rc", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, T.pan + 1.2);
click("#{p}-cur", "#{p}-rip", 1500, 900, {cx}, {cy}, T.confirm);
tl.to("#{p}-cur", {{ opacity: 0, duration: 0.25 }}, T.confirm + 0.3);
tl.to("#{p}-rc", {{ opacity: 0, duration: 0.2 }}, T.confirm + 0.2);
// the page changes to its verified state (a navigation, so a quick dip rather than a camera move)
tl.to("#{p}-blank", {{ opacity: 1, duration: 0.15 }}, T.verified);
tl.set("#{p}-br-cam", {camv(k, *Cv)}, T.verified + 0.16);
tl.set("#{p}-i3", {{ opacity: 1 }}, T.verified + 0.16);
tl.set(["#{p}-i1", "#{p}-i2"], {{ opacity: 0 }}, T.verified + 0.16);
tl.to("#{p}-blank", {{ opacity: 0, duration: 0.3 }}, T.verified + 0.2);
tl.fromTo("#{p}-rv", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35 }}, T.verified + 0.6);
tl.to("#{p}-q2", {{ opacity: 0, duration: 0.3 }}, T.verified);
rise("#{p}-q3", T.verified + 0.3);
fadeIn("#{p}-legend", 0.6);
"""
    # document in; fields land on the real form for review; the person's Confirm click; the page turns Verified
    T["sfx_select"] = T["pdf"] + 0.3; T["sfx_review"] = T["fields"] + 0.95; T["sfx_tap"] = T["confirm"]; T["sfx_success"] = T["verified"] + 0.2
    return css, body, js, T

# ================================================================================================
def s06(sid, dur, C):
    T = {"next": C.at("Next, dedicated"), "models": C.at("time-series models"), "notllm": C.at("forecast future demand"),
         "each": C.at("StockPulse compares"), "units": C.at("what they may need"), "weeks": C.at("coming weeks"), "scored": C.at("The goal is")}
    T["strip"] = T["scored"] + 1.4
    p = sid
    h, fc = FC["history"], FC["forecast"][:14]
    X0, X1, Y0, VS = 200, 1260, 640, 2.9
    n = len(h) + len(fc) - 1
    X = lambda i: X0 + i * (X1 - X0) / n
    Y = lambda v: Y0 - v * VS
    act = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(h))
    fpts = [(len(h) - 1, h[-1])] + [(len(h) + j, f["value"]) for j, f in enumerate(fc)]
    fore = "M" + " L".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in fpts)
    band = "M" + " L".join(f"{X(len(h)+j):.1f},{Y(f['hi']):.1f}" for j, f in enumerate(fc)) + " L" + " L".join(f"{X(len(h)+j):.1f},{Y(f['lo']):.1f}" for j, f in reversed(list(enumerate(fc)))) + " Z"
    today = X(len(h) - 0.5)
    sma = FC["sma14"]
    grid = "".join(f'<line x1="{X0}" y1="{Y(v):.0f}" x2="{X1}" y2="{Y(v):.0f}" stroke="#E3E8EF" stroke-width="1.5"/><text x="{X0-14}" y="{Y(v)+6:.0f}" font-family="Geist Mono" font-size="18" fill="#667085" text-anchor="end">{v}</text>' for v in (0, 50, 100, 150))
    dates = "".join(f'<text x="{X(i):.0f}" y="{Y0+34}" font-family="Geist Mono" font-size="18" fill="#667085" text-anchor="middle">{d}</text>' for i, d in [(0, "Aug 21"), (14, "Sep 4"), (28, "Sep 18"), (42, "Oct 2"), (56, "Oct 16"), (69, "Oct 29")])
    m, b_ = FC["holdout"]["metrics"]["model"]["wape"] * 100, FC["holdout"]["metrics"]["sma14"]["wape"] * 100
    k = 1.2
    body = f"""
<div id="{p}-tag" class="chip blue">No language model in these numbers</div>
<div id="{p}-chart" class="card"></div>
<svg id="{p}-plot" class="full" viewBox="0 0 1920 1080" width="1920" height="1080" fill="none">
  <defs><clipPath id="{p}-bclip"><rect id="{p}-bclipr" x="{X(len(h)-1):.1f}" y="150" width="{X1 - X(len(h)-1) + 4:.1f}" height="520"/></clipPath></defs>
  <g id="{p}-grid">{grid}{dates}</g>
  <path id="{p}-band" d="{band}" fill="#3478F6" fill-opacity="0.16" stroke="none" clip-path="url(#{p}-bclip)"/>
  <line id="{p}-today" x1="{today:.1f}" y1="200" x2="{today:.1f}" y2="{Y0}" stroke="#98A2B3" stroke-width="2" stroke-dasharray="5 6"/>
  <text id="{p}-todayt" x="{today - 10:.1f}" y="232" font-family="Geist" font-size="20" font-weight="500" fill="#667085" text-anchor="end">Today</text>
  <path id="{p}-act" d="{act}" stroke="#202A3B" stroke-width="2.5" stroke-linejoin="round"/>
  <path id="{p}-sma" d="M{X(len(h)):.1f},{Y(sma):.1f} L{X1},{Y(sma):.1f}" stroke="#D99A22" stroke-width="3" stroke-dasharray="9 7"/>
  <path id="{p}-fore" d="{fore}" stroke="#3478F6" stroke-width="4" stroke-linejoin="round"/>
  <path id="{p}-brk" d="M{X(len(h)):.1f},232 L{X(len(h)):.1f},222 L{X1},222 L{X1},232" stroke="#3478F6" stroke-width="2.5"/>
</svg>
<div id="{p}-ctitle" class="label">Cola 330ml · units sold per day</div>
<div id="{p}-leg"><span class="a">Actual sales</span><span class="f">Forecast</span><span class="b">80% range</span><span class="s">14-day average</span></div>
<div id="{p}-right">
  <div id="{p}-c1"><div class="big c-blue"><span id="{p}-n">861</span> units</div><div class="sub">Cola 330ml, next 14 days</div></div>
  <div id="{p}-c2"><div class="mid c-blue">754–968</div><div class="sub">80% range</div></div>
  <div id="{p}-wape" class="card">
    <div class="label">Held-out error (WAPE), lower is better</div>
    <div class="wl">Forecast model <b>{m:.1f}%</b></div><div class="wb"><i id="{p}-b1" style="width:{m/35*100:.1f}%;background:var(--blue)"></i></div>
    <div class="wl">14-day average <b>{b_:.1f}%</b></div><div class="wb"><i id="{p}-b2" style="width:{b_/35*100:.1f}%;background:#D99A22"></i></div>
  </div>
</div>
{browser(f"{p}-br", 120, 716, 1006, 176, "forecasts?sku=SKU008", [("c03-forecast.png", f"{p}-img")], k)}
{LEGEND(p)}
"""
    css = f"""
#{p}-scene .full {{ position:absolute; inset:0; }}
#{p}-tag {{ position:absolute; left:120px; top:84px; }}
#{p}-chart {{ position:absolute; left:120px; top:140px; width:1200px; height:556px; }}
#{p}-ctitle {{ position:absolute; left:150px; top:158px; }}
#{p}-leg {{ position:absolute; left:640px; top:162px; display:flex; gap:22px; font-size:19px; color: var(--ink-2); }}
#{p}-leg span::before {{ content:""; display:inline-block; width:22px; height:4px; margin-right:8px; vertical-align:5px; border-radius:2px; }}
#{p}-leg .a::before {{ background: var(--ink); }} #{p}-leg .f::before {{ background: var(--blue); }}
#{p}-leg .b::before {{ height:12px; vertical-align:1px; background: rgba(52,120,246,.2); }} #{p}-leg .s::before {{ background: repeating-linear-gradient(90deg, #D99A22 0 7px, transparent 7px 11px); }}
#{p}-right {{ position:absolute; left:1380px; top:150px; width:420px; display:flex; flex-direction:column; gap:28px; }}
#{p}-right .big {{ font-size:72px; font-weight:600; letter-spacing:-0.025em; font-variant-numeric: tabular-nums; }}
#{p}-right .mid {{ font-size:52px; font-weight:600; letter-spacing:-0.02em; }}
#{p}-right .sub {{ font-size:24px; color: var(--ink-2); margin-top:4px; }}
#{p}-wape {{ padding:24px 26px; }}
#{p}-wape .wl {{ display:flex; justify-content:space-between; font-size:22px; margin-top:16px; }}
#{p}-wape .wl b {{ font-family: var(--mono); font-weight:500; }}
#{p}-wape .wb {{ height:16px; margin-top:8px; border-radius:4px; background: var(--line); }}
#{p}-wape .wb i {{ display:block; height:16px; border-radius:4px; transform-origin:0 50%; }}
"""
    js = f"""
gsap.set("#{p}-br-cam", {camv(k, 312, 304)});
rise(["#{p}-chart", "#{p}-ctitle"], 0.2, {{ y: 20 }});
fadeIn(["#{p}-grid", "#{p}-leg"], 0.5, 0.5);
fadeIn("#{p}-legend", 0.6);
// 56 days of real sales draw in, then the model's 14 days and its range
draw("#{p}-act", T.next + 0.2, 2.4, 1, "power1.inOut");
fadeIn(["#{p}-today", "#{p}-todayt"], T.models, 0.4);
rise("#{p}-tag", T.notllm - 0.1);
draw("#{p}-fore", T.each - 0.2, 1.2, 1, "power2.inOut");
tl.fromTo("#{p}-bclipr", {{ scaleX: 0, svgOrigin: "{X(len(h)-1):.1f} 400" }}, {{ scaleX: 1, duration: 1.2, ease: "power2.inOut", svgOrigin: "{X(len(h)-1):.1f} 400" }}, T.each - 0.2);
draw("#{p}-brk", T.units - 0.3, 0.6, 1, "power2.out");
rise("#{p}-c1", T.units - 0.3);
count($("#{p}-n"), 0, 861, T.units, 1.2, (v) => Math.round(v));
rise("#{p}-c2", T.weeks);
tl.to("#{p}-band", {{ fillOpacity: 0.3, duration: 0.4, yoyo: true, repeat: 1 }}, T.weeks + 0.1);
// scored against the simple baseline
draw("#{p}-sma", T.scored, 0.8, 1, "power2.out");
rise("#{p}-wape", T.scored + 0.2);
tl.fromTo(["#{p}-b1", "#{p}-b2"], {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.9, stagger: 0.2, ease: "power2.out" }}, T.scored + 0.5);
// the same numbers in the real app
tl.fromTo("#{p}-br", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, T.strip);
"""
    return css, body, js, T

# ================================================================================================
def s07(sid, dur, C):
    X0, PX, AY = 240, 130, 560
    T = {"head": 0.3, "eight": C.at("delivery taking longer"), "stock": C.at("current stock"), "lasts": C.at("run out before"),
         "rules": C.at("StockPulse combines"), "critical": C.at("flag products")}
    p = sid
    k, BX, BY = 1.2, 231, 692
    d5, d8, s57 = X0 + 5 * PX, X0 + 8 * PX, X0 + 5.7 * PX
    ticks = "".join(f'<line x1="{X0+d*PX}" y1="{AY}" x2="{X0+d*PX}" y2="{AY+12}" stroke="#98A2B3" stroke-width="2"/><text x="{X0+d*PX}" y="{AY+40}" font-family="Geist Mono" font-size="19" fill="#667085" text-anchor="middle">{d}d</text>' for d in range(11))
    ring = f'<div id="{p}-ring" class="ring red" style="{box(k, 330, 400, 760, 462, 6)}"></div>'
    body = f"""
<div id="{p}-eyebrow" class="eyebrow">Cola 330ml · Angkor’s new terms</div>
<div id="{p}-head" class="headline">Stock vs. delivery</div>
<svg id="{p}-viz" class="full" viewBox="0 0 1920 1080" width="1920" height="1080">
  <rect id="{p}-gap" x="{s57:.0f}" y="300" width="{d8 - s57:.0f}" height="{AY - 300}" fill="#FCEDEF" stroke="#D94F61" stroke-width="2"/>
  <path id="{p}-axis" d="M{X0},{AY} L{X0+10*PX},{AY}" stroke="#CDD5E0" stroke-width="3"/><g id="{p}-ticks">{ticks}</g>
  <rect id="{p}-supply" x="{X0}" y="330" width="{s57 - X0:.0f}" height="46" rx="8" fill="#3478F6"/>
  <rect id="{p}-lead" x="{X0}" y="452" width="{d8 - X0}" height="46" rx="8" fill="#202A3B"/>
  <g id="{p}-was"><line x1="{d5}" y1="444" x2="{d5}" y2="506" stroke="#F7F9FC" stroke-width="3"/></g>
  <g id="{p}-truck" transform="translate({d5},{AY-6}) scale(1.25)">{TRUCK}</g>
</svg>
<div class="l" id="{p}-l1" style="top:282px"><b class="c-blue">Stock lasts 5.7 days</b><span> · 110 on hand + 240 on order ÷ 61.3 a day</span></div>
<div class="l" id="{p}-l2" style="top:404px"><b>Lead time <span id="{p}-lt5">5</span><span id="{p}-lt8">8</span> days</b></div>
<div id="{p}-gaplab"><div class="fig c-red">2.3 days</div><div class="sub">shelf empty before delivery</div></div>
<div id="{p}-rule">stock + on order  &lt;  daily demand × lead time   →   <b class="c-red">critical</b></div>
{browser(f"{p}-br", BX, BY, 1458, 162, "risk?sku=SKU008", [("c04-risk.png", f"{p}-img")], k, ring)}
"""
    css = f"""
#{p}-scene .full {{ position:absolute; inset:0; }}
#{p}-eyebrow {{ position:absolute; left:120px; top:96px; }}
#{p}-head {{ position:absolute; left:120px; top:132px; }}
#{p}-scene .l {{ position:absolute; left:{X0}px; font-size:28px; }}
#{p}-scene .l span {{ color: var(--ink-2); font-size:24px; }}
#{p}-l2 span {{ color: inherit !important; font-size:inherit !important; }}
#{p}-lt5, #{p}-lt8 {{ display:inline-block; }}
#{p}-gaplab {{ position:absolute; left:{d8 + 30}px; top:300px; }}
#{p}-gaplab .fig {{ font-size:56px; font-weight:600; letter-spacing:-0.02em; }}
#{p}-gaplab .sub {{ font-size:26px; color: var(--ink-2); }}
#{p}-rule {{ position:absolute; left:{X0}px; top:618px; font-family: var(--mono); font-size:24px; white-space:pre; }}
"""
    js = f"""
gsap.set("#{p}-br-cam", {camv(k, 312, 380)});
fadeIn("#{p}-eyebrow", 0.2);
rise("#{p}-head", T.head);
draw("#{p}-axis", 0.6, 0.6, 1, "power2.out");
fadeIn("#{p}-ticks", 0.8, 0.4);
fadeIn("#{p}-l2", 0.9);
tl.fromTo("#{p}-lead", {{ scaleX: 0, svgOrigin: "{X0} 475" }}, {{ scaleX: 5 / 8, duration: 0.8, ease: "power2.out", svgOrigin: "{X0} 475" }}, 1.0);
tl.fromTo("#{p}-truck", {{ opacity: 0, y: {AY - 26} }}, {{ opacity: 1, y: {AY - 6}, duration: 0.4, ease: "power2.out" }}, 1.4);
gsap.set("#{p}-truck", {{ x: {d5} }});
// eight days: the truck and the lead-time bar move together
gsap.set("#{p}-lt8", {{ opacity: 0, display: "none" }});
tl.set("#{p}-lt5", {{ display: "none" }}, T.eight + 0.5);
tl.set("#{p}-lt8", {{ display: "inline-block", opacity: 1 }}, T.eight + 0.5);
fadeIn("#{p}-was", T.eight);
tl.to("#{p}-lead", {{ scaleX: 1, duration: 1.0, ease: "power2.inOut", svgOrigin: "{X0} 475" }}, T.eight + 0.1);
tl.to("#{p}-truck", {{ x: {d8}, duration: 1.0, ease: "power2.inOut" }}, T.eight + 0.1);
// stock on hand and on order
rise("#{p}-l1", T.stock - 0.3);
tl.fromTo("#{p}-supply", {{ scaleX: 0, svgOrigin: "{X0} 353" }}, {{ scaleX: 1, duration: 1.1, ease: "power2.out", svgOrigin: "{X0} 353" }}, T.stock);
// the gap
tl.fromTo("#{p}-gap", {{ opacity: 0, scaleX: 0, svgOrigin: "{s57:.0f} 430" }}, {{ opacity: 1, scaleX: 1, duration: 0.6, ease: "power2.out", svgOrigin: "{s57:.0f} 430" }}, T.lasts);
rise("#{p}-gaplab", T.lasts + 0.2);
rise("#{p}-rule", T.rules - 0.1);
tl.fromTo("#{p}-br", {{ opacity: 0, y: 30 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power3.out" }}, T.critical - 0.6);
tl.fromTo("#{p}-ring", {{ opacity: 0, scale: 1.12 }}, {{ opacity: 1, scale: 1, duration: 0.4 }}, T.critical + 0.2);
"""
    T["sfx_review"] = T["critical"] + 0.2  # the real Risk Radar row is ringed as Critical
    return css, body, js, T

# ================================================================================================
def s08(sid, dur, C):
    T = {"head": 0.3, "t1": C.at("expected demand"), "t2": C.at("lead time"), "t3": C.at("safety stock"),
         "t4": C.at("incoming orders"), "t5": C.at("incoming orders", 0.6), "res": C.at("When the budget", -0.2),
         "cut": C.at("is limited"), "covered": C.at("prioritizes critical"), "lower": C.at("explains the trade-offs")}
    T["b"] = T["cut"] - 0.8
    T["click"] = T["cut"] + 0.9
    p = sid
    k, BX, BY, BW, BH = 1.2, 942, 150, 836, 578
    PXD = 720 / 12000  # budget bar: px per dollar
    rings = (f'<div class="ring" id="{p}-ra" style="{box(k, 1093, 368, 1275, 452, 6)}"></div>'
             f'<div class="ring" id="{p}-rb" style="{box(k, 1295, 375, 1495, 445, 6)}"></div>'
             f'<div class="ring" id="{p}-rd" style="{box(k, 848, 474, 1045, 560, 6)}"></div>')
    cx, cy = scr(BX, BY, k, 830, 180, 876, 328)
    def tile(i, n, lab, cls=""):
        return f'<div class="t {cls}" id="{p}-t{i}"><div class="n">{n}</div><div class="l">{lab}</div></div>'
    op = lambda i, o: f'<div class="op" id="{p}-o{i}">{o}</div>'
    crit = "".join(f'<i class="cs" id="{p}-cs{i}"></i>' for i in range(5))
    body = f"""
<div id="{p}-a">
  <div id="{p}-head" class="headline">How much to buy?</div>
  <div id="{p}-eq">
    {tile(1, "486", "demand over the 8-day lead time")}{op(1, "+")}{tile(2, "429", "demand over the 7-day review")}{op(2, "+")}{tile(3, "174", "safety stock")}{op(3, "−")}{tile(4, "350", "on hand + on order")}{op(4, "=")}{tile(5, "740", "needed")}{op(5, "→")}{tile(6, "744", "rounded to cases of 24 · MOQ 48", "final")}
  </div>
  <div id="{p}-res" class="title">744 cans · 31 cases · <span class="c-blue">$1,011.84</span> at $1.36</div>
</div>
<div id="{p}-b">
  <div id="{p}-bh" class="eyebrow">Weekly budget</div>
  <div id="{p}-track"><i id="{p}-plan"></i><i id="{p}-over"></i></div>
  <div id="{p}-lim" data-layout-allow-overflow><span id="{p}-limv">$12,000</span></div>
  <div id="{p}-planl">Plan <b id="{p}-planv">$9,714.28</b></div>
  <div id="{p}-lines">
    <div class="ln" id="{p}-ln0"><div class="nm">Critical lines</div><div class="crit">{crit}</div><div class="q c-blue" id="{p}-cq">5 of 5 covered</div></div>
    <div class="ln" id="{p}-ln1"><div class="nm">Dish Soap 750ml</div><div class="qb"><i id="{p}-qd" style="width:{260*1.1:.0f}px"></i></div><div class="q">260 → <b>190</b></div></div>
    <div class="ln" id="{p}-ln2"><div class="nm">Body Lotion 300ml</div><div class="qb"><i id="{p}-ql" style="width:{318*1.1:.0f}px"></i></div><div class="q">318 → <b>132</b></div></div>
    <div id="{p}-note">Lower-priority lines give up safety stock first</div>
  </div>
  {browser(f"{p}-br", BX, BY, BW, BH, "cart", [("c06a-cart-plan.png", f"{p}-i1"), ("c06b-whatif-30.png", f"{p}-i2")], k, rings)}
  {CURSOR(p)}
</div>
"""
    css = f"""
#{p}-a, #{p}-b {{ position:absolute; inset:0; }}
#{p}-head {{ position:absolute; left:120px; top:110px; }}
#{p}-eq {{ position:absolute; left:120px; right:120px; top:300px; display:flex; align-items:flex-start; gap:14px; }}
#{p}-eq .t {{ background:#fff; border:1px solid var(--line); border-radius:12px; padding:20px 22px; min-width:150px; box-shadow: var(--shadow); }}
#{p}-eq .n {{ font-size:60px; font-weight:600; color: var(--blue); letter-spacing:-.02em; }}
#{p}-eq .l {{ font-size:20px; color: var(--ink-2); margin-top:6px; max-width:170px; line-height:1.3; }}
#{p}-eq .t.final {{ border:3px solid var(--blue); background: var(--blue-tint); }}
#{p}-eq .op {{ font-size:52px; color: var(--ink-2); padding-top:22px; }}
#{p}-res {{ position:absolute; left:120px; top:580px; }}
#{p}-bh {{ position:absolute; left:140px; top:160px; }}
#{p}-track {{ position:absolute; left:140px; top:226px; width:720px; height:56px; border-radius:10px; background:#EEF1F6; border:1px solid var(--line); overflow:hidden; }}
#{p}-plan {{ position:absolute; left:0; top:8px; height:40px; width:{9714.28*PXD:.1f}px; border-radius:0 6px 6px 0; background: var(--blue); }}
#{p}-over {{ position:absolute; left:{8400*PXD:.1f}px; top:8px; height:40px; width:{(9714.28-8400)*PXD:.1f}px; background: var(--red); opacity:0; }}
#{p}-lim {{ position:absolute; left:{140 + 720 - 2}px; top:206px; width:4px; height:96px; background: var(--ink); border-radius:2px; }}
#{p}-lim span {{ position:absolute; left:50%; bottom:100%; transform:translateX(-50%); margin-bottom:6px; font-family: var(--mono); font-size:24px; font-weight:500; white-space:nowrap; }}
#{p}-planl {{ position:absolute; left:140px; top:312px; font-size:26px; color: var(--ink-2); }}
#{p}-planl b {{ color: var(--blue-ink); font-family: var(--mono); font-weight:500; }}
#{p}-lines {{ position:absolute; left:140px; top:400px; width:720px; }}
#{p}-lines .ln {{ display:grid; grid-template-columns: 230px 1fr 170px; align-items:center; gap:16px; padding:18px 0; border-top:1px solid var(--line); }}
#{p}-lines .nm {{ font-size:24px; font-weight:500; }}
#{p}-lines .q {{ font-size:24px; font-family: var(--mono); text-align:right; }}
#{p}-lines .crit {{ display:flex; gap:10px; }}
#{p}-lines .cs {{ width:30px; height:30px; border-radius:6px; background: var(--blue); display:block; }}
#{p}-lines .qb {{ height:24px; }} #{p}-lines .qb i {{ display:block; height:24px; border-radius:5px; background: #9DBDF9; }}
#{p}-note {{ font-size:22px; color: var(--ink-2); padding-top:14px; border-top:1px solid var(--line); }}
"""
    js = f"""
rise("#{p}-head", T.head);
[[1, T.t1], [2, T.t2], [3, T.t3], [4, T.t4], [5, T.t5]].forEach(([i, t]) => {{
  rise("#{p}-t" + i, t, {{ y: 24 }});
  if (i > 1) fadeIn("#{p}-o" + (i - 1), t - 0.15, 0.3);
}});
fadeIn("#{p}-o5", T.t5 + 0.5, 0.3);
tl.fromTo("#{p}-t6", {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "back.out(1.6)" }}, T.t5 + 0.6);
rise("#{p}-res", T.res);
// part B: the budget cut, as a bar and in the real cart
tl.to("#{p}-a", {{ opacity: 0, duration: 0.4 }}, T.b);
fadeIn("#{p}-b", T.b, 0.01);
gsap.set("#{p}-br-cam", {camv(k, 830, 180)});
rise(["#{p}-bh", "#{p}-track", "#{p}-lim", "#{p}-planl"], T.b + 0.1, {{ s: 0.06, y: 16 }});
rise(["#{p}-ln0", "#{p}-ln1", "#{p}-ln2"], T.b + 0.3, {{ s: 0.08, y: 16 }});
tl.fromTo("#{p}-br", {{ opacity: 0, x: 40 }}, {{ opacity: 1, x: 0, duration: 0.7, ease: "power3.out" }}, T.b + 0.2);
click("#{p}-cur", "#{p}-rip", 1300, 820, {cx}, {cy}, T.click);
tl.fromTo("#{p}-i2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, T.click + 0.15);
tl.to("#{p}-cur", {{ opacity: 0, duration: 0.25 }}, T.click + 0.35);
// the limit moves: the plan no longer fits, then re-solves under it
tl.to("#{p}-lim", {{ x: {(8400 - 12000) * PXD:.1f}, duration: 0.9, ease: "power2.inOut" }}, T.click + 0.2);
count($("#{p}-limv"), 12000, 8400, T.click + 0.2, 0.9, (v) => "$" + Math.round(v).toLocaleString("en-US"));
tl.to("#{p}-over", {{ opacity: 0.85, duration: 0.25 }}, T.click + 0.9);
tl.to("#{p}-over", {{ opacity: 0, duration: 0.3 }}, T.click + 1.5);
tl.to("#{p}-plan", {{ width: {8355.02 * PXD:.1f}, duration: 0.8, ease: "power2.inOut" }}, T.click + 1.4);
count($("#{p}-planv"), 9714.28, 8355.02, T.click + 1.4, 0.8, (v) => "$" + v.toLocaleString("en-US", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}));
tl.fromTo("#{p}-ra", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, T.click + 1.4);
tl.to("#{p}-ra", {{ opacity: 0, duration: 0.3 }}, T.covered);
// critical lines hold; lower-priority lines shrink
tl.fromTo("#{p}-ln0 .cs", {{ boxShadow: "0 0 0 0px rgba(52,120,246,0)" }}, {{ boxShadow: "0 0 0 4px rgba(52,120,246,.3)", duration: 0.3, stagger: 0.08 }}, T.covered);
tl.fromTo("#{p}-rb", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, T.covered);
tl.to("#{p}-rb", {{ opacity: 0, duration: 0.3 }}, T.lower - 0.2);
tl.to("#{p}-qd", {{ width: {190*1.1:.0f}, duration: 0.8, ease: "power2.inOut" }}, T.lower);
tl.to("#{p}-ql", {{ width: {132*1.1:.0f}, duration: 0.8, ease: "power2.inOut" }}, T.lower + 0.15);
tl.fromTo("#{p}-rd", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3 }}, T.lower);
rise("#{p}-note", T.lower + 0.6, {{ y: 10 }});
"""
    T["sfx_tap"] = T["click"]  # the −30% button press
    return css, body, js, T

# ================================================================================================
def s09(sid, dur, C):
    T = {"brief": C.at("clear explanation", -0.3), "po": C.at("purchase order draft"), "numbers": C.at("logic remains auditable"),
         "cant": C.at("cannot approve"), "person": C.at("The retailer makes")}
    T["b"] = T["person"] - 0.6
    T["c1"] = T["b"] + 1.6
    T["c2"] = T["c1"] + 1.3
    p = sid
    k, BX, BY, BW, BH = 1.2, 231, 130, 1458, 616
    CAM = (312, 60)
    ax, ay = scr(BX, BY, k, *CAM, 1347, 416)
    fx, fy = scr(BX, BY, k, *CAM, 1237, 473)
    brief = ("Cola 330ml will run out <span class='tok'>2.3 days</span> before Angkor’s new <span class='tok'>8-day</span> delivery. "
             "Order <span class='tok'>744</span> cans at the new <span class='tok'>$1.36</span> cost. Within the <span class='tok'>$8,400</span> budget, "
             "Dish Soap and Body Lotion give up safety stock first.")
    parts = re.findall(r"<span class='tok'>.*?</span>|[^\s]+", brief)  # word spans, keeping token spans whole
    brief_html = " ".join(f'<span class="w">{x}</span>' for x in parts)
    body = f"""
<div id="{p}-a">
  <div id="{p}-brief" class="card"><div class="h"><i></i>Procurement agent · briefing</div><p>{brief_html}</p></div>
  <div id="{p}-lock"><div class="btn"><svg width="18" height="20" viewBox="0 0 18 20" fill="none" stroke="#98A2B3" stroke-width="2"><rect x="2" y="9" width="14" height="10" rx="2"/><path d="M5 9V6a4 4 0 0 1 8 0v3"/></svg>Approve</div><div class="label" style="color:var(--ink-2)">The agent drafts. Only a person approves.</div></div>
  <div id="{p}-po" class="card">
    <div class="top" id="{p}-p1"><div><div class="eyebrow">Purchase order</div><div class="title" style="margin-top:6px">PO-00001 · Angkor Beverage Co</div></div><span class="pill">Draft</span></div>
    <table><tr id="{p}-p2"><th>Product</th><th class="r">Qty</th><th class="r">Unit</th><th class="r">Total</th></tr>
    <tr id="{p}-p3"><td>Cola 330ml <span class="mono" style="color:var(--ink-2);font-size:17px">SKU008</span></td><td class="r c-blue">744</td><td class="r c-blue">$1.36</td><td class="r c-blue">$1,011.84</td></tr>
    <tr id="{p}-p4"><td colspan="3" style="text-align:right;font-weight:600;border:0">Total order value</td><td class="r" style="font-weight:600;border:0">$1,011.84</td></tr></table>
  </div>
</div>
<div id="{p}-b">
  {browser(f"{p}-br", BX, BY, BW, BH, "orders/PO-00001", [("c07d-po-key.png", f"{p}-i1"), ("c07e-approve-dialog.png", f"{p}-i2"), ("c07f-po-approved.png", f"{p}-i3")], k)}
  <div id="{p}-ok" class="chip green">✓ Approved by a person · approver key required</div>
  {CURSOR(p)}
</div>
"""
    css = f"""
#{p}-a, #{p}-b {{ position:absolute; inset:0; }}
#{p}-brief {{ position:absolute; left:120px; top:120px; width:820px; padding:34px 38px; border:1.5px solid var(--ember); }}
#{p}-brief .h {{ display:flex; align-items:center; gap:12px; font-size:22px; font-weight:600; color: var(--ember-ink); margin-bottom:22px; }}
#{p}-brief .h i {{ width:12px; height:12px; border-radius:3px; background: var(--ember); display:block; }}
#{p}-brief p {{ font-size:30px; line-height:1.55; }}
#{p}-brief .w {{ display:inline-block; }}
#{p}-lock {{ position:absolute; left:120px; top:640px; display:flex; align-items:center; gap:18px; }}
#{p}-lock .btn {{ font-size:22px; font-weight:500; padding:12px 26px; border-radius:10px; background:#EEF0F4; color:#98A2B3; display:flex; gap:10px; align-items:center; }}
#{p}-po {{ position:absolute; left:1010px; top:120px; width:790px; padding:34px 38px; }}
#{p}-po .top {{ display:flex; justify-content:space-between; align-items:baseline; }}
#{p}-po table {{ width:100%; border-collapse:collapse; margin-top:26px; font-size:22px; }}
#{p}-po th {{ text-align:left; font-weight:500; color: var(--ink-2); font-size:18px; padding:10px 0; border-bottom:1px solid var(--line); }}
#{p}-po td {{ padding:16px 0; border-bottom:1px solid var(--line); }}
#{p}-po .r {{ text-align:right; }}
#{p}-scene .pill {{ font-size:18px; font-weight:500; padding:5px 14px; border-radius:999px; background:#EEF0F4; color: var(--ink-2); }}
#{p}-ok {{ position:absolute; left:{BX}px; top:{BY + BH + 26}px; }}
"""
    js = f"""
rise("#{p}-brief", T.brief - 0.3, {{ y: 24 }});
tl.fromTo("#{p}-brief .w", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.15, stagger: 0.07 }}, T.brief + 0.2);
rise("#{p}-po", T.po - 0.2, {{ y: 24 }});
rise(["#{p}-p1", "#{p}-p2", "#{p}-p3", "#{p}-p4"], T.po, {{ y: 12, s: 0.25 }});
tl.fromTo("#{p}-brief .tok", {{ boxShadow: "0 0 0 0px rgba(52,120,246,0)" }}, {{ boxShadow: "0 0 0 3px rgba(52,120,246,.45)", duration: 0.3, stagger: 0.12, yoyo: true, repeat: 1 }}, T.numbers);
rise("#{p}-lock", T.cant - 0.2);
// part B: the human approval in the real app, one fixed framing for every state
gsap.set("#{p}-br-cam", {camv(k, *CAM)});
tl.fromTo("#{p}-b", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5 }}, T.b);
tl.to("#{p}-a", {{ opacity: 0, duration: 0.4 }}, T.b);
click("#{p}-cur", "#{p}-rip", 1250, 860, {ax}, {ay}, T.c1);
tl.fromTo("#{p}-i2", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, T.c1 + 0.15);
tl.to("#{p}-cur", {{ x: {fx}, y: {fy}, duration: 0.7, ease: "power2.inOut" }}, T.c2 - 0.8);
tl.to("#{p}-cur", {{ scale: 0.86, duration: 0.08 }}, T.c2);
tl.to("#{p}-cur", {{ scale: 1, duration: 0.18 }}, T.c2 + 0.08);
tl.fromTo("#{p}-i3", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.2 }}, T.c2 + 0.15);
tl.to("#{p}-cur", {{ opacity: 0, duration: 0.25 }}, T.c2 + 0.3);
rise("#{p}-ok", T.c2 + 0.4);
"""
    T["sfx_tap"] = T["c1"]; T["sfx_success"] = T["c2"] + 0.15  # Approve click; the PO turns Approved (no tap on Confirm: it would stack on the chime)
    return css, body, js, T

# ================================================================================================
ICONS = {
    "doc": '<path d="M18 8h26l12 12v44H18z"/><path d="M44 8v12h12"/><path d="M26 34h22M26 43h22M26 52h14"/>',
    "chart": '<path d="M10 60h52"/><path d="M14 50l12-14 10 8 12-18 12 6"/>',
    "alert": '<path d="M36 10l28 50H8z"/><path d="M36 28v14"/><circle cx="36" cy="50" r="1.5"/>',
    "cart": '<path d="M8 14h9l7 32h30l6-22H20"/><circle cx="28" cy="56" r="4"/><circle cx="50" cy="56" r="4"/>',
    "chat": '<path d="M10 14h52v32H32l-12 10V46H10z"/><path d="M20 26h32M20 34h22"/>',
    "check": '<circle cx="36" cy="36" r="26"/><path d="M24 37l8 8 16-17"/>',
}

def s10(sid, dur, C):
    T = {"head": 0.3, "n0": C.at("supplier documents"), "n1": C.at("forecasts"), "n2": C.at("risk detection"),
         "n3": C.at("replenishment"), "n4": C.at("brings the purchasing"), "built": C.at("It is designed"), "u0": C.at("independent retailers"),
         "u1": C.at("specialty grocers"), "u2": C.at("small wholesalers"), "foot": C.at("working with POS")}
    p = sid
    nodes = [("Intake", "doc", "#E86A4A"), ("Forecast", "chart", "#3478F6"), ("Risk", "alert", "#3478F6"),
             ("Replenish", "cart", "#3478F6"), ("Explain &amp; draft", "chat", "#E86A4A"), ("Approve", "check", "#289879")]
    nx = [120 + i * 286 for i in range(6)]
    nodes_html = "".join(f'<div class="nd" id="{p}-n{i}" style="left:{x}px;--c:{c}"><svg width="72" height="72" viewBox="0 0 72 72" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">{ICONS[ic]}</svg><div class="nl">{n}</div></div>'
                         for i, ((n, ic, c), x) in enumerate(zip(nodes, nx)))
    users = ["Independent retailers &amp; mini-marts", "Specialty grocers", "Small wholesale distributors"]
    body = f"""
<div id="{p}-head" class="headline">One connected workflow.</div>
<div id="{p}-line"></div>
{nodes_html}
<div id="{p}-thread" class="chip">● Cola 330ml</div>
<div id="{p}-users">{''.join(f'<div class="card" id="{p}-u{i}"><div class="title">{u}</div></div>' for i, u in enumerate(users))}</div>
<div id="{p}-foot">100 to 10,000+ SKUs · already on a POS or spreadsheet · no ERP migration</div>
"""
    css = f"""
#{p}-head {{ position:absolute; left:120px; top:96px; }}
#{p}-line {{ position:absolute; left:245px; width:1430px; top:452px; height:3px; background: var(--line-strong); transform-origin:0 50%; }}
#{p}-scene .nd {{ position:absolute; top:206px; width:250px; height:214px; background:#fff; border:2px solid var(--line); border-radius:16px; box-shadow: var(--shadow); display:flex; flex-direction:column; align-items:center; justify-content:center; gap:18px; }}
#{p}-scene .nd .nl {{ font-size:28px; font-weight:600; text-align:center; }}
#{p}-thread {{ position:absolute; left:0; top:432px; color:var(--indigo); border-color:var(--indigo); background:var(--indigo-tint); font-size:20px; padding:6px 16px; white-space:nowrap; }}
#{p}-users {{ position:absolute; left:120px; right:120px; top:540px; display:grid; grid-template-columns: repeat(3, 1fr); gap:32px; }}
#{p}-users .card {{ padding:30px 34px; }}
#{p}-foot {{ position:absolute; left:120px; top:730px; font-size:28px; color: var(--ink-2); }}
"""
    js = f"""
rise("#{p}-head", T.head);
tl.fromTo("#{p}-line", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 1.2, ease: "power2.inOut" }}, 0.5);
const xs = {json.dumps([x + 125 for x in nx])};
const nt = [T.n0, T.n1, T.n2, T.n3, T.n4, T.n4 + 1.2];
const cols = {json.dumps([c for _, _, c in nodes])};
gsap.set("#{p}-thread", {{ xPercent: -50 }});
tl.fromTo("#{p}-thread", {{ opacity: 0, x: xs[0] }}, {{ opacity: 1, duration: 0.3 }}, T.n0 - 0.4);
nt.forEach((t, i) => {{
  rise("#{p}-n" + i, t - 0.25, {{ y: 20 }});
  tl.to("#{p}-n" + i, {{ borderColor: cols[i], duration: 0.3 }}, t + 0.2);
  if (i) tl.to("#{p}-thread", {{ x: xs[i], duration: Math.max(0.4, t - nt[i - 1] - 0.1), ease: "power1.inOut" }}, nt[i - 1] + 0.1);
}});
tl.to("#{p}-thread", {{ opacity: 0, duration: 0.4 }}, T.built);
rise("#{p}-u0", T.u0 - 0.2, {{ y: 24 }});
rise("#{p}-u1", T.u1 - 0.2, {{ y: 24 }});
rise("#{p}-u2", T.u2 - 0.2, {{ y: 24 }});
rise("#{p}-foot", T.foot, {{ y: 12 }});
"""
    return css, body, js, T

# ================================================================================================
def s11(sid, dur, C):
    T = {"head": 0.3, "forecasts": C.at("dependable business logic"), "lm": C.at("Language models"), "read": C.at("interpret documents"),
         "explain": C.at("explain recommendations"), "private": C.at("privacy and access")}
    T["dec"] = T["private"] + 0.9
    T["foot"] = T["private"] + 1.8
    p = sid
    body = f"""
<div id="{p}-head" class="headline">The line is strict.</div>
<div class="eyebrow ch" id="{p}-h1" style="left:120px">Operational data</div>
<div class="eyebrow ch" id="{p}-h2" style="left:640px">Intelligence &amp; optimization</div>
<div class="eyebrow ch" id="{p}-h3" style="left:1420px">Procurement decisions</div>
<svg id="{p}-ar" class="full" viewBox="0 0 1920 1080" width="1920" height="1080" fill="none" stroke-width="3" stroke-linecap="round">
  <defs><marker id="{p}-ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="context-stroke" stroke="none"/></marker></defs>
  <path id="{p}-a1" d="M500,330 L626,340" stroke="#3478F6" marker-end="url(#{p}-ah)"/>
  <path id="{p}-a2" d="M500,630 L626,630" stroke="#E86A4A" marker-end="url(#{p}-ah)"/>
  <path id="{p}-a3" d="M960,540 L960,474" stroke="#E86A4A" marker-end="url(#{p}-ah)"/>
  <path id="{p}-a4" d="M1300,330 L1414,320" stroke="#3478F6" marker-end="url(#{p}-ah)"/>
  <path id="{p}-a5" d="M1300,620 C1360,620 1380,400 1414,370" stroke="#E86A4A" stroke-dasharray="2 9" marker-end="url(#{p}-ah)"/>
  <path id="{p}-a6" d="M1610,386 L1610,466" stroke="#289879" marker-end="url(#{p}-ah)"/>
</svg>
<div class="blk card" id="{p}-pos" style="left:120px;top:262px;width:380px"><div class="bt">POS &amp; inventory</div><div class="bs">sales · stock · suppliers</div></div>
<div class="blk card" id="{p}-docs" style="left:120px;top:560px;width:380px"><div class="bt">Supplier documents</div><div class="bs">PDFs · invoices · emails</div></div>
<div class="blk" id="{p}-det"><div class="k c-blue">Deterministic, auditable code</div>
  <div class="row"><span class="it b" id="{p}-d1">Forecasts</span><span class="it b" id="{p}-d2">Risk rules</span><span class="it b" id="{p}-d3">Order quantities</span></div></div>
<div class="alab c-ember" id="{p}-l3" style="left:976px;top:490px">confirmed fields</div>
<div class="blk" id="{p}-ai"><div class="k c-ember">AI · AMD Developer Cloud</div>
  <div class="row"><span class="it e" id="{p}-e1">Reads documents</span><span class="it e" id="{p}-e2">Explains results</span></div>
  <div class="amd mono">AMD Instinct GPUs · ROCm</div>
  <div class="priv" id="{p}-priv"><svg width="18" height="20" viewBox="0 0 18 20" fill="none" stroke="#202A3B" stroke-width="2"><rect x="2" y="9" width="14" height="10" rx="2"/><path d="M5 9V6a4 4 0 0 1 8 0v3"/></svg>Pricing and margin data stay private</div></div>
<div class="blk card" id="{p}-po" style="left:1420px;top:262px;width:380px"><div class="bt">Purchase order draft</div><div class="bs">calculated quantities, explained</div></div>
<div class="blk card" id="{p}-appr" style="left:1420px;top:474px;width:380px;border:2px solid var(--green)"><div class="bt c-green">Human approval</div><div class="bs">a person signs off</div></div>
<div id="{p}-foot">Prototype shown on sample data · AI layer on AMD Developer Cloud rolling out per the implementation plan.</div>
{LEGEND(p)}
"""
    css = f"""
#{p}-scene .full {{ position:absolute; inset:0; }}
#{p}-head {{ position:absolute; left:120px; top:96px; }}
#{p}-scene .ch {{ position:absolute; top:210px; }}
#{p}-scene .blk {{ position:absolute; padding:24px 28px; border-radius:16px; background:#fff; }}
#{p}-scene .bt {{ font-size:30px; font-weight:600; }}
#{p}-scene .bs {{ font-size:22px; color: var(--ink-2); margin-top:6px; }}
#{p}-scene .k {{ font-family: var(--mono); font-size:19px; letter-spacing:.06em; text-transform:uppercase; font-weight:500; }}
#{p}-scene .row {{ display:flex; gap:14px; margin-top:18px; flex-wrap:wrap; }}
#{p}-scene .it {{ font-size:28px; font-weight:600; padding:10px 18px; border-radius:10px; }}
#{p}-scene .it.b {{ background: var(--blue-tint); color: var(--blue-ink); }}
#{p}-scene .it.e {{ background: var(--ember-tint); color: var(--ember-ink); }}
#{p}-det {{ left:640px; top:262px; width:660px; height:212px; border:2.5px solid var(--blue); }}
#{p}-ai {{ left:640px; top:540px; width:660px; height:250px; border:2.5px dashed var(--ember); }}
#{p}-ai .amd {{ position:absolute; left:28px; bottom:26px; font-size:17px; color: var(--ink-2); }}
#{p}-ai .priv {{ position:absolute; right:28px; bottom:22px; display:flex; align-items:center; gap:10px; font-size:20px; font-weight:500; }}
#{p}-scene .alab {{ position:absolute; font-size:20px; font-weight:500; }}
#{p}-foot {{ position:absolute; left:120px; top:830px; font-size:20px; color: var(--ink-2); }}
"""
    js = f"""
rise("#{p}-head", T.head);
fadeIn("#{p}-legend", 0.6);
fadeIn(["#{p}-h1", "#{p}-h2", "#{p}-h3"], 0.7);
rise(["#{p}-pos", "#{p}-docs"], 0.9, {{ s: 0.15 }});
// deterministic layer (blue)
rise("#{p}-det", T.forecasts - 0.3, {{ y: 20 }});
rise(["#{p}-d1", "#{p}-d2", "#{p}-d3"], T.forecasts, {{ s: 0.35, y: 10 }});
draw("#{p}-a1", T.forecasts + 0.6, 0.5);
// AI services (coral) on AMD Developer Cloud
rise("#{p}-ai", T.lm - 0.2, {{ y: 20 }});
rise("#{p}-e1", T.read - 0.1, {{ y: 10 }});
draw("#{p}-a2", T.read, 0.5);
draw("#{p}-a3", T.read + 0.5, 0.4); fadeIn("#{p}-l3", T.read + 0.6);
rise("#{p}-e2", T.explain - 0.1, {{ y: 10 }});
pop("#{p}-priv", T.private);
// decisions: calculated quantities into a draft, a person approves
rise("#{p}-po", T.dec, {{ y: 16 }}); draw("#{p}-a4", T.dec, 0.5); draw("#{p}-a5", T.dec + 0.3, 0.7);
rise("#{p}-appr", T.dec + 0.7, {{ y: 16 }}); draw("#{p}-a6", T.dec + 0.6, 0.4);
fadeIn("#{p}-foot", T.foot);
"""
    return css, body, js, T

# ================================================================================================
def s12(sid, dur, C):
    T = {"fewer": C.at("Fewer empty shelves"), "less": C.at("Less cash"), "dec": C.at("decisions retailers"), "logo": C.at("StockPulse", -0.4)}
    T["tag"] = T["logo"] + 1.2
    p = sid
    body = f"""<div id="{p}-world">{world(p, end=True)}</div>
<img id="{p}-logo" src="{BRAND}logo.png" alt="StockPulse">
<div id="{p}-tagl" class="title">Purchasing decisions you can explain.</div>
<div id="{p}-sub">Inventory intelligence &amp; procurement · on AMD Developer Cloud</div>
"""
    css = WORLD_CSS(p) + f"""
#{p}-world {{ position:absolute; inset:0; }}
#{p}-logo {{ position:absolute; left:640px; top:330px; width:640px; }}
#{p}-tagl {{ position:absolute; left:0; right:0; top:560px; text-align:center; }}
#{p}-sub {{ position:absolute; left:0; right:0; top:650px; text-align:center; font-family: var(--mono); font-size:22px; color: var(--ink-2); }}
"""
    gone = [f"#{p}-c{r}{c}" for r, c in DROP[2:]]  # the stockroom keeps two rows' worth
    js = f"""
gsap.set(["#{p}-cl", "#{p}-cr", "#{p}-tag"], {{ opacity: 0 }});
gsap.set("#{p}-knob", {{ x: 118 }});
// fewer empty shelves: the gaps fill
{json.dumps(SOLD)}.forEach((i, j) => {{
  const t = T.fewer + 0.1 + j * 0.05;
  tl.to("#{p}-g" + i, {{ opacity: 0, duration: 0.2 }}, t);
  tl.fromTo("#{p}-p" + i, {{ opacity: 0, y: -12 }}, {{ opacity: 1, y: 0, duration: 0.28, ease: "power2.out" }}, t);
}});
// less cash stuck on the floor: the excess cartons leave
tl.to({json.dumps(gone[::-1])}, {{ y: -60, opacity: 0, duration: 0.35, stagger: 0.05, ease: "power2.in" }}, T.less);
tl.to("#{p}-cash", {{ opacity: 0, duration: 0.3 }}, T.less);
// decisions you can explain: the order settles in the middle
tl.to("#{p}-knob", {{ x: 0, duration: 0.7, ease: "power2.inOut" }}, T.dec);
tl.to(["#{p}-less", "#{p}-more"], {{ color: "#667085", duration: 0.4 }}, T.dec);
tl.to("#{p}-world", {{ opacity: 0, scale: 0.97, duration: 0.6, ease: "power2.in" }}, T.logo - 0.6);
tl.fromTo("#{p}-logo", {{ opacity: 0, scale: 0.96, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 1.2, ease: "power2.out" }}, T.logo);
rise("#{p}-tagl", T.tag);
fadeIn("#{p}-sub", T.tag + 0.8);
"""
    return css, body, js, T

BUILDERS = [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12]
# matched-frame seams in the opening: S01→S02→S03→S04 cut on identical frames, so no fade there
FADES = {"s01-hook": (True, False), "s02-problem": (False, False), "s03-stakes": (False, False), "s04-intro": (False, True)}

if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    cues = {}
    for (sid, start, dur, vo, text), fn in zip(SCENES, BUILDERS):
        C = Cues(sid, vo, text)
        assert C.end < dur - 0.4, f"{sid}: narration ends at {C.end:.1f}s, past its {dur}s window"
        css, body, js, T = fn(sid, dur, C)
        open(os.path.join(OUT, sid + ".html"), "w").write(page(sid, dur, css, body, js, T, FADES.get(sid, (True, True))))
        cues[sid] = {"start": start, "duration": dur, "vo": vo, "vo_end": C.end,
                     "sfx": [[k[4:].rstrip("0123456789"), round(start + v, 3)] for k, v in T.items() if k.startswith("sfx_")],
                     "words": [[w, round(start + t, 3)] for w, t in zip(C.words, C.times)]}
    json.dump(cues, open(os.path.join(ROOT, "build", "cues.json"), "w"), indent=1)
    print("wrote", len(cues), "scenes;", "real VO timing" if _real else "estimated VO timing", f"; {TOTAL}s")
