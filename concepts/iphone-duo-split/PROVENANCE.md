# 时间戳与文件指纹 / Provenance

用于证明本方案在某一时间点已由作者公开发布、且内容未被篡改。
*Evidence that this concept was published by the author at a given time and has not been altered since.*

| 项目 | 内容 |
| --- | --- |
| 作品 | iPhone Duo Split 产品概念方案 v1.2（AI 生成的非官方概念，与 Apple 无关） |
| 作者 / 发布者 | 邹志华 (Zou Zhihua) · GitHub `joshuazou-web` |
| 首次公开时间 | 2026-09-26T06:23:39Z (UTC) |
| 独立时间证据 | 本目录首次合入的 Git 提交哈希及 GitHub 服务器记录的提交/合并时间 |

## SHA-256 文件指纹 / File hashes

以下哈希在首次提交前生成。任何人可在本地运行 `sha256sum` 复核；结果一致即说明文件与首次发布版本完全相同。
*Generated before the first commit. Re-run `sha256sum` to verify.*

```text
01419ddf515de30241cb1dfd7d6a24be26a1bc295572678a30be434fe374625a  README.md
6fa81894eef38d0e7a254ee13ba08f2af94d3382577d92eced5a4617d108cc42  DISCLAIMER.md
c5094816f6f68b3b1147f2a994280c2811e758ae470ce5bedf31f3d98e7b12af  LICENSE.md
953833a73e870f00c2dab9bc55f8899c6ba7523f7dff2ed5e9b514c90618d2e3  images/duo-split-ai-generated-unofficial-concept.png
```

复核命令 / Verify:

```bash
cd concepts/iphone-duo-split
sha256sum -c <<'SUMS'
01419ddf515de30241cb1dfd7d6a24be26a1bc295572678a30be434fe374625a  README.md
6fa81894eef38d0e7a254ee13ba08f2af94d3382577d92eced5a4617d108cc42  DISCLAIMER.md
c5094816f6f68b3b1147f2a994280c2811e758ae470ce5bedf31f3d98e7b12af  LICENSE.md
953833a73e870f00c2dab9bc55f8899c6ba7523f7dff2ed5e9b514c90618d2e3  images/duo-split-ai-generated-unofficial-concept.png
SUMS
```

## 说明 / Notes

- Git 提交时间可以由提交者在本地设定，因此更可靠的时间依据是 GitHub 服务器端记录（PR 创建/合并时间、推送事件）。
- 若需要第三方可信时间戳，可在本地对上述文件运行 [OpenTimestamps](https://opentimestamps.org/)（`ots stamp <file>`），把生成的 `.ots` 证明文件追加提交到本目录；或将本目录打包后到公证/版权登记机构办理作品登记。
- 后续修改会产生新的提交和新的哈希；请以版本号区分（当前为 v1.2）。
