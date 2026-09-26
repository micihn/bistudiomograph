# BI Studio teaser (by PORTOKO)

A 56-second teaser for the BI Studio Odoo module. It uses live-action footage, a desktop chat and real Odoo screens, with a soundtrack built only from real CC0 recordings.

## Story
1. Real footage: hands on a gaming keyboard, then over the shoulder to the monitor. The green screen is replaced with a game, and a message banner arrives from Daniel (the client).
2. Mike clicks it and the Messages window opens. Nothing zooms; the screen is shown flat and still.
3. Daniel explains the report he wants. Mike types the honest answer (export everything and dump it into AI), with an intercut to real hands typing. He selects it all and deletes it.
4. He types "Ofc, give me a couple hours 👍". Daniel replies first: "Actually we need it in an hour. ASAP please!!". Mike slowly backspaces.
5. A light switch clicks and the screen cuts to black. "Build Odoo reports faster." then "with BI Studio", each on a soft piano chord.
6. Real product flow, played as a screen recording with a cursor:
   - group a question by vendor
   - sort by Margin %
   - show it as a bar chart
   - sort a dashboard tile
   - run the Vendor Margin Comparison report to PDF
7. by PORTOKO

Every cut has its own small real sound (pen click, marble, glass tap, coin, switch), and every mouse click has a real click. The music is marimba, contrabass pizzicato and piano samples at 100 bpm. See CREDITS.md.

## Files
- `teaser.html`: all screen content and timing (`T`), plus the monitor texture (`renderTexture`).
- `render.js`: renders HTML frames and monitor textures, and writes `cues.json`.
- `comp.py`: adds the footage, tracks the green screen (`corners_raw.json`), keys it and composites the texture.
- `audio.py`: sequences the real samples on the cue times, including keystrokes sliced from a real keyboard recording.

## Rebuild
```
pip install numpy scipy pillow imageio-ffmpeg
node render.js            # frames/ + tex/ + cues.json
python3 comp.py           # footage + green-screen frames into frames/
python3 audio.py          # audio.wav (expects ../snd/wav, ../vcsl, ../vsco; see CREDITS.md)
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
$FF -framerate 24 -i frames/%05d.jpg -i audio.wav -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac -shortest bi_studio_teaser.mp4
```
