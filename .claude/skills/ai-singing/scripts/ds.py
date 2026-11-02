# DiffSinger (Qixuan 绮萱 v2.7.0) inference, mirroring OpenUtau's renderer
import sys, json, yaml, numpy as np, onnxruntime as ort, soundfile as sf
from pypinyin import lazy_pinyin, Style
import score as S
VB = '../qx/Qixuan_v2.7.0_DiffSinger_OpenUtau'; VOC = '../qx/voc/pc_nsf_hifigan_44.1k_hop512_128bin_2025.02.onnx'
SR, HOP = 44100, 512; FPS = SR / HOP
so = ort.SessionOptions(); so.intra_op_num_threads = 4
def sess(p): return ort.InferenceSession(f'{VB}/{p}', so, providers=['CPUExecutionProvider'])
def jl(p): return json.load(open(f'{VB}/{p}'))
DICT = {}
for e in yaml.safe_load(open(f'{VB}/dsdur/dsdict-zh.yaml'))['entries']:
    DICT.setdefault(e['grapheme'], e['phonemes'])
FIX = {'着': 'zhe', '一': 'yi', '重': 'chong'}
def phones(ch):
    py = FIX.get(ch) or lazy_pinyin(ch, style=Style.NORMAL)[0]
    if py not in DICT: raise KeyError(f'{ch} {py}')
    return DICT[py]
P = dict(vib=0.32, vib_rate=5.6, vib_delay=0.28, shift=5, steps_ac=20, steps_var=10, depth=0.6, expr=1.0, gender=0.0, pad=0.6, breath=0.0, seed=0)
for kv in sys.argv[2:]:
    k, v = kv.split('='); P[k] = float(v)
def fr(t): return int(round(t * FPS))
def build():
    """words: (phonemes, frames, midi or None for rest)"""
    words = []; t = -P['pad']
    for n in S.N:
        if n['t'] - t > 0.01: words.append((['SP'], fr(n['t'] + P['pad']) - fr(t + P['pad']), None))
        e = n['t'] + n['len']
        words.append((phones(n['ch']), fr(e + P['pad']) - fr(n['t'] + P['pad']), n['midi'] + P['shift']))
        t = e
    words.append((['SP'], fr(S.TOTAL + P['pad']) - fr(t + P['pad']), None))
    # rests take neighbour pitch for the models
    mids = [w[2] for w in words]
    for i in range(len(mids)):
        if mids[i] is None:
            j = next((k for k in range(i + 1, len(mids)) if mids[k] is not None), None)
            mids[i] = mids[j] if j is not None else next(m for m in reversed(mids[:i]) if m is not None)
    return words, mids
def ids(phs, js):
    m = jl(js); return np.array([[m[p] for p in phs]], np.int64)
def langs(phs, js):
    m = jl(js); return np.array([[m['zh'] if '/' in p else 0 for p in phs]], np.int64)
