"""Soundtrack built only from real recordings (CC0):
- Freesound CC0: keyboard, mouse, pen, marble, glass, coins, light switch, room tone, gaming clicks
- VCSL (CC0): Steinway B piano, marimba, glockenspiel
- VSCO 2 CE (CC0): solo contrabass pizzicato
No oscillators or synthesis: every sound is a sample, only placed, trimmed, faded, mixed
and (for melody notes between sampled pitches) resampled."""
import json, re, glob, numpy as np
from scipy.io import wavfile

SR = 44100
D = json.load(open('cues.json')); T, CUES = D['T'], D['cues']
N = int((T['total'] + 1.0) * SR)
SND = '../snd/wav'
VCSL = '../vcsl'; VSCO = '../vsco'
rs = np.random.default_rng(7)

def load(p):
    sr, x = wavfile.read(p)
    if x.dtype == np.int16: x = x.astype(np.float32) / 32768
    elif x.dtype == np.int32: x = x.astype(np.float32) / 2147483648
    elif x.dtype == np.uint8: x = (x.astype(np.float32) - 128) / 128
    else: x = x.astype(np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    x = x[:, :2]
    if sr != SR:
        n = int(len(x) * SR / sr); idx = np.linspace(0, len(x) - 1, n)
        x = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], 1)
    return x
def fs(i): return load(f'{SND}/fs_{i}.wav')
def trim(x, t0, t1=None, fade=.01):
    a = int(t0 * SR); b = len(x) if t1 is None else int(t1 * SR)
    y = x[a:b].copy(); f = int(fade * SR)
    if f and len(y) > 2 * f:
        y[:f] *= np.linspace(0, 1, f)[:, None]; y[-f:] *= np.linspace(1, 0, f)[:, None]
    return y
def first_hit(x, pre=.004, dur=.6, thr=.3):
    m = np.abs(x).mean(1); i = int(np.argmax(m > m.max() * thr))
    return trim(x, max(0, i / SR - pre), min(len(x) / SR, i / SR + dur), .004)
def norm(x, peak=1.0): return x / (np.abs(x).max() + 1e-9) * peak
def pitch(x, semis):
    if abs(semis) < 1e-3: return x
    r = 2 ** (semis / 12); n = int(len(x) / r); idx = np.arange(n) * r
    return np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], 1)

mix = np.zeros((N, 2), np.float32)
def put(x, t, g=1.0, pan=0.0, bus=None):
    b = mix if bus is None else bus
    i = int(round(t * SR))
    if i < 0: x = x[-i:]; i = 0
    x = x[:max(0, len(b) - i)]
    l, r = np.sqrt(.5 * (1 - pan)) * 1.414, np.sqrt(.5 * (1 + pan)) * 1.414
    b[i:i + len(x), 0] += x[:, 0] * g * l; b[i:i + len(x), 1] += x[:, 1] * g * r

# ------------------------------------------------ keystrokes sliced from a real keyboard
kb = fs(546167); m = np.abs(kb).mean(1)
env = np.convolve(m, np.ones(64) / 64, 'same'); thr = np.percentile(env, 99) * .35
on = np.nonzero((env[1:] > thr) & (env[:-1] <= thr))[0]
keep = []; last = -1e9
for o in on:
    if o - last > .07 * SR: keep.append(o)
    last = o
keys = []
for a, b in zip(keep, keep[1:]):
    if (b - a) > .16 * SR:
        seg = trim(kb, a / SR - .004, a / SR + .12, .004)
        keys.append(seg)
