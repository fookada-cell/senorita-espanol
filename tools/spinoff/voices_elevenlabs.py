"""Generate one MP3 per dialogue line for the week 1 spin-off with ElevenLabs.
The API key is injected by the network proxy; nothing secret lives here."""
import json, os, re, sys, time, urllib.request, urllib.error

PACK = "/home/user/senorita-espanol/content/spinoffs/semana-01/PRODUCTION_PACK.md"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "el", "semana-01")
os.makedirs(OUT, exist_ok=True)

VOICES = {
    "Elena":    "dNjJKg63Fr5AXwIdkATa",  # Cristina (same as the Sunday videos)
    "Panadero": "hFeIFfaOsIqH1YpJJFS0",  # Max
    "Javier":   "QdeV7TsH9psct2D4UdTk",  # Marco
    "Frutero":  "ZCh4e9eZSUf41K4cmCEL",  # Emilio (peninsular, middle-aged)
    "Camarera": "jQvo2VZEqNV6YXEBghzl",  # Violeta
}

# --- parse the four dialogue tables from the pack ---
text = open(PACK, encoding="utf-8").read()
convs = []
for block in re.split(r"\n## Conversation ", text)[1:5]:
    title = block.splitlines()[0]
    rows = re.findall(r"^\| (\d+) \| (\w+) \| (.+?) \| (.+?) \|$", block, re.M)
    lines = [dict(n=int(n), who=w, es=es.replace("**", "").strip(), en=en.strip()) for n, w, es, en in rows]
    convs.append(dict(title=title, lines=lines))
assert len(convs) == 4 and all(c["lines"] for c in convs), "could not parse dialogues"

# --- narration lines (Elena's voice) ---
NARR = {
    "intro": "Conversaciones de mi semana en Madrid.",
    "c1": "Conversación uno. En la panadería.",
    "c2": "Conversación dos. En el espacio compartido.",
    "c3": "Conversación tres. En el mercado.",
    "c4": "Conversación cuatro. En la cafetería.",
    "repite": "Ahora, escucha y repite.",
    "outro": "¡Muy bien! Hasta la próxima semana.",
}

def tts(voice, text, path, prev=None, nxt=None):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return "cached"
    body = {"text": text, "model_id": "eleven_multilingual_v2", "language_code": "es",
            "voice_settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "speed": 0.7}}
    if prev: body["previous_text"] = prev
    if nxt: body["next_text"] = nxt
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                open(path, "wb").write(r.read()); return "ok"
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]
            if e.code == 400 and "language_code" in msg:   # model may not accept language_code
                body.pop("language_code", None)
                req.data = json.dumps(body).encode(); continue
            if e.code in (429, 500, 502, 503):
                time.sleep(3 * (attempt + 1)); continue
            sys.exit(f"HTTP {e.code} for {path}: {msg}")
    sys.exit(f"failed after retries: {path}")

chars = 0
for k, t in NARR.items():
    print(k, tts(VOICES["Elena"], t, f"{OUT}/n_{k}.mp3")); chars += len(t)
for ci, c in enumerate(convs, 1):
    L = c["lines"]
    for i, l in enumerate(L):
        prev = L[i - 1]["es"] if i else None
        nxt = L[i + 1]["es"] if i + 1 < len(L) else None
        path = f"{OUT}/c{ci}_{l['n']:02d}_{l['who']}.mp3"
        l["audio"] = os.path.basename(path)
        print(path.split("/")[-1], tts(VOICES[l["who"]], l["es"], path, prev, nxt)); chars += len(l["es"])
json.dump(dict(convs=convs, narr=NARR, voices=VOICES), open(f"{OUT}/script.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("characters sent:", chars)
