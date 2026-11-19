# Spin-off video tools

Builds the weekly "Conversaciones" spin-off (published 8 hours after the Sunday story).

1. `voices_elevenlabs.py`: reads the dialogue tables in `content/spinoffs/semana-XX/PRODUCTION_PACK.md` and makes one MP3 per line with ElevenLabs (Peninsular Spanish cast, speed 0.7). The API key is injected by the cloud environment's network proxy; it is never stored in this repo.
2. `build_week.py`: puts the scene images (Elena LEFT, partner RIGHT), the speech bubbles, the two rounds (Escucha / Repite), the key-phrase cards and the audio together into one 1080p MP4 plus an SRT caption file.

Per-week inputs: 8 scene images `0NA/0NB` + `thumb`, the `SPOTS` table (mouth positions and bubble centre per image), the key phrases, and the generated audio.
Both scripts currently use paths in the session scratchpad; adjust the paths at the top when reusing them.
