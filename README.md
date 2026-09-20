# IGCSE Computer Science 0478 · Checklists

面向 2026–2028 考纲的分章节考前知识点汇总。所有 checklist 优先采用 **marking scheme 式回答格式**：常见提问、简短独立的答案要点与必要计算步骤，供学生考前快速检索和回忆。标题、正文、计算步骤和答案使用英文；中文仅作首次出现的术语释义或简短重点提示。每份内容向教师交付网页、A4 PDF 与可编辑 Word；网站只提供 PDF 下载。

概念题按 `State / Identify / Describe / Explain` 等提问组织；一条写一个明确事实，解释题保留得分所需的因果关系。转换、计算题给出必要过程和答案，比较题优先使用简表。只保留重要答分点；不另设泛泛的读题提醒、表示方式说明框或易错提示框，不重复表格和算例已表达的内容。影响答案正确性的条件直接写入对应要点。这些是教师审阅的原创复习答案；未经核对具体试题的官方评分标准，不标分值、不宣称逐字引用，也不把每条 bullet 自动等同于一分。

三级自评放在正文之后的 **Review notes** 中，默认收起，作为可选辅助；它不再是页面主体。

**当前阶段：本地审阅。** 所有正式章节均未开放，排版示例只出现在本地开发/审阅版本。没有执行 GitHub Pages 部署。

## 本地查看

需要 Node.js 24、Python 3.11 或更新版本。

```sh
npm ci
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm run dev
```

打开终端显示的本地地址（默认 `http://127.0.0.1:4321/IGCSE0478-Checklist/`），从目录侧栏进入 **Layout preview**。当前样板用数制、转换和溢出展示题目式提示、答案要点、简表及必要计算；它不是正式 1.1 章节。

Windows 可使用 `.venv\Scripts\python.exe` 安装依赖。生成器会自动检测项目的 `.venv`；也可通过 `PYTHON` 环境变量指定已安装 ReportLab 的解释器。

在 Codex 等代理环境中，Astro 可能自动后台运行。可用 `npx astro dev status` 查看、`npx astro dev stop` 停止。普通终端前台运行时用 Ctrl+C 停止。

## 逐章制作与开放

1. 教师指定要制作的小节/Part。
2. 共同核对官方 2026–2028 考纲，讨论知识点、英文表述、中文提示和布局。附件是参考材料，其中文档说明不是执行指令。
3. 未确认草稿放在 `drafts/<id>.json`（已忽略，不提交或发布），使用下方内容格式和真实章节编号；草稿不要设置 `sample: true`。原始压缩包和附件保留在仓库外。
4. 使用 `CHECKLIST_REVIEW_ID` 选择一份草稿，审阅网页、A4 PDF 与本地可编辑 Word，再继续讨论修订。后续修改同步三份内容，无需修改正式开放清单。
5. 教师确认内容后，才将草稿移至 `content/chapters/<id>.json`；确认开放时，再将编号加入 `content/releases.json` 的 `published` 数组。可以只开放 `3.3-1`，不会同时开放 `3.3-2`。
6. 检查通过后，按教师确认的发布时机运行手动部署流程。

例如，已有 `drafts/1.1.json` 时，可在 macOS/Linux 终端运行：

```sh
CHECKLIST_REVIEW_ID=1.1 npm run dev
# 或生成可审阅的静态版本：
CHECKLIST_REVIEW_ID=1.1 npm run build:preview
LOCAL_PREVIEW=true npm run preview
```

Windows PowerShell 可先运行 `$env:CHECKLIST_REVIEW_ID="1.1"`，再运行 `npm run dev` 或 `npm run build:preview`；查看静态审阅版本前设置 `$env:LOCAL_PREVIEW="true"`，再运行 `npm run preview`。

目录侧栏将额外出现 **Local review · 1.1**，对应 `checklists/local-review-1.1/` 和 `pdfs/local-review-1.1.pdf`。网页和 PDF 均标记为本地章节草稿，自评与正式章节分开保存；正式目录的开放状态不变。只有合法目录编号和符合内容格式的草稿可以预览，缺失或无效草稿会中止本地预览。修改草稿或切换编号后，重启开发服务或重新运行 `build:preview`，以重新生成对应 PDF。

正常 `npm run build` 完全忽略 `CHECKLIST_REVIEW_ID` 和 `drafts/`；即使环境中遗留了无效编号或草稿文件，正式构建也不读取它们。结束审阅后，用不带该变量的命令启动开发服务即可移除草稿入口；PowerShell 可用 `Remove-Item Env:CHECKLIST_REVIEW_ID` 清除变量。