pk = np.array([np.abs(k).max() for k in keys])
order = np.argsort(pk)
light = [norm(keys[i], .5) for i in order[len(order) // 4: len(order) * 3 // 4]]
heavy = [norm(keys[i], .7) for i in order[-12:]]
print('keystrokes', len(keys), 'light', len(light), 'heavy', len(heavy))
def key(kind='key'):
    pool = heavy if kind in ('space', 'backspace', 'cmdA') else light
    return pool[rs.integers(len(pool))]

# ------------------------------------------------ one-shots
S = {
 'mouse': [norm(first_hit(fs(678248), dur=.25), .8), norm(first_hit(fs(213004), dur=.25), .8), norm(first_hit(fs(534104), dur=.2), .8)],
 'pen_in': norm(first_hit(fs(321484), dur=.3), .6),
 'pen': norm(first_hit(fs(323744), dur=.12), .6),
 'marble': norm(first_hit(fs(334222), dur=.5), .6),
 'glass_tap': norm(first_hit(fs(667275), dur=1.2, thr=.5), .6),
 'bottle_tap': norm(first_hit(fs(610392), dur=.5, thr=.5), .6),
 'clink': norm(first_hit(fs(573160), dur=1.5), .6),
 'clink2': norm(first_hit(fs(573157), dur=1.2), .6),
 'coin': norm(first_hit(fs(842173), dur=.8), .5),
 'switch_off': norm(first_hit(fs(440499), dur=.4), .9),
 'switch_on': norm(first_hit(fs(788643), dur=.2), .6),
}

# ------------------------------------------------ instruments
def note_num(n):
    m = re.match(r'([A-G])(#?)(-?\d)', n); pc = 'C D EF G A B'.index(m[1]) + (1 if m[2] else 0)
    return 12 * (int(m[3]) + 1) + pc
def bank(files, rx, offset):
    out = {}
    for f in files:
        mm = re.search(rx, f.split('/')[-1])
        if mm: out[note_num(mm[1]) + offset] = f
    return out
PIANO = bank(glob.glob(f'{VCSL}/Chordophones/Zithers/Grand Piano, Steinway B/Sus/*vl2*.wav'), r'Close_([A-G]#?\d)_', 0)
MAR = bank(glob.glob(f'{VCSL}/Idiophones/Struck Idiophones/Marimba/*_med_*.wav'), r'Outrigger_([A-G]#?\d)_', 12)
GLK = bank(glob.glob(f'{VCSL}/Idiophones/Struck Idiophones/Glockenspiel/glock_soft_*.wav'), r'soft_([A-G]#?\d)_', 12)
BAS = bank(glob.glob(f'{VSCO}/Strings/Solo Contrabass/Pizz/*_v1_rr1.wav'), r'Pizz_([A-G]#?\d)_', 12)
cache = {}
def inst(b, midi, dur=None):
    k = min(b, key=lambda n: abs(n - midi)); ck = (id(b), k)
    if ck not in cache: cache[ck] = load(b[k])
    x = pitch(cache[ck], midi - k)
    i = int(np.argmax(np.abs(x).mean(1) > np.abs(x).max() * .05)); x = x[max(0, i - 40):]
    if dur: x = trim(x, 0, min(dur, len(x) / SR), .03)
    return x
nm = lambda s: note_num(s)

# ------------------------------------------------ ambience (0 .. switch)
room = fs(466123); room = norm(room, 1.0)
amb = np.tile(room, (int(np.ceil(T['black'] * SR / len(room))) + 1, 1))[:int((T['black'] + 1.2) * SR)]
amb[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))[:, None] ** 3
put(amb, 0, .018)
game = fs(125377)
gd = norm(trim(game, 2.0, 2.0 + T['D'], .2), .9)
gd[-int(.25 * SR):] *= np.linspace(1, 0, int(.25 * SR))[:, None]
gain = np.ones(len(gd)); c0 = int((T['C']) * SR); gain[c0:] = .55
put(gd * gain[:, None], 0, .5)

# ------------------------------------------------ cue sounds
for c in CUES:
    t, s = c['t'], c['s']
    if s.startswith('cut') or s in ('switch', 'end', 'title1', 'title2'):
        t = np.ceil(t * 24 - 1e-6) / 24   # land on the first frame of the new shot
    if s in ('key', 'space'): put(key(s), t, .28 if s == 'key' else .33, rs.uniform(-.15, .15))
    elif s == 'backspace': put(key('backspace'), t, .45)
    elif s == 'backspace_soft': put(key('backspace'), t, .3)
    elif s == 'cmdA': put(key('cmdA'), t - .07, .5); put(key('key'), t, .5)
    elif s == 'mouse': put(S['mouse'][rs.integers(3)], t, 0.180, .1)
    elif s == 'cut_hands': put(S['pen'], t, 0.200)
    elif s == 'cut_monitor': put(S['marble'], t, 0.180)
    elif s == 'notify':
        put(inst(GLK, nm('G6')), t, .22, .3); put(inst(GLK, nm('C7')), t + .11, .2, .3)
    elif s == 'cut_chat': pass  # the mouse click is the cut
    elif s == 'recv': put(S['bottle_tap'], t, 0.300, -.1)
    elif s == 'recv2': put(S['clink'], t, 0.270, -.1)
    elif s == 'cut_in': put(S['pen_in'], t, 0.140)
    elif s == 'cut_out': put(S['pen'], t, 0.140)
    elif s == 'switch': put(S['switch_off'], t, 0.360)
    elif s == 'title1':
        for n_, d in (('A2', 0), ('E3', .0), ('C4', .0), ('E4', 0)): put(inst(PIANO, nm(n_)), t + d, .12)
    elif s == 'title2':
        for n_, d in (('F2', 0), ('C3', 0), ('A3', 0), ('C4', 0), ('E4', 0)): put(inst(PIANO, nm(n_)), t + d, .12)
    elif s == 'cut_p1': put(S['marble'], t, 0.200)
    elif s == 'cut_p2': put(S['glass_tap'], t, 0.175)
    elif s == 'cut_p3': put(S['coin'], t, 0.175)
    elif s == 'cut_p4': put(S['switch_on'], t, 0.200)
    elif s == 'cut_p5': put(S['clink2'], t, 0.150)
    elif s == 'cut_pdf': put(S['pen_in'], t, 0.180)
    elif s == 'end':
        for n_ in ('C2', 'G2', 'E3', 'C4', 'G4', 'E5'): put(inst(PIANO, nm(n_)), t, .13)
        put(inst(GLK, nm('G6')), t + .6, .16)

# ------------------------------------------------ music: marimba + pizz bass + piano, 100 bpm
B = .6; G0 = T['G']
prog = [('A', [57, 60, 64]), ('F', [53, 57, 60]), ('C', [48, 52, 55]), ('G', [55, 59, 62]), ('A', [57, 60, 64]), ('F', [53, 57, 60])]
roots = {'A': 45, 'F': 41, 'C': 48, 'G': 43}
music = np.zeros_like(mix)
for bar, (r, ch) in enumerate(prog):
    beats = 4 if bar < 5 else 2
    t0 = G0 + bar * 4 * B
    # piano chord, soft, on the bar
    for n_ in ch: put(inst(PIANO, n_), t0, .14, 0, music)
    # pizzicato bass on 1 and 3
    put(inst(BAS, roots[r] - 12, 1.2), t0, .55, 0, music)
    if beats == 4: put(inst(BAS, roots[r] - 12 + 7, 1.0), t0 + 2 * B, .45, 0, music)
    # marimba ostinato in eighths
    pat = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[2] + 12, ch[1] + 12, ch[2] + 12]
    for k in range(beats * 2):
        vel = .2 if k % 2 == 0 else .14
        put(inst(MAR, pat[k % 8], .5), t0 + k * B / 2, vel, (-.35 if k % 2 else .35), music)
# fade music into the end chord
mix += music

# ------------------------------------------------ master
e0 = int((T['total'] - .6) * SR); mix[e0:] *= np.linspace(1, 0, len(mix) - e0)[:, None]
mix = mix[:int(T['total'] * SR)]
seg = mix[int(T['G'] * SR):int(T['H'] * SR)]
mix *= 10 ** (-20 / 20) / np.sqrt((seg ** 2).mean())
peak = np.abs(mix).max()
# look-ahead peak limiter (gain riding only)
from scipy.ndimage import maximum_filter1d, uniform_filter1d
ceil = .89
pk = maximum_filter1d(np.abs(mix).max(1), size=int(.006 * SR))
g = np.minimum(1, ceil / (pk + 1e-9))
g = -maximum_filter1d(-g, size=int(.012 * SR))          # hold the reduction a little
g = uniform_filter1d(g, size=int(.004 * SR))             # smooth attack/release
mix = mix * g[:, None]
mix = np.clip(mix, -ceil, ceil)
wavfile.write('audio.wav', SR, (mix * 32767).astype(np.int16))
print('ok', len(mix) / SR, 'peak before norm', peak)
