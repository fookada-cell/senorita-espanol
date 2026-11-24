# Builds the "Small Story Español" section (Sunday stories + conversation spin-offs).
# Sources (all in this repo):
#   content/small-story/ep01..04-story.json   cleaned from the aired videos (EP01-04)
#   content/small-story/import/epNN-lines.json  Sunday scripts EP05-08 (from the video-build chat)
#   content/small-story/import/semana-NN-script.json + -PACK.md  spin-off dialogues + key phrases
#   small-story/epNN/conversaciones/audio/*.mp3  real ElevenLabs voices for each spin-off line
# Output: small-story/index.html, small-story/epNN/{index.html,data.json},
#         small-story/epNN/conversaciones/{index.html,data.json}
# Usage: python3 tools/build_small_story.py   (run from the repo root)
import json, re, os, unicodedata, random

SERIES = "Small Story Español"
PLAYLIST = "https://youtube.com/playlist?list=PLKwKE3jX8DWzjYAM_4OSd71BynvgZ9guG"
EPS = {
  1: dict(title="Mi semana en Madrid", en="My Week in Madrid", who="Elena", story_vid="8Snx4RInMRY", conv_vid="NHUq5zUHrHM"),
  2: dict(title="Mi primer viaje en tren a Toledo", en="My First Train Trip to Toledo", who="Elena", story_vid="AnBuvDNf9Hg"),
  3: dict(title="Mi semana de lluvia en Sevilla", en="My Rainy Week in Seville", who="Elena"),
  4: dict(title="Mi primera clase de cocina española", en="My First Spanish Cooking Class", who="Marina"),
  5: dict(title="De compras en el mercado", en="Shopping at a Madrid Market", who="Marina", dele=True),
  6: dict(title="Una cena para Laura", en="Dinner for Laura at Home", who="Marina", dele=True),
  7: dict(title="Mi primera vez conduciendo en Madrid", en="My First Time Driving in Madrid", who="Mateo", dele=True),
  8: dict(title="Mi primera clase de pintura en Málaga", en="My First Painting Class in Málaga", who="Mateo", dele=True),
}

def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

ARTICLES = ("el ", "la ", "los ", "las ", "un ", "una ")
def core(es):
    e = es.strip(" ¡!¿?.")
    for a in ARTICLES:
        if norm(e).startswith(a): return e[len(a):]
    return e

def find_span(text, phrase):
    """Return (start, end) of phrase (or a verb/plural form of it) in text, else None."""
    t = norm(text); p = norm(core(phrase))
    cands = [p]
    words = p.split()
    if len(words) == 1:
        w = words[0]
        if w.endswith("se") and len(w) > 5: w = w[:-2]
        if w.endswith(("ar", "er", "ir")) and len(w) > 4: cands.append(w[:-2])  # verb stem: desayun-
        cands += [p + "s", p + "es"]
    for c in cands:
        m = re.search(r"(?<![a-zñ])" + re.escape(c) + r"[a-zñ]*", t)
        if m and (c == p or m.end() - m.start() <= len(c) + 4):
            end = m.end() if m.end() - m.start() <= len(c) + 4 else m.start() + len(c)
            return m.start(), end
    return None

def tag(lines, words):
    """Wrap the first occurrence of each word in [[key|surface]]; record its line."""
    for key, w in words.items():
        for L in lines:
            if "[[" in L["es"] and key in L["es"]: break
            plain = re.sub(r"\[\[\w+\|([^\]]+)\]\]", r"\1", L["es"])
            if plain != L["es"]: continue  # keep it simple: one tagged word per line
            sp = find_span(L["es"], w["src"])
            if sp:
                a, b = sp
                L["es"] = L["es"][:a] + "[[" + key + "|" + L["es"][a:b] + "]]" + L["es"][b:]
                w["line"] = plain; w["lineEn"] = L.get("en", "")
                break

def slug(s):
    s = norm(s); s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s[:24] or "w"

