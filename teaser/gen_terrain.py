"""Painterly top-down battlefield for the opening game shot (lit heightmap + trees)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

W, H = 2880, 1620
rs = np.random.default_rng(11)

def vnoise(w, h, cell, seed):
    r = np.random.default_rng(seed)
    g = r.random((h // cell + 3, w // cell + 3))
    im = Image.fromarray((g * 255).astype(np.uint8)).resize(((w // cell + 3) * cell, (h // cell + 3) * cell), Image.BICUBIC)
    return np.asarray(im).astype(np.float32)[:h, :w] / 255

def fbm(w, h, base, octs, seed):
    out = np.zeros((h, w), np.float32); amp = 1; tot = 0
    for o in range(octs):
        out += amp * vnoise(w, h, max(2, base >> o), seed + o); tot += amp; amp *= .5
    return out / tot

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# river: meandering diagonal top-left -> bottom-right
rx = xx; ry = 260 + xx * 0.42 + 70 * np.sin(xx / 330) + 40 * np.sin(xx / 120 + 1)
d_river = np.abs(yy - ry)
# lane: bottom-left -> top-right, slightly curved
lx0, ly0, lx1, ly1 = 120, 1560, 2760, 80
t = np.clip(((xx - lx0) * (lx1 - lx0) + (yy - ly0) * (ly1 - ly0)) / ((lx1 - lx0) ** 2 + (ly1 - ly0) ** 2), 0, 1)
px = lx0 + t * (lx1 - lx0) + 60 * np.sin(t * 7); py = ly0 + t * (ly1 - ly0)
d_lane = np.hypot(xx - px, yy - py)

n1 = fbm(W, H, 256, 6, 1); n2 = fbm(W, H, 64, 4, 9); n3 = fbm(W, H, 16, 3, 21)
height = n1 * 1.0 + n2 * .22 + n3 * .03
river_w = 95 + 25 * n2
bank = np.clip(1 - (d_river - river_w) / 60, 0, 1)
water = (d_river < river_w).astype(np.float32)
water_s = ndimage.gaussian_filter(water, 6)
lane_w = 70 + 15 * n2
lane = np.clip(1 - (d_lane - lane_w) / 22, 0, 1)
height = height - water_s * .35 - lane * .06 + bank * 0
height = ndimage.gaussian_filter(height, 1.2)

# colours
grass_a = np.array([62, 92, 44]); grass_b = np.array([96, 124, 56]); grass_c = np.array([46, 70, 38])
col = grass_a[None, None] * (1 - n2[..., None]) + grass_b[None, None] * n2[..., None]
col = col * (1 - (n3[..., None] > .62) * .25) + grass_c[None, None] * ((n3[..., None] > .62) * .25)
dirt = np.array([128, 104, 72]) * (0.85 + .3 * n3[..., None])
col = col * (1 - lane[..., None]) + dirt * lane[..., None]
sand = np.array([150, 136, 98])
col = col * (1 - bank[..., None] * (1 - water[..., None])) + sand * (bank[..., None] * (1 - water[..., None]))
deep = np.array([22, 70, 88]); shallow = np.array([48, 120, 128])
wd = np.clip((river_w - d_river) / river_w, 0, 1)[..., None]
wcol = shallow * (1 - wd) + deep * wd
col = col * (1 - water_s[..., None]) + wcol * water_s[..., None]

# lighting from height
gy, gx = np.gradient(height * 260)
nz = 1 / np.sqrt(gx ** 2 + gy ** 2 + 1)
L = np.array([-.55, -.6, .58]); L /= np.linalg.norm(L)
lam = np.clip((-gx * L[0] - gy * L[1] + L[2]) * nz, 0, 1)[..., None]
ao = np.clip(1 - (ndimage.gaussian_filter(height, 25) - height) * 2.2, .55, 1.1)[..., None]
light = (np.array([1.08, 1.0, .86]) * lam + np.array([.38, .44, .56]) * (1 - lam) * .9)
col = col * light * ao
# water sparkle
spark = (vnoise(W, H, 6, 77) > .93) * water * (n2 > .5)
col += spark[..., None] * np.array([90, 120, 120])

img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))

# trees
forest = fbm(W, H, 180, 3, 5)
dr = ImageDraw.Draw(img, 'RGBA')
cands = rs.random((9000, 2)) * [W, H]
trees = []
for x, y in cands:
    xi, yi = int(x), int(y)
    if d_lane[yi, xi] < lane_w[yi, xi] + 55 or d_river[yi, xi] < river_w[yi, xi] + 70: continue
    if forest[yi, xi] < .52: continue
    trees.append((x, y, 14 + rs.random() * 20 * (0.6 + forest[yi, xi])))
trees.sort(key=lambda a: a[1])
shadow = Image.new('L', (W, H), 0); sd = ImageDraw.Draw(shadow)
for x, y, s in trees:
    sd.ellipse([x - s + s * .5, y - s * .6 + s * .55, x + s + s * .5, y + s * .6 + s * .55], fill=150)
shadow = shadow.filter(ImageFilter.GaussianBlur(6))
arr = np.asarray(img).astype(np.float32) * (1 - np.asarray(shadow)[..., None] / 255 * .55)
img = Image.fromarray(arr.astype(np.uint8)); dr = ImageDraw.Draw(img, 'RGBA')
for x, y, s in trees:
    base = np.array([34, 60, 30]) * (0.8 + .4 * rs.random())
    for k, (f, off) in enumerate([(1.0, 0), (.78, -.18), (.52, -.32), (.28, -.42)]):
        c = np.clip(base * (1 + k * .32) + np.array([k * 6, k * 10, 0]), 0, 255).astype(int)
        r = s * f; ox = oy = s * off
        dr.ellipse([x - r + ox, y - r + oy, x + r + ox, y + r + oy], fill=(*c, 255))
# towers / shrines with glow
glow = Image.new('RGB', (W, H), 0); gd = ImageDraw.Draw(glow)
for (tx, ty, c) in [(700, 1120, (90, 220, 120)), (1980, 520, (240, 90, 70))]:
    dr.ellipse([tx - 46, ty - 20, tx + 46, ty + 30], fill=(0, 0, 0, 90))
    dr.rounded_rectangle([tx - 30, ty - 44, tx + 30, ty + 16], 8, fill=(88, 84, 78, 255))
    dr.rounded_rectangle([tx - 30, ty - 44, tx + 30, ty - 30], 6, fill=(120, 116, 104, 255))
    dr.ellipse([tx - 12, ty - 34, tx + 12, ty - 10], fill=(*c, 255))
    gd.ellipse([tx - 60, ty - 70, tx + 60, ty + 30], fill=c)
glow = glow.filter(ImageFilter.GaussianBlur(40))
arr = np.asarray(img).astype(np.float32) + np.asarray(glow).astype(np.float32) * .55
# grade: teal shadows / warm highlights, slight contrast
lum = arr.mean(2, keepdims=True) / 255
arr = arr * (0.92 + .16 * lum) + (1 - lum) * np.array([-4, 4, 10]) + lum * np.array([8, 4, -6])
Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save('assets/terrain.jpg', quality=92)
Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((288, 162), Image.LANCZOS).save('assets/minimap.jpg', quality=90)
print('trees', len(trees))
