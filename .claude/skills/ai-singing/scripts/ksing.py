# Kokoro-as-singer: override per-token durations and the F0 curve inside the neural decoder
import numpy as np, onnxruntime as ort, soundfile as sf, re, sys
import syl
from kokoro_onnx import Kokoro
M = '../models'
K = Kokoro(f'{M}/kokoro-v1.0.onnx', f'{M}/voices-v1.0.bin')
so = ort.SessionOptions(); so.intra_op_num_threads = 4
PROBE = ort.InferenceSession(f'{M}/kokoro_probe.onnx', so)
SING = ort.InferenceSession(f'{M}/kokoro_sing.onnx', so)
SINGN = ort.InferenceSession(f'{M}/kokoro_singn.onnx', so)
INV = {v: k for k, v in K.tokenizer.vocab.items()}
HOP = 600; SR = 24000; FR = HOP / SR   # 25 ms per duration unit; F0 at 2x
VOICELESS = set('ptkfsʂɕxhʦʨꭧʰ')
VOWELS = set('aeiouɤəɛɨyʊɔæɑɪʏœøɐɚ')
def toks(ph): return K.tokenizer.tokenize(ph)

def syl_parts(ph):
    """split one syllable's phonemes into onset / nucleus / coda char lists"""
    p = ph.replace('→', '')
    i = 0
    while i < len(p) and p[i] not in VOWELS and p[i] not in 'jwɥ': i += 1
    onset = p[:i]; rest = p[i:]
    m = re.match(r'([jwɥ]?)(.*?)([nŋ]?)$', rest)
    glide, nuc, coda = m.group(1), m.group(2), m.group(3)
    if not nuc: nuc, glide = glide or 'ə', ''
    return onset, glide, nuc, coda

