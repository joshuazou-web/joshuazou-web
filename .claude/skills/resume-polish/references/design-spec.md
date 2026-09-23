# 设计参数（已被用户确认的版本）

这些数值是从用户认可的"解决方案版"PDF 里用 PyMuPDF 直接读出来的，`assets/template.html` 已全部内置。改动前先想清楚理由；用户对"更粗/更挤/更空"都很敏感。

| 元素 | 数值 |
|---|---|
| 页面 | A4，页边距 上 6.9mm / 右 8.7mm / 下 6mm / 左 9mm |
| 正文 | 8.64pt，行高 1.25（行距 10.8pt），颜色 #222222 |
| 中文正文字体 | 宋体系：Songti SC / STSong / SimSun / Noto Serif CJK SC；英文 Times New Roman / Liberation Serif |
| 加粗标签（"背景与目标："、关键数字） | 宋体 600、#3a3a3a —— 用黑体会过粗、压过蓝色标题 |
| 姓名 | 21.1pt，黑体系加粗 |
| 求职意向/联系方式/个人定位 | 8.82pt |
| 分区标题 | 13.43pt 黑体系、#2458b8，下方 0.72pt 蓝线 |
| 公司条 | 高 15.1pt、底色 #f0f1f4、圆角 4px；公司名 9.21pt 加粗 + 职位常规字重；日期 8.82pt 加粗 |
| 项目标题 | 9.21pt、#1f4e9c 加粗，分隔符 `|` 常规字重 |
| 子要点 | "○" 缩进 11.5pt |
| 公司 Logo / 校徽 | 16px / 14px，保持比例 |
| 右侧文档链接 | 8.44pt、#2458b8 加粗，如 `Product Report ↗` |

一行约 60–62 个中文字符；一行 ≈ 14px（测量脚本里的单位）。

## 从一份 PDF 反推设计参数

用户给出"照这个设计"的 PDF 时，不要看截图估，直接读：

```python
import pymupdf as f
from collections import Counter
pg = f.open('ref.pdf')[0]
c = Counter()
for b in pg.get_text('dict')['blocks']:
    for l in b.get('lines', []):
        for s in l['spans']:
            c[(s['font'], round(s['size'], 2), '#%06x' % s['color'])] += len(s['text'])
print(c.most_common(20))                       # 字体/字号/颜色
print([(round(l['bbox'][1], 1), ''.join(s['text'] for s in l['spans'])[:20])
       for b in pg.get_text('dict')['blocks'] for l in b.get('lines', [])][:40])  # 行距与左右边界
print({(tuple(round(x, 3) for x in d['fill']) if d.get('fill') else None) for d in pg.get_drawings()})  # 色块/线条颜色
```

Chromium 打印的 PDF 常带 0.96 缩放，所以会出现 8.64、9.21 这类数；直接照抄即可，不必还原。
