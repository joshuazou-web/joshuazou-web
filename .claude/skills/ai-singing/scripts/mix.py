# Mix: vocal chain + reverb/delay sends + music ducking + master to -14 LUFS
import sys, numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import butter, sosfilt, fftconvolve
import score as S
SR = 44100
P = dict(vox_db=0.0, rev=0.16, dly=0.10, duck=2.5, pres=3.0, air=2.0, lufs=-14.0, mus_scoop=2.0)
args = [a for a in sys.argv[1:] if '=' not in a]
for kv in [a for a in sys.argv[1:] if '=' in a]:
    k, v = kv.split('='); P[k] = float(v)
vox_f, inst_f, out_f = args
def db(x): return 10 ** (x / 20)
def peq(x, f, g, q=1.0):  # RBJ peaking EQ
    A = db(g / 2); w = 2 * np.pi * f / SR; al = np.sin(w) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w), 1 - al * A]); a = np.array([1 + al / A, -2 * np.cos(w), 1 - al / A])
    from scipy.signal import lfilter
    return lfilter(b / a[0], a / a[0], x, axis=0)
def shelf_hi(x, f, g):
    A = db(g / 2); w = 2 * np.pi * f / SR; al = np.sin(w) / 2 * np.sqrt(2)
    c = np.cos(w); sA = 2 * np.sqrt(A) * al
    b = np.array([A * ((A + 1) + (A - 1) * c + sA), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sA)])
    a = np.array([(A + 1) - (A - 1) * c + sA, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sA])
    from scipy.signal import lfilter
    return lfilter(b / a[0], a / a[0], x, axis=0)
def comp(x, thr=-20, ratio=4, att=0.005, rel=0.08, makeup=0):
    mono = np.abs(x if x.ndim == 1 else x.mean(1))
    ga = np.exp(-1 / (att * SR)); gr = np.exp(-1 / (rel * SR))
    env = np.zeros_like(mono); e = 0.0
    # vectorised-ish envelope follower via blocks
    blk = 64; out = np.empty(len(mono) // blk + 1); k = 0
    for i in range(0, len(mono), blk):
        v = mono[i:i + blk].max(); c = ga ** blk if v > e else gr ** blk
        e = c * e + (1 - c) * v; out[k] = e; k += 1
    env = np.repeat(out[:k], blk)[:len(mono)]
    lvl = 20 * np.log10(env + 1e-9); over = np.maximum(0, lvl - thr)
    g = db(-over * (1 - 1 / ratio) + makeup)
    return x * (g if x.ndim == 1 else g[:, None])
def reverb_ir(sec=1.6, pre=0.025, seed=0):
    r = np.random.default_rng(seed); n = int(sec * SR); t = np.arange(n) / SR
    ir = r.standard_normal((n, 2)) * np.exp(-t * 6.9 / sec)[:, None]
    ir = sosfilt(butter(2, 6500, 'low', fs=SR, output='sos'), ir, axis=0)
    ir = sosfilt(butter(2, 250, 'high', fs=SR, output='sos'), ir, axis=0)
    return np.concatenate([np.zeros((int(pre * SR), 2)), ir]) / np.sqrt((ir ** 2).sum() / 2)
v, _ = sf.read(vox_f); m, _ = sf.read(inst_f)
if v.ndim > 1: v = v.mean(1)
L = int((S.TOTAL) * SR); v = np.pad(v, (0, max(0, L - len(v))))[:L]; m = np.pad(m, ((0, max(0, L - len(m))), (0, 0)))[:L]
# --- vocal chain
v = sosfilt(butter(2, 110, 'high', fs=SR, output='sos'), v)
v = peq(v, 300, -2.0, 1.0); v = peq(v, 3200, P['pres'], 0.9); v = shelf_hi(v, 9000, P['air'])
v = comp(v, thr=-24, ratio=3.5, att=0.004, rel=0.09)
v = comp(v, thr=-14, ratio=8, att=0.001, rel=0.05)          # peak catch
v = v / (np.sqrt(np.mean(v[v != 0] ** 2)) + 1e-9) * 0.1
v2 = np.stack([v, v], 1)
rev = fftconvolve(v2[:, :1].repeat(2, 1), reverb_ir(), axes=0)[:L] if False else np.stack([fftconvolve(v, reverb_ir()[:, c])[:L] for c in range(2)], 1)
d = int(S.BEAT / 2 * SR); dl = np.zeros_like(v2); dl[d:, 0] = v[:-d]; dl[2 * d:, 1] = v[:-2 * d] * 0.6
dl = sosfilt(butter(2, [400, 5000], 'band', fs=SR, output='sos'), dl, axis=0)
hookmask = np.zeros(L)
for b, s in enumerate(S.SECTION):
    if s in ('hook', 'tag'): hookmask[int(b * S.BAR * SR):int((b + 1) * S.BAR * SR)] = 1
hookmask = np.convolve(hookmask, np.ones(4410) / 4410, 'same')
vox = v2 * db(P['vox_db']) + rev * P['rev'] + dl * P['dly'] * hookmask[:, None]
# --- music: carve vocal space + duck under the voice
m = peq(m, 2800, -P['mus_scoop'], 0.8)
venv = np.convolve(np.abs(v), np.ones(2205) / 2205, 'same'); venv = venv / (venv.max() + 1e-9)
duck = db(-P['duck'] * np.clip(venv * 3, 0, 1))
m = m * duck[:, None]
m = m / (np.sqrt(np.mean(m ** 2)) + 1e-9) * 0.1
mixd = vox + m * db(-1.5)
mixd = comp(mixd, thr=-12, ratio=2, att=0.01, rel=0.15)
meter = pyln.Meter(SR)
from scipy.ndimage import minimum_filter1d
def limit(x, ceil_db=-1.0, look=0.003, rel=0.06):
    c = db(ceil_db); a = np.abs(x).max(1)
    g = np.minimum(1, c / (a + 1e-12))
    n = int(look * SR); g = minimum_filter1d(g, 2 * n + 1)       # lookahead window
    r = np.exp(-1 / (rel * SR)); out = np.empty_like(g); e = 1.0
    for i in range(0, len(g), 32):                             # block release follower
        gi = g[i:i + 32].min(); e = gi if gi < e else (r ** 32) * e + (1 - r ** 32) * gi
        out[i:i + 32] = min(e, gi) if gi < e else e
    out = np.convolve(out, np.ones(n) / n, 'same')
    return x * np.minimum(out, g)[:, None]
for _ in range(3):
    lo = meter.integrated_loudness(mixd); mixd = limit(mixd * db(P['lufs'] - lo))
f = int(1.0 * SR); mixd[-f:] *= np.linspace(1, 0, f)[:, None] ** 2
sf.write(out_f, mixd, SR, subtype='PCM_16')
lo2 = meter.integrated_loudness(mixd)
# vocal intelligibility proxy: vocal vs music energy in 1-4 kHz during sung notes
bp = butter(4, [1000, 4000], 'band', fs=SR, output='sos')
vb = sosfilt(bp, vox.mean(1)); mb = sosfilt(bp, (m * db(-1.5)).mean(1))
sing = np.zeros(L, bool)
for n in S.N: sing[int(n['t'] * SR):int((n['t'] + n['len']) * SR)] = True
snr = 10 * np.log10(np.mean(vb[sing] ** 2) / np.mean(mb[sing] ** 2))
print(f'{out_f}: LUFS={lo2:.1f} peak={20*np.log10(np.abs(mixd).max()):.1f}dBFS  vocal/music(1-4k)={snr:.1f}dB')
