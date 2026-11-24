"""Misterios de cada día: episode MP3 + video from a script.py (S list).
Usage: python3 tools/misterios/build.py content/misterios/<ep> [audio|preview|video]
audio  : ElevenLabs per line (eleven_multilingual_v2, stab 0.5, sim 0.75, speed 0.7), trimmed, joined
         (0.5 s between lines, 1.2 s at sections, PAUSA as given), loudnorm -16 LUFS, MP3 192k mono.
video  : scene image per line, speaker + Spanish + English subtitle, title card, options/repeat/quiz pills,
         logo; writes mp4 + srt + chapters.txt. Voices as in MP3_WORKFLOW_Misterios_de_cada_dia.md.
"""
import os, sys, json, subprocess, wave, math, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EP = os.path.abspath(sys.argv[1]); MODE = sys.argv[2] if len(sys.argv) > 2 else "video"
ns = {}; exec(open(f"{EP}/script.py", encoding="utf-8").read(), ns); S = ns["S"]
CFG = json.load(open(f"{EP}/config.json", encoding="utf-8"))
VOICE = {"Lucía": "JddqVF50ZSIR7SRbJE6u", "Marcos": "uPc5TJmLHicJAPs7qpif", "Abuela Carmen": "iuYybvSfclFoJ9ab2Im6",
         "Paco": "dabBScGPxrhZRE621vIm"}
SR = 44100; A = f"{EP}/audio"; os.makedirs(A, exist_ok=True); OUT = f"{EP}/out"; os.makedirs(OUT, exist_ok=True)
SPEAK = set(VOICE)

def tts(i, who, text, slow=1.0):
    wav = f"{A}/{i:03d}.wav"
    if os.path.exists(wav): return wav
    mp3 = f"{A}/{i:03d}.mp3"
    if not os.path.exists(mp3):
        body = json.dumps({"text": text, "model_id": "eleven_multilingual_v2",
                           "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": 0.7}}).encode()
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE[who]}?output_format=mp3_44100_128",
                                     data=body, headers={"Content-Type": "application/json", "xi-api-key": "proxy"})
        open(mp3, "wb").write(urllib.request.urlopen(req, timeout=120).read())
    trim = "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse"
    if slow != 1.0: trim += f",atempo={slow}"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-af", trim, "-ar", str(SR), "-ac", "1", wav], check=True)
    return wav
def read(w):
    with wave.open(w) as f: return np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(np.float32) / 32768

# ---- timeline: (start, end, kind, data) ----
EV, CH, CLIPS = [], [], []
t, img, n, first = 0.3, None, 0, True
def add(dur, **d):
    global t; EV.append(dict(start=t, end=t + dur, img=img, **d)); t += dur
for x in S:
    k = x[0]
    if k == "sec": CH.append((t, x[1])); t += 0 if first else 0.7; first = False
    elif k == "img": img = x[1]
    elif k == "pause": add(x[1], pill=EV[-1].get("pill_after", "Tu turno · Your turn"), sub=EV[-1].get("sub") if EV[-1].get("keep") else None)
    elif k == "card":
        if x[1] == "title": add(3.5, title=True)
        else: EV[-1]["opts"] = True; EV[-1]["keep"] = True; EV[-1]["pill_after"] = "¿Qué crees tú? · Escríbelo en los comentarios"
    elif k == "rep":
        for slow in (1.0, 0.85):
            n += 1; w = tts(n, "Abuela Carmen", x[1], slow); CLIPS.append((t, w)); d = len(read(w)) / SR
            add(d + 0.5, sub=("Abuela Carmen", x[1], x[2]), pill="Repite conmigo")
        add(5.0, sub=("", x[1], x[2]), pill="Tu turno · Your turn")
    elif k in SPEAK:
        n += 1; w = tts(n, k, x[1]); CLIPS.append((t, w)); d = len(read(w)) / SR
        add(d + 0.5, sub=(k, x[1], x[2]))
TOTAL = t + 1.0
def mmss(s): return f"{int(s // 60)}:{int(s % 60):02d}"
print("lines", n, "length", mmss(TOTAL))
mix = np.zeros(int(TOTAL * SR) + SR, np.float32)
for st, w in CLIPS: a = read(w); mix[int(st * SR): int(st * SR) + len(a)] += a
with wave.open(f"{OUT}/mix.wav", "w") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
NAME = CFG["name"]
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{OUT}/mix.wav", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(SR),
                f"{OUT}/norm.wav"], check=True)
if MODE == "audio":
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{OUT}/norm.wav", "-c:a", "libmp3lame", "-b:a", "192k", "-ac", "1",
                    "-metadata", f"title={CFG['title']}", "-metadata", "artist=Señorita Christina Español", f"{OUT}/{NAME}.mp3"], check=True)
    with open(f"{OUT}/chapters.txt", "w") as f:
        f.write("⏱️ Chapters:\n" + "".join(f"{mmss(s)} {c}\n" for s, c in CH))
    print(open(f"{OUT}/chapters.txt").read()); sys.exit()

# ---- frames ----
W, H, FPS = 1920, 1080, 30; F = f"{REPO}/tools/spinoff/fonts"
def mont(s, w="SemiBold"):
    f = ImageFont.truetype(f"{F}/Montserrat[wght].ttf", s); f.set_variation_by_name(w); return f
