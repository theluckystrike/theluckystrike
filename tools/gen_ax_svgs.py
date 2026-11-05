"""Axdale-style SVGs for the theluckystrike profile README.
Writes light and dark versions of every figure into <repo>/assets/ax/.
Fonts: Newsreader (two optical-size instances) and Geist Mono, subset per file and embedded as base64 woff2.
Usage: python3 gen.py <repo_dir>"""
import base64
import io
import math
import os
import random
import sys
from xml.sax.saxutils import escape

from fontTools.ttLib import TTFont
from fontTools import subset as ftsubset

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(sys.argv[1] if len(sys.argv) > 1 else ".", "assets", "ax")
os.makedirs(OUT, exist_ok=True)

FONTS = {
    "D": ("AxSerifD", os.path.join(HERE, "fonts/serif-d.ttf"), "Georgia, 'Times New Roman', serif"),
    "S": ("AxSerif", os.path.join(HERE, "fonts/serif-t.ttf"), "Georgia, 'Times New Roman', serif"),
    "M": ("AxMono", os.path.join(HERE, "fonts/mono.ttf"), "ui-monospace, SFMono-Regular, Menlo, monospace"),
}
_tt = {k: TTFont(v[1]) for k, v in FONTS.items()}
_cmap = {k: t.getBestCmap() for k, t in _tt.items()}
_hmtx = {k: t["hmtx"] for k, t in _tt.items()}
_upm = {k: t["head"].unitsPerEm for k, t in _tt.items()}

PAL = {
    "light": dict(paper="#ffffff", sunk="#f6f6f6", ink="#111111", ink2="#333333", muted="#666666", faint="#999999",
                  rule="#eeeeee", rules="#dddddd", acc="#ff5b1f", acct="#b33a0e", btnfg="#ffffff"),
    "dark": dict(paper="#0f0f0e", sunk="#171716", ink="#ecebe6", ink2="#c9c8c2", muted="#9a9a94", faint="#8a8a83",
                 rule="#262624", rules="#3a3a37", acc="#ff7a45", acct="#ff8a5c", btnfg="#0f0f0e"),
}
# tracking per font, in em
TRACK = {"D": -0.022, "S": -0.005, "M": 0.02}


def width(s, f, size, track=None):
    tr = TRACK[f] if track is None else track
    cm, hm, upm = _cmap[f], _hmtx[f], _upm[f]
    w = 0
    for ch in s:
        g = cm.get(ord(ch))
        w += (hm[g][0] if g else upm * 0.55) / upm * size
    return w + tr * size * len(s)


def wrap(s, f, size, maxw):
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if width(t, f, size) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(s, f, size, maxw, minsize=8):
    while size > minsize and width(s, f, size) > maxw:
        size -= 0.5
    return size


class Fig:
    def __init__(self, name, W, H, title, desc):
        self.name, self.W, self.H, self.title, self.desc = name, W, H, title, desc
        self.parts = []
        self.chars = {"D": set(), "S": set(), "M": set()}
        self.css = ""

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, f="M", size=13, c="ink2", anchor="start", track=None, extra=""):
        self.chars[f].update(s)
        tr = TRACK[f] if track is None else track
        self.add('<text x="%s" y="%s" class="f%s c-%s" font-size="%s" letter-spacing="%s" text-anchor="%s" xml:space="preserve"%s>%s</text>' % (
            r(x), r(y), f, c, r(size), r(tr * size, 2), anchor, extra, escape(s)))
        return width(s, f, size, track)

    def spans(self, x, y, items, f="M", size=13, extra="", cls=""):
        """items = [(text, colour)] laid out on one line."""
        out = []
        for s, c in items:
            self.chars[f].update(s)
            out.append('<tspan class="c-%s">%s</tspan>' % (c, escape(s)))
        self.add('<text x="%s" y="%s" class="f%s%s" font-size="%s" letter-spacing="%s" xml:space="preserve"%s>%s</text>' % (
            r(x), r(y), f, (" " + cls) if cls else "", r(size), r(TRACK[f] * size, 2), extra, "".join(out)))
        return width("".join(s for s, _ in items), f, size)

    def line(self, x1, y1, x2, y2, c="rules", w=1, extra=""):
        self.add('<path d="M%s %sL%s %s" class="s-%s" stroke-width="%s" fill="none"%s/>' % (r(x1), r(y1), r(x2), r(y2), c, w, extra))

    def path(self, d, c="ink", w=1, fill="none", extra=""):
        fc = ' class="s-%s"' % c if fill == "none" else ' class="s-%s k-%s"' % (c, fill)
        self.add('<path d="%s"%s stroke-width="%s"%s%s/>' % (d, fc, w, ' fill="none"' if fill == "none" else "", extra))

    def rect(self, x, y, w, h, stroke="rules", fill="paper", sw=1, rx=0, extra="", cls=""):
        st = ' class="k-%s%s%s"' % (fill, (" s-" + stroke) if stroke else "", (" " + cls) if cls else "")
        self.add('<rect x="%s" y="%s" width="%s" height="%s" rx="%s"%s stroke-width="%s"%s/>' % (r(x), r(y), r(w), r(h), rx, st, sw, extra))

    def circle(self, cx, cy, rad, stroke=None, fill="paper", sw=1, extra=""):
        cls = "k-%s" % fill + ((" s-" + stroke) if stroke else "")
        self.add('<circle cx="%s" cy="%s" r="%s" class="%s" stroke-width="%s"%s/>' % (r(cx), r(cy), r(rad), cls, sw, extra))

    def arrow(self, x, y, size, kind="ne", c="acct", w=1.3):
        """Vector arrow. (x, y) is the left of the glyph box on the baseline."""
        s = size
        if kind == "ne":
            a, b = x + s * 0.12, y - s * 0.08
            e, f = x + s * 0.62, y - s * 0.58
            self.path("M%s %sL%s %sM%s %sH%sV%s" % (r(a), r(b), r(e), r(f), r(e - s * 0.36), r(f), r(e), r(f + s * 0.36)), c, w,
                      extra=' stroke-linecap="square"')
            return s * 0.72
        else:  # right
            yy = y - s * 0.32
            self.path("M%s %sH%sM%s %sL%s %sL%s %s" % (r(x + s * 0.05), r(yy), r(x + s * 0.8), r(x + s * 0.55), r(yy - s * 0.25),
                                                    r(x + s * 0.8), r(yy), r(x + s * 0.55), r(yy + s * 0.25)), c, w,
                      extra=' stroke-linecap="square" stroke-linejoin="miter"')
            return s * 0.9

    def star(self, cx, cy, rad, c="ink"):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = rad if i % 2 == 0 else rad * 0.42
            pts.append("%s %s" % (r(cx + rr * math.cos(a)), r(cy + rr * math.sin(a))))
        self.add('<path d="M%sZ" class="k-%s"/>' % ("L".join(pts), c))

    def frame(self, fill="paper"):
        self.parts.insert(0, '<rect x=".5" y=".5" width="%s" height="%s" class="k-%s s-rules" stroke-width="1"/>' % (self.W - 1, self.H - 1, fill))

    def fontface(self):
        out = []
        for k, chars in self.chars.items():
            if not chars:
                continue
            fam, path, _ = FONTS[k]
            opts = ftsubset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["kern", "liga", "lnum", "tnum"]
            opts.name_IDs = []
            opts.notdef_outline = True
            opts.hinting = False
            f = TTFont(path)
            sub = ftsubset.Subsetter(opts)
            sub.populate(text="".join(chars) + " ")
            sub.subset(f)
            buf = io.BytesIO()
            f.flavor = "woff2"
            f.save(buf)
            out.append("@font-face{font-family:%s;src:url(data:font/woff2;base64,%s) format('woff2');font-weight:400;font-style:normal}" % (
                fam, base64.b64encode(buf.getvalue()).decode()))
        return "".join(out)

    def render(self, mode):
        p = PAL[mode]
        css = [self.fontface()]
        for k, (fam, _, fb) in FONTS.items():
            css.append(".f%s{font-family:%s,%s;font-weight:400}" % (k, fam, fb))
        for n, v in p.items():
            css.append(".c-%s{fill:%s}.s-%s{stroke:%s}.k-%s{fill:%s}" % (n, v, n, v, n, v))
        css.append(".k-none{fill:none}text{font-kerning:normal;font-variant-numeric:lining-nums}")
        css.append(self.css)
        svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-labelledby="t d">' % (
            self.W, self.H, self.W, self.H),
            "<title id=\"t\">%s</title><desc id=\"d\">%s</desc>" % (escape(self.title), escape(self.desc)),
            "<style>%s</style>" % "".join(css),
            '<rect width="%d" height="%d" class="k-paper"/>' % (self.W, self.H)]
        svg += self.parts
        svg.append("</svg>")
        s = "\n".join(svg)
        fn = os.path.join(OUT, "%s-%s.svg" % (self.name, mode))
        open(fn, "w").write(s)
        return fn, len(s)


