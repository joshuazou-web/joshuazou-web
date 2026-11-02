# 天天向上 · 抖音30秒版 — written in C, transposed by KEY_SHIFT
BPM = 100
BEAT = 60 / BPM
BAR = 4 * BEAT
KEY_SHIFT = -3          # C -> A major (lead range E3..E4 for a young male voice)
# chords per bar (root midi in C, chord tones); bars 0..11
CHORDS = ['C', 'F', 'G', 'C', 'Am', 'F', 'G', 'C', 'Am', 'F', 'G', 'C']
SECTION = ['intro', 'pre', 'pre', 'hook', 'hook', 'hook', 'hook', 'hook', 'hook', 'hook', 'hook', 'tag']
# (bar, beat_in_bar, dur_beats, char, midi_in_C, accent)
N = []
def bar(b, *notes):
    for st, du, ch, m, *acc in notes:
        N.append(dict(bar=b, beat=st, dur=du, ch=ch, midi=m, acc=acc[0] if acc else 1.0, fall=acc[1] if len(acc) > 1 else 0))
# intro: count-in, then the hook name
bar(0, (0, .5, '一', 60, 1.1), (1, .5, '二', 62, 1.1), (2, .5, '三', 64, 1.15),
       (3, .5, '天', 67, 1.25), (3.5, .5, '天', 67, 1.25))
# pre-chorus: one step at a time
bar(1, (0, .5, '一', 57), (.5, .5, '步', 57), (1, .5, '一', 57), (1.5, .5, '步', 60), (2, 1.5, '走', 60, 1.1))
bar(2, (0, .5, '路', 59), (.5, .5, '就', 59), (1, .5, '会', 59), (1.5, .5, '变', 62),
       (2, .5, '宽', 64, 1.1), (2.5, 1.0, '广', 67, 1.2))          # beat 3.5-4: drop (silence)
# hook A
bar(3, (0, .5, '天', 55, 1.2), (.5, .5, '天', 55), (1, .5, '向', 57), (1.5, 2.0, '上', 60, 1.15))
bar(4, (0, .5, '天', 60, 1.2), (.5, .5, '天', 60), (1, .5, '向', 62), (1.5, 2.0, '上', 64, 1.2))
bar(5, (0, .5, '每', 65, 1.1), (.5, .5, '天', 64), (1, .5, '进', 62), (1.5, .5, '步', 60),
       (2, .5, '一', 62), (2.5, .5, '点', 60), (3, .5, '点', 57), (3.5, .5, '就', 64))
bar(6, (0, .5, '是', 62, 1.1), (.5, 3.0, '光', 62, 1.2))
# hook B (answers higher)
bar(7, (0, .5, '天', 55, 1.2), (.5, .5, '天', 55), (1, .5, '向', 57), (1.5, 2.0, '上', 60, 1.15))
bar(8, (0, .5, '天', 60, 1.2), (.5, .5, '天', 60), (1, .5, '向', 62), (1.5, 2.0, '上', 64, 1.2))
bar(9, (0, .5, '笑', 65, 1.1), (.5, .5, '着', 64), (1, .5, '出', 62), (1.5, .5, '发', 60),
       (2, .5, '汗', 62), (2.5, .5, '水', 64), (3, 1.0, '也', 62, 1.1))
bar(10, (0, .5, '闪', 62, 1.15), (.5, 3.0, '亮', 67, 1.3, 2))
# tag
bar(11, (0, .5, '嘿', 67, 1.3), (1, .5, '一', 60), (1.5, .5, '起', 62), (2, .5, '向', 69, 1.15), (2.5, 1.5, '上', 67, 1.35, 2))
for n in N:
    n['t'] = (n['bar'] * 4 + n['beat']) * BEAT
    n['len'] = n['dur'] * BEAT
    n['m'] = n['midi'] + KEY_SHIFT
LINES = [  # on-screen lyric lines: (first note idx, last note idx)
]
def lines():
    out, cur = [], []
    brk = {(1, 0), (2, 0), (3, 0), (5, 0), (5, 3.5), (7, 0), (9, 0), (10, 0), (11, 0)}
    for i, n in enumerate(N):
        if (n['bar'], n['beat']) in brk and cur: out.append(cur); cur = []
        cur.append(i)
    out.append(cur)
    return out
TOTAL = 12 * BAR + 1.2
