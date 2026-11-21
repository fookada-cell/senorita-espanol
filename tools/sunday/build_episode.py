"""Sunday main-episode builder: one illustrated story heard three times + learning activities.
Order: English opening -> listen 1 (Spanish subtitles) -> listen 2 (Spanish line + English translation, both subtitled)
-> listen 3 (no story subtitles, same speed) -> 3 questions (5 s pause each) -> 16 vocabulary cards
-> expressions from Spain -> closing. Same 12 images and the same recordings in all three listens.

Usage: python3 tools/sunday/build_episode.py content/sunday/epXX [preview|chapters|testNN]
Inputs in the episode folder: lines.json, config.json, audio/<ID>.wav (tools/sunday/voices.py), scenes/scene-NN.jpg
"""
import os, sys, json, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EP = os.path.abspath(sys.argv[1]); MODE = sys.argv[2] if len(sys.argv) > 2 else "render"
C = json.load(open(f"{EP}/config.json", encoding="utf-8"))
L = json.load(open(f"{EP}/lines.json", encoding="utf-8"))
OUT = f"{EP}/out"; os.makedirs(OUT, exist_ok=True)
WID, HEI, FPS, SR = 1920, 1080, 30, 44100
FONTS = f"{REPO}/tools/spinoff/fonts"

def mont(size, w="SemiBold"):
    f = ImageFont.truetype(f"{FONTS}/Montserrat[wght].ttf", size); f.set_variation_by_name(w); return f
def serif(size):
    return ImageFont.truetype(f"{FONTS}/AbrilFatface-Regular.ttf", size)

# ---------- images ----------
def cover(im):
    r = max(WID / im.width, HEI / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - WID) // 2, (im.height - HEI) // 2
    return im.crop((x, y, x + WID, y + HEI))
SCN, BLUR = {}, {}
for k in C["scenes"]:
    im = cover(Image.open(f"{EP}/scenes/scene-{k}.jpg").convert("RGB"))
    if Image.open(f"{EP}/scenes/scene-{k}.jpg").width < 1500:
        im = im.filter(ImageFilter.UnsharpMask(2, 80, 2))
    SCN[k] = im
    dark = Image.new("RGB", (WID, HEI), (20, 14, 10))
    BLUR[k] = Image.blend(im.filter(ImageFilter.GaussianBlur(14)), dark, 0.35)
def scene_of(fid):
    n = int(fid[1:])
    for k, (a, b) in C["scenes"].items():
        if a <= n <= b: return k
    return list(C["scenes"])[-1]

# ---------- text helpers ----------
def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: out.append(cur); cur = w
    return out + [cur]