CARRIER = ('今天天气很好我们一起去公园散步然后再去图书馆看书', '晚上回家以后跟爸爸妈妈一起吃饭聊天说说今天的事情')
def render_phrase(notes, voice, style_len_bias=0, f0fn=None, nfix=None, carrier=True):
    """notes: list of dict(ch, t(sec), len(sec), hz_curve fn); returns audio, t0 (sec of audio sample 0)"""
    phs = [syl.ipa(n['ch']) for n in notes]
    # token list per syllable with role tags
    T, roles, owner = [], [], []
    for si, ph in enumerate(phs):
        seen_v = False; tone_seen = False
        for c in ph:
            if c == '→': role = 'tone'; tone_seen = True
            elif tone_seen and c in 'nŋ': role = 'co'
            elif c in VOWELS: role = 'nu'; seen_v = True
            elif c in 'jwɥ' and not seen_v: role = 'gl'
            elif not seen_v: role = 'on'
            else: role = 'nu'
            for x in toks(c): T.append(x); roles.append(role); owner.append(si)
    ca = cb = []
    if carrier:
        ca = toks(''.join(syl.ipa(c, flat=False) for c in CARRIER[0])) + toks(',')
        cb = toks(',') + toks(''.join(syl.ipa(c, flat=False) for c in CARRIER[1]))
    seq = [0] + ca + T + cb + [0]
    style = K.voices[voice][min(len(T) + style_len_bias, 509)]
    out = PROBE.run(None, {'tokens': np.array([seq], np.int64), 'style': style, 'speed': np.array([1.0], np.float32)})
    natall = out[1].ravel(); nat = natall[1 + len(ca):1 + len(ca) + len(T)]
    nat_ca = natall[1:1 + len(ca)]; nat_cb = natall[1 + len(ca) + len(T):-1]
    # ---- assign durations so each syllable's nucleus starts on its beat
    lead = 6  # frames of silence before first onset
    t0 = notes[0]['t']
    dur = np.zeros(len(T))
    # place syllables on absolute frame grid relative to phrase start
    onsets = []
    for si, n in enumerate(notes):
        idx = [k for k in range(len(T)) if owner[k] == si]
        on_frames = sum(min(nat[k], 4) for k in idx if roles[k] == 'on')
        onsets.append((si, idx, on_frames))
    base = t0 - (onsets[0][2] + lead) * FR   # audio time of frame 0
    cursor = float(lead)  # frames used so far (lead pad is its own token)
    for si, idx, onf in onsets:
        n = notes[si]
        beat_f = (n['t'] - base) / FR                      # frame where nucleus should start
        end_f = (n['t'] + n['len'] - base) / FR
        if si + 1 < len(notes):
            nn = notes[si + 1]; nxt_on = onsets[si + 1][2]
            nb = (nn['t'] - base) / FR - nxt_on
            end_f = nb if nn['t'] - (n['t'] + n['len']) < 0.03 else min(end_f - 1, nb)
        # onset tokens: fill from cursor to beat_f
        on_idx = [k for k in idx if roles[k] == 'on']
        gap = beat_f - cursor
        if on_idx:
            w = np.array([min(nat[k], 4) for k in on_idx], float)
            sil = max(0, gap - w.sum())
            w = w * (min(gap, w.sum()) / w.sum())
            for k, x in zip(on_idx, w): dur[k] = x
            dur[on_idx[0]] += sil
        else:
            # vowel-initial: silence must go somewhere -> add to previous syllable's last token
            if si == 0: pass
            elif gap > 0: dur[[k for k in onsets[si - 1][1]][-1]] += gap
        cursor = beat_f
        body = [k for k in idx if roles[k] != 'on']
        tot = max(2, end_f - cursor)
        fixed = {}
        for k in body:
            if roles[k] == 'gl': fixed[k] = min(nat[k], 2)
            elif roles[k] == 'co': fixed[k] = min(max(nat[k], 2), 3)
            elif roles[k] == 'tone': fixed[k] = 0.0
        nuc = [k for k in body if roles[k] == 'nu']
        rem = max(1.0, tot - sum(fixed.values()))
        for k in nuc: dur[k] = rem / len(nuc)
        for k, v in fixed.items(): dur[k] = v
        cursor += sum(dur[k] for k in body)
    dur_full = np.concatenate([[lead], dur, [8]]).astype(np.float32)
    natf0 = out[2].ravel()
    # integer frames with error diffusion (keeps the cumulative grid exact)
    cs = np.round(np.cumsum(dur_full)); di = np.diff(np.concatenate([[0], cs]))
    di = np.maximum(di, 0)
    di[1:-1] = np.where((di[1:-1] == 0) & (np.array(roles) != 'tone'), 1, di[1:-1])
    if carrier:
        dca = np.maximum(1, np.round(nat_ca)); dca[-1] = max(dca[-1], 4)
        dcb = np.maximum(1, np.round(nat_cb)); dcb[0] = max(dcb[0], 4)
        di_all = np.concatenate([[di[0]], dca, di[1:-1], dcb, [di[-1]]])
    else:
        di_all = di
    off = int(di[0] + (dca.sum() if carrier else 0))      # frames before phrase tokens
    base_all = base - (dca.sum() if carrier else 0) * FR
    nF = int(di_all.sum())
    # ---- F0 curve at 2x frame rate
    tt = base_all + (np.arange(2 * nF) + 0.5) * FR / 2
    f0 = f0fn(tt)
    if carrier:   # carriers spoken around the phrase's register
        mref = np.median(f0fn(np.array([n['t'] + 0.05 for n in notes])))
        a1 = int(2 * di[0]); a2 = int(2 * off); b1 = int(2 * (off + di[1:-1].sum())); b2 = int(2 * (nF - di[-1]))
        f0[a1:a2] = mref * 0.85; f0[b1:b2] = mref * 0.85
    # voiceless consonant frames -> 0
    edges = (np.concatenate([[0], np.cumsum(di[1:-1])]) + off - 1 + 1) * 2
    edges = np.concatenate([[0], edges]) if False else np.concatenate([[off * 2 - 2 * di[0]], edges])
    for k, r in enumerate(roles):
        if r == 'on' and INV.get(T[k], '') in VOICELESS:
            a, b = int(edges[k + 1]), int(edges[k + 2]); f0[a:b] = 0
    f0[:int(2 * di[0])] = 0; f0[int(2 * (nF - di[-1])):] = 0
    feed = {'tokens': np.array([seq], np.int64), 'style': style, 'speed': np.array([1.0], np.float32),
            'dur_in': di_all[None, :].astype(np.float32), 'f0_in': f0[None, None, :].astype(np.float32)}
    audio, N = SING.run(None, feed)
    info = dict(di=di, roles=roles, owner=owner, edges=edges, N=N.ravel().copy(), f0=f0, base=base, off=off)
    if nfix is not None:
        N2 = nfix(N.ravel().copy(), info)
        feed['n_in'] = N2[None, None, :].astype(np.float32)
        audio = SINGN.run(None, feed)[0]
        info['N2'] = N2
    audio = audio.ravel()
    if carrier:   # cut the carriers away: keep [lead before phrase .. end of phrase + tail]
        s0 = int((off - di[0]) * HOP); s1 = int((off + di[1:-1].sum() + 6) * HOP)
        audio = audio[s0:s1]
    return audio, base, info

def sustain_N(N, info, floor=5.5, release=0.06, accents=None):
    """hold vowel energy through stretched nuclei; the model was never trained on 1-second vowels"""
    e = info['edges'].astype(int); roles = info['roles']; owner = info['owner']
    N = N.copy(); fps = 2 / FR
    nsyl = max(owner) + 1
    for si in range(nsyl):
        ks = [k for k in range(len(roles)) if owner[k] == si and roles[k] in ('gl', 'nu', 'tone', 'co')]
        if not ks: continue
        a, b = e[ks[0] + 1], e[ks[-1] + 2]
        if b - a < 2: continue
        head = N[a:a + max(2, min(8, (b - a) // 3))]
        L = max(floor, float(np.max(head))) + (accents[si] if accents else 0)
        seg = np.full(b - a, L)
        tt = np.arange(b - a) / fps
        seg += 0.4 * np.minimum(1, tt / 0.25)          # slight swell
        r = int(release * fps)
        if r and b - a > r * 2:
            seg[-r:] -= np.linspace(0, 2.0, r)          # soft release
        N[a:b] = np.maximum(N[a:b], seg)
    return N
