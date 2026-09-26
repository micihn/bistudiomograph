"""Sequel soundtrack: 'Funkee Monkeee' (Michael Ramir C., Mixkit free license) on its own
bar grid (video bar k = song bar k), with Mixkit UI sounds on the exact cues."""
import json, subprocess, numpy as np
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d, uniform_filter1d
import imageio_ffmpeg

SR = 44100; FF = imageio_ffmpeg.get_ffmpeg_exe()
D = json.load(open('cuesS.json')); T, CUES = D['T'], D['cues']
N = int((T['total'] + .5) * SR); MUS = '../mus'; SFX = '../sfx'
rs = np.random.default_rng(5)

def load(p):
    raw = subprocess.run([FF, '-loglevel', 'error', '-i', p, '-f', 's16le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True).stdout
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

# ------------------------------------------------ music
song = load(f'{MUS}/1140.mp3'); PH, BAR = 0.995, 2.0
def seg(t0, t1):   # song time -> clip
    return song[int(t0 * SR):int(t1 * SR)]
stop = T['whoa']; back = T['TT']
a = seg(PH, PH + stop); a = fade(a, .01, .012)
put(a, 0, 1.0, bus=mus)
b = seg(PH + back, PH + T['total'] + .5); b = fade(b, .004, .01)
put(b, back, 1.0, bus=mus)
fo = int((T['total'] - 2.5) * SR); mus[fo:] *= np.linspace(1, 0, len(mus) - fo)[:, None] ** 1.6
# sit the music a little lower under the chat/UI story, full on the titles
d0, d1 = 0, int(back * SR); mus[d0:d1] *= .62

# ------------------------------------------------ sfx
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
    return [norm(fade(x[max(0, a - 150):a + int(dur * SR)], .002, .03), .6) for a, b in zip(keep, keep[1:]) if (b - a) > min_gap * SR]
keys = slices(S(2537)) + slices(S(2531))
H = lambda i, d=.5, thr=.25: norm(first_hit(S(i), dur=d, thr=thr), .8)
snd = {'notify': (H(2354, 1.2, .1), .28), 'click': (H(1113, .25), .26), 'swipe': (norm(S(166), .8), .2),
       'recv': (H(2356, 1.0, .1), .26), 'send': (H(2358, .6, .1), .16), 'pop': (H(2364, .4), .12),
       'chip': (H(1120, .4), .14), 'tick': (H(2573, .35), .14), 'lift': (norm(S(3005), .8), .22),
       'whip': (norm(S(3115), .8), .22), 'land': (H(2364, .4), .2), 'check': (H(1120, .4), .12),
       'toast': (H(2356, 1.0, .1), .2), 'whoosh': (norm(S(175), .8), .14), 'cut': (norm(S(2618), .8), .1)}
for c in CUES:
    t, s = c['t'], c['s']
    if s in ('key', 'space'): put(keys[rs.integers(len(keys))], t - .004, .2, rs.uniform(-.1, .1))
    elif s in snd:
        x, g = snd[s]
        put(x, snap(t) if s in ('swipe', 'whip', 'cut', 'whoosh') else t, g, rs.uniform(-.2, .2))

mix += mus
seg_ = mix[int(back * SR):int(T['END'] * SR)]
mix *= 10 ** (-15 / 20) / np.sqrt((seg_ ** 2).mean())
ceil = .89
g = np.minimum(1, ceil / (maximum_filter1d(np.abs(mix).max(1), size=int(.006 * SR)) + 1e-9))
g = uniform_filter1d(-maximum_filter1d(-g, size=int(.015 * SR)), size=int(.005 * SR))
mix = np.clip(mix * g[:, None], -ceil, ceil)[:int(T['total'] * SR)]
wavfile.write('audioS.wav', SR, (mix * 32767).astype(np.int16))
print('ok', len(mix) / SR)
