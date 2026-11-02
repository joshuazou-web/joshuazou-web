# 1080x1920 lyric video, every character lit exactly when it is sung
import sys, math, random, numpy as np, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from multiprocessing import Pool
import score as S
W, H, FPS = 1080, 1920, 30
FB = '/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc'
def font(sz): return ImageFont.truetype(FB, sz, index=2)
F = {s: font(s) for s in (36, 44, 52, 64, 120, 132, 150, 220, 300)}
PAL = {'intro': ((18, 22, 64), (92, 36, 150), (255, 214, 90)),
       'pre': ((44, 40, 140), (232, 96, 150), (255, 236, 140)),
       'hook': ((255, 112, 40), (255, 46, 120), (255, 250, 130)),
       'tag': ((255, 86, 60), (120, 40, 220), (255, 250, 150))}
LINES = S.lines(); N = S.N
def sec_at(t): return S.SECTION[min(11, int(t / S.BAR))]
ys = np.linspace(0, 1, H)[:, None]
random.seed(4)
PART = [dict(x=random.uniform(0, W), y=random.uniform(0, H), v=random.uniform(80, 260), s=random.uniform(8, 24),
             arrow=random.random() < .4) for _ in range(50)]
DROP = (2 * 4 + 3.5) * S.BEAT       # silence before the hook
HOOK = 3 * S.BAR
def line_at(t):
    cur = 0
    for li, l in enumerate(LINES):
        if N[l[0]]['t'] - 0.25 <= t: cur = li
    return cur
