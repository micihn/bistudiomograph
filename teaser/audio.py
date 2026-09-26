import json, numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 44100
D = json.load(open('cues.json'))
T, CUES = D['T'], D['cues']
N = int((T['total'] + 0.5) * SR)
rs = np.random.default_rng(3)

sfx = np.zeros((N, 2))
bed_game = np.zeros(N); bed_chat = np.zeros(N); bed_mont = np.zeros((N, 2)); pad = np.zeros((N, 2))

def t_(d): return np.arange(int(d * SR)) / SR
def env(n, a, r):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi, o=2): return sosfilt(butter(o, [lo, hi], 'band', fs=SR, output='sos'), x)
def put(buf, t, x, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0: return
    x = x[:len(buf) - i]
    if buf.ndim == 2:
        l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
        buf[i:i + len(x), 0] += x * gain * l * 1.414
        buf[i:i + len(x), 1] += x * gain * r * 1.414
    else:
        buf[i:i + len(x)] += x * gain
def noise(d): return rs.standard_normal(int(d * SR))
def sine(f, d, ph=0): return np.sin(2 * np.pi * f * t_(d) + ph)
def note(m): return 440 * 2 ** ((m - 69) / 12)

# ---------------- sfx ----------------
def add(*xs):
    n = max(len(x) for x in xs); o = np.zeros(n)
    for x in xs: o[:len(x)] += x
    return o
def s_key(v=1):
    d = .05; n = int(d * SR)
    c = bp(noise(d), 1800 + rs.random() * 1500, 6500) * env(n, .0005, .006)
    th = sine(140 + rs.random() * 60, d) * env(n, .001, .012) * .5
    return (c * .9 + th) * (.6 + .4 * rs.random()) * v
def s_click():
    n = int(.04 * SR); return bp(noise(.04), 2500, 9000) * env(n, .0003, .004) + sine(900, .04) * env(n, .0005, .006) * .3
def s_ping():
    out = np.zeros(int(1.2 * SR))
    for k, (f, st) in enumerate([(1318.5, 0), (1975.5, .11)]):
        d = 1.0; x = (sine(f, d) + .25 * sine(2 * f, d) + .1 * sine(3.01 * f, d)) * env(int(d * SR), .003, .22)
        i = int(st * SR); out[i:i + len(x)] += x[:len(out) - i]
    return out * .5
def s_recv():
    d = .14; tt = t_(d); f = 520 + 520 * (tt / d) ** .5
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), .002, .04) * .6
def s_sent():
    d = .22; tt = t_(d); f = 700 + 900 * (tt / d)
    w = hp(noise(d), 2000) * np.sin(np.pi * tt / d) * .15
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), .002, .05) * .55 + w
def s_swoosh(d=.45, lo=300, hi=5000, up=True):
    n = int(d * SR); x = noise(d); out = np.zeros(n); blk = 1024
    for i in range(0, n, blk):
        p = i / n; p = p if up else 1 - p
        f = lo * (hi / lo) ** p
        out[i:i + blk] = bp(x[i:i + blk], f * .7, min(f * 1.4, 20000))
    return out * np.sin(np.pi * np.arange(n) / n) ** 2 * .6
def s_thud(f=70, d=.35):
    n = int(d * SR); tt = t_(d); fr = f * (1 + 2.5 * np.exp(-tt / .03))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * env(n, .001, d / 3.5)
def s_spell():
    d = .8; tt = t_(d); n = len(tt)
    sh = sum(np.sin(2 * np.pi * (900 * k + 400 * tt) * tt) for k in (1, 1.5, 2.02)) * env(n, .01, .25) * .12
    return sh + s_swoosh(d, 800, 9000) * .5
def s_hit(): return add(s_thud(90, .25) * .8, bp(noise(.08), 1500, 6000) * env(int(.08 * SR), .0005, .015) * .5)
def s_kick():
    d = .45; tt = t_(d); fr = 48 + 110 * np.exp(-tt / .035)
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * env(len(tt), .001, .16)
def s_clap():
    d = .3; n = int(d * SR); x = bp(noise(d), 900, 5000)
    e = np.zeros(n)
    for o in (0, .011, .022): i = int(o * SR); e[i:] += env(n - i, .0005, .01 if o < .02 else .09)
    return x * e * .7
def s_hat(open_=False):
    d = .2 if open_ else .06; n = int(d * SR)
    return hp(noise(d), 7000) * env(n, .0005, .06 if open_ else .012) * .5
def s_tick(): return add(s_click() * .6, s_swoosh(.18, 2000, 10000) * .35)