def r(v, n=1):
    v = round(v, n)
    return int(v) if v == int(v) else v


def both(fig):
    res = [fig.render("light"), fig.render("dark")]
    for fn, n in res:
        print("%-40s %6.1f KB" % (os.path.basename(fn), n / 1024))


def status(fig, x, y, s, size=14):
    fig.circle(x + 4, y - size * 0.34, 4, fill="acc")
    return fig.text(x + 16, y, s, "M", size, "muted")


def lanes(fig, x0, y0, x1, y1, n, spread, seed=7, cls_ops=(0.34, 0.22, 0.14)):
    rnd = random.Random(seed)
    for i in range(n):
        ty = y0 - spread / 2 + i * spread / (n - 1)
        mx = x0 + (x1 - x0) * (0.3 + rnd.random() * 0.4)
        op = cls_ops[i % 3]
        fig.path("M%s %sC%s %s %s %s %s %sC%s %s %s %s %s %s" % (
            r(x0), r(y0), r(x0 + (x1 - x0) * 0.18), r(y0), r(mx - (x1 - x0) * 0.25), r(ty), r(mx), r(ty),
            r(mx + (x1 - x0) * 0.25), r(ty), r(x1 - (x1 - x0) * 0.18), r(y1), r(x1), r(y1)), "ink", 1,
            extra=' stroke-opacity="%s"' % op)


def review_node(fig, x, y, scale=1.0):
    fig.circle(x, y, 22 * scale, stroke="acc", fill="paper", sw=2)
    fig.circle(x, y, 13 * scale, stroke="ink2", fill="paper", sw=1)
    fig.circle(x, y, 4.5 * scale, fill="ink")


# ---------------------------------------------------------------- hero
def hero():
    W, H = 840, 404
    f = Fig("hero", W, H, "Michael Lip, full-stack engineer, fully agentic, whole projects",
            "9,000+ users in production, Chrome ext portfolio, 308 PRs in 102 orgs, 55+ vuln reports, #1 obsidian author, "
            "weekly written reports. Taking new briefs at axdale.com.")
    f.frame()
    P = 32
    status(f, P, 44, "taking new briefs", 14)
    w = f.text(W - P, 44, "axdale.com", "M", 14, "ink", "end")
    f.arrow(W - P + 4, 44, 14, "ne", "ink", 1.2)
    f.line(P, 64, W - P, 64, "rules")
    f.text(P - 3, 150, "Michael Lip", "D", 76, "ink")
    f.text(P, 192, "Full-stack engineer,", "S", 25, "ink2")
    f.text(P, 222, "fully agentic, whole projects.", "S", 25, "ink2")
    # the whole-project figure, small: brief, agent lanes, one review, shipped
    bx, by = 452, 150
    f.rect(bx, by - 46, 50, 86, "ink", "paper")
    f.path("M%s %sl10 0 0 10" % (bx + 40, by - 46), "rules")
    for i in range(5):
        f.line(bx + 9, by - 26 + i * 12, bx + 41 - (12 if i % 3 == 2 else 0), by - 26 + i * 12, "rules")
    f.line(bx + 50, by, bx + 70, by, "ink")
    nx = 700
    lanes(f, bx + 70, by, nx - 22, by, 15, 128, seed=1105)
    review_node(f, nx, by)
    f.line(nx + 22, by, W - P, by, "ink")
    for i, mx in enumerate([738, 762, 786]):
        f.circle(mx, by, 4.5, fill="acc")
    f.text(W - P, by - 14, "main", "M", 12, "muted", "end")
    # stats table
    top = 258
    f.line(P, top, W - P, top, "ink")
    cells = [("9,000+", "users in production"), ("308", "PRs in 102 orgs"), ("55+", "vuln reports"), ("#1", "obsidian author")]
    cw = (W - 2 * P) / 4
    for i, (n, lab) in enumerate(cells):
        x = P + i * cw + (0 if i == 0 else 18)
        if i:
            f.line(P + i * cw, top + 14, P + i * cw, top + 84, "rules")
        f.text(x, top + 48, n, "D", 40, "ink")
        f.text(x, top + 74, lab, "M", 13.5, "muted")
    f.line(P, top + 100, W - P, top + 100, "rules")
    f.text(P, H - 18, "Chrome ext portfolio  /  weekly written reports", "M", 13.5, "ink2")
    both(f)


