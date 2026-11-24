# Small Story Español: website sources
- `ep01..04-story.json`: the EP01–04 stories as aired, cleaned from the automatic transcript. Translations for sentences the video didn't translate were added by Claude.
- `import/`: copies of the Sunday EP05–08 scripts and the spin-off scripts and production packs, taken on 2026-11-24 from the video-build chat's branch `claude/video-build-request-85al3n`.
- Rebuild every page: `python3 tools/build_small_story.py`. YouTube IDs, titles and characters are set at the top of that file (`EPS`).
- Known YouTube links (2026-11-24): story EP01 8Snx4RInMRY, story EP02 AnBuvDNf9Hg, spin-off EP01 NHUq5zUHrHM (assumed; titled "Can You Order a Coffee in Spanish?"). All others point to the playlist until their IDs are added.