def chord_pad(freqs, d, a=.8, r=1.6, bright=1200):
    n = int(d * SR); tt = t_(d); x = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.12):
            ff = f * 2 ** (det / 12)
            x += np.sin(2 * np.pi * ff * tt) + .3 * np.sin(4 * np.pi * ff * tt) + .12 * np.sin(6 * np.pi * ff * tt)
    x = lp(x, bright)
    e = np.minimum(1, tt / a) * np.minimum(1, np.maximum(0, (d - tt) / r))
    return x * e / len(freqs) * .35

for c in CUES:
    t, s, v = c['t'], c['s'], c['v']
    pan = 0
    if s == 'key': put(sfx, t, s_key(v), .32, (rs.random() - .5) * .3)
    elif s == 'bs': put(sfx, t, s_key(v) * .8, .28)
    elif s == 'rclick': put(sfx, t, s_click(), .15, .2)
    elif s == 'click': put(sfx, t, s_click(), .5)
    elif s == 'ping': put(sfx, t, s_ping(), .55, .35)
    elif s == 'recv': put(sfx, t, s_recv(), .5, -.1)
    elif s == 'sent': put(sfx, t, s_sent(), .5, .1)
    elif s == 'swoosh': put(sfx, t, s_swoosh(.4, 300, 4000), .35)
    elif s == 'select': put(sfx, t, s_click(), .5)
    elif s == 'delete': put(sfx, t, s_swoosh(.25, 600, 8000, up=False), .7)
    elif s == 'spell': put(sfx, t, s_spell(), .16)
    elif s == 'hit': put(sfx, t, s_hit(), .16 * v)
    elif s == 'sting':  # comedic low "dun" as ASAP lands
        x = s_thud(55, 1.2) * .9 + chord_pad([note(38), note(41), note(44)], 1.2, .005, .9, 900) * 2.2
        put(sfx, t, x, .38)
    elif s == 'tone1': put(pad, t, chord_pad([note(57), note(64), note(69), note(71)], 2.9, .9, 1.4, 1600), .55)
    elif s == 'tone2': put(pad, t, chord_pad([note(53), note(60), note(64), note(69)], 2.0, .6, .9, 2200), .6)
    elif s == 'cutfx': put(sfx, t, s_tick(), .35 * v)
    elif s == 'riseout': put(sfx, t, s_swoosh(.5, 3000, 300, up=True), .25)
    elif s == 'end':
        put(pad, t, chord_pad([note(45), note(57), note(64), note(69), note(73), note(76)], 4.2, .02, 2.8, 3000), .9)
        bell = sum(np.sin(2 * np.pi * f * t_(3)) * a for f, a in [(note(81), 1), (note(81) * 2.76, .3), (note(81) * 5.4, .1)]) * env(int(3 * SR), .002, .7)
        put(sfx, t + .55, bell, .12)

# ---------------- game bed (0 .. cut), muffled once chat opens ----------------
gd = T['cut']; n = int(gd * SR); tt = t_(gd)
drone = (np.sin(2 * np.pi * note(38) * tt) + .6 * np.sin(2 * np.pi * note(45) * tt) + .3 * np.sin(2 * np.pi * note(50) * tt * 1.001))
drone *= .55 + .45 * np.sin(2 * np.pi * .5 * tt) ** 2
amb = lp(noise(gd), 500) * .5
drums = np.zeros(n)
for b in np.arange(0, gd, 60 / 100):
    i = int(b * SR); k = s_thud(60, .5) * .7
    drums[i:i + len(k)] += k[:n - i]
g = drone * .22 + amb * .6 + drums * .35
g = lp(g, 3000)
g_muf = lp(g, 350, 4)
m = np.clip((tt - T['open']) / .5, 0, 1)
g = g * (1 - m) + g_muf * m * .7
g *= np.minimum(1, tt / .8)
bed_game[:n] = g

# ---------------- chat lo-fi bed (b1 .. b3 with tape stop) ----------------
bpm = 84; bt = 60 / bpm
c0, c1 = T['b1'] - .3, T['b3']
dur = c1 - c0 + 1.0
nn = int(dur * SR); x = np.zeros(nn)
prog = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]
bars = int(dur / (4 * bt)) + 1
def ep(f, d):
    tt = t_(d); v = np.sin(2 * np.pi * f * tt) + .35 * np.sin(4 * np.pi * f * tt) * np.exp(-tt / .3) + .08 * np.sin(2 * np.pi * 3 * f * tt) * np.exp(-tt / .1)
    return v * env(len(tt), .004, .9) * (1 + .15 * np.sin(2 * np.pi * 4.5 * tt))