# ---------------------------------------------------------------- cta
def cta():
    W, H = 840, 318
    f = Fig("cta", W, H, "Axdale. Send me your project. I take it from brief to shipped.",
            "Hire Michael Lip at axdale.com. Send a written brief. Free written plan in one working day, then USD 65 an hour.")
    f.frame()
    P = 32
    status(f, P, 44, "Taking new projects  /  Full-stack, fully agentic", 14)
    f.text(W - P - 14, 44, "axdale.com", "M", 14, "ink", "end")
    f.arrow(W - P - 10, 44, 14, "ne", "ink", 1.2)
    f.line(P, 64, W - P, 64, "rules")
    f.text(P - 2, 132, "Send me your project.", "D", 54, "ink")
    f.text(P - 2, 190, "I take it from brief to shipped.", "D", 54, "ink")
    # button
    by = 228
    f.rect(P, by, 252, 52, None, "ink", rx=26)
    tw = width("Send your project", "M", 15)
    tx = P + (252 - tw - 16) / 2
    f.text(tx, by + 31, "Send your project", "M", 15, "btnfg")
    f.arrow(tx + tw + 6, by + 31, 15, "ne", "btnfg", 1.3)
    f.text(P + 280, by + 22, "Free written plan in one working day, then USD 65 an hour.", "S", 18.5, "muted")
    f.text(P + 280, by + 46, "50+ client projects delivered. Async, from Warsaw.", "S", 18.5, "muted")
    both(f)


# ---------------------------------------------------------------- code
def code():
    W = 840
    L = [
        [("// what a 14-day cycle ships", "cm")],
        [("const", "kw"), (" cycle ", "id"), ("=", "p"), (" ", "id"), ("await", "kw"), (" ", "id"), ("pipeline", "fn"), ("({", "p")],
        [("  spec", "id"), (":", "p"), ("    ", "id"), ("writeSpec", "fn"), ("(", "p"), ("client", "id"), (".", "p"), ("brief", "id"), ("),", "p")],
        [("  tests", "id"), (":", "p"), ("   ", "id"), ("generateEvals", "fn"), ("(", "p"), ("spec", "id"), (", { ", "p"), ("framework", "id"), (":", "p"), (" ", "id"), ("'vitest'", "st"), (" }),", "p")],
        [("  agent", "id"), (":", "p"), ("   ", "id"), ("deployAgent", "fn"), ("(", "p"), ("spec", "id"), (", { ", "p"), ("model", "id"), (":", "p"), (" ", "id"), ("'claude'", "st"), (", ", "p"), ("mcp", "id"), (":", "p"), (" ", "id"), ("true", "kw"), (" }),", "p")],
        [("  review", "id"), (":", "p"), ("  ", "id"), ("writtenReview", "fn"), ("(", "p"), ("client", "id"), (".", "p"), ("engineer", "id"), ("),", "p")],
        [("  ship", "id"), (":", "p"), ("    ", "id"), ("deploy", "fn"), ("({ ", "p"), ("target", "id"), (":", "p"), (" ", "id"), ("'cloudflare'", "st"), (", ", "p"), ("rollback", "id"), (":", "p"), (" ", "id"), ("'<60s'", "st"), (" }),", "p")],
        [("});", "p")],
        [],
        [("assert", "fn"), ("(", "p"), ("cycle", "id"), (".", "p"), ("evals", "id"), (".", "p"), ("pass", "id"), (");", "p")],
        [("assert", "fn"), ("(", "p"), ("cycle", "id"), (".", "p"), ("uptime", "id"), (" >= ", "p"), ("0.999", "nu"), (");", "p")],
        [("// handoff.md written. your team maintains.", "cm")],
    ]
    col = {"cm": "muted", "kw": "acct", "id": "ink2", "p": "muted", "fn": "ink", "st": "ink", "nu": "ink"}
    lh, top, size = 25, 96, 15.5
    H = top + lh * (len(L) - 1) + 36
    f = Fig("code", W, H, "ship.ts, the pitch as TypeScript",
            "const cycle = await pipeline({ spec, tests, agent, review, ship }). assert evals pass, assert uptime >= 0.999. "
            "handoff.md written, your team maintains.")
    f.frame("sunk")
    P = 32
    f.rect(.5, .5, W - 1, 52, None, "paper")
    f.line(0, 52.5, W, 52.5, "rules")
    f.text(P, 33, "ship.ts", "M", 14, "ink")
    f.text(P + width("ship.ts", "M", 14) + 14, 33, "TypeScript", "M", 12.5, "muted")
    f.circle(W - P - width("live", "M", 13) - 14, 28.5, 4, fill="acc")
    f.text(W - P, 33, "live", "M", 13, "muted", "end")
    css = ["@keyframes ln{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:none}}",
           ".ln{animation:ln .45s cubic-bezier(.22,1,.36,1) backwards}",
           "@keyframes bl{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:bl 1.05s step-end infinite 4.6s}",
           "@media (prefers-reduced-motion:reduce){.ln,.cur{animation:none}}"]
    for i, toks in enumerate(L):
        y = top + i * lh
        f.text(P, y, "%2d" % (i + 1), "M", 12.5, "faint", "start")
        if not toks:
            continue
        d = 0.25 + i * 0.33
        x = P + 44
        spans = [(s, col[k]) for s, k in toks]
        f.spans(x, y, spans, "M", size, cls="ln", extra=' style="animation-delay:%.2fs"' % d)
        if i == len(L) - 1:
            cw = width(toks[0][0], "M", size)
            f.rect(x + cw + 6, y - 14, 9, 18, None, "acc", cls="cur")
    f.line(P + 32, 66, P + 32, H - 18, "rules")
    f.css = "".join(css)
    both(f)


