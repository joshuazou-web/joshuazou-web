# Per-syllable TTS cache: Kokoro, tone-flattened IPA
import os, re, numpy as np, soundfile as sf, functools
from misaki import zh
_g = zh.ZHG2P()
_k = None
M = os.path.join(os.path.dirname(__file__), '..', 'models')
def kokoro():
    global _k
    if _k is None:
        from kokoro_onnx import Kokoro
        _k = Kokoro(f'{M}/kokoro-v1.0.onnx', f'{M}/voices-v1.0.bin')
    return _k
TONES = '→↗↓↘'
def ipa(ch, flat=True):
    p = _g(ch)
    if isinstance(p, tuple): p = p[0]
    p = p.strip()
    if flat:
        p = re.sub('[↗↓↘]', '→', p)
        if '→' not in p: p = p + '→'
    return p
def syllable(ch, voice, speed=0.8, flat=True):
    os.makedirs('cache', exist_ok=True)
    f = f'cache/{voice}_{ord(ch)}_{speed}_{int(flat)}.wav'
    if not os.path.exists(f):
        a, sr = kokoro().create(ipa(ch, flat), voice=voice, speed=speed, lang='cmn', is_phonemes=True)
        sf.write(f, a, sr)
    a, sr = sf.read(f)
    return a.astype(np.float64), sr
