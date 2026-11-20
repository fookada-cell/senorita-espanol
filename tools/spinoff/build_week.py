"""Spin-off builder: 4 conversations, each = title card, Round 1 Escucha, Round 2 Repite, key phrases.
Usage: python3 tools/spinoff/build_week.py content/spinoffs/semana-XX [preview|chapters]"""
import os, sys, json, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if len(sys.argv) < 2: sys.exit("usage: python3 tools/spinoff/build_week.py content/spinoffs/semana-XX [preview|chapters]")
WEEK = os.path.abspath(sys.argv[1]); MODE = sys.argv[2] if len(sys.argv) > 2 else "render"
CFG = json.load(open(f"{WEEK}/config.json", encoding="utf-8"))
IMG = f"{WEEK}/scenes"; AUD = f"{WEEK}/audio-norm"; W = f"{WEEK}/.work"; OUT = f"{WEEK}/out"
os.makedirs(W, exist_ok=True); os.makedirs(OUT, exist_ok=True)
F = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(F + n, s)
FPS, WID, HEI, SR = 25, 1920, 1080, 44100

data = json.load(open(f"{AUD}/script.json", encoding="utf-8"))
CONVS = data["convs"]
OTHER = CFG["other_speakers"]
TITLES = CFG["titles"]

# Per image: mouth positions (image-normalized) and the bubble centre (image-normalized, calm space between faces)
SPOTS = {k: {kk: tuple(vv) for kk, vv in v.items()} for k, v in CFG["spots"].items()}
KEY = [[tuple(p) for p in c] for c in CFG["key_phrases"]]

CREAM, INK, MUTED, GOLD, RED = (250, 244, 228), (40, 30, 24), (110, 92, 78), (205, 145, 55), (176, 58, 46)

# ---------- images ----------
SW = 2304
SCN, BLUR = {}, {}
for k in list(SPOTS) + ["thumb"]:
    name = "thumb-art" if k == "thumb" else k
    path = next(p for p in (f"{IMG}/{name}.jpg", f"{IMG}/{name}.png") if os.path.exists(p))
    im = Image.open(path).convert("RGB")
    im = im.resize((SW, round(SW * 9 / 16)), Image.LANCZOS)
    if k == "thumb": im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    SCN[k] = im
    BLUR[k] = im.filter(ImageFilter.GaussianBlur(10))
SH = round(SW * 9 / 16)

# ---------- drawing helpers ----------
def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: out.append(cur); cur = w
    return out + [cur]

def bubble(es, en, turn=False):
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    fe, fen = font("Inter-Bold.otf", 42), font("Inter-Italic.otf", 27)
    les = wrap(tmp, es, fe, 470); len_ = wrap(tmp, en, fen, 470) if en else []
    pad = 26; top = 38 if turn else 0
    w = max([tmp.textlength(l, font=fe) for l in les] + [tmp.textlength(l, font=fen) for l in len_] + [250 if turn else 120])
    h = top + len(les) * 52 + (8 + len(len_) * 35 if len_ else 0)
    bw, bh = int(w + pad * 2), int(h + pad * 2 - 6)
    im = Image.new("RGBA", (bw + 40, bh + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([20, 24, 20 + bw, 24 + bh], radius=28, fill=(0, 0, 0, 80))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, 20 + bw, 20 + bh], radius=28, fill=CREAM + (242,))
    y = 20 + pad - 4
    if turn:
        fp = font("Inter-Bold.otf", 21); t = "TU TURNO · YOUR TURN"; tw = d.textlength(t, font=fp)
        d.rounded_rectangle([20 + pad, y, 20 + pad + tw + 24, y + 30], radius=15, fill=GOLD)
        d.text((20 + pad + 12, y + 3), t, font=fp, fill=(255, 255, 255)); y += top
    for l in les: d.text((20 + pad, y), l, font=fe, fill=INK); y += 52
    if len_:
        y += 6
        for l in len_: d.text((20 + pad, y), l, font=fen, fill=MUTED); y += 35
    return im, (bw, bh)

