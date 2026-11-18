# HANDOFF: Señorita Christina Español website

> **Read this first.** This file is for any assistant (Claude, Grok or another) or person who takes over this site.
> **Primary maintainer:** Claude. **Backup:** Grok.
> **Rule:** only one assistant works on the site at a time. Before starting, read the **Current status** section. When you finish, update it.

---

## 1. What this site is
- Companion website for the YouTube channel **Señorita Christina Español** (youtube.com/@senioritachristina).
- Each drama episode becomes a **reading chapter** that viewers can interact with:
  - tap a word for meaning, IPA and audio at 1x / 0.7x
  - save words to a personal word bank
  - quiz, quick-fire game and a mistake notebook
- Levels: **A2 and B1** (DELE). Every word and grammar card carries an A2 or B1 badge.
- First series: ***Una novia por accidente*** (EP01–06).
- Business model: free EP01 chapter as a test → later a paid pack (*Volumen 1: A2 → B1*), sold through Payhip or Gumroad. **No payments or logins on this site.**

## 2. Where things live
| Thing | Location |
|---|---|
| Source code | GitHub repo `fookada-cell/senorita-espanol` |
| Hosting | Netlify, auto-deploys from the GitHub `main` branch |
| Live URL | https://senoritachristina.netlify.app (Netlify project `senoritachristina`, team `bible-site`, deploys from GitHub `main`) |
| Visit counting | GoatCounter, dashboard https://senoritachristina.goatcounter.com (owner's login). Set the code in `assets/stats.js` (`GOATCOUNTER_CODE`); empty = off. Events counted: `epN/word/<key>`, `epN/save/<key>`, `epN/audio/normal|slow`, `epN/quiz-done/X-of-3`, `epN/game-done/X-of-5`, `epN/watch-youtube` |
| YouTube links per episode | _TBD: `watch.url` in data.json currently points to the channel page_ |
| Drama videos | Google Drive folder `Una-novia-por-accidente` |
| Transcripts | Google Drive `Una-novia-por-accidente/Transcripts` (plain text, no timestamps) |

## 3. How the site is built (planned structure)
```
/index.html                  Channel home: list of series and chapters
/assets/app.js               Shared chapter engine (popups, audio, quiz, game, word bank)
/assets/style.css            Shared styles (light + dark)
/una-novia-por-accidente/
    ep01/index.html          Chapter page: loads the engine + data.json
    ep01/data.json           ALL episode content: chapter text, words, quiz
    ep02/ ...
/content/                    Locked chapter texts (the approved source for each data.json)
/netlify.toml                Netlify settings (no build step, publish the root)
/HANDOFF.md                  This file
/CHANGELOG.md                One line per change
```
- **Plain static HTML/CSS/JS.** No framework, no build step, no backend.
- Word bank and mistakes are stored in each viewer's browser (localStorage).

## 4. How to do common jobs
- **Add an episode:** copy the `ep01/` folder → rename it → replace `data.json` only. Don't change the engine for content. Then add a link on `/index.html`, and set `next.url` in the previous episode's data.json.
- **data.json format:** `blocks` hold the chapter (`t:"n"` = narration, `t:"d"` = dialogue with `who`/`es`/`en`). Tappable words are written `[[key|text shown]]`, and every key must exist in `words`. `target:true` marks the tested words; the others are bonus words. Levels: A1 / A2 / B1.
- **Fix a typo in a chapter:** edit that episode's `data.json`.
- **Drafts stay private:** build a new chapter on a branch named `epNN-draft`. Netlify only publishes `main`, so the branch isn't live. Show it to the owner with `tools/build_preview.py`, which makes a single-file preview (published as a private claude.ai page). Merge to `main` only after the owner approves.
- **Deploy:** commit and push to `main`. Netlify publishes in 1–2 minutes. **Never drag and drop a folder into Netlify.** That would make the site differ from GitHub.

## 5. Content rules (do not break)
1. **Spanish from Spain (es-ES) only:** móvil, ordenador, vale, vosotros. Never carro, computadora or celular.
2. **Dialogue is locked.** It must match the aired episode word for word. Narration may only describe what is on screen. No new plot.
3. **Level tags** (A2/B1) must be checked against the Instituto Cervantes Plan Curricular. Unchecked tags are marked "to verify".
4. Characters: **Emma Carter**, **Alejandro de Vargas**, **Valeria** (his ex-fiancée and secret wife), **Isabel** (Emma's late mother).
5. Known transcript errors (never copy them): "Sue, esposa" → "Su esposa"; junk lines such as "ご視聴ありがとうございました", "Terima kasih", "Bye".

## 6. Current status
_Update this section every time you finish work._

| Date | Who | State |
|---|---|---|
| 2026-11-18 | Claude | Step 1 done (A2 + B1 level map). Prototype exists as a private claude.ai page. GitHub repo + Netlify setup **not started**. Next: Step 2, the EP01 chapter text for the owner's approval. |
| 2026-11-18 | Claude | Step 2 draft written: `content/EP01_CHAPTER_DRAFT.md`. Narration checked against frames from the EP01 Mon/Wed/Fri videos.  Cast seen on screen: Emma (auburn hair, cream blazer), Alejandro (black hair, charcoal suit), an unnamed assistant (older man, greying hair, navy suit). |

| 2026-11-18 | Claude | EP01 chapter **APPROVED and LOCKED**: `content/EP01_CHAPTER_LOCKED.md`. Prototype page updated with the locked text. Next: GitHub repo + Netlify setup, then build `una-novia-por-accidente/ep01/` from the locked text. |
| 2026-11-18 | Claude | Site v1 built and tested in a phone-size browser: home page + EP01 chapter page (read, word sheet with audio, quiz, game, word bank, mistakes). Committed on `main`. **Netlify not connected yet.** |
| 2026-11-18 | Claude | Netlify connected: project `senoritachristina` publishes from GitHub `main`. It started as **Private** (Netlify access protection); the owner needs to tap **Make public** before sharing with viewers. Next: the owner tests EP01 on their phone. |
| 2026-11-18 | Claude | The owner tested EP01 on their phone: **passed**. Next: Step 3, the free launch test (pinned comment + description link on the EP01 videos, 1–2 weeks), with optional visit counting. |
| 2026-11-18 | Claude | Added GoatCounter counting (`assets/stats.js`), **switched off** until the owner creates an account and sends the code. |
| 2026-11-18 | Claude | GoatCounter **switched on** (code `senoritachristina`). |
| 2026-11-18 | Claude | **Launch test started.** The owner added the site link to the YouTube channel profile, pinned comments on the 4 EP01 Shorts (Shorts links aren't clickable, so the comments point to the profile link and ask for "CAPÍTULO 2"), and put the link in the EP01–06 long-form description. Review around 2026-12-02: GoatCounter week view + count of "CAPÍTULO 2" comments, then decide on EP02–06 and Volume 1. |
| 2026-11-18 | Claude | EP02 chapter drafted on branch `ep02-draft` (**not live**). Private preview sent to the owner. Waiting for approval; open questions are listed in content/EP02_NOTES.md. |

## 7. Decision log
- 2026-11-17: Case 3 model chosen (drama = funnel, readable chapter pack = product).
- 2026-11-18: Launch test runs 1–2 weeks before building EP02–06.
- 2026-11-18: EP01 chapter locked. The assistant character stays unnamed.
- 2026-11-18: Levels = A2 + B1. One Netlify site for this channel only. Claude maintains, Grok is backup. GitHub is the single source of truth.