def run(out='vox_ds.wav'):
    rng = np.random.default_rng(int(P['seed'])); np.random.seed(int(P['seed']))
    words, mids = build()
    phs = [p for w in words for p in w[0]]
    wdiv = np.array([[len(w[0]) for w in words]], np.int64); wdur = np.array([[w[1] for w in words]], np.int64)
    ph_midi = np.array([[mids[i] for i, w in enumerate(words) for _ in w[0]]], np.int64)
    # 1) durations
    L = sess('dsdur/0102_qixuan_newdict_dur.qixuan.linguistic.onnx'); D = sess('dsdur/0102_qixuan_newdict_dur.qixuan.dur.onnx')
    pj, lj = 'dsdur/0102_qixuan_newdict_dur.phonemes.json', 'dsdur/0102_qixuan_newdict_dur.languages.json'
    enc, msk = L.run(None, {'tokens': ids(phs, pj), 'languages': langs(phs, lj), 'word_div': wdiv, 'word_dur': wdur})
    pred = D.run(None, {'encoder_out': enc, 'x_masks': msk, 'ph_midi': ph_midi})[0][0]
    # 2) align: vowel starts on the note, leading consonants borrow from the previous word
    ph_dur = []; k = 0
    for wi, (wp, wf, _) in enumerate(words):
        d = [0] * len(wp); d[-1] = wf
        if len(wp) > 1:
            cons = [max(1, pred[k + j]) for j in range(len(wp) - 1)]
            prev = ph_dur[-1] if ph_dur else 0
            budget = max(0, min(sum(cons), prev * 0.6))
            sc = budget / sum(cons)
            cons_f = [c * sc for c in cons]
            ci = np.round(np.cumsum(cons_f)).astype(int); ci = np.diff(np.concatenate([[0], ci]))
            ci = np.maximum(ci, 1) if budget >= len(cons) else ci
            take = int(ci.sum())
            if ph_dur: ph_dur[-1] -= take
            d[:-1] = list(ci)
        ph_dur += d; k += len(wp)
    ph_dur = np.array([ph_dur], np.int64); nF = int(ph_dur.sum())
    assert (ph_dur > 0).all() or True
    note_midi = np.array([mids], np.float32); note_rest = np.array([[w[2] is None for w in words]])
    note_dur = wdur
    # 3) pitch
    L = sess('dspitch/0102_qixuan_muon1_pitch.qixuan.linguistic.onnx'); PM = sess('dspitch/0102_qixuan_muon1_pitch.qixuan.pitch.onnx')
    pj, lj = 'dspitch/0102_qixuan_muon1_pitch.phonemes.json', 'dspitch/0102_qixuan_muon1_pitch.languages.json'
    enc, _ = L.run(None, {'tokens': ids(phs, pj), 'languages': langs(phs, lj), 'ph_dur': ph_dur})
    base = np.repeat(note_midi[0], note_dur[0])[None, :].astype(np.float32)
    pitch = PM.run(None, {'encoder_out': enc, 'ph_dur': ph_dur, 'note_midi': note_midi, 'note_rest': note_rest, 'note_dur': note_dur,
                          'pitch': base, 'expr': np.full((1, nF), P['expr'], np.float32), 'retake': np.ones((1, nF), bool),
                          'steps': np.array(int(P['steps_var']), np.int64)})[0]
    # expressive vibrato on sustained notes (the pitch model keeps long notes ruler-straight)
    if P['vib'] > 0:
        for n in S.N:
            if n['len'] < 0.5: continue
            a = fr(n['t'] + P['pad'] + P['vib_delay']); b = fr(n['t'] + n['len'] + P['pad']) - 3
            if b - a < 8: continue
            tt = np.arange(b - a) / FPS
            env = np.minimum(1, tt / 0.3) * np.minimum(1, (b - a - np.arange(b - a)) / 6)
            pitch[0, a:b] += P['vib'] * env * np.sin(2 * np.pi * P['vib_rate'] * tt)
    # 4) breathiness / voicing
    L = sess('dsvariance/0102_qixuan_muon1_multivar.qixuan.linguistic.onnx'); V = sess('dsvariance/0102_qixuan_muon1_multivar.qixuan.variance.onnx')
    pj, lj = 'dsvariance/0102_qixuan_muon1_multivar.phonemes.json', 'dsvariance/0102_qixuan_muon1_multivar.languages.json'
    enc, _ = L.run(None, {'tokens': ids(phs, pj), 'languages': langs(phs, lj), 'ph_dur': ph_dur})
    br, vo = V.run(None, {'encoder_out': enc, 'ph_dur': ph_dur, 'pitch': pitch, 'breathiness': np.zeros((1, nF), np.float32),
                          'voicing': np.zeros((1, nF), np.float32), 'retake': np.ones((1, nF, 2), bool), 'steps': np.array(int(P['steps_var']), np.int64)})
    br = br + P['breath']
    # 5) acoustic
    A = sess('0101_qixuan_muon1_acoustic.qixuan.onnx')
    f0 = (440 * 2 ** ((pitch - 69) / 12)).astype(np.float32)
    mel = A.run(None, {'tokens': ids(phs, '0101_qixuan_muon1_acoustic.phonemes.json'), 'languages': langs(phs, '0101_qixuan_muon1_acoustic.languages.json'),
                       'durations': ph_dur, 'f0': f0, 'breathiness': br.astype(np.float32), 'voicing': vo.astype(np.float32),
                       'gender': np.full((1, nF), P['gender'], np.float32), 'velocity': np.ones((1, nF), np.float32),
                       'depth': np.array(P['depth'], np.float32), 'steps': np.array(int(P['steps_ac']), np.int64)})[0]
    # 6) vocoder
    VC = ort.InferenceSession(VOC, so, providers=['CPUExecutionProvider'])
    wav = VC.run(None, {'mel': mel.astype(np.float32), 'f0': f0})[0][0]
    s0 = int(P['pad'] * SR); wav = wav[s0:s0 + int(S.TOTAL * SR)]
    wav = wav / (np.abs(wav).max() + 1e-9) * 0.9
    sf.write(out, wav, SR)
    np.save(out.replace('.wav', '_pitch.npy'), pitch[0][fr(P['pad']):])
    print('wrote', out, len(wav) / SR, 's  frames', nF, ' pitch range', pitch.min().round(1), pitch.max().round(1))
if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'vox_ds.wav')
