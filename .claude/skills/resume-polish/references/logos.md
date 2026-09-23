# Logo 与图标

`assets/logos/` 已有：NUS、MUST（澳科大，已加深为藏蓝）、Cambridge、Columbia、华泰、Sequoia、奇绩（MiraclePlus）、广发（CGB）、GitHub，以及用户自己的项目图标（ThinkBeforeClick 盾牌、AI Star、横琴厂房、潮汕店铺）。新增的 Logo 放同目录，SVG 需要再跑 `scripts/svg2png.cjs` 生成 PNG 供 Word 使用。

## 网络受限时去哪找

云端会话通常只能访问 GitHub 和 npm，Wikipedia、Google favicon、Clearbit、各公司官网都会被拦。可用来源：

| 需要 | 来源（git clone 后取文件） |
|---|---|
| 中国银行类 | `cellier/bank-icon-cn` 的 `svg/` |
| 大量公司 SVG | `detain/svg-logos`（用 `--filter=blob:none --no-checkout` 后 `git ls-tree` 搜文件名，再单独 checkout） |
| 大学校徽 | 各校 LaTeX beamer/论文模板仓库，如 NUS-Slides-Latex-Template、MUST-Thesis、CambridgeUK-Beamer、CU_Beamer |
| 公司自己的素材 | 公司 GitHub 组织里的 banner 图（如奇绩的仓库图片），从中裁出标志 |

搜索仓库用 WebSearch（"github <学校> beamer template logo"），GitHub API 搜索在会话里不可用。实在找不到（如华泰），直接请用户发一张 Logo 截图——比画一个仿冒 Logo 好得多。

## 裁剪与去底

- 从"徽标 + 文字"的横版图里只要徽标：按列扫描非白像素，遇到足够宽的空白列就截断。
- 浅色水印式校徽：按亮度映射成单色（藏蓝 `#003380`）并用亮度做透明度。
- 用户截图里的 App 图标：按高饱和度像素求外接框，再套圆角遮罩（半径约 20%）。
- 横版 SVG 只要图形部分：改 `viewBox` 裁到图形区域。

所有 Logo 只用真实品牌素材；不确定是不是官方标志时宁可只写文字。
