# "Ears": SenseVoice ASR (lyric intelligibility, per line) + DNSMOS (signal quality) on a vocal or mix
import sys, re, numpy as np, soundfile as sf, sherpa_onnx
from scipy.signal import resample_poly
import score as S
MD = '../models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17'
_rec = None
def rec():
    global _rec
    if _rec is None:
        _rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=f'{MD}/model.int8.onnx', tokens=f'{MD}/tokens.txt',
                                                              language='zh', use_itn=False, num_threads=4)
    return _rec
def asr(x16):
    s = rec().create_stream(); s.accept_waveform(16000, x16.astype(np.float32)); rec().decode_stream(s)
    return re.sub(r'[^一-鿿]', '', s.result.text)
def cer(ref, hyp):
    d = np.arange(len(hyp) + 1)
    for i, r in enumerate(ref, 1):
        p = d.copy(); d[0] = i
        for j, h in enumerate(hyp, 1): d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (r != h))
    return d[-1] / max(1, len(ref))
def load16(f):
    y, sr = sf.read(f)
    if y.ndim > 1: y = y.mean(1)
    return resample_poly(y, 160, sr // 100).astype(np.float32) if sr != 16000 else y.astype(np.float32)
def run(f):
    y = load16(f); out = []
    for l in S.lines():
        ns = [S.N[i] for i in l]; a = max(0, ns[0]['t'] - 0.25); b = ns[-1]['t'] + ns[-1]['len'] + 0.3
        ref = ''.join(n['ch'] for n in ns); hyp = asr(y[int(a * 16000):int(b * 16000)])
        out.append((ref, hyp, cer(ref, hyp)))
    allref = ''.join(n['ch'] for n in S.N)
    tot = sum(c * len(r) for r, h, c in out) / len(allref)
    from speechmos import dnsmos
    seg = []
    for k in range(0, len(y) - 16000 * 9, 16000 * 9):
        r = dnsmos.run(y[k:k + 16000 * 9], sr=16000); seg.append((r['sig_mos'], r['bak_mos'], r['ovrl_mos']))
    sig, bak, ovr = np.mean(seg, 0)
    print(f'{f}: lyric CER={tot:.2f}  (intelligibility {100*(1-tot):.0f}%)   DNSMOS sig={sig:.2f} bak={bak:.2f} ovrl={ovr:.2f}')
    for r, h, c in out:
        if c > 0: print(f'   {r} -> heard "{h}"  cer={c:.2f}')
    return tot, sig, ovr
if __name__ == '__main__':
    for f in sys.argv[1:]: run(f)
