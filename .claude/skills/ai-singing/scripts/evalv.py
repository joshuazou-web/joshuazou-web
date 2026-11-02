# Objective vocal QA: per-note pitch error (cents), voicing coverage, onset timing, spectrogram
import sys, os, numpy as np, parselmouth, score as S
_SH = os.environ.get('SHIFT')
if _SH is not None:
    for _n in S.N: _n['m'] = _n['midi'] + float(_SH)
f = sys.argv[1]
snd = parselmouth.Sound(f)
import pyworld as pw, soundfile as sf
_y, _sr = sf.read(f)
if _y.ndim > 1: _y = _y.mean(1)
_f0, ts = pw.harvest(_y.astype(float), _sr, frame_period=5, f0_floor=80, f0_ceil=600)
hz = pw.stonemask(_y.astype(float), _f0, ts, _sr)
def mc(x): return 69 + 12 * np.log2(x / 440)
rows = []; errs = []; covs = []
for n in S.N:
    a, b = n['t'] + 0.06, n['t'] + n['len'] - 0.08
    if b - a < 0.05: a, b = n['t'] + 0.02, n['t'] + n['len'] - 0.03
    m = (ts >= a) & (ts <= b); v = hz[m]; vv = v[v > 0]
    cov = len(vv) / max(1, len(v)); covs.append(cov)
    if len(vv):
        e = (np.median(mc(vv)) - n['m']) * 100; errs.append(abs(e))
    else: e = np.nan
    rows.append((n['ch'], n['m'], round(float(e), 0) if not np.isnan(e) else None, round(cov, 2)))
# onset: energy rise near each note
int_ = snd.to_intensity(time_step=0.005); it = int_.xs(); iv = int_.values[0]
lag = []
for n in S.N:
    m = (it > n['t'] - 0.12) & (it < n['t'] + 0.12)
    if m.sum() > 3:
        d = np.diff(iv[m]); lag.append((it[m][1:][np.argmax(d)] - n['t']) * 1000)
errs = np.array(errs)
print(f'{f}: notes={len(S.N)}  pitch |err| median={np.median(errs):.0f}c  p90={np.percentile(errs,90):.0f}c  '
      f'>50c: {(errs>50).sum()}  voiced-cov mean={np.mean(covs):.2f} min={np.min(covs):.2f}  onset lag median={np.median(lag):.0f}ms')
bad = [r for r in rows if r[2] is None or abs(r[2]) > 50 or r[3] < 0.6]
print('worst:', bad[:12])
if '--png' in sys.argv:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(18, 7), sharex=True)
    sg = snd.to_spectrogram(maximum_frequency=6000)
    X, Y = sg.x_grid(), sg.y_grid(); Sdb = 10 * np.log10(sg.values + 1e-12)
    ax[0].pcolormesh(X, Y, Sdb, vmin=Sdb.max() - 70, cmap='magma'); ax[0].set_ylabel('Hz')
    ax[1].plot(ts, np.where(hz > 0, mc(np.where(hz>0,hz,1)), np.nan), '.', ms=2, label='sung')
    for n in S.N:
        ax[1].hlines(n['m'], n['t'], n['t'] + n['len'], color='r', lw=3, alpha=.4)
        ax[1].text(n['t'], n['m'] + .6, n['ch'], fontsize=9, fontproperties=matplotlib.font_manager.FontProperties(fname='/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc') if __import__('os').path.exists('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc') else None)
    ax[1].set_ylim(min(n['m'] for n in S.N)-4, max(n['m'] for n in S.N)+4); ax[1].set_ylabel('MIDI'); plt.tight_layout(); plt.savefig(f.replace('.wav', '.png'), dpi=60)
