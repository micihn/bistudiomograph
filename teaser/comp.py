"""Builds the live-action frames: two hands close-ups and the green-screen monitor
shot with our screen content tracked into it."""
import json, glob, os, subprocess, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from scipy.signal import savgol_filter
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
FOOT = '../foot'
T = json.load(open('cues.json'))['T']
FPS = 24
os.makedirs('frames', exist_ok=True)

def extract(src, start, n, outdir):
    os.makedirs(outdir, exist_ok=True)
    subprocess.run([FF, '-loglevel', 'error', '-y', '-ss', str(start), '-i', src, '-frames:v', str(n),
                    '-vf', 'fps=24,scale=1920:1080', f'{outdir}/%04d.png'], check=True)
    return sorted(glob.glob(f'{outdir}/*.png'))

def grade(im):
    return im  # footage already graded

def put_range(t0, t1, src, start, tag):
    i0, i1 = round(t0 * FPS), round(t1 * FPS)
    fs = extract(src, start, i1 - i0, f'/tmp/_ex_{tag}')
    for k, i in enumerate(range(i0, i1)):
        Image.open(fs[min(k, len(fs) - 1)]).convert('RGB').save(f'frames/{i:05d}.jpg', quality=95)

# ---- plain footage ranges ----
put_range(T['A'], T['B'], f'{FOOT}/h_51609.mp4', 1.0, 'a')
put_range(T['B'], T['C'], f'{FOOT}/h_51603.mp4', 2.0, 'b')
put_range(T['Ein'], T['Eout'], f'{FOOT}/h_51609.mp4', 5.0, 'e')

# ---- green screen comp ----
src = sorted(glob.glob(f'{FOOT}/src51602/*.png'))   # extracted from 3.0 s
if not src:
    src = extract(f'{FOOT}/g_51602.mp4', 3.0, 204, f'{FOOT}/src51602')
C = np.array(json.load(open('corners_raw.json')))
Cs = savgol_filter(C, 11, 2, axis=0)

def persp_coeffs(dst, w, h):
    # coefficients mapping output (dst quad) -> input rect (texture)
    srcpts = [(0, 0), (w, 0), (w, h), (0, h)]
    A, B = [], []
    for (x, y), (u, v) in zip(dst, srcpts):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float))

def expand(q, px):
    c = q.mean(0); d = q - c
    return c + d * (1 + px / np.linalg.norm(d, axis=1, keepdims=True))

rs = np.random.default_rng(1)
i0, i1 = round(T['C'] * FPS), round(T['D'] * FPS)
for k, i in enumerate(range(i0, i1)):
    fr = np.asarray(Image.open(src[k]).convert('RGB')).astype(np.float32)
    tex = Image.open(f'tex/{i:05d}.png').convert('RGB')
    q = expand(Cs[k], 7)
    co = persp_coeffs(q, 1920, 1080)
    warped = tex.transform((1920, 1080), Image.PERSPECTIVE, tuple(co), Image.BICUBIC)
    warped = warped.filter(ImageFilter.GaussianBlur(1.1))
    W = np.asarray(warped).astype(np.float32) * 0.9
    r, g, b = fr[..., 0], fr[..., 1], fr[..., 2]
    key = np.clip((g - np.maximum(r, b) + 4) / 30, 0, 1)
    # only inside (slightly grown) screen quad
    qm = Image.new('L', (1920, 1080), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(qm).polygon([tuple(p) for p in expand(Cs[k], 12)], fill=255)
    qm = np.asarray(qm).astype(np.float32) / 255
    key *= qm
    key = ndimage.gaussian_filter(key, 0.8)[..., None]
    # despill everything near the screen
    spill = np.minimum(g, np.maximum(r, b) * 0.95)
    fr[..., 1] = np.where(ndimage.binary_dilation(qm > 0, iterations=10), spill, g)
    W += rs.normal(0, 3.0, W.shape).astype(np.float32)
    out = fr * (1 - key) + W * key
    # screen light spilling onto the room
    glow = ndimage.gaussian_filter(W * key, (45, 45, 0))
    out = out + glow * 0.16
    out = np.clip(out, 0, 255).astype(np.uint8)
    im = Image.fromarray(out).crop((0, 100, 1280, 820)).resize((1920, 1080), Image.LANCZOS)
    im.save(f'frames/{i:05d}.jpg', quality=95)
    if k % 20 == 0: print('comp', k, i1 - i0)
print('ok')
