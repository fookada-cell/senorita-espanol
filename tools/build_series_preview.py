# Builds one private, single-file preview of a whole series (all chapters, switchable at the top).
# Published as a private claude.ai page for the owner to review before anything goes live.
# Usage: python3 tools/build_series_preview.py <repo-root> <series-slug> <output.html>
import json, re, sys, glob, os
repo, slug, out = sys.argv[1], sys.argv[2], sys.argv[3]
css = open(f'{repo}/assets/style.css', encoding='utf-8').read()
js = open(f'{repo}/assets/app.js', encoding='utf-8').read()
shell = open(f'{repo}/{slug}/ep01/index.html', encoding='utf-8').read()
chapters = {}
for p in sorted(glob.glob(f'{repo}/{slug}/ep*/data.json')):
    key = os.path.basename(os.path.dirname(p))
    d = json.load(open(p, encoding='utf-8'))
    if d['next'].get('url'):
        d['next']['url'] = '#' + d['next']['url'].strip('./').strip('/')
    chapters[key] = d
dark = re.search(r'@media \(prefers-color-scheme:dark\)\{:root\{(.*?)\}\}', css, re.S).group(1)
css = css.replace('@media (prefers-color-scheme:dark){:root{', '@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){', 1)
css += '\n:root[data-theme="dark"]{' + dark + '}\nbody{background:var(--bg)}\n'
js = js.replace('fetch("data.json", {cache:"no-cache"}).then(r => { if(!r.ok) throw new Error(r.status); return r.json(); })', 'Promise.resolve(window.SCE_DATA)')
body = shell[shell.index('<body>') + 6: shell.index('<script src="../../assets/app.js"></script>')]
body = body.replace('href="../../"', 'href="https://senoritachristina.netlify.app/"')
nav = ''.join(f'<a class="chap" href="#{k}" data-k="{k}">{int(k[2:])}</a>' for k in chapters)
title = chapters[next(iter(chapters))]['series']
page = f'''<title>{title} Preview</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600;700&display=swap">
<style>{css}
.pv{{max-width:640px;margin:0 auto;padding-block:12px 0;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:10px}}
.pv p{{background:var(--amber-soft);color:var(--ink);border-radius:10px;padding:10px 12px;font-size:13.5px}}
.chaps{{display:grid;grid-template-columns:auto repeat({len(chapters)},minmax(0,1fr));gap:6px;align-items:center}}
.chaps span{{font-size:12.5px;color:var(--muted);font-weight:600;padding-right:4px}}
.chap{{text-align:center;padding:8px 0;border-radius:9px;border:1px solid var(--line);background:var(--surface);color:var(--ink);text-decoration:none;font:700 14px var(--ui)}}
.chap.on{{background:var(--rosa);border-color:var(--rosa);color:var(--surface)}}
</style>
<div class="pv"><p><b>Private preview · draft.</b> Only you can open this page. Nothing here is on the public site yet. Saved words and mistakes carry across all chapters.</p>
<nav class="chaps" aria-label="Chapters"><span>Capítulo</span>{nav}</nav></div>
{body}
<script>
window.SCE_ALL={json.dumps(chapters, ensure_ascii=False)};
(function(){{var k=(location.hash||"").slice(1);if(!window.SCE_ALL[k])k="ep01";window.SCE_DATA=window.SCE_ALL[k];
document.querySelectorAll(".chap").forEach(function(a){{if(a.dataset.k===k)a.classList.add("on");}});
window.addEventListener("hashchange",function(){{location.reload();}});}})();
</script>
<script>{js}</script>
'''
open(out, 'w', encoding='utf-8').write(page)
print('ok', len(chapters), 'chapters,', len(page), 'bytes')
