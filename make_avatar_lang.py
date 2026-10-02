"""Builds the generic multi-language avatar assets/avatar_lang.png (640x640) and the welcome picture assets/logo.png:
four speech bubbles with 中 (Chinese), A (Latin/English), Я (Russian) and ä (German) on a deep-blue gradient, plus «معلم زبان» / Language Teacher."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, features
BASE = os.path.dirname(os.path.abspath(__file__))
CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
LATIN = next((p for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf") if os.path.exists(p)), None)
FA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "Vazirmatn-Bold.ttf")
if not os.path.exists(FA): FA = os.path.join(BASE, "assets", "Vazirmatn-Bold.ttf")
S = 2                                     # supersampling factor
N = 640 * S

def shaped(text):
    if features.check("raqm"): return text, dict(direction="rtl", language="fa")
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text)), {}

def gradient():
    im = Image.new("RGB", (N, N)); px = im.load()
    top, bot = (22, 42, 104), (14, 130, 150)
    for y in range(N):
        t = y / (N - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(N): px[x, y] = c
    return im

def bubble(base, box, tail, fill, glyph, font_path, fscale, fg, dy=0):
    """box = (x0,y0,x1,y1) in 640-space; tail = 'bl' | 'br' (corner the speech tail points to)."""
    x0, y0, x1, y1 = [int(v * S) for v in box]
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.rounded_rectangle((x0 + 8 * S, y0 + 10 * S, x1 + 8 * S, y1 + 10 * S), radius=44 * S, fill=(0, 0, 0, 90))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10 * S)))
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle((x0, y0, x1, y1), radius=44 * S, fill=fill, outline=(255, 255, 255, 235), width=5 * S)
    w = x1 - x0
    if tail == "bl": pts = [(x0 + int(w * .16), y1 - 4 * S), (x0 + int(w * .40), y1 - 4 * S), (x0 + int(w * .08), y1 + 46 * S)]
    else: pts = [(x1 - int(w * .16), y1 - 4 * S), (x1 - int(w * .40), y1 - 4 * S), (x1 - int(w * .08), y1 + 46 * S)]
    d.polygon(pts, fill=fill)
    d.line([pts[0], pts[2], pts[1]], fill=(255, 255, 255, 235), width=5 * S, joint="curve")
    d.polygon([(pts[0][0] + (3 if tail == "bl" else -3) * S, pts[0][1] - 3 * S), (pts[1][0], pts[1][1] - 3 * S), (pts[2][0] + (6 if tail == "bl" else -6) * S, pts[2][1] - 10 * S)], fill=fill)
    base.alpha_composite(ov)
    f = ImageFont.truetype(font_path, int((y1 - y0) * fscale))
    d = ImageDraw.Draw(base)
    d.text(((x0 + x1) // 2, (y0 + y1) // 2 + dy * S), glyph, font=f, fill=fg, anchor="mm")

def build():
    base = gradient().convert("RGBA")
    # soft glow behind the bubbles
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    gd.ellipse((N * .08, N * .02, N * .92, N * .80), fill=(120, 220, 255, 55)); base.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40 * S)))
    bubble(base, (44, 52, 292, 250), "bl", (214, 40, 57, 255), "中", CJK, 0.78, (255, 240, 200, 255), dy=-4)
    bubble(base, (348, 78, 596, 276), "br", (250, 252, 255, 255), "A", LATIN, 0.70, (24, 62, 140, 255), dy=-2)
    bubble(base, (44, 306, 292, 504), "bl", (255, 196, 43, 255), "Я", LATIN, 0.70, (60, 28, 6, 255), dy=-2)
    bubble(base, (348, 332, 596, 530), "br", (46, 184, 114, 255), "ä", LATIN, 0.74, (255, 255, 255, 255), dy=-6)
    d = ImageDraw.Draw(base)
    f = ImageFont.truetype(FA, int(50 * S)); t, kw = shaped("معلم زبان")
    d.rounded_rectangle((150 * S, 566 * S, 490 * S, 628 * S), radius=30 * S, fill=(10, 24, 70, 215), outline=(255, 214, 102, 255), width=3 * S)
    d.text((320 * S, 598 * S), t, font=f, fill=(255, 236, 170, 255), anchor="mm", **kw)
    return base.convert("RGB").resize((640, 640), Image.LANCZOS)

if __name__ == "__main__":
    img = build()
    out = os.path.join(BASE, "assets", "avatar_lang.png"); img.save(out, optimize=True)
    old = os.path.join(BASE, "assets", "logo.png"); keep = os.path.join(BASE, "assets", "logo_zh_old.png")
    if os.path.exists(old) and not os.path.exists(keep): os.replace(old, keep)
    img.save(old, optimize=True)
    print("ok", out, img.size, "raqm" if features.check("raqm") else "reshaper")