def frame(fi):
    t = fi / FPS
    sec = sec_at(t); top, bot, acc = PAL[sec]
    bp = (t / S.BEAT) % 1; pulse = math.exp(-bp * 5) if t < S.TOTAL - 1.2 else 0
    hot = sec in ('hook', 'tag')
    g = (np.array(top) * (1 - ys) + np.array(bot) * ys)[:, None, :] * (1 + (0.16 if hot else 0.05) * pulse)
    img = Image.fromarray(np.clip(np.broadcast_to(g, (H, W, 3)), 0, 255).astype(np.uint8)).convert('RGBA')
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if hot or sec == 'pre':   # sunburst
        cx, cy, R = W / 2, H * 0.95, 2600; rot = t * (0.35 if hot else 0.12)
        for k in range(18):
            a0 = rot + k * 2 * math.pi / 18; a1 = a0 + math.pi / 36
            d.polygon([(cx, cy), (cx + R * math.cos(a0), cy - R * math.sin(a0)), (cx + R * math.cos(a1), cy - R * math.sin(a1))],
                      fill=(255, 255, 255, int(18 + 30 * pulse)))
    for p in PART:            # everything rises = 向上
        y = (p['y'] - t * p['v'] * (1.9 if hot else 1)) % (H + 120) - 60; s = p['s'] * (1 + .35 * pulse); x = p['x']
        if p['arrow']:
            d.polygon([(x, y - s * 1.6), (x - s, y), (x - s * .4, y), (x - s * .4, y + s * 1.2), (x + s * .4, y + s * 1.2), (x + s * .4, y), (x + s, y)], fill=(255, 255, 255, 110))
        else: d.ellipse((x - s / 2, y - s / 2, x + s / 2, y + s / 2), fill=(255, 255, 255, 80))
    # staircase: one step per hook bar, a little ball climbs it
    steps = 9; sw = 96; sh = 30; x0 = (W - steps * sw) / 2; yb = H - 150
    nb = int(np.clip((t - HOOK) / S.BAR + 1, 0, steps)) if t >= HOOK else 0
    for k in range(steps):
        lit = k < nb
        d.rectangle((x0 + k * sw, yb - (k + 1) * sh, x0 + (k + 1) * sw - 6, yb), fill=(255, 255, 255, 200 if lit else 46))
    if t >= HOOK - 0.2:
        k = min(steps - 1, max(0, nb - 1)); ph = ((t - HOOK) / S.BEAT) % 1
        bx = x0 + k * sw + sw / 2 - 3; by = yb - (k + 1) * sh - 30 - 40 * abs(math.sin(math.pi * ph))
        d.ellipse((bx - 26, by - 26, bx + 26, by + 26), fill=acc + (255,), outline=(60, 20, 60, 255), width=5)
    # header
    d.rounded_rectangle((70, 96, W - 70, 196), 50, fill=(0, 0, 0, 80))
    d.text((W / 2, 146), '《天天向上》 Unofficial MV', font=F[52], fill=(255, 255, 255), anchor='mm')
    # intro: count-in numbers + title stamp
    if t < S.BAR:
        k = int(t / S.BEAT); lt = t - k * S.BEAT; sc = 1 + 0.5 * math.exp(-lt * 9)
        txt = ['1', '2', '3', '天天!'][k]
        fz = F[300] if k < 3 else F[220]
        tf = font(int(fz.size * sc))
        d.text((W / 2 + 10, H * .40 + 12), txt, font=tf, fill=(0, 0, 0, 110), anchor='mm')
        d.text((W / 2, H * .40), txt, font=tf, fill=acc + (255,), anchor='mm', stroke_width=10, stroke_fill=(40, 10, 60))
    # lyrics: current line (karaoke per character) + next line
    li = line_at(t); idx = LINES[li]
    if t < S.BAR - 0.3: idx = []
    chars = [N[i] for i in idx]
    if not chars: chars = []
    big = F[150] if len(chars) <= 5 else (F[132] if len(chars) <= 7 else F[120])
    cy = H * (0.58 if t >= S.BAR else 0.64)
    bounce = -16 * pulse if hot else 0
    # wrap long lines into two rows
    rows = [] if not chars else [chars] if len(chars) <= 7 else [chars[:(len(chars) + 1) // 2], chars[(len(chars) + 1) // 2:]]
    lh = big.size * 1.18
    for r, row in enumerate(rows):
        w = sum(big.getlength(n['ch']) for n in row); x = (W - w) / 2
        y = cy + (r - (len(rows) - 1) / 2) * lh + bounce
        for n in row:
            cw = big.getlength(n['ch'])
            on = t >= n['t'] - 0.02; age = t - n['t']
            sc = 1 + (0.28 * math.exp(-age * 10) if on and age < 0.5 else 0)
            fz = font(int(big.size * sc)) if sc > 1.01 else big
            col = acc + (255,) if on else (255, 255, 255, 235)
            d.text((x + cw / 2 + 8, y + 10), n['ch'], font=fz, fill=(0, 0, 0, 120), anchor='mm')
            d.text((x + cw / 2, y), n['ch'], font=fz, fill=col, anchor='mm', stroke_width=7, stroke_fill=(40, 12, 70))
            x += cw
    if li + 1 < len(LINES) and t < S.TOTAL - 1.5:
        nxt = ''.join(N[i]['ch'] for i in LINES[li + 1])
        d.text((W / 2, cy + (len(rows) * lh) / 2 + 150), nxt, font=F[64], fill=(255, 255, 255, 150), anchor='mm')
    # gesture cue for 天天向上: ☝ ☝ ↑ ↑
    if hot:
        lab = '跟着比：☝  ☝  🙌  ⬆'
        d.rounded_rectangle((W / 2 - 300, H * .30 - 52, W / 2 + 300, H * .30 + 52), 52, fill=(0, 0, 0, 70))
        d.text((W / 2, H * .30), '跟着比  1 · 1 · 举手 · 跳', font=F[44], fill=(255, 255, 255, 230), anchor='mm')
    # ending CTA
    if t > S.TOTAL - 2.6:
        a = int(255 * min(1, (t - (S.TOTAL - 2.6)) / .4))
        d.rounded_rectangle((90, H * .17 - 70, W - 90, H * .17 + 70), 40, fill=(0, 0, 0, int(a * .45)))
        d.text((W / 2, H * .17), '你今天进步了哪一点？', font=F[64], fill=(255, 255, 255, a), anchor='mm')
        d.text((W / 2, H * .17 + 120), '#天天向上挑战', font=F[52], fill=acc + (a,), anchor='mm')
    d.text((W / 2, H - 60), 'AI 合成演唱 · 声库：绮萱 · DiffSinger', font=F[36], fill=(255, 255, 255, 200), anchor='mm')
    img = Image.alpha_composite(img, ov)
    # drop: freeze + flash into the hook
    if DROP <= t < HOOK:
        img = Image.blend(img, Image.new('RGBA', (W, H), (10, 10, 20, 255)), 0.75)
    if HOOK <= t < HOOK + 0.25:
        img = Image.blend(img, Image.new('RGBA', (W, H), (255, 255, 255, 255)), 0.8 * (1 - (t - HOOK) / 0.25))
    if hot and pulse > 0.6:   # tiny zoom punch on the beat
        z = 1 + 0.02 * pulse; cw_, ch_ = int(W / z), int(H / z)
        img = img.crop(((W - cw_) // 2, (H - ch_) // 2, (W + cw_) // 2, (H + ch_) // 2)).resize((W, H))
    return img.convert('RGB').tobytes()
def render(out, a=0, b=None):
    b = b or int(S.TOTAL * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for fr in pool.imap(frame, range(a, b), chunksize=8): p.stdin.write(fr)
    p.stdin.close(); p.wait()
if __name__ == '__main__':
    if sys.argv[1] == 'preview':
        for t in map(float, sys.argv[2:]):
            Image.frombytes('RGB', (W, H), frame(int(t * FPS))).resize((360, 640)).save(f'prev_{t}.png')
    else: render(sys.argv[1])