# ---------------------------------------------------------------- support
def support():
    W, H = 840, 330
    f = Fig("support", W, H, "Support the work. Open source must win. $4.99 per month at zovo.one.",
            "One subscription funds full-time open-source work. Real fixes, translations, verified docs, shipped, not promised. "
            "If my contributions helped you, the best thank-you is keeping it going.")
    f.frame()
    P = 32
    f.text(P, 44, "[00]  support the work", "M", 14, "muted")
    f.text(W - P - 14, 44, "axdale.com", "M", 14, "ink", "end")
    f.arrow(W - P - 10, 44, 14, "ne", "ink", 1.2)
    f.line(P, 64, W - P, 64, "rules")
    f.text(P - 2, 132, "Open source must win.", "D", 50, "ink")
    for i, ln in enumerate(wrap("zovo.one · one subscription funds full-time open-source work", "S", 20, 440)):
        f.text(P, 172 + i * 27, ln, "S", 20, "ink2")
    # price column
    cx = 560
    f.line(cx, 84, cx, 210, "rules")
    f.text(cx + 30, 106, "per month", "M", 13, "muted")
    f.text(cx + 26, 172, "$4.99", "D", 76, "ink")
    f.rect(cx + 30, 190, 36, 3, None, "acc")
    # deliverables row
    top = 230
    f.line(P, top, W - P, top, "ink")
    items = ["real fixes", "translations", "verified docs", "shipped, not promised"]
    ws = [34 + width(it, "S", 18) for it in items]
    gap = (W - 2 * P - sum(ws)) / 3
    x = P
    for i, it in enumerate(items):
        if i:
            f.line(x - gap / 2, top + 12, x - gap / 2, top + 44, "rules")
        f.text(x, top + 32, "[%d]" % (i + 1), "M", 12.5, "muted")
        f.text(x + 34, top + 33, it, "S", 18, "ink")
        x += ws[i] + gap
    f.line(P, top + 56, W - P, top + 56, "rules")
    f.text(P, H - 20, "If my contributions helped you, the best thank-you is keeping it going.", "S", 18, "muted")
    both(f)