def make_quiz(words, n, seed):
    rnd = random.Random(seed)
    keys = [k for k, w in words.items() if w.get("target") and w.get("en") and w.get("exact", True)]
    if len(keys) < 3: keys = [k for k, w in words.items() if w.get("target") and w.get("en") and w["en"] != "(key phrase)"]
    rnd.shuffle(keys); out = []
    for k in keys[:n]:
        if len(set(words[o]["en"] for o in keys) - {words[k]["en"]}) < 2: break
        others = sorted(set(words[o]["en"] for o in keys if words[o]["en"] != words[k]["en"]))
        opts = rnd.sample(others, 2) + [words[k]["en"]]; rnd.shuffle(opts)
        out.append({"lvl": words[k]["lvl"], "q": "¿Qué significa «" + words[k]["w"] + "»?", "o": opts,
                    "a": opts.index(words[k]["en"]), "tag": words[k]["w"]})
    return out

def page_html(depth, title):
    up = "../" * depth
    tpl = open("una-novia-por-accidente/ep01/index.html", encoding="utf-8").read()
    tpl = tpl.replace("../../", up)
    tpl = re.sub(r"<title>.*?</title>", "<title>" + title + "</title>", tpl)
    tpl = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="' + title + ' · Small Story Español: lee, escucha y practica español de España.">', tpl)
    tpl = tpl.replace('<h1 id="h-title">Capítulo 1</h1>', '<h1 id="h-title">' + title + '</h1>')
    tpl = tpl.replace("Highlight A1–A2 words only", "Show English under every line" if False else "Highlight A1–A2 words only")
    return tpl

def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(obj, str): f.write(obj)
        else: json.dump(obj, f, ensure_ascii=False, indent=1); f.write("\n")

def story_source(n):
    if n <= 4:
        d = json.load(open(f"content/small-story/ep0{n}-story.json", encoding="utf-8"))
        return d["lines"], [(v["es"], v["en"]) for v in d["vocab"]], [(s["es"], s["en"]) for s in d["slang"]], d["questions"]
    d = json.load(open(f"content/small-story/import/ep0{n}-lines.json", encoding="utf-8"))
    lines = []
    for k in sorted([k for k in d if re.fullmatch(r"F\d+", k)], key=lambda k: int(k[1:])):
        lines.append({"es": d[k]["text"], "en": d.get("M%03d" % (int(k[1:]) + 10), {}).get("text", "")})
    vocab = [(d[k]["text"], d[k + "e"]["text"]) for k in sorted(d) if re.fullmatch(r"V\d+", k) and k + "e" in d]
    slang = [(d[k]["text"], d[k + "e"]["text"]) for k in sorted(d) if re.fullmatch(r"S\d+", k) and k + "e" in d]
    qs = [d[k]["text"] for k in sorted(d) if re.fullmatch(r"Q\d+", k)]
    return lines, vocab, slang, qs

