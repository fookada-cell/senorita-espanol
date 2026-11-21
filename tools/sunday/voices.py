"""Generate every recording of a Sunday main episode once (ElevenLabs eleven_v4, normal speed),
then slow it to 0.7x with pitch preserved and level it to -19 LUFS.
Usage: python3 tools/sunday/voices.py content/sunday/epXX
Reads <ep>/lines.json ({id: {voice: "es"|"en", text}}) and <ep>/config.json ({voices: {es, en}, tempo, skip}).
Writes <ep>/audio-raw/<id>.mp3 (cached, with a .voice stamp) and <ep>/audio/<id>.wav.
The API key is injected by the network proxy."""
import json, os, re, subprocess, sys, time, urllib.request, urllib.error
EP = os.path.abspath(sys.argv[1])
L = json.load(open(f"{EP}/lines.json", encoding="utf-8"))
C = json.load(open(f"{EP}/config.json", encoding="utf-8"))
RAW, OUT = f"{EP}/audio-raw", f"{EP}/audio"; os.makedirs(RAW, exist_ok=True); os.makedirs(OUT, exist_ok=True)
TEMPO = C.get("tempo", 0.7)
def tts(voice, text, path):
    body = {"text": text, "model_id": "eleven_v4", "voice_settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.15, "speed": 1.0}}
    for a in range(4):
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
              data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r: open(path, "wb").write(r.read()); return
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503): time.sleep(4 * (a + 1)); continue
            sys.exit(f"HTTP {e.code} {path}: {e.read()[:300]}")
    sys.exit(f"failed {path}")
def lufs(p):
    o = subprocess.run(["ffmpeg", "-i", p, "-af", "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.search(r'"input_i" : "(-?[\d.]+)"', o).group(1))
chars = 0
for k, l in L.items():
    if k in C.get("skip", []): continue
    raw, wav, stamp = f"{RAW}/{k}.mp3", f"{OUT}/{k}.wav", f"{RAW}/{k}.voice"
    voice = C["voices"][l["voice"]]
    fresh = False
    if not (os.path.exists(raw) and os.path.getsize(raw) > 1000 and os.path.exists(stamp) and open(stamp).read() == voice):
        tts(voice, l["text"], raw); open(stamp, "w").write(voice); chars += len(l["text"]); fresh = True
    if fresh or not os.path.exists(wav):
        slow = wav + ".slow.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-af", f"atempo={TEMPO}", "-ar", "44100", "-ac", "1", slow], check=True)
        g = -19.0 - lufs(slow)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", slow, "-af", f"volume={g:.2f}dB,alimiter=limit=0.89", "-ar", "44100", "-ac", "1", wav], check=True)
        os.remove(slow)
    print(k, "ok", flush=True)
print("new characters sent:", chars)
