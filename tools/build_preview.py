# Builds a single-file private preview of a chapter (for review on claude.ai before publishing).
# Usage: python3 tools/build_preview.py <repo-root> <episode, e.g. 02> <output.html>
import json,sys,re
repo,ep,out=sys.argv[1],sys.argv[2],sys.argv[3]
css=open(f'{repo}/assets/style.css',encoding='utf-8').read()
js=open(f'{repo}/assets/app.js',encoding='utf-8').read()
data=open(f'{repo}/una-novia-por-accidente/ep{ep}/data.json',encoding='utf-8').read()
html=open(f'{repo}/una-novia-por-accidente/ep{ep}/index.html',encoding='utf-8').read()
# theme: honour the viewer's explicit choice too
dark=re.search(r'@media \(prefers-color-scheme:dark\)\{:root\{(.*?)\}\}',css,re.S).group(1)
css=css.replace('@media (prefers-color-scheme:dark){:root{','@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){',1)
css+='\n:root[data-theme="dark"]{'+dark+'}\nbody{background:var(--bg)}\n'
js=js.replace('fetch("data.json", {cache:"no-cache"}).then(r => { if(!r.ok) throw new Error(r.status); return r.json(); })','Promise.resolve(window.SCE_DATA)')
body=html[html.index('<body>')+6:html.index('<script src="../../assets/app.js"></script>')]
body=body.replace('href="../../"','href="https://senoritachristina.netlify.app/"')
title=re.search(r'<title>(.*?)</title>',html).group(1)
page=f'''<title>EP{ep} Private Preview</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600;700&display=swap">
<style>{css}
.preview-note{{max-width:640px;margin:0 auto;padding-block:12px 0;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}}
.preview-note p{{background:var(--amber-soft);color:var(--ink);border-radius:10px;padding:10px 12px;font-size:13.5px}}
</style>
<div class="preview-note"><p><b>Private preview · draft.</b> Only you can open this page. It is not on the public site yet. Your saved words here are separate from the live site.</p></div>
{body}
<script>window.SCE_DATA={data};</script>
<script>{js}</script>
'''
open(out,'w',encoding='utf-8').write(page)
print('ok',len(page))