CAM = {}
def img2scr(nx, ny):
    x0, y0, cw, ch = CAM["box"]
    return ((nx * SW - x0) / cw * WID, (ny * SH - y0) / ch * HEI)

def tail(frame, box, target, alpha):
    L, T, R, B = box; tx, ty = target
    if tx < L:   e = "l"
    elif tx > R: e = "r"
    elif ty < T: e = "t"
    else:        e = "b"
    if e in "lr":
        X = L if e == "l" else R; yb = min(max(ty, T + 34), B - 34); b1, b2, edge = (X, yb - 20), (X, yb + 20), (X, yb)
    else:
        Y = T if e == "t" else B; xb = min(max(tx, L + 34), R - 34); b1, b2, edge = (xb - 20, Y), (xb + 20, Y), (xb, Y)
    k = 0.55; tip = (edge[0] + (tx - edge[0]) * k, edge[1] + (ty - edge[1]) * k)
    lay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon([b1, b2, tip], fill=CREAM + (int(242 * alpha),))
    return Image.alpha_composite(frame, lay)

def pill(d, x, y, text, f, bg, fg=(255, 255, 255), right=False):
    tw = d.textlength(text, font=f)
    if right: x = x - tw - 44
    d.rounded_rectangle([x, y, x + tw + 44, y + 54], radius=27, fill=bg)
    d.text((x + 22, y + 10), text, font=f, fill=fg)

def chrome(frame, ev):
    d = ImageDraw.Draw(frame); f1, f2 = font("Inter-Bold.otf", 30), font("Inter-SemiBold.otf", 26)
    if ev.get("conv"):
        pill(d, 40, 32, f"Conversación {ev['conv']} · {TITLES[ev['conv']-1]}", f1, (30, 22, 18, 200))
    if ev.get("label"):
        pill(d, WID - 40, 32, ev["label"], f1, GOLD + (235,), right=True)
    if ev.get("step"):
        sw = d.textlength(ev["step"], font=f2)
        d.rounded_rectangle([40, HEI - 76, 40 + sw + 36, HEI - 32], radius=22, fill=(30, 22, 18, 170))
        d.text((58, HEI - 71), ev["step"], font=f2, fill=(255, 255, 255))
    return frame

def card_overlay(big, small, kicker=None):
    lay = Image.new("RGBA", (WID, HEI), (20, 14, 10, 140)); d = ImageDraw.Draw(lay)
    fb, fs, fk = font("Inter-Bold.otf", 104), font("Inter-Medium.otf", 46), font("Inter-Bold.otf", 34)
    y = 380
    if kicker:
        kw = d.textlength(kicker, font=fk)
        d.rounded_rectangle([(WID - kw) / 2 - 26, y - 90, (WID + kw) / 2 + 26, y - 34], radius=28, fill=RED)
        d.text(((WID - kw) / 2, y - 82), kicker, font=fk, fill=(255, 255, 255))
    for l in wrap(d, big, fb, 1600):
        d.text(((WID - d.textlength(l, font=fb)) / 2, y), l, font=fb, fill=(255, 255, 255)); y += 124
    d.text(((WID - d.textlength(small, font=fs)) / 2, y + 30), small, font=fs, fill=(240, 225, 200))
    return lay

