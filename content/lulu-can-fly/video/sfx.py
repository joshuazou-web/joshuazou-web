# 合成音效轨（18s，44.1kHz）：泡泡、弹射、呼啸、坠落哨音、落水。音量刻意压低，给抖音原曲 BGM 让位。
import numpy as np, wave, sys
SR, DUR = 44100, 18.0
out = np.zeros(int(SR * DUR))
rng = np.random.default_rng(1)
def put(t0, sig, vol):
    i = int(t0 * SR); n = min(len(sig), len(out) - i); out[i:i + n] += sig[:n] * vol
def env(n, a=.005, r=None):
    e = np.ones(n); ai = max(1, int(a * SR)); e[:ai] = np.linspace(0, 1, ai)
    e *= np.exp(-np.linspace(0, r or 5, n)); return e
def sweep(f0, f1, d):
    n = int(d * SR); f = np.geomspace(f0, f1, n); return np.sin(2 * np.pi * np.cumsum(f) / SR)
def noise(d, lp=1.0):
    n = int(d * SR); x = rng.standard_normal(n)
    if lp < 1:  # 一阶低通
        y = np.zeros(n); k = lp
        for i in range(1, n): y[i] = y[i - 1] + k * (x[i] - y[i - 1])
        x = y / (np.abs(y).max() + 1e-9)
    return x
def bubble(t, f=380): s = sweep(f, f * 2.2, .09); put(t, s * env(len(s), r=4), .35)
def whoosh(t, d=.45, v=.35):
    x = noise(d, .08); n = len(x); put(t, x * np.sin(np.linspace(0, np.pi, n)) ** 2, v)
def splash_(t, v=.6):
    x = noise(.9, .35); put(t, x * env(len(x), a=.002, r=6), v)
    for k in range(6): bubble(t + .15 + k * .07, 300 + 90 * k)
# 0-2s 泡澡：水声底噪 + 咕嘟
amb = noise(3.0, .02); put(0, amb * .5 * np.minimum(1, np.linspace(3, 0, len(amb))), .5)
for t in (.35, .9, 1.5, 17.5, 17.75): bubble(t)
put(2.4, sweep(1800, 2400, .05) * env(int(.05 * SR), r=3), .2)          # 睁眼 叮
s = sweep(160, 900, .35) * (1 + .3 * np.sin(np.linspace(0, 60, int(.35 * SR)))); put(3.0, s * env(len(s), r=3), .45)  # 橘子弹起 boing
splash_(3.2); whoosh(3.25, .6, .5)
s = sweep(900, 300, .3); put(4.2, s * env(len(s), r=3), .3)             # 橘子落回头顶
for t in (5.0, 8.0, 11.0): whoosh(t - .15, .45, .4)                     # 转场
s = sweep(2200, 350, 1.9); put(14.05, s * np.linspace(.3, 1, len(s)), .22)  # 坠落哨音
whoosh(14.0, 2.0, .25)
splash_(16.25, .9)
s = sweep(700, 350, .12); put(16.62, s * env(len(s), r=4), .35)          # 橘子落头 boop
s = sweep(700, 350, .12); put(16.85, s * env(len(s), r=4), .3)
out = np.tanh(out * 1.2) * .8
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
