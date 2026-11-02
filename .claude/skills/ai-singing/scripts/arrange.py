# Backing track: GM arrangement rendered with FluidSynth (FluidR3_GM)
import pretty_midi as pm, numpy as np, subprocess, score as S
B = S.BEAT; T = S.KEY_SHIFT
CH = {'C': (48, [60, 64, 67]), 'F': (41, [57, 60, 65]), 'G': (43, [59, 62, 67]), 'Am': (45, [57, 60, 64])}
def t(bar, beat): return (bar * 4 + beat) * B
def note(inst, p, s, e, v): inst.notes.append(pm.Note(velocity=int(np.clip(v, 1, 127)), pitch=int(p), start=s, end=e))
def build(seed=1, swing=0.0):
    rng = np.random.default_rng(seed)
    m = pm.PrettyMIDI(initial_tempo=S.BPM)
    dr = pm.Instrument(0, is_drum=True, name='drums')
    bass = pm.Instrument(38, name='bass'); pno = pm.Instrument(0, name='piano'); brs = pm.Instrument(61, name='brass')
    strg = pm.Instrument(48, name='strings'); glk = pm.Instrument(9, name='glock'); pad = pm.Instrument(89, name='pad')
    hum = lambda: rng.normal(0, 0.006)
    for b, (cn, sec) in enumerate(zip(S.CHORDS, S.SECTION)):
        root, tones = CH[cn]; root += T; tones = [x + T for x in tones]
        hot = sec == 'hook'
        if sec == 'intro':
            for k in range(4): note(pno, tones[k % 3] + 12, t(b, k), t(b, k + .9), 70 + 8 * k)
            for k in range(8): note(dr, 42, t(b, k / 2), t(b, k / 2) + .05, 50 + 6 * k)
            note(pad, root + 24, t(b, 0), t(b, 4), 55); note(bass, root, t(b, 3), t(b, 4), 70)
        elif sec == 'pre':
            for x in tones: note(pad, x, t(b, 0), t(b, 4), 60)
            note(strg, root + 12, t(b, 0), t(b, 3.5), 60 + 20 * (b - 1))
            for k in range(4):
                if not (b == 2 and k == 3): note(pno, tones[k % 3] + 12, t(b, k + .5), t(b, k + .9), 76)
            note(dr, 36, t(b, 0), t(b, .1), 100); note(dr, 36, t(b, 2), t(b, 2.1), 95)
            # snare build: 8ths in bar1, 16ths in bar2, stop at beat 3.5 (the drop)
            step = .5 if b == 1 else .25
            k = 0
            while k * step < (4 if b == 1 else 3.5):
                note(dr, 38, t(b, k * step) + hum(), t(b, k * step) + .05, 45 + 70 * ((b - 1) * 4 + k * step) / 8); k += 1
            for k in range(8 if b == 1 else 7): note(bass, root, t(b, k / 2), t(b, k / 2 + .4), 85)
        elif hot or sec == 'tag':
            if sec == 'tag':
                for x in [root, root + 12]: note(bass, x, t(b, 0), t(b, .45), 110)
                for x in tones + [tones[0] + 12]: note(brs, x + 12, t(b, 0), t(b, .4), 112)
                note(dr, 49, t(b, 0), t(b, 1), 120); note(dr, 36, t(b, 0), t(b, .1), 120); note(dr, 39, t(b, 0), t(b, .1), 110)
                for k, bb in enumerate([1, 1.5, 2, 2.5]):
                    note(dr, 42, t(b, bb), t(b, bb) + .05, 70)
                    note(bass, root + (0, 2, 4, 7)[k], t(b, bb), t(b, bb + .45), 95)
                # final hit on 上 and ring
                for x in tones + [tones[0] + 12, tones[1] + 12]:
                    note(brs, x + 12, t(b, 2.5), t(b, 4.4), 118); note(strg, x, t(b, 2.5), t(b, 4.6), 95)
                note(pno, root + 12, t(b, 2.5), t(b, 4.6), 110)
                for x in tones: note(pno, x + 12, t(b, 2.5), t(b, 4.6), 100)
                note(dr, 49, t(b, 2.5), t(b, 4.5), 127); note(dr, 36, t(b, 2.5), t(b, 2.6), 127); note(bass, root, t(b, 2.5), t(b, 4.4), 115)
                continue
            first = b == 3 or b == 7
            if first: note(dr, 49, t(b, 0), t(b, 2), 118)
            # boom-bap-pop groove
            for bb, v in ((0, 118), (1.75, 90), (2.5, 105)): note(dr, 36, t(b, bb), t(b, bb) + .1, v)
            for bb in (1, 3):
                note(dr, 38, t(b, bb) + hum(), t(b, bb) + .1, 112); note(dr, 39, t(b, bb) + .008, t(b, bb) + .1, 100)
            for k in range(8):
                note(dr, 42 if k != 7 else 46, t(b, k / 2) + hum(), t(b, k / 2) + .06, 72 + 14 * (k % 2 == 0))
            for k in range(16): note(dr, 54, t(b, k / 4) + hum(), t(b, k / 4) + .04, 38 + 22 * (k % 4 == 2))
            if b in (6, 10): # fill into next bar
                for k, p_ in enumerate([45, 45, 43, 43]): note(dr, p_, t(b, 3 + k / 4), t(b, 3 + k / 4) + .1, 90 + 6 * k)
            # bass: driving 8ths with octave pops
            pat = [0, 0, 12, 0, 0, 12, 0, 7]
            for k in range(8): note(bass, root + pat[k], t(b, k / 2), t(b, k / 2 + .42), 100 if k % 2 == 0 else 84)
            # piano offbeat stabs
            for k in range(4):
                for x in tones: note(pno, x + 12, t(b, k + .5), t(b, k + .85), 82)
            # strings sustain
            for x in tones: note(strg, x, t(b, 0), t(b, 4), 70)
            note(strg, tones[0] + 12, t(b, 0), t(b, 4), 64)
            # brass answers in the 天天向上 bars (space while the voice holds 上)
            if b in (3, 4, 7, 8):
                for x in tones: note(brs, x + 12, t(b, 2.5), t(b, 2.8), 100); note(brs, x + 12, t(b, 3), t(b, 3.6), 108)
            if b in (6, 10):
                for x in tones: note(brs, x + 12, t(b, 2.5), t(b, 3.0), 96); note(brs, x + 12, t(b, 3.5), t(b, 3.9), 108)
    # glockenspiel doubles the hook melody two octaves up (sparkle), only hook bars
    for n in S.N:
        if S.SECTION[n['bar']] == 'hook': note(glk, n['m'] + 24, n['t'], n['t'] + min(n['len'], .6), 72)
    for i in (dr, bass, pno, brs, strg, glk, pad): m.instruments.append(i)
    return m
def render(fn='inst.wav', **kw):
    m = build(**kw)
    m.write(fn.replace('.wav', '.mid'))
    subprocess.run(['fluidsynth', '-ni', '-q', '-g', '0.35', '-r', '44100', '-R', '1', '-C', '1', '-F', fn,
                    '/usr/share/sounds/sf2/FluidR3_GM.sf2', fn.replace('.wav', '.mid')], check=True)
    return fn
if __name__ == '__main__':
    import sys; print(render(sys.argv[1] if len(sys.argv) > 1 else 'inst.wav'))
