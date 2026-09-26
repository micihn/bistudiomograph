"""Soundtrack v3: 'Hazy After Hours' (Mixkit, free license) edited on its bar grid,
plus Mixkit UI sound effects placed on the exact video cues."""
import json, subprocess, numpy as np
from scipy.io import wavfile
import imageio_ffmpeg

SR = 44100
FF = imageio_ffmpeg.get_ffmpeg_exe()
D = json.load(open('cues.json')); T, CUES = D['T'], D['cues']
N = int((T['total'] + .5) * SR)
MUS = '../mus'; SFX = '../sfx'
rs = np.random.default_rng(3)

def load(path):
    raw = subprocess.run([FF, '-loglevel', 'error', '-i', path, '-f', 's16le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.int16).reshape(-1, 2).astype(np.float32) / 32768
def fade(x, a=.005, b=.005):
    x = x.copy(); na, nb = int(a * SR), int(b * SR)
    if na: x[:na] *= np.linspace(0, 1, na)[:, None]
    if nb: x[-nb:] *= np.linspace(1, 0, nb)[:, None]
    return x
def norm(x, pk=1.0): return x / (np.abs(x).max() + 1e-9) * pk
mix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32)
def put(x, t, g=1.0, pan=0.0, bus=None):
    b = mix if bus is None else bus; i = int(round(t * SR))
    if i < 0: x = x[-i:]; i = 0
    x = x[:max(0, len(b) - i)]
    l, r = np.sqrt(.5 * (1 - pan)) * 1.414, np.sqrt(.5 * (1 + pan)) * 1.414
    b[i:i + len(x), 0] += x[:, 0] * g * l; b[i:i + len(x), 1] += x[:, 1] * g * r
def snap(t): return np.ceil(t * 24 - 1e-6) / 24

# ---------------------------------------------------------------- music edit
song = load(f'{MUS}/132.mp3')
PH, BAR = 0.02, T['BAR']
def bar(k, n=1):
    a = int((PH + k * BAR) * SR); b = int((PH + (k + n) * BAR) * SR)
    return song[a:b]
# story bed: bars 0-5 then 2-5, hard stop on the "ASAP" bubble
bed = np.concatenate([fade(bar(k), .004, .004) for k in [0, 1, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3]])
t0, t1 = T['D'], T['b3']
bed = bed[:int((t1 - t0) * SR)]
bed[:int(.4 * SR)] *= np.linspace(0, 1, int(.4 * SR))[:, None]
bed[-int(.012 * SR):] *= np.linspace(1, 0, int(.012 * SR))[:, None]
put(bed, t0, .42, bus=mus)
# re-entry one bar before the drop, then the drop lands on the first montage frame
t_back = T['M'] - BAR
tail_bars = int(np.ceil((T['total'] - T['M']) / BAR)) + 1
body = bar(7, 1 + tail_bars)
body[:int(.06 * SR)] *= np.linspace(0, 1, int(.06 * SR))[:, None]
put(body, t_back, 1.0, bus=mus)
# fade the music out under the logo
fo0 = int((T['total'] - 2.2) * SR); mus[fo0:] *= np.linspace(1, 0, len(mus) - fo0)[:, None] ** 1.5
# duck the music a touch under the title before the drop
tb0, tb1 = int(t_back * SR), int(T['M'] * SR); mus[tb0:tb1] *= np.linspace(.55, .8, tb1 - tb0)[:, None]

# ---------------------------------------------------------------- sfx
S = lambda i: load(f'{SFX}/{i}.mp3')
def first_hit(x, pre=.004, dur=.5, thr=.25):
    m = np.abs(x).mean(1); i = int(np.argmax(m > m.max() * thr)); a = max(0, i - int(pre * SR))
    return fade(x[a:a + int(dur * SR)], .002, .03)
def slices(x, min_gap=.12, dur=.11):
    m = np.abs(x).mean(1); env = np.convolve(m, np.ones(64) / 64, 'same'); thr = np.percentile(env, 98) * .3
    on = np.nonzero((env[1:] > thr) & (env[:-1] <= thr))[0]; keep = []; last = -1e9
    for o in on:
        if o - last > .06 * SR: keep.append(o)
        last = o
    out = []
    for a, b in zip(keep, keep[1:]):
        if (b - a) > min_gap * SR: out.append(norm(fade(x[max(0, a - 150):a + int(dur * SR)], .002, .03), .6))
    return out
keys = slices(S(2537)) + slices(S(2531)) + slices(S(2536))
bsp = slices(S(2539)) or keys
print('keys', len(keys), 'backspace', len(bsp))
hard = norm(first_hit(S(2542), dur=.2), .7)
click = norm(first_hit(S(1113), dur=.25), .8)
uiclick = norm(first_hit(S(2573), dur=.35), .8)
notif = norm(first_hit(S(2354), dur=1.2, thr=.1), .8)
recv = norm(first_hit(S(2356), dur=1.0, thr=.1), .8)
swipe = norm(S(166), .8)
cutsnd = [norm(S(3115), .8), norm(S(175), .8), norm(S(3005), .8), norm(S(2618), .8)]
pop = norm(first_hit(S(2358), dur=.6, thr=.1), .8)
spell = norm(S(1463), .8); spell2 = norm(S(2350), .8)
rclick = norm(first_hit(S(2997), dur=.15), .8)

ci = 0
for c in CUES:
    t, s = c['t'], c['s']
    if s in ('key', 'space'): put(keys[rs.integers(len(keys))], t - .004, .22 if s == 'key' else .26, rs.uniform(-.12, .12))
    elif s == 'backspace': put(bsp[rs.integers(len(bsp))], t - .004, .2)
    elif s == 'cmdA': put(hard, t - .08, .16); put(keys[0], t, .2)
    elif s == 'delete': put(hard, t, .26)
    elif s == 'rclick': put(rclick, t, .12, .15)
    elif s == 'spell': put(spell if t < 2 else spell2, t - .05, .08, .2)
    elif s == 'notify': put(notif, t, .30, .35)
    elif s == 'click': put(click, t, .30, .3)
    elif s == 'swipe': put(swipe, snap(t), .22)
    elif s == 'recv': put(recv, t, .26, -.1)
    elif s == 'recv_asap': put(recv, t, .30, -.1)
    elif s == 'cut':
        put(cutsnd[ci % len(cutsnd)], snap(t) - .02, .11, (-.25 if ci % 2 else .25)); ci += 1
    elif s == 'uiclick': put(uiclick, t, .22)
    elif s == 'pop': put(pop, t, .12)

# game bed: river/forest ambience + distant creep clashes, gone once Mike swipes away
amb = load(f'{SFX}/61.mp3'); gl = int(T['D'] * SR)
amb = amb[int(2 * SR):int(2 * SR) + gl].copy()
env = np.ones(len(amb)); s0 = int(T['swipe'] * SR); env[s0:] = np.linspace(1, 0, len(amb) - s0) ** 2
env[:int(.3 * SR)] = np.linspace(0, 1, int(.3 * SR))
put(norm(amb, .9) * env[:, None], 0, .55)
clash = [norm(first_hit(S(i), dur=.6), .8) for i in (2764, 2763, 2765, 2160)]
for k, tt in enumerate(np.arange(.15, T['swipe'] - .1, .37)):
    put(clash[k % 4], tt + rs.uniform(-.06, .06), .09 + .05 * rs.random(), rs.uniform(-.5, .1))
lspell = norm(S(873), .8); poof = norm(first_hit(S(3082), dur=1.2, thr=.1), .8)
for st in (1.2, 2.8): put(lspell, st - .03, .16, .1); put(poof, st + .28, .14, .25)
mix += mus
# ---------------------------------------------------------------- master: loudness + look-ahead limiter
from scipy.ndimage import maximum_filter1d, uniform_filter1d
seg = mix[int(T['M'] * SR):int(T['END'] * SR)]
mix *= 10 ** (-15 / 20) / np.sqrt((seg ** 2).mean())
ceil = .89
g = np.minimum(1, ceil / (maximum_filter1d(np.abs(mix).max(1), size=int(.006 * SR)) + 1e-9))
g = uniform_filter1d(-maximum_filter1d(-g, size=int(.015 * SR)), size=int(.005 * SR))
mix = np.clip(mix * g[:, None], -ceil, ceil)[:int(T['total'] * SR)]
wavfile.write('audio.wav', SR, (mix * 32767).astype(np.int16))
print('ok', len(mix) / SR)
