# Spin-off workflow · Sunday story → "Conversaciones"

> **Read this first** when the owner says "let's do the spin-off for week N" (any assistant: Claude, Grok or another).
> Finished example to copy: `content/spinoffs/semana-01/`.

## What it is
- Every **Sunday** the channel publishes a slow A1–A2 story about **Elena** (e.g. *Mi semana en Madrid*).
- **8 hours later** the spin-off goes out: **4 real conversations** taken from scenes in that story, ~13–15 min.
- Each conversation = title card → **Ronda 1 · Escucha** (bubbles in Spanish + small English) → **Ronda 2 · Repite** (line, then a "Tu turno" pause of 1.3 × the line's length + 1 s, with a progress bar) → **Frases clave** card (6 phrases, 9 s).
- Spanish from **Spain** only (vale, ¿qué te pongo?, vosotros, móvil, ordenador).

## Steps (approval gates marked ✋)

| # | Who | Step | Output |
|---|---|---|---|
| 1 | Owner | Upload the Sunday transcript (.txt) | `content/spinoffs/sources/EPxx-….txt` |
| 2 | Assistant | Check the transcript for errors (e.g. *llevo* → *llego*, *acubierto* → *a cubierto*) and report them before the video is published | message to the owner |
| 3 | Assistant | Pick 4 scenes from the story where Elena would really talk to someone; write 4 dialogues of 12–14 lines that reuse the story's words | `PRODUCTION_PACK.md` dialogue tables |
| 4 | ✋ Owner | Approve the dialogues | |
| 5 | Assistant | Write the image prompts: 4 supporting-character sheets (only for new characters), 8 scenes (A = wide, B = closer, per conversation) and thumbnail art | `PRODUCTION_PACK.md` image section |
| 6 | Owner | Make the images in **Gemini**, attaching both official Elena refs every time; upload originals (full size, not screenshots or PDFs) | `scenes/01A.jpg … 04B.jpg`, `scenes/thumb-art.jpg` |
| 7 | Assistant | Generate voices: `python3 tools/spinoff/voices_elevenlabs.py content/spinoffs/semana-XX` (also levels all voices to −19 LUFS) | `audio/`, `audio-norm/` |
| 8 | ✋ Owner | Listen to the voice preview | |
| 9 | Assistant | Mark positions in `config.json → spots`: each speaker's **mouth** (tail target) and **chest** (bubble centre), image-normalised 0–1. Check with `build_week.py … preview` | `out/preview_*.jpg` |
| 10 | Assistant | Render: `python3 tools/spinoff/build_week.py content/spinoffs/semana-XX` (~10–15 min), then a compressed copy for the phone (`ffmpeg -crf 28`) | `out/<slug>.mp4`, `out/<slug>.srt` |
| 11 | Assistant | Thumbnail: `python3 tools/spinoff/thumbnail.py content/spinoffs/semana-XX` | `thumbnail.jpg` |
| 12 | Assistant | YouTube post: chapter times from `build_week.py … chapters` | `YOUTUBE_POST.md` |
| 13 | ✋ Owner | Watch the full video, then publish 8 h after the Sunday story | |

## Locked decisions (don't change without the owner)

**Elena (visual).** Follow `content/spinoffs/ELENA-LOCK-EP01-EP03.md`. Paste the locked master block **verbatim** and attach **both** official references (`semana-01/style-refs/OFFICIAL-…`) to every image. Style: *Japanese Retro Travel-Poster Anime*. Light olive skin, centre-parted chestnut bob, amber eyes of normal size, ivory ribbed sweater, navy trousers, white trainers, cognac crossbody bag.
**Spin-off exception (approved):** the conversation partner is a second sharp, foreground character. Everyone else stays anonymous and blurred.

**Scene layout.** Elena LEFT, partner RIGHT, facing each other, faces in the upper half. No text in the images; the assistant adds all text.

**Bubbles.** Small cream bubble, **no name labels and no tail/pointer** (owner decision 20 Nov 2026, from EP03 on). It sits on the **speaker's chest**, never over a face, and pops in when the line starts. (`bubble_tail: true` in `config.json` would bring the pointer back; EP01–EP02 were made with it.)

**Voices (ElevenLabs, all Peninsular Spanish, `eleven_multilingual_v2`, speed 0.7).**
| Role | Voice | ID |
|---|---|---|
| **Elena** (always) | Cristina – Empathetic Customer support | `dNjJKg63Fr5AXwIdkATa` |
| Panadero (40s man) | Max | `hFeIFfaOsIqH1YpJJFS0` |
| Javier (30s man) | Marco | `QdeV7TsH9psct2D4UdTk` |
| Frutero (40s man) | Emilio | `ZCh4e9eZSUf41K4cmCEL` |
| Camarera (20s woman) | Violeta | `jQvo2VZEqNV6YXEBghzl` |
For new characters, pick a **Peninsular** voice of the right age and gender from the owner's ElevenLabs library (check the labels via the API). **Always level the volume.** Raw ElevenLabs voices differ by up to 12 dB.

**Narrator (host lines).** The intro, the four conversation titles, "Now... listen and repeat!" and the closing are read **in English by Daniel – Calm, Polished and Direct** (`ZMK5OD2jmsdse3EKE4W5`), the same host as the Sunday videos, but **energetic**: model **`eleven_v4`**, stability **0.0**, similarity 0.75, normal speed (no slowing), with emotion tags in the text, e.g. `[excited] Welcome! [cheerfully] Today, practise real conversations from … ! [warmly] First listen... then repeat each line.` · `[cheerfully] Conversation one: at …!` · `[warmly] Now... listen and repeat!` · `[excited] Well done! [warmly] See you next week!` Set in `config.json` (`narrator_voice`, `narrator_model`, `narrator_settings`, `narration_language: null`). Approved by the owner on 20 Nov 2026 (EP02). EP01 keeps its earlier Daniel version.

**Per-character speed.** Default 0.7. If a voice sounds too slow, raise only that character with `config.json → voice_speeds` (e.g. EP02 Dependienta = 0.9).

**On screen.** A top-left pill shows "Conversación N · Place", a top-right pill shows the round, and the line counter (e.g. "10 / 14") sits bottom-left. The **channel logo** sits bottom-right, stays still, and does a 1.4 s coin-flip spin every 20 s (`content/brand/senorita-christina-logo-transparent.png`).

**Thumbnail** = **identical to that Sunday's thumbnail**, same title (e.g. "Mi semana en / Madrid / (My Week in Madrid)"), the Spain/UK badge top-right and "Señorita Christina Español" as text bottom-left (no logo). The **only** change is the red banner: **"Conversación real · A1–A2"** instead of "Historia lenta · A1–A2". Art: Elena alone on the right (new art each week). Set it in `config.json → thumbnail`. **EP04–06 (Marina) style:** stacked white serif title (Fraunces Black, dark outline) in 3 lines, e.g. "Mi primera clase / de cocina / española", sans channel name. Set `thumbnail.lines`, `title_fill`, `name_font: "sans"` in `config.json`.

**File name rule.** Final video: `Senorita-SUNDAY-Conversation-EPxx.mp4` (EP number = the Sunday episode), set as `slug` in `config.json`. Captions use the same name with `.srt`.

**YouTube title rule.** Sunday: *Learn Spanish with an Easy Story (X)*. Spin-off: ***Speak Spanish with Easy Conversations (X)***, with the same bracket.
**Description.** Same structure as the Sunday description: ⏱️ Chapters → story-style summary → "This is Spanish from Spain…" → 📖 link to the Sunday story → 💡 Pregunta de Hoy 💡 (a question viewers answer by *using* a phrase) → 🔔 subscribe link → hashtags.

## Accounts and tools
- **ElevenLabs:** the owner's paid Creator plan. The key is saved as a network secret for `api.elevenlabs.io` in the cloud environment. Never paste it in chat or commit it. A free-plan key can't use library voices through the API.
- **Images:** Gemini (owner). Ask for the full-size originals; images inside PDFs come out at only 1024 px.
- **vidIQ:** only for research, titles and analytics. It has too few credits for voices.
- Outputs (`out/`, `.work/`) are git-ignored. The final MP4 is ~200 MB, so send a compressed copy for review.

## Week plan
| Week | Sunday story | Spin-off scenes (proposed) |
|---|---|---|
| 1 · 15 Nov | Mi semana en Madrid | panadería · espacio compartido · mercado · cafetería ✅ done |
| 2 · 22 Nov | Mi primer viaje en tren a Toledo | billete de ida y vuelta at Atocha · finding the seat by the window · menú del día on a terrace · mazapán for her mother |
| 3 · 29 Nov | Mi semana de lluvia en Sevilla | asking the way in the rain · museum ticket · café in the patio · photo at the Torre del Oro |
| 4 · 6 Dec | Mi primera clase de cocina española (**Marina**, 27, not Elena; `main_speaker: "Marina"` in config) | arriving at the class · with Laura · flipping the omelette · at the long table |