def key_overlay(ci):
    lay = Image.new("RGBA", (WID, HEI), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([200, 150, WID - 200, HEI - 130], radius=48, fill=CREAM + (240,))
    d.text((290, 205), f"Frases clave · Key phrases", font=font("Inter-Bold.otf", 60), fill=INK)
    fe, fn = font("Inter-SemiBold.otf", 44), font("Inter-Italic.otf", 38)
    for i, (es, en) in enumerate(KEY[ci]):
        y = 330 + i * 92
        d.ellipse([290, y + 18, 306, y + 34], fill=GOLD)
        d.text((330, y), es, font=fe, fill=INK); d.text((1060, y + 4), en, font=fn, fill=MUTED)
    return lay

# ---------- audio ----------
def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768
CLIPS = {}
def clip(name):
    if name not in CLIPS: CLIPS[name] = load(f"{AUD}/{name}")
    return CLIPS[name]
def dur(name): return len(clip(name)) / SR

# ---------- timeline ----------
events, audio, t = [], [], 0.0
def add(kind, length, **kw):
    global t
    events.append(dict(kind=kind, start=t, end=t + length, **kw)); t += length
def spoken(kind, name, pre, post, **kw):
    audio.append((t + pre, name)); add(kind, pre + dur(name) + post, **kw)

spoken("card", "n_intro.mp3", 0.8, 1.6, img="thumb", big=CFG["series_title"],
       small=CFG["intro_sub"], kicker="Conversación real")
for ci, c in enumerate(CONVS):
    n = ci + 1; L = c["lines"]; half = (len(L) + 1) // 2
    other = OTHER[ci]
    def img_for(i): return f"0{n}A" if i < half else f"0{n}B"
    spoken("card", f"n_c{n}.mp3", 0.7, 1.4, img=f"0{n}A", big=TITLES[ci], small=f"Conversación {n}", kicker=f"Conversación {n}")
    for i, l in enumerate(L):
        sp = "Elena" if l["who"] == CFG.get("main_speaker", "Elena") else "Other"
        spoken("line", l["audio"], 0.35, 0.8, img=img_for(i), sp=sp, es=l["es"], en=l["en"], conv=n,
               label="Ronda 1 · Escucha", step=f"{i+1} / {len(L)}")
    spoken("card", "n_repite.mp3", 0.6, 1.0, img=f"0{n}A", big="Escucha y repite", small="Listen, then repeat each line in the pause",
           kicker="Ronda 2")
    for i, l in enumerate(L):
        sp = "Elena" if l["who"] == CFG.get("main_speaker", "Elena") else "Other"
        common = dict(img=img_for(i), sp=sp, es=l["es"], en=l["en"], conv=n, label="Ronda 2 · Repite", step=f"{i+1} / {len(L)}")
        spoken("line", l["audio"], 0.3, 0.2, **common)
        add("line", round(dur(l["audio"]) * 1.3 + 1.0, 2), turn=True, cont=True, **common)
    add("key", 9.0, img=f"0{n}B", ci=ci, conv=n, label="Frases clave")
spoken("card", "n_outro.mp3", 0.6, 2.4, img="thumb", big="¡Muy bien!", small=CFG["outro_sub"])
TOTAL = t

if MODE == "chapters":
    def mmss(x): return f"{int(x//60):02d}:{int(x%60):02d}"
    seen=set()
    for e in events:
        if e["kind"]=="card" and e["big"] in TITLES: print(mmss(e["start"]), "CONV", e["big"])
        elif e["kind"]=="card": print(mmss(e["start"]), "CARD", e["big"])
        elif e["kind"]=="key": print(mmss(e["start"]), "KEY", e["conv"])
        elif e["kind"]=="line" and (e["conv"], e["label"]) not in seen:
            seen.add((e["conv"], e["label"])); print(mmss(e["start"]), "ROUND", e["conv"], e["label"])
    print(mmss(TOTAL), "END"); sys.exit()

mix = np.zeros((int(TOTAL * SR) + SR, 2), dtype=np.float32)
for st, name in audio:
    a = clip(name); i0 = int(st * SR); mix[i0:i0 + len(a)] += a
mix *= 0.9 / max(1e-6, np.abs(mix).max())
with wave.open(f"{W}/mix.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())


LOGO = Image.open(f"{REPO}/content/brand/senorita-christina-logo-transparent.png").convert("RGBA")
LOGO_H = 175
LOGO = LOGO.resize((round(LOGO.width * LOGO_H / LOGO.height), LOGO_H), Image.LANCZOS)
SPIN_EVERY, SPIN_LEN = 20.0, 1.4
def add_logo(fr, tt):
    ph = (tt % SPIN_EVERY) - (SPIN_EVERY - SPIN_LEN)
    lg = LOGO
    if ph > 0:
        ang = (ph / SPIN_LEN) * 2 * math.pi
        sx = abs(math.cos(ang))
        w = max(2, round(LOGO.width * sx))
        lg = LOGO.resize((w, LOGO_H), Image.BILINEAR)
    x = WID - 26 - LOGO.width + (LOGO.width - lg.width) // 2
    fr.alpha_composite(lg, (x, HEI - 22 - LOGO_H))
    return fr

# ---------- frames ----------
cache = {}
def cam_target(ev):
    if ev["kind"] == "line":
        cx = SPOTS[ev["img"]][ev["sp"]][0]; return 0.5 + (cx - 0.5) * 0.25
    return 0.5
camera_fx = [0.5]
def scene_frame(key, tt, fx, blur=False):
    z = 1.0 + 0.035 * (0.5 + 0.5 * math.sin(tt / 11.0))
    cw = SW / 1.05 / z; ch = cw * 9 / 16
    cx = min(max(fx * SW, cw / 2), SW - cw / 2); cy = min(max(SH * 0.48, ch / 2), SH - ch / 2)
    CAM["box"] = (cx - cw / 2, cy - ch / 2, cw, ch)
    src = (BLUR if blur else SCN)[key]
    return src.resize((WID, HEI), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)).convert("RGBA")

def frame_at(tt, idx=[0]):
    while idx[0] + 1 < len(events) and tt >= events[idx[0]]["end"]: idx[0] += 1
    ev = events[idx[0]]
    camera_fx[0] += (cam_target(ev) - camera_fx[0]) * 0.025
    blur = ev["kind"] in ("card", "key")
    fr = scene_frame(ev["img"], tt, camera_fx[0], blur)
    # crossfade from previous image at scene changes
    prev = events[idx[0] - 1] if idx[0] else None
    age = tt - ev["start"]
    if prev and (prev["img"] != ev["img"] or (prev["kind"] in ("card", "key")) != blur) and age < 0.5:
        old = scene_frame(prev["img"], tt, camera_fx[0], prev["kind"] in ("card", "key"))
        fr = Image.blend(old, fr, age / 0.5)
        scene_frame(ev["img"], tt, camera_fx[0], blur)  # restore CAM box for this event
    if ev["kind"] == "card":
        k = ("card", ev["big"], ev.get("kicker"))
        if k not in cache: cache[k] = card_overlay(ev["big"], ev["small"], ev.get("kicker"))
        fr = Image.alpha_composite(fr, cache[k])
    elif ev["kind"] == "key":
        k = ("key", ev["ci"])
        if k not in cache: cache[k] = key_overlay(ev["ci"])
        fr = Image.alpha_composite(fr, cache[k])
    else:
        turn = ev.get("turn", False); k = (ev["es"], turn)
        if k not in cache: cache[k] = bubble(ev["es"], ev["en"], turn)
        b, (bw, bh) = cache[k]
        a = 1.0 if ev.get("cont") else min(1, age / 0.22)
        s = 1.0 if ev.get("cont") else 0.85 + 0.15 * (1 - (1 - a) ** 3) + 0.04 * math.sin(min(1, age / 0.35) * math.pi)
        spot = SPOTS[ev["img"]]
        cxs, cys = img2scr(*spot["at" + ev["sp"]])
        bx = int(min(max(cxs - bw / 2, 40), WID - bw - 40)) - 20
        by = int(min(max(cys - bh / 2, 100), HEI - bh - 100)) - 20
        if CFG.get("bubble_tail", False):
            fr = tail(fr, (bx + 20, by + 20, bx + 20 + bw, by + 20 + bh), img2scr(*spot[ev["sp"]]), a)
        bb = b if s == 1 else b.resize((max(1, int(b.width * s)), max(1, int(b.height * s))), Image.BILINEAR)
        if a < 1:
            bb = bb.copy(); bb.putalpha(bb.getchannel("A").point(lambda v: int(v * a)))
        fr.alpha_composite(bb, (max(0, bx + (b.width - bb.width) // 2), max(0, by + (b.height - bb.height) // 2)))
        if turn:
            d = ImageDraw.Draw(fr); pr = age / (ev["end"] - ev["start"])
            d.rounded_rectangle([WID // 2 - 300, HEI - 60, WID // 2 + 300, HEI - 44], radius=8, fill=(30, 22, 18, 160))
            d.rounded_rectangle([WID // 2 - 300, HEI - 60, WID // 2 - 300 + int(600 * pr), HEI - 44], radius=8, fill=GOLD + (255,))
    return add_logo(chrome(fr, ev), tt).convert("RGB")

def ts(x): return f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(round((x%1)*1000))%1000:03d}"

if MODE.startswith("check"):   # "check3" = one frame per Ronda 1 line of conversation 3 (and its turn frame)
    n = int(MODE[5:]); k = 0
    for i, e in enumerate(events):
        if e["kind"] == "line" and e.get("conv") == n and "1" in e["label"]:
            camera_fx[0] = cam_target(e); frame_at(e["start"] + 1.0, [i]).save(f"{OUT}/check{n}_{k:02d}.jpg", quality=80); k += 1
    print("check frames", k); sys.exit()
if MODE == "preview":
    picks = {}
    for e in events:
        if e["kind"] == "line" and not e.get("turn"):
            picks.setdefault(e["img"], e)
    for k, e in picks.items():
        idx = [events.index(e)]; camera_fx[0] = cam_target(e)
        frame_at(e["start"] + 1.0, idx).save(f"{OUT}/preview_{k}.jpg", quality=85)
    e = next(e for e in events if e.get("turn")); camera_fx[0] = cam_target(e)
    frame_at(e["start"] + 1.0, [events.index(e)]).save(f"{OUT}/preview_turn.jpg", quality=85)
    e = next(e for e in events if e["kind"] == "key"); frame_at(e["start"] + 1.0, [events.index(e)]).save(f"{OUT}/preview_key.jpg", quality=85)
    frame_at(1.0, [0]).save(f"{OUT}/preview_intro.jpg", quality=85)
    print("preview ok · total", round(TOTAL / 60, 2), "min"); sys.exit()

TEST = MODE.startswith("test")   # e.g. "test30" renders only the first 30 seconds
if TEST: TOTAL = min(TOTAL, float(MODE[4:] or 30))
out = f"{OUT}/{CFG['slug']}" + ("-test.mp4" if TEST else ".mp4")
ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WID}x{HEI}", "-r", str(FPS), "-i", "-",
                       "-i", f"{W}/mix.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-tune", "animation", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "160k", "-shortest", "-t", f"{TOTAL:.3f}", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
idx = [0]
for nfr in range(int(TOTAL * FPS)):
    ff.stdin.write(frame_at(nfr / FPS, idx).tobytes())
ff.stdin.close(); ff.wait()
if TEST: sys.exit(print("test done", round(TOTAL, 1), "s"))
srt, k = [], 1
for e in events:
    if e["kind"] == "line" and not e.get("turn"):
        srt.append(f"{k}\n{ts(e['start'])} --> {ts(e['end'])}\n{e['es']}\n{e['en']}\n"); k += 1
open(f"{OUT}/{CFG['slug']}.srt", "w", encoding="utf-8").write("\n".join(srt))
print("done", round(TOTAL / 60, 2), "min")
