"""Spin-off thumbnail in the Sunday-series style: Abril Fatface title, Montserrat subtitle,
Spain/UK badge top-right, channel logo + name bottom-left, red banner."""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Usage: python3 tools/spinoff/thumbnail.py content/spinoffs/semana-XX
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEEK = os.path.abspath(sys.argv[1]); T = json.load(open(f"{WEEK}/config.json", encoding="utf-8"))["thumbnail"]
ART, OUT = f"{WEEK}/scenes/thumb-art.jpg", f"{WEEK}/thumbnail.jpg"
LINE1, LINE2, SUB, BANNER = T["line1"], T["line2"], T["sub"], T["banner"]
W, H = 1280, 720
F = f"{REPO}/tools/spinoff/fonts/"
LOGO = f"{REPO}/content/brand/senorita-christina-logo-transparent.png"
def abril(s): return ImageFont.truetype(F + "AbrilFatface-Regular.ttf", s)
def mont(s, w="Bold"):
    f = ImageFont.truetype(F + "Montserrat[wght].ttf", s); f.set_variation_by_name(w); return f

src = Image.open(ART).convert("RGB")
im = src.resize((W, round(W * src.height / src.width)), Image.LANCZOS)
im = im.crop((0, 0, W, H)) if im.height >= H else im.resize((W, H))
im = im.convert("RGBA")

def txt(xy, t, f, fill=(20, 16, 14), stroke=(255, 255, 255), sw=6, shadow=True):
    global im
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((xy[0] + 4, xy[1] + 5), t, font=f, fill=(0, 0, 0, 120), stroke_width=sw, stroke_fill=(0, 0, 0, 120))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(4)))
    ImageDraw.Draw(im).text(xy, t, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

# fit line 1 and line 2 to the left ~58% of the frame
def fit(t, maker, start, maxw):
    s = start
    while ImageDraw.Draw(im).textlength(t, font=maker(s)) > maxw and s > 20: s -= 2
    return maker(s)
f1 = fit(LINE1, abril, 84, 700); f2 = fit(LINE2, abril, 196, 720)
txt((40, 18), LINE1, f1)
txt((36, 105), LINE2, f2, sw=8)
txt((46, 322), SUB, fit(SUB, mont, 34, 700), sw=5)

d = ImageDraw.Draw(im)
d.rectangle([0, 628, W, H], fill=(181, 52, 42))
fb = mont(52); tw = d.textlength(BANNER, font=fb)
d.text(((W - tw) / 2, 640), BANNER, font=fb, fill=(255, 255, 255))

# channel name as text, like the Sunday thumbnails (optional logo via config "show_logo")
nx = 40
if T.get("show_logo"):
    logo = Image.open(LOGO).convert("RGBA"); lh = 118
    logo = logo.resize((round(logo.width * lh / logo.height), lh), Image.LANCZOS)
    im.alpha_composite(logo, (30, 628 - lh - 8)); nx = 30 + logo.width + 12
txt((nx, 628 - 52), "Señorita Christina Español", abril(32), sw=4, shadow=False)

# Spain / UK badge: Spain lower-left, UK upper-right, white ring
R = 62; cx, cy = W - 90, 92; S2 = 8 * R
flag = Image.new("RGB", (S2, S2)); fd = ImageDraw.Draw(flag)
fd.rectangle([0, 0, S2, S2], fill=(198, 11, 30)); fd.rectangle([0, S2 // 4, S2, 3 * S2 // 4], fill=(255, 196, 0))
uk = Image.new("RGB", (S2, S2), (1, 33, 105)); ud = ImageDraw.Draw(uk); w = S2 // 10
ud.line([(0, 0), (S2, S2)], fill="white", width=w * 2); ud.line([(0, S2), (S2, 0)], fill="white", width=w * 2)
ud.line([(0, 0), (S2, S2)], fill=(200, 16, 46), width=int(w * 0.7)); ud.line([(0, S2), (S2, 0)], fill=(200, 16, 46), width=int(w * 0.7))
ud.rectangle([S2 // 2 - int(w * 1.5), 0, S2 // 2 + int(w * 1.5), S2], fill="white"); ud.rectangle([0, S2 // 2 - int(w * 1.5), S2, S2 // 2 + int(w * 1.5)], fill="white")
ud.rectangle([S2 // 2 - int(w * 0.9), 0, S2 // 2 + int(w * 0.9), S2], fill=(200, 16, 46)); ud.rectangle([0, S2 // 2 - int(w * 0.9), S2, S2 // 2 + int(w * 0.9)], fill=(200, 16, 46))
m = Image.new("L", (S2, S2), 0); ImageDraw.Draw(m).polygon([(0, 0), (S2, 0), (S2, S2)], fill=255)
flag.paste(uk, (0, 0), m)
circ = Image.new("L", (S2, S2), 0); ImageDraw.Draw(circ).ellipse([0, 0, S2 - 1, S2 - 1], fill=255)
flag = flag.resize((2 * R, 2 * R), Image.LANCZOS); circ = circ.resize((2 * R, 2 * R), Image.LANCZOS)
d = ImageDraw.Draw(im); d.ellipse([cx - R - 7, cy - R - 7, cx + R + 7, cy + R + 7], fill=(255, 255, 255))
im.paste(flag, (cx - R, cy - R), circ)
im.convert("RGB").save(OUT, quality=93)
print("ok", OUT)
