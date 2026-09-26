# 时间戳与作者证明 / Provenance

用于证明本方案由邹志华 (Zou Zhihua) 在下列时间首次公开发布，且内容未被篡改。做法与作者的另一部作品《被允许动的钱》一致：以公开仓库的提交历史作为同期记录，刻意保留、永不改写。

*Evidence that this concept was first published by Zou Zhihua at the time below and has not been altered. The commit history of this public repository is kept as a contemporaneous record and is never rewritten.*

## 一、三重时间证据 / Three independent time anchors

| # | 证据 | 内容 | 谁能改 |
| --- | --- | --- | --- |
| 1 | 首次发布提交 | `54fbf1e56c75254cee1f5acee262b19ceaad6292`，提交时间 2026-09-26T06:25:12Z | 提交哈希由全部文件内容计算，改动任何一个字节都会变 |
| 2 | GitHub 服务器记录 | 分支推送事件与 [Pull Request #12](https://github.com/joshuazou-web/joshuazou-web/pull/12) 的创建时间（2026-09-26 UTC） | 由 GitHub 服务器写入，作者无法修改 |
| 3 | SHA-256 文件指纹 | 见下表，发布时即写入本文件并随提交公开 | 任何人可在本地复核 |

## 二、文件指纹 / SHA-256

**首次发布版（提交 `54fbf1e`）**

```text
01419ddf515de30241cb1dfd7d6a24be26a1bc295572678a30be434fe374625a  README.md
6fa81894eef38d0e7a254ee13ba08f2af94d3382577d92eced5a4617d108cc42  DISCLAIMER.md
c5094816f6f68b3b1147f2a994280c2811e758ae470ce5bedf31f3d98e7b12af  LICENSE.md
953833a73e870f00c2dab9bc55f8899c6ba7523f7dff2ed5e9b514c90618d2e3  images/duo-split-ai-generated-unofficial-concept.png
```

**当前版（补充作者与版权章节、许可证改为与书相同的格式；方案正文与概念图未改）**

```text
52f7c400a8cf02e15fd36f771267bf54943b6e0cb7a97f41dd9dbab9f398db3c  README.md
6fa81894eef38d0e7a254ee13ba08f2af94d3382577d92eced5a4617d108cc42  DISCLAIMER.md
74a38f0328c1a54bbdcebfb1321767a1e245997b2c3976b647dd3f11d270fdfb  LICENSE
953833a73e870f00c2dab9bc55f8899c6ba7523f7dff2ed5e9b514c90618d2e3  images/duo-split-ai-generated-unofficial-concept.png
```

概念图的指纹两版相同，说明图片自首次发布起从未改动。

## 三、如何复核 / How to verify

```bash
git clone https://github.com/joshuazou-web/joshuazou-web
cd joshuazou-web
git show --stat 54fbf1e                       # 首次发布提交及其时间
git log --follow -- concepts/iphone-duo-split # 全部修改记录
cd concepts/iphone-duo-split && sha256sum README.md DISCLAIMER.md LICENSE images/*.png
```

## 说明 / Notes

- 本地提交时间可由提交者设定，因此以 GitHub 服务器端时间（推送、PR 创建与合并时间）为准。
- 以后每次修改都会产生新的提交和新的指纹，旧版本在历史中永久可查；请以版本号区分（当前 v1.2）。
- 方案文字与概念图由 AI 生成，本文件证明的是**发布时间与发布者**，不是对 AI 生成内容主张超出法律允许范围的权利。
