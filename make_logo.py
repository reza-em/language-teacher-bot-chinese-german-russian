"""Builds assets/avatar.png (profile photo) and assets/channel_avatar.png from assets/logo.png, adding correctly shaped Persian text (PIL + raqm, fallback arabic_reshaper+bidi)."""
import os
from PIL import Image, ImageDraw, ImageFont, features
BASE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "Vazirmatn-Bold.ttf")
if not os.path.exists(FONT): FONT = os.path.join(BASE, "assets", "Vazirmatn-Bold.ttf")

def shaped(text):
    if features.check("raqm"): return text, dict(direction="rtl", language="fa")
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text)), {}

def banner(img, text, sub=None):
    W, H = img.size; im = img.convert("RGBA"); ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    h = int(H * 0.22); y0 = H - h - int(H * 0.04)
    d.rounded_rectangle((int(W * 0.08), y0, int(W * 0.92), y0 + h), radius=int(h * 0.3), fill=(120, 10, 15, 225), outline=(255, 214, 102, 255), width=max(3, W // 160))
    f = ImageFont.truetype(FONT, int(h * 0.52)); t, kw = shaped(text)
    d.text((W // 2, y0 + (h * (0.42 if sub else 0.5))), t, font=f, fill=(255, 236, 170, 255), anchor="mm", **kw)
    if sub:
        f2 = ImageFont.truetype(FONT, int(h * 0.24)); d.text((W // 2, y0 + h * 0.80), sub, font=f2, fill=(255, 255, 255, 235), anchor="mm")
    return Image.alpha_composite(im, ov).convert("RGB")

if __name__ == "__main__":
    src = Image.open(os.path.join(BASE, "assets", "logo.png")).convert("RGB")
    a = banner(src, "معلم چینی", "Chinese Teacher"); a.save(os.path.join(BASE, "assets", "avatar.png"), optimize=True)
    c = banner(src, "آموزش چینی", "Learn Mandarin"); c.save(os.path.join(BASE, "assets", "channel_avatar.png"), optimize=True)
    print("ok", a.size, "raqm" if features.check("raqm") else "reshaper")
