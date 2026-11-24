# Sunday main video · Format 2 (EP09 onwards)

Decided 2026-11-24 after the ListenES comparison (`REFERENCE-ListenES-structure.md`): apply the 🔴 High and 🟡 Medium items from EP09.
EP01–EP08 stay as they are.

## How to switch it on
`config.json` → `"format": 2`. Everything else is the same as EP05–EP08 (`tools/sunday/voices.py`, then `tools/sunday/build_episode.py`).

## What changes
| Item | Format 1 (EP01–08) | Format 2 (EP09+) |
|---|---|---|
| Listen 2 repeat gap | 0.4 s | Spanish line → **pause = line length + 1 s** with a "Repite · Your turn" pill → English |
| 3-step roadmap | spoken only | **card 1·2·3** at the intro (all), before listen 2 (step 2 lit, 1 ticked), before listen 3 |
| Questions | 5 s pause | same pause + "Answer in the comments · Responde en los comentarios" on each card |
| Vocabulary | 16 single words | **25–35 phrases in story order** (V01…V35), Spanish → repeat pause → English, counter "n/N" |

## Script template lines (lines.json, host voice)
- **M001** (intro): "Welcome! In this lesson, you will hear one easy story in Spanish from Spain, three times: first with Spanish subtitles, then with an English translation, and finally without subtitles. Then answer three questions and review DELE A2 vocabulary. Today, <one-sentence story hook>."
- **M002**: "Now listen again, with translation. After each Spanish line, try to repeat it in the pause. Then you will hear the English."
- **M003**: "Finally, listen one last time, without subtitles. Then try to answer the questions."
- **M004**: "Here are three questions. Pause the video and answer them in the comments!"
- **M005**: "Now, useful phrases from the story, in order. Listen, repeat, then hear the English."
- Questions: open questions (¿Por qué…? ¿Dónde…? ¿Qué…?), not only yes/no.
- Vocabulary: phrases, not single nouns (*pedir un café con leche*, *pagar con tarjeta*, *volver a casa*), all DELE A2 level, in the order they appear.

## Length
About +5 min for listen 2 and +1–2 min for vocabulary → ~28–31 min (ListenES: 25–31 min). Test render of EP05 in format 2: 28:54 with 16 words.

## Still open (not in format 2)
- Story title read before listen 1 (🟢 low).
- PDF guide / membership offer (business decision).
- Twist endings + punchline titles, grammar-theme stories (content choice for scripts).