# ---------------------------------------------------------------- 2x2 panels
def panel_grid(name, title, desc, cards, cell_h=None, kcol=118, vfont="S", vsize=17):
    W = 840
    P = 28
    cwid = W / 2 - 2 * P

    def need(c):
        n = len(wrap(c["desc"], "S", 17, cwid)[:2])
        return 108 + n * 23 + 6 + len(c["rows"]) * 32 + (62 if c.get("links") else 30)
    rows_h = [max(need(cards[0]), need(cards[1])), max(need(cards[2]), need(cards[3]))]
    H = sum(rows_h)
    f = Fig(name, W, H, title, desc)
    f.frame()
    f.line(W / 2, 0, W / 2, H, "rules")
    f.line(0, rows_h[0], W, rows_h[0], "rules")
    for idx, c in enumerate(cards):
        cx = (idx % 2) * W / 2
        cy = 0 if idx < 2 else rows_h[0]
        cell_h = rows_h[idx // 2]
        x0, x1 = cx + P, cx + W / 2 - P
        f.text(x0, cy + 38, "[%d]" % (idx + 1), "M", 13, "muted")
        if c.get("badge"):
            bw = width(c["badge"], "M", 12.5)
            f.circle(x1 - bw - 12, cy + 33.5, 4, fill="acc")
            f.text(x1, cy + 38, c["badge"], "M", 12.5, "acct", "end")
        ts = fit(c["title"], "D", 28, x1 - x0)
        f.text(x0 - 1, cy + 78, c["title"], "D", ts, "ink")
        y = cy + 108
        for ln in wrap(c["desc"], "S", 17, x1 - x0)[:2]:
            f.text(x0, y, ln, "S", 17, "ink2")
            y += 23
        y += 6
        for k, v in c["rows"]:
            f.line(x0, y, x1, y, "rule")
            vs = fit(v, vfont, vsize, x1 - x0 - kcol)
            f.text(x0, y + 22, k, "M", 12.5, "muted")
            f.text(x1, y + 22.5, v, vfont, vs, "ink", "end")
            y += 32
        f.line(x0, y, x1, y, "rule")
        if c.get("links"):
            lx = x0
            ly = y + 36
            for i, l in enumerate(c["links"]):
                if i:
                    lx += f.text(lx, ly, "  ·  ", "M", 13, "faint")
                lx += f.text(lx, ly, l, "M", 13, "acct")
            f.arrow(lx + 5, ly, 13, "ne", "acct", 1.2)
    both(f)


def proof():
    cards = [
        dict(title="tab-suspender-pro", desc="The great suspender replacement. 2M stranded, live in 14 days.",
             rows=[("cws.users", "1,100+"), ("rating", "4.6 / 5"), ("data.sent", "0 bytes"), ("license", "bsl-1.1")],
             links=["axdale.com"]),
        dict(title="belikenative · mcp grammar server", desc="70 rules · 18 L1-aware. Claude Desktop & Cursor.",
             rows=[("rules", "70 · 18 l1-aware"), ("ext.users", "9,000+"), ("rating", "4.6 / 5"), ("license", "mit")],
             links=["axdale.com"]),
        dict(title="chrome-extension-toolkit", desc="TS-first MV3 scaffolding. The starter for every client build.",
             rows=[("language", "typescript"), ("manifest", "v3"), ("used.in", "12+ extensions")], links=["axdale.com"]),
        dict(title="content engine · the funnel", desc="chrome-tips · claude-skills-guide · ai-tools-compared.",
             rows=[("articles", "4,200+"), ("cadence", "daily"), ("views", "1,700+ / mo")], links=["axdale.com"]),
    ]
    panel_grid("proof", "Proof of work",
               "tab-suspender-pro 1,100+ users, 4.6 rating, BSL-1.1. belikenative mcp grammar server, 70 rules, 9,000+ users, 4.6 rating, MIT. "
               "chrome-extension-toolkit, TypeScript-first MV3 scaffolding. Content engine, 4,200+ articles, daily cadence.",
               cards, 352)


def security():
    cards = [
        dict(title="vulnerability research", badge="active",
             desc="55+ reports filed via GitHub Private Vulnerability Reporting",
             rows=[("scope", "mlflow · keras · sglang"), ("", "nltk · gradio · feast"), ("focus", "pickle deserialization · sql injection"),
                   ("method", "static analysis · source code review")]),
        dict(title="research areas", desc="AI/ML infrastructure security",
             rows=[("sglang", "36 pickle.loads instances audited"), ("feast", "f-string sqli across 12 backends"),
                   ("mlflow", "model deserialization vectors"), ("keras", "model loading attack surface")]),
        dict(title="methodology", desc="Source-level review across web and blockchain",
             rows=[("application", "static analysis · code review"), ("blockchain", "solidity smart contract auditing"),
                   ("defi", "protocol analysis · pipeline scan")]),
        dict(title="platforms", desc="Active vulnerability disclosure programs",
             rows=[("web/ml", "github pvr · huntr"), ("blockchain", "immunefi · sherlock · cantina"), ("status", "active researcher")]),
    ]
    panel_grid("security", "Security research",
               "55+ vulnerability reports filed via GitHub PVR across mlflow, keras, sglang, nltk, gradio, feast. Focus pickle deserialization, "
               "sql injection, model loading. Methodology static analysis, source code review, solidity smart contract auditing, defi protocol "
               "analysis. Platforms github pvr, huntr, immunefi, sherlock, cantina.",
               cards, 300, kcol=96, vfont="S", vsize=16.5)


# ---------------------------------------------------------------- ml0x
def ml0x():
    W, H = 840, 330
    f = Fig("ml0x", W, H, "ml0x, the engine behind every square below",
            "My open-source agentic engineering pipeline. One developer, the output of a 100-person team. Analyze, implement, test, review, ship. "
            "85% cheaper model routing, 90% cache savings, production-grade quality gates, full pipeline shared with zovo lifetime members.")
    f.frame()
    P = 32
    f.text(P, 44, "ml0x.com  ·  the engine behind every square below", "M", 14, "muted")
    f.text(W - P - 14, 44, "axdale.com", "M", 14, "acct", "end")
    f.arrow(W - P - 10, 44, 14, "ne", "acct", 1.2)
    f.line(P, 64, W - P, 64, "rules")
    f.text(P - 3, 128, "ml0x", "D", 64, "ink")
    tx = 210
    for i, ln in enumerate(wrap("my open-source agentic engineering pipeline. one developer, the output of a 100-person team.", "S", 21, W - P - tx)):
        f.text(tx, 102 + i * 28, ln, "S", 21, "ink2")
    # pipeline figure
    y = 186
    stages = ["analyze", "implement", "test", "review", "ship"]
    xs = [P + 30, 230, 430, 600, W - P - 40]
    f.line(xs[0], y, xs[1] - 10, y, "ink")
    lanes(f, xs[1] + 10, y, xs[2] - 10, y, 9, 46, seed=3)
    f.line(xs[2] + 10, y, xs[3] - 22, y, "ink")
    f.line(xs[3] + 22, y, xs[4], y, "ink")
    for i, (x, s) in enumerate(zip(xs, stages)):
        if s == "review":
            review_node(f, x, y, 0.85)
        elif s == "ship":
            for k in range(3):
                f.circle(x - 24 + k * 16, y, 4.5, fill="acc")
        else:
            f.circle(x, y, 7, stroke="ink", fill="paper")
        lab = "[%d] %s" % (i + 1, s)
        anchor = "end" if s == "ship" else ("start" if i == 0 else "middle")
        ax = x + 8 if s == "ship" else (x - 7 if i == 0 else x)
        f.text(ax, y + 42, lab, "M", 13, "ink2", anchor)
    # stats
    top = 246
    f.line(P, top, W - P, top, "ink")
    cells = [("85%", "cheaper model routing"), ("90%", "cache savings")]
    f.text(P, top + 48, "85%", "D", 36, "ink")
    f.text(P + 86, top + 30, "cheaper model", "M", 12.5, "muted")
    f.text(P + 86, top + 47, "routing", "M", 12.5, "muted")
    f.line(240, top + 14, 240, top + 64, "rules")
    f.text(258, top + 48, "90%", "D", 36, "ink")
    f.text(258 + 86, top + 30, "cache", "M", 12.5, "muted")
    f.text(258 + 86, top + 47, "savings", "M", 12.5, "muted")
    f.line(450, top + 14, 450, top + 64, "rules")
    f.text(468, top + 30, "production-grade quality gates", "M", 12.5, "ink2")
    f.text(468, top + 47, "full pipeline shared with", "M", 12.5, "ink2")
    f.text(468, top + 64, "zovo lifetime members", "M", 12.5, "ink2")
    both(f)


# ---------------------------------------------------------------- squares
SQ = [
    ("belikenative", "belikenative", "belikenative.com", "ai writing assistant for non-native speakers. fix, rewrite & translate in one shortcut.", "26,000+ users · 4.66", True),
    ("claudecodeguides", "claude code guides", "claudecodeguides.com", "the reference devs reach for when claude code breaks. configs, tools, mcp servers.", "3,021+ guides · daily", False),
    ("heytensor", "heytensor", "heytensor.com", "pytorch / tensorflow tensor-shape calculator. chain mode + instant error fixes.", "14 layer types · free", False),
    ("zovo", "zovo", "zovo.one", "privacy + security x-ray for the chrome web store. scan & compare any extension.", "244,000+ analyzed", False),
    ("scanthechain", "scan the chain", "scanthechain.com", "automated defi smart-contract audits. the honest ledger of white-hat economics.", "58 campaigns · $11B TVL", False),
    ("bugbountyreality", "bug bounty reality", "bugbountyreality.com", "the security-research ops database nobody else publishes. $2k spent, $0 collected.", "600+ vulns · 55 advisories", False),
    ("earlythunder", "early thunder", "earlythunder.com", "pre-mainstream opportunity intelligence across defi, equities & private markets.", "247 opportunities · daily", False),
    ("deepvalueradar", "deepvalue radar", "deepvalueradar.com", "deep-value equity screener. fair-value models + catalysts, cross-validated.", "18 picks / 451 universe", False),
    ("dscrradar", "dscr radar", "dscrradar.com", "weekly rental-market analysis. ranks us metros by cash-flow strength via the investor yield index.", "18 metros ranked weekly", False),
    ("ingredientcalculator", "ingredient calculator", "ingredientcalculator.com", "fast recipe scaler, unit converter, substitutions + macros. a cup is not a cup.", "free · polished", False),
    ("examscorecalc", "exam score calc", "examscorecalc.com", "free score calculators for ap, sat (400-1600) and act (1-36). enter raw points, get projections.", "ap · sat · act · free", False),
    ("statewage", "statewage", "statewage.com", "free paycheck calculator. estimates take-home pay after federal, fica and state taxes.", "all 50 states · free", False),
    ("lakelevelnow", "lake level now", "lakelevelnow.com", "current level, percent full and 30-day trend for lakes nationwide, from usgs + cdec gages.", "42 lakes tracked", False),
    ("goldgramprice", "gold gram price", "goldgramprice.com", "live gold spot price + jewelry melt value by karat purity and weight. free calculator.", "live spot · by karat", False),
    ("notemods", "notemods", "notemods.com", "open-source obsidian plugins for bases, tables and tasks. free to install, optional pro.", "132 plugins · 13,269 downloads", False),
    ("toolroutine", "toolroutine", "toolroutine.com", "plugins for chatgpt and claude, plus custom builds for business.", "106 plugins · custom from $5k", False),
    ("addthisbot", "addthisbot", "addthisbot.com", "telegram group bots where one admin pays once and every member gets pro.", "35 live bots · 18 for groups", False),
]


def squares():
    W, H = 264, 272
    P = 20
    for i, (slug, t, dom, desc, stat, star) in enumerate(SQ):
        f = Fig("sq-" + slug, W, H, "%s, %s" % (t, dom), "%s %s" % (desc, stat + ("★" if star else "")))
        f.frame()
        f.text(P, 32, "[%02d]" % (i + 1), "M", 12.5, "muted")
        ds = fit(dom, "M", 12.5, W - 2 * P - 44)
        f.text(W - P, 32, dom, "M", ds, "muted", "end")
        f.line(P, 46, W - P, 46, "rules")
        ts = fit(t, "D", 30, W - 2 * P)
        f.text(P - 1, 84, t, "D", ts, "ink")
        size = 16.5
        lines = wrap(desc, "S", size, W - 2 * P)
        while len(lines) > 4:
            size -= 0.5
            lines = wrap(desc, "S", size, W - 2 * P)
        for k, ln in enumerate(lines):
            f.text(P, 112 + k * (size + 4.5), ln, "S", size, "ink2")
        f.line(P, 196, W - P, 196, "ink")
        ss = fit(stat + ("  " if star else ""), "S", 20, W - 2 * P)
        sw = f.text(P, 224, stat, "S", ss, "ink")
        if star:
            f.star(P + sw + 9, 217.5, 6.5, "ink")
        f.text(P, 251, "axdale.com", "M", 12.5, "acct")
        f.arrow(P + width("axdale.com", "M", 12.5) + 4, 251, 12.5, "ne", "acct", 1.2)
        both(f)


# ---------------------------------------------------------------- stack
def stack():
    rows = [("agentic", "claude code · mcp · gemini cli · minimax · langgraph · vercel ai sdk"),
            ("frontend", "typescript · react · next · vite · tailwind · shadcn"),
            ("backend", "node · python · django · supabase · postgres · trpc"),
            ("extensions", "mv3 · service workers · dnr · wxt · plasmo"),
            ("infra", "cloudflare workers · aws · docker · github actions"),
            ("testing", "vitest · playwright · msw · zod · eval harnesses")]
    W = 840
    rh = 52
    H = 24 + rh * len(rows) + 8
    f = Fig("stack", W, H, "Tech stack",
            "; ".join("%s %s" % (a, b.replace(" · ", ", ")) for a, b in rows))
    f.frame()
    P = 32
    for i, (k, v) in enumerate(rows):
        y = 16 + i * rh
        if i:
            f.line(P, y, W - P, y, "rule")
        f.text(P, y + 33, "[%d]" % (i + 1), "M", 12.5, "muted")
        f.text(P + 38, y + 33, k, "M", 13.5, "ink")
        vs = fit(v, "S", 20, W - 2 * P - 170)
        f.text(P + 170, y + 34, v, "S", vs, "ink2")
    both(f)


# ---------------------------------------------------------------- flow
def flow():
    W, H = 840, 520
    f = Fig("flow", W, H, "How a whole project runs",
            "Six stages from left to right. One, your brief with the scope and the files. Two, a written plan, free in one working day. "
            "Three, many thin agent lanes fan out in parallel. Four, every lane meets one review node, every change reviewed. "
            "Five, small pull requests with tests. Six, shipped to main. Below, a week axis with one written report every week, 18:00 CET.")
    f.frame()
    P = 32
    f.text(P - 1, 50, "How a whole project runs", "D", 30, "ink")
    f.text(W - P, 50, "brief to shipped", "M", 13, "muted", "end")
    f.line(P, 70, W - P, 70, "rules")
    step = (W - 2 * P) / 6
    xs = [P + step * (i + 0.5) for i in range(6)]
    heads = [("Brief", ["scope and files"]), ("Written plan", ["free, in one", "working day"]),
             ("Agent lanes", ["many, in parallel"]), ("Review", ["one engineer"]),
             ("Pull requests", ["small, with tests"]), ("Shipped", ["to main"])]
    for i, (x, (h, subs)) in enumerate(zip(xs, heads)):
        f.text(x, 100, "[%d]" % (i + 1), "M", 12.5, "muted", "middle")
        f.text(x, 121, h, "M", 14, "ink", "middle")
        for k, sb in enumerate(subs):
            f.text(x, 140 + k * 16, sb, "M", 12, "muted", "middle")
        f.line(x, 170, x, 372 if i != 3 else 360, "rules", extra=' stroke-dasharray="3 3"')
    yC = 272
    # [1] brief
    bx = xs[0] - 28
    f.rect(bx, yC - 50, 56, 100, "ink", "paper")
    f.path("M%s %sl12 0 0 12" % (r(bx + 44), yC - 50), "rules")
    for i in range(6):
        f.line(bx + 9, yC - 30 + i * 13, bx + 47 - (12 if i % 3 == 2 else 0), yC - 30 + i * 13, "rules")
    # [2] plan
    pw, ph = 112, 138
    px = xs[1] - pw / 2
    f.line(bx + 56, yC, px, yC, "ink")
    f.rect(px, yC - ph / 2, pw, ph, "ink", "paper")
    for i, lab in enumerate(["scope", "milestones", "risks", "estimate", "access"]):
        cy = yC - ph / 2 + 26 + i * 24
        f.rect(px + 11, cy - 9, 10, 10, "ink2", "none")
        f.path("M%s %sl3 3 6 -7" % (r(px + 13), cy - 4), "acc", 1.6)
        f.text(px + 28, cy, lab, "M", 12, "ink2")
    # [3] lanes, [4] node
    nx = xs[3]
    lanes(f, px + pw, yC, nx - 24, yC, 21, 190, seed=1105)
    review_node(f, nx, yC)
    f.line(nx, yC + 24, nx, yC + 98, "ink2", 0.75)
    f.text(nx, yC + 116, "every change reviewed", "M", 12.5, "ink", "middle")
    # [5] pull requests
    cw, ch = 86, 30
    cx = xs[4] - cw / 2
    ys = [yC - 81, yC - 27, yC + 27, yC + 81]
    mx = xs[5] - 52
    for i, cy in enumerate(ys):
        f.path("M%s %sC%s %s %s %s %s %s" % (nx + 24, yC, nx + 64, yC, cx - 40, cy, cx, cy), "ink")
        f.rect(cx, cy - ch / 2, cw, ch, "ink", "paper")
        f.path("M%s %sl4 4 8 -9" % (r(cx + 10), cy + 1), "ink2", 1.3)
        f.line(cx + 30, cy - 4, cx + cw - 10 - (i % 2) * 14, cy - 4, "rules")
        f.line(cx + 30, cy + 5, cx + cw - 22, cy + 5, "rules")
        f.path("M%s %sC%s %s %s %s %s %s" % (cx + cw, cy, cx + cw + 26, cy, mx - 22, yC, mx, yC), "ink")
    # [6] main
    f.line(mx, yC, W - P, yC, "ink")
    for k in range(4):
        f.circle(mx + 14 + k * 22, yC, 4.5, fill="acc")
    f.text(W - P, yC - 14, "main", "M", 12, "muted", "end")
    # week axis, from the plan onwards
    ay = 466
    a0, a1 = xs[1], W - P - 26
    f.text(a0, ay - 34, "one written report every week, 18:00 CET", "M", 12.5, "ink2")
    f.line(a0, ay, a1 + 0, ay, "ink")
    n = 6
    for i in range(n + 1):
        wx = a0 + i * (a1 - a0) / n
        f.line(wx, ay - 5, wx, ay + 5, "ink")
        if i:
            f.rect(wx - 1.5, ay - 20, 3, 15, None, "acc")
            f.text(wx, ay + 24, "week %d" % i, "M", 12, "muted", "middle")
    both(f)


# ---------------------------------------------------------------- record
def record():
    import datetime as dt
    rows = []
    for l in open(os.path.join(HERE, "../data/prs.tsv")):
        u, t, n = l.rstrip("\n").split("\t")
        rows.append((t, u.split("/repos/")[1]))
    assert len(rows) == 308, len(rows)
    rows.sort()
    W, H = 840, 470
    f = Fig("record", W, H, "Merged pull requests in other people's repositories",
            "308 merged pull requests in 102 orgs, one dot per pull request, stacked by week. Labelled, Prefect, Remotion, Scalar and Appium.")
    f.frame()
    P = 32
    f.text(P - 1, 50, "Merged pull requests in other people’s repositories", "D", 26, "ink")
    f.line(P, 70, W - P, 70, "rules")
    f.text(P - 4, 162, "308", "D", 96, "ink")
    nw = width("308", "D", 96)
    f.text(P, 204, "merged pull requests", "M", 13, "muted")
    f.text(P - 1, 262, "102 orgs", "D", 40, "ink")
    f.text(P, 288, "maintainers merged them", "M", 13, "muted")
    # plot
    def monday(d):
        return d - dt.timedelta(days=d.weekday())
    first = dt.date(2026, 3, 2)
    last = dt.date(2026, 10, 19)
    nweeks = (last - first).days // 7 + 1
    x0, x1 = 300, W - P
    base = 392
    old = [r_ for r_ in rows if r_[0] < "2026"]
    colw = (x1 - (x0 + 44)) / nweeks
    pitch = 4.6
    per = 3
    cols = {}
    for t, repo in rows:
        d = dt.date.fromisoformat(t[:10])
        key = -1 if d.year < 2026 else (monday(d) - first).days // 7
        cols.setdefault(key, []).append((t, repo))
    mark = {}
    notable = {"PrefectHQ/prefect", "remotion-dev/remotion", "scalar/scalar", "appium/appium"}
    for key, items in cols.items():
        cx = x0 + 6 if key == -1 else x0 + 44 + key * colw + colw / 2
        items.sort(key=lambda it: (it[1] in notable, it[0]))
        for j, (t, repo) in enumerate(items):
            row, c = divmod(j, per)
            px = cx + (c - 1) * pitch
            py = base - 6 - row * pitch
            if repo == "PrefectHQ/prefect":
                px = cx
            if repo in notable:
                f.circle(px, py, 2.6 if repo == "PrefectHQ/prefect" else 1.9, fill="acc")
                mark[repo] = (px, py)
            else:
                f.circle(px, py, 1.6, fill="ink")
    # axis
    f.line(x0, base, x0 + 14, base, "ink")
    f.path("M%s %sl5 -8M%s %sl5 -8" % (x0 + 17, base + 4, x0 + 23, base + 4), "ink")
    f.line(x0 + 30, base, x1, base, "ink")
    f.text(x0 + 6, base + 22, "2024", "M", 11.5, "muted", "middle")
    months = ["Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]
    for m, name in zip(range(3, 11), months):
        d = dt.date(2026, m, 1)
        k = (d - first).days / 7
        mx_ = x0 + 44 + k * colw
        f.line(mx_, base, mx_, base + 5, "ink")
        f.text(mx_ + 2, base + 22, name, "M", 11.5, "muted")
    f.text(x1, base + 42, "2026, one dot per merged pull request", "M", 11.5, "muted", "end")
    # notable labels
    px, py = mark["PrefectHQ/prefect"]
    f.text(px, 300, "Prefect", "M", 12.5, "ink", "middle")
    f.line(px, 308, px, py - 5, "ink2", 0.75)
    oct_ = [("scalar/scalar", "Scalar"), ("remotion-dev/remotion", "Remotion"), ("appium/appium", "Appium")]
    topy = min(mark[r_][1] for r_, _ in oct_)
    lx = min(mark[r_][0] for r_, _ in oct_) - 30
    # rightmost dot gets the highest label, so no leader crosses another
    for k, (repo, lab) in enumerate(sorted(oct_, key=lambda it: -mark[it[0]][0])):
        px, py = mark[repo]
        ly = topy - 36 + k * 16
        f.text(lx - 6, ly + 4.5, lab, "M", 12.5, "ink", "end")
        f.path("M%s %sH%sV%s" % (r(lx), r(ly), r(px), r(py - 3)), "ink2", 0.75)
    both(f)
    return old


# ---------------------------------------------------------------- advisories
def advisories():
    adv = [("NLTK", "GHSA-p3m8-78j2-g5p3", "CVE-2026-62388", "High", 8.7, "2026-09-02"),
           ("NLTK", "GHSA-3gqm-fcw5-w839", "CVE-2026-63311", "Medium", 6.9, "2026-09-02"),
           ("NLTK", "GHSA-5wp5-5229-5g6q", "CVE-2026-12259", "Medium", None, "2026-09-08"),
           ("Gitea", "GHSA-x77v-q46j-393g", "CVE-2026-23603", "Low", None, "2026-07-21")]
    bands = {"Low": (0.1, 3.9), "Medium": (4.0, 6.9), "High": (7.0, 8.9), "Critical": (9.0, 10.0)}
    W = 840
    rh = 72
    top = 150
    H = top + rh * len(adv) + 64
    f = Fig("advisories", W, H, "4 published advisories credit me as reporter",
            "; ".join("%s %s %s %s%s, published %s" % (a[0], a[2], a[1], a[3], (" %.1f" % a[4]) if a[4] else ", no score", a[5]) for a in adv))
    f.frame()
    P = 32
    f.text(P - 1, 50, "4 published advisories credit me as reporter", "D", 30, "ink")
    f.line(P, 70, W - P, 70, "rules")
    s0, s1 = 420, W - P
    sx = lambda v: s0 + (s1 - s0) * v / 10.0
    f.text(P, 112, "package", "M", 12, "muted")
    f.text(214, 112, "identifiers", "M", 12, "muted")
    for name, (a, b) in bands.items():
        lo = 0 if name == "Low" else a
        if name == "Critical":
            f.text(s1, 112, "critical", "M", 12, "muted", "end")
        elif name == "High":
            f.text(sx(7) + 5, 112, "high", "M", 12, "muted")
        else:
            f.text((sx(lo) + sx(b)) / 2, 112, name.lower(), "M", 12, "muted", "middle")
    for v in [0, 4, 7, 9, 10]:
        f.line(sx(v), 124, sx(v), top + rh * len(adv), "rule")
        f.text(sx(v), 138, "%g" % v, "M", 11, "faint", "middle")
    f.line(P, top - 6, W - P, top - 6, "ink")
    for i, (pkg, ghsa, cve, sev, score, date) in enumerate(adv):
        y = top + i * rh
        if i:
            f.line(P, y - 6, W - P, y - 6, "rule")
        f.text(P, y + 26, pkg, "S", 22, "ink")
        f.text(P, y + 48, date, "M", 12, "muted")
        f.text(214, y + 26, cve, "M", 13.5, "ink")
        f.text(214, y + 48, ghsa, "M", 12, "muted")
        ty = y + 30
        lo, hi = bands[sev]
        if score is not None:
            f.line(sx(0), ty, sx(score), ty, "acc" if sev == "High" else "ink", 3)
            f.circle(sx(score), ty, 5, fill="acc" if sev == "High" else "ink")
            lab = "%s  %.1f" % (sev, score)
            f.text(sx(score) - 12 if score > 8 else sx(score) + 14, ty - 12 if score > 8 else ty + 4.5, lab, "M", 13, "ink",
                   "end" if score > 8 else "start")
        else:
            f.rect(sx(lo if sev != "Low" else 0), ty - 7, sx(hi) - sx(lo if sev != "Low" else 0), 14, "ink2", "none",
                   extra=' stroke-dasharray="3 3"')
            f.text((sx(lo if sev != "Low" else 0) + sx(hi)) / 2, ty + 28, "%s, no score" % sev, "M", 12, "ink2", "middle")
    fy = H - 26
    f.text(P, fy, "axdale.com", "M", 12.5, "acct")
    f.arrow(P + width("axdale.com", "M", 12.5) + 5, fy, 12.5, "ne", "acct", 1.2)
    f.text(W - P, fy, "base score where published", "M", 12, "muted", "end")
    both(f)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "new":
        flow()
        record()
        advisories()
        sys.exit(0)
    hero()
    cta()
    code()
    support()
    proof()
    security()
    ml0x()
    squares()
    stack()