SUB_F = mont(54)
def subtitle(frame, text, lang):
    """Bottom-centre subtitle, max 2 lines (shrinks if needed), dark backing."""
    d = ImageDraw.Draw(frame); size = 54
    while True:
        f = mont(size); lines = wrap(d, text, f, 1500)
        if len(lines) <= 2 or size <= 40: break
        size -= 2
    lh = int(size * 1.3); h = lh * len(lines) + 28
    w = max(d.textlength(l, font=f) for l in lines) + 60
    y0 = HEI - 78 - h
    lay = Image.new("RGBA", frame.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([(WID - w) / 2, y0, (WID + w) / 2, y0 + h], radius=18, fill=(15, 10, 8, 175))
    fill = (255, 255, 255) if lang == "es" else (255, 226, 160)
    for i, l in enumerate(lines):
        ld.text(((WID - ld.textlength(l, font=f)) / 2, y0 + 14 + i * lh), l, font=f, fill=fill + (255,))
    return Image.alpha_composite(frame, lay)

def center_card(frame, kicker, big, small, tag=None):
    lay = Image.new("RGBA", frame.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    top, bot = 220, HEI - 220
    d.rounded_rectangle([240, top, WID - 240, bot], radius=48, fill=(250, 244, 228, 238))
    size = 96
    while size > 50:
        fb = serif(size); blines = wrap(d, big, fb, WID - 620)
        if len(blines) <= 2: break
        size -= 6
    fs = mont(44, "Medium"); slines = wrap(d, small, fs, WID - 620)[:3] if small else []
    fk = mont(36, "Bold")
    h = (100 if kicker else 0) + len(blines) * int(size * 1.15) + (16 + 58 * len(slines) if slines else 0)
    y = top + (bot - top - h) // 2
    if kicker:
        kw = d.textlength(kicker, font=fk)
        d.rounded_rectangle([(WID - kw) / 2 - 28, y, (WID + kw) / 2 + 28, y + 60], radius=30, fill=(181, 52, 42, 255))
        d.text(((WID - kw) / 2, y + 9), kicker, font=fk, fill=(255, 255, 255)); y += 100
    for l in blines:
        d.text(((WID - d.textlength(l, font=fb)) / 2, y), l, font=fb, fill=(40, 30, 24)); y += int(size * 1.15)
    y += 16
    for l in slines:
        d.text(((WID - d.textlength(l, font=fs)) / 2, y), l, font=fs, fill=(110, 92, 78)); y += 58
    if tag:
        ft = mont(30, "Bold"); tw = d.textlength(tag, font=ft)
        d.rounded_rectangle([WID - 240 - tw - 90, top + 30, WID - 270, top + 84], radius=27, fill=(198, 11, 30, 255))
        d.text((WID - 240 - tw - 66, top + 38), tag, font=ft, fill=(255, 196, 0))
    return Image.alpha_composite(frame, lay)

# ---------- audio ----------
def load(id_):
    with wave.open(f"{EP}/audio/{id_}.wav") as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return a
CL = {}
def clip(i):
    if i not in CL: CL[i] = load(i)
    return CL[i]
def dur(i): return len(clip(i)) / SR

# ---------- timeline ----------
EV, AUD, CH = [], [], []
t = 0.0
def gap(s, **v):
    global t
    if s > 0: EV.append(dict(start=t, end=t + s, **v)); t += s
def say(i, post=0.0, **v):
    global t
    AUD.append((t, i)); d = dur(i)
    EV.append(dict(start=t, end=t + d + post, **v)); t += d + post
def chapter(name): CH.append((t, name))

F = sorted([k for k in L if k[0] == "F" and k[1:].isdigit()], key=lambda k: int(k[1:]))
M = lambda f: f"M{int(f[1:]) + 10:03d}"
first = list(C["scenes"])[0]; last = list(C["scenes"])[-1]

chapter("Introduction")
say("M001", 0.8, img=first, sub=(L["M001"]["text"], "en"))
gap(0.6, img=first)
chapter("Listen in Spanish with subtitles")
for i, f in enumerate(F):
    nxt = F[i + 1] if i + 1 < len(F) else None
    say(f, 1.0 if (nxt and scene_of(nxt) != scene_of(f)) else 0.6, img=scene_of(f), sub=(L[f]["text"], "es"))
gap(0.6, img=last)
chapter("With English translation")
say("M002", 0.9, img=first, sub=(L["M002"]["text"], "en"))
for i, f in enumerate(F):
    k = scene_of(f)
    say(f, 0.4, img=k, sub=(L[f]["text"], "es"))
    nxt = F[i + 1] if i + 1 < len(F) else None
    say(M(f), 1.0 if (nxt and scene_of(nxt) != k) else 0.7, img=k, sub=(L[M(f)]["text"], "en"))
gap(0.6, img=last)
chapter("Spanish only, no subtitles")
say("M003", 0.9, img=first, sub=(L["M003"]["text"], "en"))
for i, f in enumerate(F):
    nxt = F[i + 1] if i + 1 < len(F) else None
    say(f, 1.0 if (nxt and scene_of(nxt) != scene_of(f)) else 0.6, img=scene_of(f))
gap(1.0, img=last)
chapter("Questions")
qs = C.get("question_scene", first)
say("M004", 0.8, img=qs, blur=True, card=("", "Preguntas", "Three questions · Tres preguntas"))
for n, q in enumerate([k for k in ("Q1", "Q2", "Q3") if k in L], 1):
    say(q, 5.0, img=qs, blur=True, card=(f"Pregunta {n}", L[q]["text"], ""))
gap(0.8, img=qs, blur=True)
chapter("Vocabulary")
vs = sorted([k for k in L if k[0] == "V" and k[1:].isdigit()])
say("M005", 0.8, img=qs, blur=True, card=("", "Vocabulario", "Sixteen useful words · Spanish first, then English"))
for v in vs:
    img = scene_of(f"F{C.get('vocab_lines', {}).get(v, 30):03d}") if C.get("vocab_lines") else qs
    card = ("Vocabulario", L[v]["text"], L[v + "e"]["text"])
    say(v, 0.3, img=img, blur=True, card=card)
    say(v + "e", 0.5, img=img, blur=True, card=card)
gap(0.6, img=qs, blur=True)
chapter("Expressions from Spain")
say("M006", 0.8, img=qs, blur=True, card=("", "Expresiones de España", "Expressions you will hear in Spain"))
for s in sorted([k for k in L if k[0] == "S" and k[1:].isdigit()]):
    sc = C.get("slang_scenes", {}).get(s, qs)
    card = ("Expresión", L[s]["text"], L[s + "e"]["text"], "España")
    say(s, 0.3, img=sc, blur=True, card=card)
    say(s + "e", 0.4, img=sc, blur=True, card=card)
    say(s + "x", 0.8, img=sc, sub=(L[s + "x"]["text"], "es"))
gap(0.6, img=last)
chapter("Closing")
for m in [k for k in ("M007", "M008", "M009", "M010") if k in L and k not in C.get("skip", [])]:
    say(m, 0.6, img=last, sub=(L[m]["text"], "en"))
say("F-GB", 2.5, img=last)
TOTAL = t

def mmss(x): return f"{int(x // 60):02d}:{int(x % 60):02d}"
if MODE == "chapters":
    for s, n in CH: print(mmss(s), n)
    print(mmss(TOTAL), "END"); sys.exit()

# ---------- frames ----------
LOGO = Image.open(f"{REPO}/content/brand/senorita-christina-logo-transparent.png").convert("RGBA")
LH = 175; LOGO = LOGO.resize((round(LOGO.width * LH / LOGO.height), LH), Image.LANCZOS)
LOGO.putalpha(LOGO.getchannel("A").point(lambda v: int(v * 0.9)))
SPIN_START, SPIN_EVERY, SPIN_LEN = 1.0, 60.0, 1.2
def logo_at(tt):
    ph = (tt - SPIN_START) % SPIN_EVERY
    if tt < SPIN_START or ph > SPIN_LEN: return LOGO
    sx = abs(math.cos(ph / SPIN_LEN * 2 * math.pi))
    return LOGO.resize((max(2, round(LOGO.width * sx)), LH), Image.BILINEAR)
def base_frame(e):
    fr = (BLUR if e.get("blur") else SCN)[e["img"]].convert("RGBA")
    if e.get("card"): fr = center_card(fr, *e["card"])
    if e.get("sub"): fr = subtitle(fr, *e["sub"])
    return fr
CACHE = {}
def frame_at(tt, idx=[0]):
    while idx[0] + 1 < len(EV) and tt >= EV[idx[0]]["end"]: idx[0] += 1
    e = EV[idx[0]]; key = (e["img"], e.get("blur"), str(e.get("card")), str(e.get("sub")))
    if key not in CACHE:
        if len(CACHE) > 40: CACHE.clear()
        CACHE[key] = base_frame(e)
    fr = CACHE[key].copy(); lg = logo_at(tt)
    fr.alpha_composite(lg, (WID - 22 - LOGO.width + (LOGO.width - lg.width) // 2, HEI - 20 - LH))
    return fr.convert("RGB")

if MODE == "preview":
    picks = {}
    for e in EV:
        tag = ("card" if e.get("card") else "sub" if e.get("sub") else "plain") + ("-blur" if e.get("blur") else "")
        picks.setdefault((e["img"], tag), e)
    for n, ((img, tag), e) in enumerate(sorted(picks.items())):
        frame_at(e["start"] + 0.5, [EV.index(e)]).resize((960, 540)).save(f"{OUT}/preview_{img}_{tag}.jpg", quality=80)
    print("preview frames:", len(picks), "· total", mmss(TOTAL)); sys.exit()

# ---------- audio mix ----------
END = TOTAL if not MODE.startswith("test") else min(TOTAL, float(MODE[4:] or 60))
mix = np.zeros(int(TOTAL * SR) + SR, dtype=np.float32)
for st, i in AUD:
    a = clip(i); s0 = int(st * SR); mix[s0:s0 + len(a)] += a
mix = np.clip(mix, -1, 1)[: int(END * SR)]
with wave.open(f"{OUT}/mix.wav", "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())

name = C["slug"] + ("-test" if MODE.startswith("test") else "")
ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WID}x{HEI}", "-r", str(FPS), "-i", "-",
                       "-i", f"{OUT}/mix.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "stillimage",
                       "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                       "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "44100", "-t", f"{END:.3f}", "-movflags", "+faststart",
                       f"{OUT}/{name}.mp4"], stdin=subprocess.PIPE)
idx = [0]
for n in range(int(END * FPS)):
    ff.stdin.write(frame_at(n / FPS, idx).tobytes())
ff.stdin.close(); ff.wait()
os.remove(f"{OUT}/mix.wav")
if MODE.startswith("test"): print("test done", round(END, 1)); sys.exit()

def ts(x): return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round((x % 1) * 1000)) % 1000:03d}"
srt, k = [], 1
for e in EV:
    if e.get("sub"):
        srt.append(f"{k}\n{ts(e['start'])} --> {ts(e['end'])}\n{e['sub'][0]}\n"); k += 1
    elif e.get("card") and e["card"][1]:
        srt.append(f"{k}\n{ts(e['start'])} --> {ts(e['end'])}\n{e['card'][1]}" + (f"\n{e['card'][2]}" if e['card'][2] else "") + "\n"); k += 1
open(f"{OUT}/{C['slug']}.srt", "w", encoding="utf-8").write("\n".join(srt))
with open(f"{OUT}/chapters.txt", "w") as f:
    for s, n in CH: f.write(f"{mmss(s)} {n}\n")
print("done", mmss(TOTAL))
