# 把报告/作品放到 GitHub 并在简历里引用

## 放哪里、怎么链

- 仓库 `joshuazou-web/joshuazou-web` 的 `evidence/` 目录，`evidence/README.md` 维护一张"文件 | 说明"索引表。
- 简历公司条右侧加链接：`<a class="doc-link" href="https://github.com/joshuazou-web/joshuazou-web/blob/main/evidence/<文件>.pdf">Product Report ↗</a>`；PDF 与 Word 都会保留可点击链接。
- 链接指向 `main`，所以要走 PR 并合并后才生效；用 **Squash 合并**，避免被替换掉的旧文件留在 main 的历史里。
- 合并后 raw.githubusercontent.com 有约 5 分钟缓存，验证时用 `git show origin/main:<path>` 读真实内容。

## 公开前必须处理

仓库是公开的：

- **他人隐私**：队友学号、手机号等一律去掉（PyMuPDF 按文字搜索后 `add_redact_annot` + `apply_redactions`，再全文检查一次正则如 `A0\d{6}[A-Z]`）。姓名作为署名可以保留。
- **本人手机号**：简历文件本身不要提交到公开仓库；交付给用户即可。

## 课程作业 → 专业报告

用户不希望作品看起来像学校作业时：

1. 用 HTML 做一张与正文风格一致的封面（同衬线字体、黑白、细线、项目图标），标题如 "Product & Technical Report"，底部保留团队署名与日期；不写课程号、学期、"Group"。
2. 替换每页的课程页眉：搜索页眉区域的文字 → 白色 redact → 用 `insert_text`（`tiro` 字体，同字号）写入新页眉。
3. 保留正文里指向真实代码仓库的链接（即使其中带课程号），改了会断链——在交付说明里说明即可。
4. 封面署名不给本人加角色标签（如 "Product Lead"），除非团队内有共识。
5. 文件名去掉 "Final_Report" 这类作业味，推荐 `<Project>_Product_Report.pdf`，简历链接文字同步为 `Product Report ↗`。