def cover(p):
    im = Image.open(f"{EP}/scenes/{p}.jpg").convert("RGB"); r = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2; return im.crop((x, y, x + W, y + H))
IMG = {}
def scene(p):
    if p not in IMG: IMG[p] = cover(p).convert("RGBA")
    return IMG[p]
COL = {"Lucía": (120, 200, 190), "Marcos": (235, 150, 90), "Abuela Carmen": (240, 200, 90), "": (255, 255, 255)}
def wrap(d, s, f, mw):
    out, cur = [], ""
    for w_ in s.split():
        tt = (cur + " " + w_).strip()
        if d.textlength(tt, font=f) <= mw: cur = tt
        else: out.append(cur); cur = w_
    return out + [cur]
def draw(e):
    fr = scene(CFG["title_image"] if e.get("title") else e["img"]).copy()
    if e.get("title"): return fr
    lay = Image.new("RGBA", fr.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if e.get("sub"):
        who, es, en = e["sub"]; fe, fn, fw = mont(54), mont(38, "Medium"), mont(32, "Bold")
        le, ln = wrap(d, es, fe, 1560), wrap(d, en, fn, 1560)
        h = 30 + (44 if who else 0) + 68 * len(le) + 50 * len(ln) + 20
        bw = max([d.textlength(l, font=fe) for l in le] + [d.textlength(l, font=fn) for l in ln] + [d.textlength(who, font=fw)]) + 90
        y0 = H - 50 - h
        d.rounded_rectangle([(W - bw) / 2, y0, (W + bw) / 2, H - 50], radius=26, fill=(14, 10, 8, 190))
        y = y0 + 22
        if who: d.text(((W - d.textlength(who, font=fw)) / 2, y), who, font=fw, fill=COL[who] + (255,)); y += 44
        for l in le: d.text(((W - d.textlength(l, font=fe)) / 2, y), l, font=fe, fill=(255, 255, 255)); y += 68
        for l in ln: d.text(((W - d.textlength(l, font=fn)) / 2, y + 4), l, font=fn, fill=(255, 222, 150)); y += 50
    pill = e.get("pill")
    if e.get("opts"): pill = "Opción A: Marcos  ·  Opción B: alguien de fuera"
    if pill:
        f = mont(42, "Bold"); pw = d.textlength(pill, font=f) + 80
        d.rounded_rectangle([(W - pw) / 2, 50, (W + pw) / 2, 128], radius=39, fill=(181, 52, 42, 240))
        d.text(((W - pw) / 2 + 40, 63), pill, font=f, fill=(255, 255, 255))
    return Image.alpha_composite(fr, lay)
LOGO = Image.open(f"{REPO}/content/brand/senorita-christina-logo-transparent.png").convert("RGBA")
LOGO = LOGO.resize((round(LOGO.width * 150 / LOGO.height), 150), Image.LANCZOS)
def frame(tt, idx=[0], cache={}):
    while idx[0] + 1 < len(EV) and tt >= EV[idx[0]]["end"]: idx[0] += 1
    e = EV[idx[0]] if tt >= EV[0]["start"] else dict(EV[0])
    key = id(e)
    if key not in cache:
        if len(cache) > 20: cache.clear()
        cache[key] = draw(e)
    fr = cache[key].copy()
    if not e.get("title"):
        ph = (tt - 1.0) % 60.0; lg = LOGO
        if ph < 1.2: lg = LOGO.resize((max(2, round(LOGO.width * abs(math.cos(ph / 1.2 * 2 * math.pi)))), 150))
        fr.alpha_composite(lg, (W - 24 - LOGO.width + (LOGO.width - lg.width) // 2, 24))
    return fr.convert("RGB")
if MODE == "preview":
    seen = set()
    for e in EV:
        tag = "title" if e.get("title") else "opts" if e.get("opts") else (e.get("pill") or "line")[:6] + "_" + e["img"]
        if tag in seen: continue
        seen.add(tag); i = EV.index(e); frame(e["start"] + 0.1, [i]).resize((960, 540)).save(f"{OUT}/prev_{len(seen):02d}.jpg", quality=80)
    print("preview", len(seen)); sys.exit()
ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-i", f"{OUT}/norm.wav", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-tune", "stillimage", "-pix_fmt", "yuv420p",
                       "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", f"{TOTAL:.2f}", "-movflags", "+faststart", f"{OUT}/{NAME}.mp4"], stdin=subprocess.PIPE)
idx = [0]
for i in range(int(TOTAL * FPS)): ff.stdin.write(frame(i / FPS, idx).tobytes())
ff.stdin.close(); ff.wait()
def ts(x): return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{int(x % 60):02d},{int(round(x % 1 * 1000)) % 1000:03d}"
srt = [f"{k}\n{ts(e['start'])} --> {ts(e['end'])}\n{e['sub'][1]}\n{e['sub'][2]}\n" for k, e in enumerate([e for e in EV if e.get("sub")], 1)]
open(f"{OUT}/{NAME}.srt", "w", encoding="utf-8").write("\n".join(srt))
print("done", mmss(TOTAL))