for bi in range(bars):
    ch = prog[bi % 4]; st = bi * 4 * bt
    for hit in (0, 1.5, 2.5):
        for j, mm in enumerate(ch):
            put(x, st + hit * bt + j * .012, ep(note(mm), 2.2), .09)
    put(x, st, ep(note(ch[0] - 24), 2.5) * .9, .25)
    for b in range(4):
        put(x, st + b * bt, s_thud(58, .3), .22 if b % 2 == 0 else 0)
        put(x, st + b * bt + bt * .5, s_hat(), .12)
        if b % 2 == 1: put(x, st + b * bt, lp(s_clap(), 3000), .25)
x = lp(x, 4200) + lp(noise(dur), 6000) * .006
x *= np.minimum(1, t_(dur) / 1.2)
# tape stop starting at b3 - .05
ts = int((T['b3'] - .05 - c0) * SR)
head = x[:ts]
seg = x[ts:ts + int(1.0 * SR)]
L = int(.55 * SR); rate = np.linspace(1, 0.05, L); pos = np.cumsum(rate)
pos = pos[pos < len(seg) - 1]
stop = np.interp(pos, np.arange(len(seg)), seg) * np.linspace(1, 0, len(pos)) ** .5
x = np.concatenate([head, stop])
put(bed_chat, c0, x, 1.0)

# ---------------- montage beat (120 bpm) ----------------
B = .5; m0 = T['mont']; nbeats = 23
# riser into the drop
rd = m0 - T['title2']
if rd > .2:
    r = s_swoosh(rd, 200, 9000, up=True) * np.linspace(0, 1, int(rd * SR)) ** 2
    put(bed_mont, T['title2'], r, .5)
roots = [45, 41, 48, 43]  # A F C G
arp = {45: [57, 60, 64, 69], 41: [53, 57, 60, 65], 48: [55, 60, 64, 67], 43: [55, 59, 62, 67]}
def pluck(f, d=.25):
    tt = t_(d); v = sum(np.sin(2 * np.pi * f * k * tt) / k ** 1.3 for k in range(1, 7))
    return lp(v * env(len(tt), .001, .07), 5000)
def bass(f, d):
    tt = t_(d); v = sum(np.sin(2 * np.pi * f * k * tt) / k for k in range(1, 8))
    return lp(v, 600) * env(len(tt), .005, d * .7) + np.sin(2 * np.pi * f * tt) * env(len(tt), .005, d)
for b in range(nbeats):
    t = m0 + b * B
    put(bed_mont, t, s_kick(), .85)
    put(bed_mont, t + B / 2, s_hat(), .35, .25)
    put(bed_mont, t + B / 4, s_hat(), .12, -.25); put(bed_mont, t + 3 * B / 4, s_hat(), .12, -.25)
    if b % 2 == 1: put(bed_mont, t, s_clap(), .5)
    root = roots[(b // 4) % 4]
    put(bed_mont, t + B / 2, bass(note(root - 12), .45), .32)
    for k in range(4):
        put(bed_mont, t + k * B / 4, pluck(note(arp[root][(b * 4 + k) % 4] + 12)), .09, (-.4 if k % 2 else .4))
    if b % 4 == 0: put(bed_mont, t, chord_pad([note(n_) for n_ in arp[root]], 2.0, .02, .6, 2500), .35)
put(bed_mont, m0, s_thud(40, 1.4), .9)
put(bed_mont, m0, hp(noise(1.5), 3000) * env(int(1.5 * SR), .001, .4), .12)
# after montage: filtered tail under the callback, fading out
i0, i1 = int(T['call'] * SR), int(T['end'] * SR)
bed_mont[i0:] = 0
tail_n = i1 - i0; tt = t_(tail_n / SR)
tail = np.zeros(tail_n)
for b in range(int(tail_n / SR / B) + 1):
    root = roots[((nbeats + b) // 4) % 4]
    put(tail, b * B, pluck(note(arp[root][b % 4] + 12)), .08)
    put(tail, b * B, s_thud(50, .3), .25)
tail = lp(tail, 1200) * np.minimum(1, tt / .2)
put(bed_mont, T['call'], tail, 1.0)

# ---------------- mix ----------------
mix = sfx.copy()
mix[:, 0] += bed_game * .55 + bed_chat * 1.0; mix[:, 1] += bed_game * .55 + bed_chat * 1.0
mix += bed_mont * .5 + pad * 1.2
# hard silence at the cut (except scheduled sfx that start after)
fade_out = int(T['cut'] * SR)
mix[fade_out:int(T['title1'] * SR) - 1] *= 0
# end fade
e0 = int((T['total'] - .8) * SR); mix[e0:] *= np.linspace(1, 0, len(mix) - e0)[:, None]
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix /= np.max(np.abs(mix)) / 0.89
wavfile.write('audio.wav', SR, (mix * 32767).astype(np.int16))
print('ok', mix.shape[0] / SR)