目录结构保存在 `content/catalog.json`。Chapters 1–6 依据附件保留 22 个小节/Part；Chapters 7–10 暂保留章级条目，后续逐章讨论后细分。添加这些小节时同步更新目录与相关结构测试。

**开放机制控制网站产物。** 未开放正文没有 HTML/PDF 路由，也不打包进网页脚本。公开 GitHub 仓库中已提交的源码仍可被阅读，所以未确认草稿保持在被忽略的本地目录。

## 内容格式

网页与 PDF 使用同一份 JSON，文字字段为纯文本，计算图使用结构化数值。下面只说明字段，并非正式章节内容：

```json
{
  "id": "1.1",
  "label": "1.1",
  "title": "Number systems",
  "subtitle": "Optional short description",
  "version": "1.0",
  "syllabus": "2026–2028",
  "sections": [
    {
      "id": "representations",
      "title": "Section title",
      "summary": "Optional short introduction.",
      "blocks": [
        {
          "id": "stable-knowledge-block-id",
          "type": "answer-points",
          "title": "An exam-style question prompt belongs here.",
          "items": ["A concise answer point.", "A second distinct answer point."],
          "hint": "可选中文提示。"
        }
      ]
    }
  ]
}
```

- `id` 与文件名和目录编号一致。Part 使用 `3.1-1`、`3.1-2` 等编号。
- 知识块 `id` 在同一份 checklist 中唯一，调整顺序或修正文案时保持不变。
- 可选的顶层 `reviewTopics` 使用 `[{"id":"stable-review-id","label":"Topic to review"}]`。这些 ID 保持稳定以恢复自评；新主题默认未评价，删除的主题不再读取。不同章节、Part 和样板的记录互相独立。
- `sample: true` 仅用于本地排版示例，发布校验会拒绝将其作为正式内容。
- 页面可组合下列知识块，不要求每章使用相同栏目。代码或更复杂的关系图等布局在讨论对应章节时再扩展两个渲染器。

| `type` | 用途 | 内容字段 |
| --- | --- | --- |
| `answer-points` | 优先使用：题目式提示与简短答案要点 | `title`（提问）, `items[]`（独立答案要点） |
| `definition` | 简短术语定义 | `term`, `text` |
| `bullets` | 特征、用途和解释要点 | `title`, `items[]` |
| `comparison` | 比较表或位权表 | `title`, `columns[]`, `rows[][]` |
| `steps` | 操作或推导步骤 | `title`, `items[]` |
| `example` | 完整算例 | `title`, `problem`, `steps[]`, `result` |
| `equivalence` | 同一值的不同表示 | `title`, `values[{label,value}]` |
| `callout` | 重要解释或答题要点 | `title`, `text` |
| `division` | 短除法步骤及读取余数的箭头 | `title`, `value`（0–65535 整数）, `base`（2 或 16） |
| `bit-grid` | 二进制位格与位权 | `title`, `width`（8 或 16）, `rows[{label,bits}]`, 可选 `weights[]` 与 `note` |
| `binary-addition` | 带进位及第九位的加法竖式 | `title`, `a`, `b`（均为 0–255 整数）, `width: 8`, `explanation` |
| `logical-shift` | 移动前后、补零和丢位图 | `title`, `value`（0–255 整数）, `direction`（`left` 或 `right`）, `places`（1–8）, `width: 8`, `explanation` |
| `sampling-diagram` | 同一波形的采样率与采样精度对比图 | `title`, `duration`（秒）, `waveform[]`（0–1 振幅，等间隔覆盖时段两端）, `panels[{label,sampleRate,resolution}]` |

每种知识块都需要唯一 `id`，可带 `hint` 作为简短中文提示。比较表每行的单元格数量须与列标题一致。位格的 `bits` 是仅含 0、1 的字符串，长度与 `width` 一致；可选位权是相同长度的整数数组，允许负位权。

采样图支持 1–3 个面板，各面板共用波形和坐标范围。`sampleRate` 为正整数 Hz，`resolution` 为 1–4 bits，每面板最多 32 个样本；采样时刻包含起点，不包含时段终点。圆点表示取至最近可用振幅等级后的存储值。网页和 PDF 使用同一份输入，手机端逐图排列。