def build_story(n):
    E = EPS[n]; lines, vocab, slang, qs = story_source(n)
    lvl = "A2"
    words = {}
    for es, en in vocab:
        k = slug(core(es)); words[k] = {"target": True, "lvl": lvl, "w": es, "en": en, "say": es, "src": es}
    for es, en in slang:
        k = "x_" + slug(core(es)); words[k] = {"target": True, "lvl": "España", "w": es, "en": en, "say": es, "src": es, "exact": False}
    L = [dict(l) for l in lines]
    tag(L, words)
    for w in words.values(): w.pop("src", None)
    blocks = [{"t": "d", "who": "", "es": l["es"], "en": l["en"]} for l in L]
    blocks.append({"t": "v", "es": "Vocabulario del episodio"})
    grammar = [{"lvl": "España", "title": es, "body": en} for es, en in slang]
    if qs: grammar.append({"lvl": "Preguntas", "title": "Preguntas del vídeo", "body": " · ".join(qs) + "<br><small>Answer in Spanish in the YouTube comments.</small>"})
    E2 = EPS.get(n + 1)
    data = {
      "series": SERIES, "seriesSlug": "small-story", "trackPrefix": "ss-", "episode": n,
      "pageTitle": f"Semana {n}: {E['title']}", "chapterTitle": E["title"], "chipLabel": f"Historia · Semana {n}",
      "levels": "DELE A2" if E.get("dele") else "A1–A2", "wordLabel": "palabras", "lineAudio": True,
      "lineLabel": "En la historia",
      "watch": {"label": "Ver la historia en YouTube" if E.get("story_vid") else "Ver la lista en YouTube",
                "url": ("https://youtu.be/" + E["story_vid"]) if E.get("story_vid") else PLAYLIST, "videoId": E.get("story_vid", "")},
      "extraLinks": [{"label": "💬 Practica las conversaciones de esta semana →", "url": "conversaciones/"}],
      "blocks": blocks, "words": words, "grammar": grammar,
      "quiz": make_quiz(words, 3, n),
      "next": {"title": f"Ahora: Conversaciones · Semana {n}", "teaser": f"Speak like {E['who']}: 4 short dialogues with real voices.", "url": "conversaciones/"},
    }
    write(f"small-story/ep0{n}/data.json", data)
    write(f"small-story/ep0{n}/index.html", page_html(2, f"Semana {n}: {E['title']}"))
    return data

def pack_phrases(n):
    md = open(f"content/small-story/import/semana-0{n}-PACK.md", encoding="utf-8").read()
    out = []
    for m in re.finditer(r"\*\*Key phrases:\*\*\s*(.+)", md):
        out.append([p.strip(" *.") for p in m.group(1).split("·") if p.strip(" *.")])
    return out

def build_conv(n):
    E = EPS[n]
    sc = json.load(open(f"content/small-story/import/semana-0{n}-script.json", encoding="utf-8"))
    phrases = pack_phrases(n)
    words = {}; blocks = []
    for ci, conv in enumerate(sc["convs"]):
        title = re.sub(r"^\d+\s*·\s*", "", conv["title"])
        blocks.append({"t": "h", "es": f"{ci+1} · {title}", "en": ""})
        L = [{"es": l["es"], "en": l["en"], "who": l["who"], "audio": "audio/" + l["audio"]} for l in conv["lines"]]
        cw = {}
        for p in (phrases[ci] if ci < len(phrases) else []):
            k = f"c{ci+1}_" + slug(core(p))
            cw[k] = {"target": True, "lvl": "A2", "w": p, "say": p, "src": p}
        tag(L, cw)
        for k, w in cw.items():
            w.pop("src", None)
            line = w.get("line", ""); len_ = w.get("lineEn", "")
            # narrow to the sentence that holds the phrase when ES and EN have the same number of sentences
            ss = [x for x in re.split(r"(?<=[.!?])\s+", line) if x]; ee = [x for x in re.split(r"(?<=[.!?])\s+", len_) if x]
            if len(ss) > 1 and len(ss) == len(ee):
                for a, b in zip(ss, ee):
                    if find_span(a, w["w"]): line, len_ = a, b; break
            exact = bool(line) and len(norm(core(w["w"]))) >= 0.6 * len(norm(line.strip(" ¡!¿?.")))
            w["en"] = len_ if line else ""
            if line: w["lineEn"] = len_
            w["exact"] = exact
            if exact: w.pop("lineEn", None)
            if not w["en"]: w["en"] = "(key phrase)"
        words.update(cw)
        blocks += [{"t": "d", **l} for l in L]
    blocks.append({"t": "v", "es": "Frases clave de la semana"})
    data = {
      "series": SERIES, "seriesSlug": "small-story", "trackPrefix": "ss-conv-", "episode": n,
      "pageTitle": f"Conversaciones · Semana {n}", "chapterTitle": E["title"], "chipLabel": f"Conversaciones · Semana {n}",
      "levels": "DELE A2" if E.get("dele") else "A1–A2", "wordLabel": "frases clave", "lineAudio": True,
      "lineLabel": "En la conversación",
      "watch": {"label": "Ver las conversaciones en YouTube" if E.get("conv_vid") else "Ver la lista en YouTube",
                "url": ("https://youtu.be/" + E["conv_vid"]) if E.get("conv_vid") else PLAYLIST, "videoId": E.get("conv_vid", "")},
      "extraLinks": [{"label": f"📖 Lee la historia: {E['title']}", "url": "../"}],
      "blocks": blocks, "words": words,
      "grammar": [{"lvl": "Cómo practicar", "title": "Escucha y repite", "body": "Tap ▶ to hear each line in the real voices from the video. Then pause and say it out loud yourself. Turn off <em>English for each line</em> to test yourself."}],
      "quiz": make_quiz(words, 3, 100 + n),
      "next": ({"title": f"Semana {n+1}: {EPS[n+1]['title']}", "teaser": "Next week's story.", "url": f"../../ep0{n+1}/"} if n + 1 in EPS
               else {"title": "Fin de la temporada", "teaser": "More stories every Sunday on YouTube.", "url": "../../"}),
    }
    write(f"small-story/ep0{n}/conversaciones/data.json", data)
    write(f"small-story/ep0{n}/conversaciones/index.html", page_html(3, f"Conversaciones · Semana {n}"))
    return data

