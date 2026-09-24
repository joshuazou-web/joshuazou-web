"""Generate the scrolling "featured projects" banner shown at the top of the profile.

Edit FEATURED below, then run:

    python3 scripts/build_featured_marquee.py

It writes assets/featured-marquee-zh-light.svg and assets/featured-marquee-zh-dark.svg.
The SVG scrolls with a CSS animation (GitHub renders it inside <img>) and stops
moving for viewers who ask for reduced motion.
"""

from pathlib import Path
from xml.sax.saxutils import escape

FEATURED = [
    {
        "no": "01",
        "tag": "金融合规 · 可运行原型",
        "title": "跨境支付反洗钱调查分诊方案",
        "repo": "CrossBorder RiskOps",
        "metric": "产能内精确率 0.223 → 0.870",
        "detail": "6,000 笔合成交易 · 20 条规则 · 453 项测试",
    },
    {
        "no": "02",
        "tag": "企业运营 · 完整数据管线",
        "title": "IT 工单智能分诊与运营看板",
        "repo": "OpsSignal",
        "metric": "自动接受 84% · 与人工一致 92.3%",
        "detail": "3,600 条合成工单 · 51 值分类法 · 166 项测试",
    },
    {
        "no": "03",
        "tag": "真实场景 · 脱敏报告",
        "title": "存量合同档案 LLM 梳理与确权",
        "repo": "Project Report A",
        "metric": "39 页扫描件 → 1 条时间线 + 5 份文书",
        "detail": "每条结论溯源原件 · 置信度分级 · 30 天计划",
    },
]

THEMES = {
    "light": {"bg": "#F4F1EB", "card": "#FBF9F5", "ink": "#171716", "muted": "#6B6760",
              "accent": "#8B6843", "rule": "#171716", "metric": "#171716"},
    "dark": {"bg": "#12110F", "card": "#1C1A17", "ink": "#F2EEE6", "muted": "#A39E94",
             "accent": "#D2A877", "rule": "#F2EEE6", "metric": "#F2EEE6"},
}

W, H = 1200, 260
CARD_W, CARD_H, GAP, TOP = 400, 196, 20, 32
PERIOD = len(FEATURED) * (CARD_W + GAP)  # width of one full set of cards
SECONDS = 24
FONT = "Arial,'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif"


def card(x, p, c):
    t = lambda s: escape(s)
    return f"""
    <g transform="translate({x},{TOP})">
      <rect width="{CARD_W}" height="{CARD_H}" fill="{c['card']}" stroke="{c['rule']}" stroke-width="2"/>
      <text x="24" y="36" font-size="14" letter-spacing="2.5" fill="{c['accent']}">精选 {p['no']} · {t(p['tag'])}</text>
      <text x="24" y="76" font-size="24" font-weight="700" fill="{c['ink']}">{t(p['title'])}</text>
      <text x="24" y="102" font-size="14" letter-spacing="1" fill="{c['muted']}">{t(p['repo'])}</text>
      <line x1="24" y1="122" x2="{CARD_W - 24}" y2="122" stroke="{c['rule']}" stroke-width="1" opacity="0.25"/>
      <text x="24" y="152" font-size="18" font-weight="700" fill="{c['metric']}">{t(p['metric'])}</text>
      <text x="24" y="178" font-size="13.5" fill="{c['muted']}">{t(p['detail'])}</text>
    </g>"""


def build(theme):
    c = THEMES[theme]
    cards = "".join(
        card(i * (CARD_W + GAP), p, c)
        for i, p in enumerate(FEATURED * 3)  # three sets keep the 1200px window full while looping
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="精选三项：{escape('、'.join(p['title'] for p in FEATURED))}">
  <style>
    .track {{ animation: flow {SECONDS}s linear infinite; }}
    @keyframes flow {{ from {{ transform: translateX(0); }} to {{ transform: translateX(-{PERIOD}px); }} }}
    @media (prefers-reduced-motion: reduce) {{ .track {{ animation: none; }} }}
  </style>
  <rect width="{W}" height="{H}" fill="{c['bg']}"/>
  <clipPath id="window"><rect x="0" y="0" width="{W}" height="{H}"/></clipPath>
  <g clip-path="url(#window)" font-family="{FONT}">
    <g class="track">{cards}
    </g>
  </g>
  <text x="{W - 20}" y="{H - 10}" text-anchor="end" font-family="{FONT}" font-size="12" letter-spacing="2" fill="{c['muted']}">SELECTED WORK · 向下查看全部项目 ↓</text>
</svg>
"""


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets"
    for theme in THEMES:
        path = out / f"featured-marquee-zh-{theme}.svg"
        path.write_text(build(theme), encoding="utf-8")
        print("wrote", path.relative_to(out.parent))
