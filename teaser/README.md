# BI Studio teaser (by PORTOKO)

A ~55 s motion-graphics teaser for the BI Studio Odoo module, built as code:

- `teaser.html` holds the whole film. `render(t)` draws any moment deterministically, and all timing lives in the `T` object.
- `render.js` steps through the timeline at 30 fps in headless Chromium and pipes the frames to ffmpeg. It also writes `cues.json` (every keystroke, ping and cut).
- `audio.py` synthesizes all sound (SFX, game bed, lo-fi chat bed, 120 bpm montage beat, end chord) from `cues.json`, so picture and sound stay in sync.

## Story beats
1. Mike is in a MOBA match, late at night.
2. A client ping arrives. "Hey Mike, we need a new report."
3. The ask: best supplier margin, average margin %, qty sold. "like… you get it???"
4. Mike types the honest answer (export it all and dump it into AI), then deletes it.
5. He types "Ofc, give me a couple hours". The client replies first: "Need it in an hour. ASAP please!!". The music tape-stops, and he slowly backspaces.
6. Cut to black. "Build Odoo reports faster." / "with BI Studio"
7. 120 bpm montage: dataset joins, then question builder, then real top-N sort, then chart types, then dashboard with a global filter, then a banded PDF/XLSX report, then real screenshots.
8. "12 minutes later": "Done ✅". "wait… already?? 😳"
9. by PORTOKO

## Rebuild
```
pip install numpy scipy imageio-ffmpeg
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())") node render.js   # video_only.mp4 + cues.json
python3 audio.py                                                                                  # audio.wav
$FF -i video_only.mp4 -i audio.wav -c:v copy -c:a aac -b:a 192k -shortest bi_studio_teaser.mp4
node stills.js 12 40.8                                                                            # preview single frames
```
Fonts: Inter (SIL OFL). The game footage is an original stylized MOBA, not Dota assets.
