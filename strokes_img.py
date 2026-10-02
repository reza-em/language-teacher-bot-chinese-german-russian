"""Stroke-order images rendered with Pillow from MakeMeAHanzi stroke outlines (Arphic Public License data)."""
import io, os, re
from PIL import Image, ImageDraw, ImageFont
import data, config

SIZE = 220

def _flatten(path, steps=8):
    toks = re.findall(r"[MLQCZ]|-?\d+\.?\d*", path); i = 0; polys = []; cur = []; pos = (0, 0)
    def num(): 
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        c = toks[i]; i += 1
        if c == "M":
            if cur: polys.append(cur)
            pos = (num(), num()); cur = [pos]
        elif c == "L":
            pos = (num(), num()); cur.append(pos)
        elif c == "Q":
            x1, y1, x, y = num(), num(), num(), num()
            for s in range(1, steps + 1):
                t = s / steps; cur.append(((1 - t) ** 2 * pos[0] + 2 * (1 - t) * t * x1 + t * t * x, (1 - t) ** 2 * pos[1] + 2 * (1 - t) * t * y1 + t * t * y))
            pos = (x, y)
        elif c == "C":
            x1, y1, x2, y2, x, y = [num() for _ in range(6)]
            for s in range(1, steps + 1):
                t = s / steps; u = 1 - t
                cur.append((u ** 3 * pos[0] + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3 * x, u ** 3 * pos[1] + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3 * y))
            pos = (x, y)
        elif c == "Z":
            if cur: polys.append(cur); cur = []
    if cur: polys.append(cur)
    return polys

def _tx(pt, size):
    # MakeMeAHanzi: 1024 box, y axis points up with baseline at 900 -> flip
    return (pt[0] * size / 1024.0, (900 - pt[1]) * size / 1024.0)

def render_panel(strokes, upto, size=SIZE):
    im = Image.new("RGB", (size, size), "white"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, size - 1, size - 1], outline="#cfa", width=1)
    d.line([(0, size / 2), (size, size / 2)], fill="#e8d0d0"); d.line([(size / 2, 0), (size / 2, size)], fill="#e8d0d0")
    for k in range(upto):
        col = "#d62828" if k == upto - 1 else "#222222"
        for poly in _flatten(strokes[k]):
            if len(poly) >= 3: d.polygon([_tx(p, size) for p in poly], fill=col)
    return im

def stroke_order_png(ch, cols=6, panel=150):
    """Progressive stroke-order sheet for one character (None if the character has no data)."""
    sd = data.stroke_data(ch)
    if not sd: return None
    n = len(sd["strokes"]); rows = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * panel, rows * panel), "white")
    for k in range(n):
        im = render_panel(sd["strokes"], k + 1, panel)
        sheet.paste(im, ((k % cols) * panel, (k // cols) * panel))
    buf = io.BytesIO(); sheet.save(buf, "PNG"); return buf.getvalue()
