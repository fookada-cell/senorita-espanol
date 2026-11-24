# One private, single-file preview of the whole Small Story section (16 pages, switchable at the top).
# Published as a private claude.ai page for the owner. Recorded audio can't be bundled into one file,
# so in the preview every ▶ uses the browser's Spanish voice; the live site plays the real voices.
# Usage: python3 tools/build_small_story_preview.py <output.html>
import json, re, sys
out = sys.argv[1]
css = open("assets/style.css", encoding="utf-8").read()
js = open("assets/app.js", encoding="utf-8").read()
shell = open("una-novia-por-accidente/ep01/index.html", encoding="utf-8").read()
pages = {}
for n in range(1, 9):
    s = json.load(open(f"small-story/ep0{n}/data.json", encoding="utf-8"))
    c = json.load(open(f"small-story/ep0{n}/conversaciones/data.json", encoding="utf-8"))
    for l in s["extraLinks"]: l["url"] = f"#s{n}c"
    s["next"]["url"] = f"#s{n}c"
    for l in c["extraLinks"]: l["url"] = f"#s{n}"
    c["next"]["url"] = f"#s{n+1}" if n < 8 else "#s1"
    for d in (s, c):
        d["watch"]["videoId"] = ""   # other sites can't be embedded in the preview; the link still works
        for b in d["blocks"]: b.pop("audio", None)
    pages[f"s{n}"] = s; pages[f"s{n}c"] = c
dark = re.search(r'@media \(prefers-color-scheme:dark\)\{:root\{(.*?)\}\}', css, re.S).group(1)
css = css.replace('@media (prefers-color-scheme:dark){:root{', '@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){', 1)
css += '\n:root[data-theme="dark"]{' + dark + '}\nbody{background:var(--bg)}\n'
js = js.replace('fetch("data.json", {cache:"no-cache"}).then(r => { if(!r.ok) throw new Error(r.status); return r.json(); })', 'Promise.resolve(window.SCE_DATA)')
body = shell[shell.index('<body>') + 6: shell.index('<script src="../../assets/app.js"></script>')]
body = body.replace('href="../../"', 'href="https://senoritachristina.netlify.app/"')
nav = "".join(f'<div class="wkn"><span>{n}</span><a class="chap" href="#s{n}" data-k="s{n}">📖</a><a class="chap" href="#s{n}c" data-k="s{n}c">💬</a></div>' for n in range(1, 9))
page = f'''<title>Small Story Preview</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600;700&display=swap">
<style>{css}
.pv{{max-width:640px;margin:0 auto;padding-block:12px 0;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:10px}}
.pv p{{background:var(--amber-soft);color:var(--ink);border-radius:10px;padding:10px 12px;font-size:13.5px}}
.wks{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}}
.wkn{{display:grid;grid-template-columns:auto 1fr 1fr;gap:4px;align-items:center;font:700 13px var(--ui);color:var(--muted)}}
.chap{{text-align:center;padding:6px 0;border-radius:8px;border:1px solid var(--line);background:var(--surface);text-decoration:none;font-size:14px}}
.chap.on{{background:var(--rosa);border-color:var(--rosa)}}
</style>
<div class="pv"><p><b>Private preview · Small Story Español.</b> Only you can open this. Pick a week: 📖 story or 💬 conversations. In this preview ▶ uses your browser's Spanish voice; the website plays the real voices from your videos.</p>
<nav class="wks" aria-label="Weeks">{nav}</nav></div>
{body}
<script>
window.SCE_ALL={json.dumps(pages, ensure_ascii=False)};
(function(){{var k=(location.hash||"").slice(1);if(!window.SCE_ALL[k])k="s1";window.SCE_DATA=window.SCE_ALL[k];
document.querySelectorAll(".chap").forEach(function(a){{if(a.dataset.k===k)a.classList.add("on");}});
window.addEventListener("hashchange",function(){{location.reload();}});}})();
</script>
<script>{js}</script>
'''
open(out, "w", encoding="utf-8").write(page)
print("ok", len(pages), "pages", len(page), "bytes")