def build_index():
    rows = []
    for n, E in EPS.items():
        rows.append(f'''<div class="wk"><div class="wk-h"><span class="chip">Semana {n}</span><span class="chip t">{"DELE A2" if E.get("dele") else "A1–A2"}</span><span class="who">{E["who"]}</span></div>
<b>{E["title"]}</b><small>{E["en"]}</small>
<div class="wk-l"><a href="ep0{n}/">📖 Historia</a><a href="ep0{n}/conversaciones/">💬 Conversaciones</a></div></div>''')
    tpl = open("index.html", encoding="utf-8").read()
    head = tpl[:tpl.index("<body>")]
    head = re.sub(r"<title>.*?</title>", "<title>Small Story Español · Señorita Christina Español</title>", head).replace('href="assets/', 'href="../assets/').replace('src="assets/', 'src="../assets/')
    head = head.replace("</style>", ".wk{display:grid;gap:4px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px}.wk-h{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.wk .who{font-size:13px;color:var(--muted);margin-left:auto}.wk b{font-family:var(--display);font-size:18px}.wk small{color:var(--muted)}.wk-l{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}.wk-l a{padding:8px 12px;border-radius:9px;border:1px solid var(--line);background:var(--bg);color:var(--ink);text-decoration:none;font-weight:600;font-size:14px}</style>")
    body = f'''<body>
<div class="wrap">
  <div class="brand"><a href="../">Señorita Christina Español</a><span>Small Story Español</span></div>
  <header style="display:grid;gap:10px">
    <span class="chip" style="justify-self:start">Cada domingo · Español de España</span>
    <h1>Small Story Español</h1>
    <p class="lede">Every Sunday, a slow, easy story in Spain Spanish. Then practise the same week as real conversations, with the voices from the video. Read along, tap words, save them and test yourself.</p>
    <a class="watch" href="{PLAYLIST}" target="_blank" rel="noopener">▶ The playlist on YouTube</a>
  </header>
  <section style="display:grid;gap:10px">{"".join(rows)}</section>
  <footer>Señorita Christina Español · Your saved words stay on your device.</footer>
</div>
</body>
</html>
'''
    write("small-story/index.html", head + body)

if __name__ == "__main__":
    for n in EPS:
        s = build_story(n); c = build_conv(n)
        nt = sum(1 for w in s["words"].values() if "line" in w); tt = len(s["words"])
        nc = sum(1 for w in c["words"].values() if "line" in w); tc = len(c["words"])
        print(f"Semana {n}: story {len(s['blocks'])} blocks, words tagged {nt}/{tt}, quiz {len(s['quiz'])} | conv {len(c['blocks'])} blocks, phrases tagged {nc}/{tc}, quiz {len(c['quiz'])}")
    build_index()
    print("index ok")
