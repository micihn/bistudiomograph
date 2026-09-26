# BI Studio teaser (by PORTOKO)

A 49-second motion-graphics teaser for the BI Studio Odoo module. It stays on screen the whole time and uses realistic interfaces.

## Story
1. A full-screen MOBA with a painterly generated map, tilt-shift depth of field, glowing spells and a detailed HUD.
2. A macOS notification (dark glass) arrives from Daniel. Mike clicks it, and the screen swipes to the Messages space the way macOS switches Spaces.
3. The chat, unchanged from v2: Daniel asks for the supplier margin report. Mike types "just dump it into AI", deletes it, then types "Ofc, give me a couple hours 👍".
4. Daniel replies first: "Actually we need it in an hour. ASAP please!!". The music stops dead on that bubble, and Mike backspaces in silence.
5. Cut to black: "Build Odoo reports faster.", then "with BI Studio" as the music comes back.
6. The drop lands on the montage: 20 beats of fast, motion-blurred cuts on the beat grid.
   - joining models in the dataset builder
   - choosing Average in the measure picker
   - the result rows cascading in
   - clicking to sort by Margin %
   - the chart as bars, then horizontal bars, then a donut
   - dashboard tiles flying into place
   - report bands stacking
   - the PDF page flipping up with PDF and XLSX
   - a collage pulling back
7. by PORTOKO

## Build
```
pip install numpy scipy pillow imageio-ffmpeg
python3 gen_terrain.py     # assets/terrain.jpg + minimap.jpg
node render.js             # f3/ frames (+ sub3/ sub-frames), cues.json
python3 blur.py            # averages the sub-frames: real motion blur
node fixcuts.js && python3 blur.py   # keeps hard cuts crisp (no shutter straddling a cut)
python3 audio.py           # audio.wav (expects ../mus/132.mp3 and ../sfx/<id>.mp3 from Mixkit)
FF=$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
$FF -framerate 24 -i f3/%05d.jpg -i audio.wav -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest bi_studio_teaser.mp4
```
All timing lives in the `T` object in `teaser.html`. The montage runs on the song's grid (`T.BAR`, `T.BEAT`).

## Part 2: Import / Export (`sequel/`)
This is a 36-second sequel. Another client, Olivia, wants the same supplier margin report fast. Mike answers "Don't worry, I gotchu 😎", then:
1. **Export:** Import / Export, the four chips fill in, Build package gives `bi_studio_export.bistudio`.
2. **Transfer:** the file card flies to Olivia's Odoo.
3. **Import:** Upload, then Validate, Import, and the new dashboard appears.
4. **Payoff:** "Done ✅", then "whoa." The music cuts out on that bubble.
5. **Titles:** "No need to create the same report again and again.", then "BI Studio can help you.", "PORTOKO can help you." and the logo.

The edit is locked to "Funkee Monkeee": video bar k equals song bar k, 2 s per bar.
Build: `node renderS.js && python3 blurS.py && python3 audioS.py`, then encode `fS/` with `audioS.wav`.
