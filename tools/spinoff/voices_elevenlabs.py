"""Make one MP3 per line for a spin-off week with ElevenLabs, then level every line to the same loudness.

Usage:  python3 tools/spinoff/voices_elevenlabs.py content/spinoffs/semana-XX

Reads:   <week>/PRODUCTION_PACK.md  (the four "## Conversation" tables: | # | Who | Spanish | English |)
         <week>/config.json         (voices, narration lines)
Writes:  <week>/audio/        raw ElevenLabs output (cached: existing files are not regenerated)
         <week>/audio-norm/   levelled to -19 LUFS, what build_week.py uses
         <week>/audio-norm/script.json

The API key is injected by the cloud environment's network proxy (saved once as a network secret
for api.elevenlabs.io). It is never stored in this repo.
"""
import json, os, re, subprocess, sys, time, urllib.error, urllib.request

if len(sys.argv) < 2:
    sys.exit(__doc__)
WEEK = os.path.abspath(sys.argv[1])
CFG = json.load(open(f"{WEEK}/config.json", encoding="utf-8"))
RAW, NORM = f"{WEEK}/audio", f"{WEEK}/audio-norm"
os.makedirs(RAW, exist_ok=True); os.makedirs(NORM, exist_ok=True)
VOICES, NARR = CFG["voices"], CFG["narration"]
SETTINGS = {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "speed": 0.7}  # 0.7 = slowest ElevenLabs allows
TARGET_LUFS = -19.0

# --- parse the four dialogue tables ---
text = open(f"{WEEK}/PRODUCTION_PACK.md", encoding="utf-8").read()
convs = []
for block in re.split(r"\n## Conversation ", text)[1:5]:
    rows = re.findall(r"^\| (\d+) \| (\w+) \| (.+?) \| (.+?) \|$", block, re.M)
    lines = [dict(n=int(n), who=w, es=es.replace("**", "").strip(), en=en.strip()) for n, w, es, en in rows]
    convs.append(dict(title=block.splitlines()[0], lines=lines))
assert len(convs) == 4 and all(c["lines"] for c in convs), "could not parse the four dialogue tables"
for c in convs:
    for l in c["lines"]:
        assert l["who"] in VOICES, f"no voice in config.json for speaker {l['who']}"

def tts(voice, text, path, prev=None, nxt=None):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return "cached"
    body = {"text": text, "model_id": "eleven_multilingual_v2", "language_code": "es", "voice_settings": SETTINGS}
    if prev: body["previous_text"] = prev
    if nxt: body["next_text"] = nxt
    for attempt in range(4):
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
            data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                open(path, "wb").write(r.read()); return "ok"
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code == 400 and "language_code" in msg:
                body.pop("language_code", None); continue
            if e.code in (429, 500, 502, 503):
                time.sleep(3 * (attempt + 1)); continue
            sys.exit(f"HTTP {e.code} for {path}: {msg}")
    sys.exit(f"failed after retries: {path}")

def lufs(path):
    out = subprocess.run(["ffmpeg", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.search(r'"input_i" : "(-?[\d.]+)"', out).group(1))

def level(src, dst):
    """Two passes: loudnorm, then an exact gain correction so every line lands at TARGET_LUFS."""
    tmp = dst + ".tmp.mp3"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af",
                    f"adelay=300|300,loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11,atrim=start=0.3,asetpts=PTS-STARTPTS",
                    "-ar", "44100", "-b:a", "192k", tmp], check=True)
    gain = TARGET_LUFS - lufs(tmp)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-af", f"volume={gain:.2f}dB,alimiter=limit=0.89",
                    "-ar", "44100", "-b:a", "192k", dst], check=True)
    os.remove(tmp)

chars = 0
jobs = [(VOICES["Elena"], t, f"n_{k}.mp3", None, None) for k, t in NARR.items()]
for ci, c in enumerate(convs, 1):
    L = c["lines"]
    for i, l in enumerate(L):
        name = f"c{ci}_{l['n']:02d}_{l['who']}.mp3"; l["audio"] = name
        jobs.append((VOICES[l["who"]], l["es"], name, L[i - 1]["es"] if i else None, L[i + 1]["es"] if i + 1 < len(L) else None))
for voice, t, name, prev, nxt in jobs:
    status = tts(voice, t, f"{RAW}/{name}", prev, nxt)
    if status == "ok": chars += len(t)
    level(f"{RAW}/{name}", f"{NORM}/{name}")
    print(name, status)
json.dump(dict(convs=convs, narr=NARR, voices=VOICES), open(f"{NORM}/script.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("new characters sent to ElevenLabs:", chars)
