/* Señorita Christina Español: chapter engine.
   Every chapter page loads this file and its own ./data.json.
   Content changes go in data.json only. See HANDOFF.md. */
(function(){
  "use strict";
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
  const store = {
    get(k, d){ try{ const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; }catch(e){ return d; } },
    set(k, v){ try{ localStorage.setItem(k, JSON.stringify(v)); }catch(e){} }
  };
  const BANK = "sce-bank", MISS = "sce-mistakes", PREF = "sce-prefs";
  let D, bank = store.get(BANK, []), mistakes = store.get(MISS, []), prefs = store.get(PREF, {en:true, a2only:false});
  let current = null;
  const track = name => { try{ window.sceTrack && window.sceTrack((D.trackPrefix || "") + "ep" + D.episode + "/" + name); }catch(e){} };
  const plain = t => String(t).replace(/\[\[\w+\|([^\]]+)\]\]/g, "$1");
  let player = null;
  function playLine(b){
    try{ if(player){ player.pause(); } }catch(e){}
    if(b.audio){
      try{ player = new Audio(b.audio); player.play().catch(() => speak(plain(b.es), 0.9)); }catch(e){ speak(plain(b.es), 0.9); }
    } else speak(plain(b.es), 0.9);
    track("line-audio");
  }

  function withWords(text){
    return esc(text).replace(/\[\[(\w+)\|([^\]]+)\]\]/g, (m, key, surface) => {
      const w = D.words[key]; if(!w) return surface;
      return '<button class="w' + (w.target ? "" : " bonus") + '" data-w="' + key + '" data-lvl="' + w.lvl + '">' + surface + "</button>";
    });
  }
  const idOf = key => D.seriesSlug + "/ep" + D.episode + "/" + key;

  function renderChapter(){
    const c = $("chapter");
    let h = "<h2>" + esc(D.chapterTitle) + "</h2>";
    D.blocks.forEach((b, i) => {
      const play = D.lineAudio ? '<button class="say" data-i="' + i + '" aria-label="Play this line">▶</button>' : "";
      if(b.t === "n") h += '<p class="n">' + withWords(b.es) + "</p>";
      else if(b.t === "h") h += '<h3 class="conv">' + esc(b.es) + (b.en ? '<small>' + esc(b.en) + "</small>" : "") + "</h3>";
      else if(b.t === "v") h += '<div class="vocab"><b>' + esc(b.es) + "</b><div>" + Object.keys(D.words).filter(k => D.words[k].target).map(k => '<button class="w" data-w="' + k + '" data-lvl="' + esc(D.words[k].lvl) + '">' + esc(D.words[k].w) + "</button>").join("") + "</div></div>";
      else h += '<p class="d' + (b.who ? "" : " solo") + '">' + play + (b.who ? '<span class="who">' + esc(b.who) + "</span>" + (D.lineAudio ? "" : "—") : "") + withWords(b.es) + '<span class="en">' + esc(b.en) + "</span></p>";
    });
    c.innerHTML = h;
    c.querySelectorAll(".say").forEach(btn => btn.addEventListener("click", () => playLine(D.blocks[+btn.dataset.i])));
    c.querySelectorAll(".w").forEach(btn => btn.addEventListener("click", () => openSheet(btn.dataset.w)));
    $("grammar").innerHTML = D.grammar.map(g => '<div class="gram"><b><span class="lvl ' + esc(g.lvl) + '">' + esc(g.lvl) + "</span>" + esc(g.title) + "</b><span>" + g.body + "</span></div>").join("");
    const n = D.next;
    $("next").innerHTML = (n.url ? '<a href="' + esc(n.url) + '" style="color:inherit">' : "") + "<b>" + esc(n.title) + "</b><small>" + esc(n.teaser) + "</small>" + (n.url ? "</a>" : "");
    applyPrefs(); markSaved();
  }
  function applyPrefs(){
    $("chapter").classList.toggle("hide-en", !prefs.en);
    $("chapter").classList.toggle("only-a2", !!prefs.a2only);
    $("opt-en").checked = !!prefs.en; $("opt-a2").checked = !!prefs.a2only;
  }
  function markSaved(){
    const ids = new Set(bank.map(b => b.id));
    document.querySelectorAll(".w").forEach(b => b.classList.toggle("saved", ids.has(idOf(b.dataset.w))));
  }

  function openSheet(key){
    current = key; const w = D.words[key];
    $("s-word").textContent = w.w; $("s-ipa").textContent = w.ipa || "";
    $("s-meta").innerHTML = '<span class="lvl ' + esc(w.lvl) + '">' + esc(w.lvl) + "</span>" + (w.pos ? esc(w.pos) + " · " : "") + "<b>" + esc(w.en) + "</b>";
    $("s-line").hidden = !w.line; if(w.line) $("s-line").textContent = (D.lineLabel || "En el capítulo") + ": «" + w.line + "»" + (w.lineEn ? " (" + w.lineEn + ")" : "");
    $("s-ex").hidden = !w.ex; if(w.ex) $("s-ex").textContent = "Ejemplo: " + w.ex + (w.exEn ? " (" + w.exEn + ")" : "");
    $("s-save").textContent = bank.some(b => b.id === idOf(key)) ? "Guardada ✓" : "+ Mi vocabulario";
    $("s-status").textContent = "";
    $("sheet").hidden = false; $("sheet-bg").hidden = false; $("s-close").focus();
    track("word/" + key);
  }
  function closeSheet(){ $("sheet").hidden = true; $("sheet-bg").hidden = true; if("speechSynthesis" in window) try{ speechSynthesis.cancel(); }catch(e){} }

  let voices = [];
  function loadVoices(){ try{ voices = speechSynthesis.getVoices(); }catch(e){} }
  if("speechSynthesis" in window){ loadVoices(); try{ speechSynthesis.onvoiceschanged = loadVoices; }catch(e){} }
  function speak(text, rate){
    const st = $("s-status");
    if(!("speechSynthesis" in window)){ st.textContent = "Audio isn't available in this browser."; return; }
    try{
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text); u.lang = "es-ES"; u.rate = rate;
      const v = voices.find(v => v.lang === "es-ES") || voices.find(v => /^es[-_]ES/i.test(v.lang));
      if(v) u.voice = v;
      speechSynthesis.speak(u); track("audio/" + (rate < 1 ? "slow" : "normal"));
      st.textContent = v ? "" : "This device has no Spain-Spanish voice, so the accent may differ.";
    }catch(e){ st.textContent = "Audio couldn't play here."; }
  }

  function save(){
    const w = D.words[current], id = idOf(current);
    if(!bank.some(b => b.id === id)){ bank.push({id, w:w.w, en:w.en, lvl:w.lvl, ep:D.episode}); store.set(BANK, bank); }
    $("s-save").textContent = "Guardada ✓"; markSaved(); track("save/" + current);
  }
  function addMistake(tag){ const id = "ep" + D.episode + ":" + tag; if(!mistakes.some(m => m.id === id)){ mistakes.push({id, tag, ep:D.episode}); store.set(MISS, mistakes); } }

  function renderQuiz(){
    const box = $("quiz"); box.innerHTML = ""; let done = 0, right = 0;
    D.quiz.forEach((item, i) => {
      const q = document.createElement("div"); q.className = "q";
      q.innerHTML = '<p><span class="lvl ' + esc(item.lvl) + '">' + esc(item.lvl) + "</span>" + (i + 1) + ". " + esc(item.q) + "</p>";
      item.o.forEach((opt, j) => {
        const b = document.createElement("button"); b.className = "opt"; b.textContent = opt;
        b.addEventListener("click", () => {
          if(q.dataset.done) return; q.dataset.done = "1"; done++;
          if(j === item.a){ b.classList.add("right"); right++; }
          else { b.classList.add("wrong"); q.querySelectorAll(".opt")[item.a].classList.add("right"); addMistake(item.tag); }
          if(done === D.quiz.length){ track("quiz-done/" + right + "-of-" + D.quiz.length); }
          if(done === D.quiz.length) $("quiz-status").textContent = right + " / " + D.quiz.length + " correct. Wrong answers are saved in Mis palabras → Mis errores.";
        });
        q.appendChild(b);
      });
      box.appendChild(q);
    });
    const again = document.createElement("button"); again.className = "btn"; again.textContent = "Repetir el quiz";
    again.addEventListener("click", () => { $("quiz-status").textContent = ""; renderQuiz(); });
    box.appendChild(again);
  }

  let round = 0, score = 0;
  function renderGame(){
    const g = $("game"), keys = Object.keys(D.words).filter(k => D.words[k].target);
    g.innerHTML = "";
    if(round >= 5){
      track("game-done/" + score + "-of-5");
      g.innerHTML = '<div class="prompt">' + score + ' / 5</div><p class="score">Reto completado. Missed words go to Mis errores.</p>';
      const b = document.createElement("button"); b.className = "btn primary"; b.textContent = "Jugar otra vez";
      b.addEventListener("click", () => { round = 0; score = 0; renderGame(); }); g.appendChild(b); return;
    }
    const key = keys[Math.floor(Math.random() * keys.length)], opts = [key];
    while(opts.length < Math.min(4, keys.length)){ const k = keys[Math.floor(Math.random() * keys.length)]; if(!opts.includes(k)) opts.push(k); }
    opts.sort(() => Math.random() - .5);
    g.innerHTML = '<p class="score">Ronda ' + (round + 1) + " de 5 · Puntos: " + score + '</p><p>¿Cómo se dice en español?</p><div class="prompt">' + esc(D.words[key].en) + "</div>";
    const grid = document.createElement("div"); grid.className = "grid2";
    opts.forEach(k => {
      const b = document.createElement("button"); b.className = "opt"; b.textContent = D.words[k].w;
      b.addEventListener("click", () => {
        if(grid.dataset.done) return; grid.dataset.done = "1";
        if(k === key){ b.classList.add("right"); score++; }
        else { b.classList.add("wrong"); grid.children[opts.indexOf(key)].classList.add("right"); addMistake(D.words[key].w); }
        setTimeout(() => { round++; renderGame(); }, 750);
      });
      grid.appendChild(b);
    });
    g.appendChild(grid);
  }

  function renderBank(){
    const b = $("bank"), m = $("mistakes");
    b.innerHTML = bank.length ? bank.map(x => '<div><span><span class="lvl ' + esc(x.lvl) + '">' + esc(x.lvl) + "</span>" + esc(x.w) + "</span><span>" + esc(x.en) + "</span></div>").join("")
      : '<p class="empty">No saved words yet. Tap a word in the chapter, then "+ Mi vocabulario".</p>';
    m.innerHTML = mistakes.length ? mistakes.map(x => "<div><span>" + esc(x.tag) + "</span><span>EP" + x.ep + "</span></div>").join("")
      : '<p class="empty">No mistakes yet. Wrong answers from the quiz and the game land here.</p>';
  }

  function showTab(name){
    document.querySelectorAll(".tab").forEach(t => t.setAttribute("aria-selected", String(t.dataset.tab === name)));
    document.querySelectorAll("[data-panel]").forEach(p => { p.hidden = p.dataset.panel !== name; });
    closeSheet();
    if(name === "bank") renderBank();
  }

  function init(data){
    D = data;
    document.title = "Capítulo " + D.episode + " · " + D.series;
    $("h-series").textContent = D.series; $("h-title").textContent = D.pageTitle || ("Capítulo " + D.episode + ": " + D.chapterTitle);
    if(D.pageTitle) document.title = D.pageTitle + " · " + D.series;
    const targets = Object.values(D.words).filter(w => w.target).length;
    $("h-chips").innerHTML = '<span class="chip">' + esc(D.chipLabel || ("EP" + String(D.episode).padStart(2, "0"))) + '</span><span class="chip t">' + esc(D.levels) + " · " + targets + " " + esc(D.wordLabel || "palabras") + "</span>";
    $("watch").addEventListener("click", () => track("watch-youtube"));
    $("watch").href = D.watch.url; $("watch").textContent = "▶ " + D.watch.label;
    if(D.watch.videoId){
      const f = document.createElement("div"); f.className = "video";
      f.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + encodeURIComponent(D.watch.videoId) + '?rel=0" title="' + esc(D.pageTitle || D.chapterTitle) + '" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen loading="lazy"></iframe>';
      $("watch").before(f);
    }
    (D.extraLinks || []).slice().reverse().forEach(l => { const a = document.createElement("a"); a.className = "watch alt"; a.href = l.url; a.textContent = l.label; $("watch").after(a); });
    renderChapter(); renderQuiz(); renderGame(); renderBank();
    document.querySelectorAll(".tab").forEach(t => t.addEventListener("click", () => showTab(t.dataset.tab)));
    $("opt-en").addEventListener("change", e => { prefs.en = e.target.checked; store.set(PREF, prefs); applyPrefs(); });
    $("opt-a2").addEventListener("change", e => { prefs.a2only = e.target.checked; store.set(PREF, prefs); applyPrefs(); });
    $("s-close").addEventListener("click", closeSheet); $("sheet-bg").addEventListener("click", closeSheet);
    $("s-1x").addEventListener("click", () => speak(D.words[current].say, 1));
    $("s-07x").addEventListener("click", () => speak(D.words[current].say, 0.7));
    $("s-save").addEventListener("click", save);
    $("clear").addEventListener("click", () => { bank = []; mistakes = []; store.set(BANK, bank); store.set(MISS, mistakes); markSaved(); renderBank(); });
    document.addEventListener("keydown", e => { if(e.key === "Escape") closeSheet(); });
  }

  fetch("data.json", {cache:"no-cache"}).then(r => { if(!r.ok) throw new Error(r.status); return r.json(); })
    .then(init)
    .catch(() => { $("chapter").innerHTML = '<p class="n">This chapter could not load. Refresh the page; if it still fails, the chapter file is missing.</p>'; });
})();