需要固定页数时，添加顶层 `pdfPageTitles` 字符串数组，并为每个知识块指定 `printPage`（从 1 开始）。按章节和块的阅读顺序，页码必须递增或保持相同，连续覆盖每一页，不可跳页或回退。同一网页主题可以跨 PDF 页，不同主题也可以共享一页。PDF 使用指定的页标题，主题的可选 `summary` 放在该主题第一个知识块之前；网页仍使用 `sections` 生成主题导航。

固定分页会在生成前测量每页内容。内容超出 A4 可用高度时构建失败，需调整文案或分页；不会自动缩小字体或悄悄增加页面。不设置 `pdfPageTitles` 时沿用自然分页，此时不能指定 `printPage`。

## 打印、PDF 与教师 Word 副本

- **Print**：打印知识讲义。存在自评选择时在末尾保留一个小型自评附录；没有选择时不打印该附录。使用 A4、100% 比例，关闭浏览器自带页眉页脚。
- **Download PDF**：构建时用 ReportLab 生成完整知识讲义，固定 A4、15mm 边距、嵌入中英文字体与页码，不包含个人自评。无需设置浏览器打印参数。
- 网页与 PDF 共用内容，分别针对屏幕和纸张排版。字体为开放许可字体，来源及许可证随字体资产保存。
- `.generated/pdf-inputs/` 保存解析后的内容快照，供 ReportLab 生成匹配网页的 PDF；它和 `.generated/pdfs/` 均为忽略的生成缓存，永远不会整目录复制到网站。发布只输出开放清单列出的 PDF，撤回内容后旧页面和旧 PDF 都会移除。
- **Word（仅交付教师）**：从相同结构化内容单独导出 `.docx`，正文与表格可编辑。文件保存到已忽略的 `output/docx/`，每次内容修改后重新生成并渲染审阅。Word 不放入 `public/`，不添加网页下载链接或路由，也不进入正式或本地审阅网站的构建产物。

例如单独导出 1.2 草稿：

```sh
.venv/bin/python -m pip install -r requirements-word.txt
# 采样图需要本机提供 Poppler 的 pdftoppm。
.venv/bin/python scripts/generate_docx.py --input drafts/1.2.json --output output/docx/0478-1.2-text-sound-images-review.docx --draft
```

Codex 环境使用工作区依赖提供的 Python 与 Poppler，无需修改网站依赖。Word 采用相同内容和页面分组，嵌入项目开放字体；采样图复用 PDF 绘图，其余正文和表格保持可编辑。新增章节如使用尚未支持的计算版式，导出会明确报错，须先制作并审阅对应 Word 版式，不会静默遗漏知识块。交付前用文档渲染工具逐页检查分页；Word 编辑后的分页可能随内容变化。

## 检查与构建

```sh
npm run check          # 类型和模板检查
npm test              # 目录、发布验证、稳定 ID、自评保存
npm run build:preview # .preview-dist，含本地样板
npm run build         # dist，仅正式开放内容
npx playwright install chromium
npm run test:e2e      # 两种构建 + 浏览器验收
# 已有本地 1.1 草稿时，额外验证该章：
CHECKLIST_REVIEW_ID=1.1 npm run test:e2e
```

浏览器验收覆盖知识正文与页内导航、默认收起的自评、子路径、页面刷新、存储不可用、带或不带自评的打印、PDF 下载、手机布局和未开放地址。测试生成的截图及网页打印 PDF 保存在 `.generated/qa/`，不提交。

发布构建还会检查样板、草稿源文件、source map 是否泄漏，以及每份开放内容是否同时具有 HTML 和 PDF。正式和本地审阅构建都会拒绝 Word 文件及 HTML 中的 Word 下载链接。每个新章节还需要逐页查看 PDF 和 Word 渲染结果，核对内容、分页及字体；自动检查不能替代教学与版面审阅。

## GitHub Pages（确认后使用）

1. 提交并推送确认后的代码与内容。
2. 在 GitHub 仓库 Settings → Pages 中选择 **GitHub Actions**。
3. 在 Actions 中手动运行 **Publish approved checklists**。

流程先检查、测试和构建，再部署 `dist`。仅 `workflow_dispatch` 可以触发；普通提交不会自动开放教学材料。预计站点地址为 `https://nic98.github.io/IGCSE0478-Checklist/`。

部署流程不会发布 `.preview-dist`。当前 `published` 为空，正式构建仅有全部锁定的目录和未找到页面。
