# Full vocal: Kokoro neural decoder driven by score durations + designed F0 + sustained energy
import sys, numpy as np, soundfile as sf
from scipy.signal import resample_poly
import score as S, ksing, pyworld as pw
P = dict(voice='zm_yunxi', port=0.07, scoop=45, vib_rate=5.5, vib_depth=30, vib_delay=0.3,
         jitter=4, floor=5.5, release=0.06, seed=3, acc_db=0.6)
for kv in sys.argv[2:]:
    k, v = kv.split('='); P[k] = v if k == 'voice' else float(v)
rng = np.random.default_rng(int(P['seed']))
notes = S.N
def hz(m): return 440 * 2 ** ((m - 69) / 12)
# global pitch curve in cents on a fine grid
G = 0.0025; tg = np.arange(0, S.TOTAL + 1, G); C = np.full(len(tg), np.nan)
for i, n in enumerate(notes):
    a, b = n['t'] - 0.12, n['t'] + n['len'] + 0.1
    m = (tg >= a) & (tg < b); tt = tg[m] - n['t']
    c = np.full(m.sum(), n['m'] * 100.0)
    prev = notes[i - 1] if i else None
    legato = prev is not None and n['t'] - (prev['t'] + prev['len']) < 0.05
    if legato:
        d = prev['m'] * 100.0 - n['m'] * 100.0
        c += d / (1 + np.exp(tt / (P['port'] / 5)))      # glide centred on the beat
    else:
        c -= P['scoop'] * np.exp(-np.maximum(tt, 0) / 0.06)
    if n['len'] > 0.5:
        ramp = np.clip((tt - P['vib_delay']) / 0.3, 0, 1)
        c += P['vib_depth'] * ramp * np.sin(2 * np.pi * P['vib_rate'] * np.maximum(tt, 0))
    own = tt >= -0.03 if legato else np.ones_like(tt, bool)
    cur = C[m]; cur[own | np.isnan(cur)] = c[own | np.isnan(cur)]; C[m] = cur
drift = np.convolve(rng.standard_normal(len(tg)), np.ones(60) / 60, 'same')
C = C + drift / drift.std() * P['jitter']
ok = ~np.isnan(C); Cf = np.interp(tg, tg[ok], C[ok])   # rests take the nearest note's pitch
def f0fn(t):
    c = np.interp(t, tg, Cf)
    return 440 * 2 ** ((c / 100 - 69) / 12)
# phrases: split at rests
phr, cur = [], [0]
for i in range(1, len(notes)):
    p = notes[i - 1]
    if notes[i]['t'] - (p['t'] + p['len']) >= 0.05: phr.append(cur); cur = []
    cur.append(i)
phr.append(cur)
SR = 24000; out = np.zeros(int((S.TOTAL + 1) * SR))
infos = []
for ph in phr:
    ns = [notes[i] for i in ph]
    acc = [P['acc_db'] * (n['acc'] - 1) * 10 for n in ns]
    nf = lambda N, info, acc=acc: ksing.sustain_N(N, info, floor=P['floor'], release=P['release'], accents=acc)
    best = None
    for take in range(int(P.get('takes', 3))):
        a, base, info = ksing.render_phrase(ns, P['voice'], f0fn=f0fn, nfix=nf)
        f0h, _ = pw.harvest(a.astype(float), SR, frame_period=10, f0_floor=80, f0_ceil=600)
        th = base + np.arange(len(f0h)) * 0.01
        errs = []
        for n in ns:
            m = (th > n['t'] + 0.05) & (th < n['t'] + n['len'] - 0.06); v = f0h[m]
            if m.sum() == 0: continue
            vv = v[v > 0]
            errs.append(400 if len(vv) < 0.6 * len(v) else min(400, abs(1200 * np.log2(np.median(vv) / hz(n['m'])))))
        sc = float(np.mean(errs)) if errs else 0
        if best is None or sc < best[0]: best = (sc, a, base, info)
        if sc < 12: break
    sc, a, base, info = best
    s = int(round(base * SR)); a = a.copy()
    f = int(0.01 * SR); a[:f] *= np.linspace(0, 1, f); a[-f:] *= np.linspace(1, 0, f)
    if s < 0: a = a[-s:]; s = 0
    out[s:s + len(a)] += a[:len(out) - s]
    infos.append((''.join(n['ch'] for n in ns), round(sc, 1)))
out = out[:int(S.TOTAL * SR)]
# level-flatten sustained notes (residual decay of the decoder on very long vowels)
if P.get('flat', 1):
    w = int(0.03 * SR); env = np.sqrt(np.convolve(out ** 2, np.ones(w) / w, 'same')) + 1e-6
    g = np.ones_like(out)
    for n in notes:
        if n['len'] < 0.5: continue
        a = int((n['t'] + 0.08) * SR); b = int((n['t'] + n['len'] - 0.1) * SR)
        ref = np.percentile(env[a:a + int(0.12 * SR)], 80)
        gg = np.clip(ref / env[a:b], 1, 2.8)
        gg = np.convolve(gg, np.ones(w * 2) / (w * 2), 'same')
        g[a:b] = gg
    out = out * g
y = resample_poly(out, 147, 80); y = y / np.abs(y).max() * 0.9
fn = sys.argv[1] if len(sys.argv) > 1 else 'voxk.wav'
sf.write(fn, y, 44100); print('wrote', fn, len(phr), 'phrases; take scores (mean cents err):', infos)
