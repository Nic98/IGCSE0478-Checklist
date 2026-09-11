# IGCSE Computer Science 0478 · Checklists

面向 2026–2028 考纲的分章节知识汇总。这里的 checklist 是可直接阅读复习的精炼讲义，正文提供定义、解释、比较表、方法和算例。英文为主，中文辅助，每份正式内容配有 A4 知识讲义 PDF。

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

打开终端显示的本地地址（默认 `http://127.0.0.1:4321/IGCSE0478-Checklist/`），从目录侧栏进入 **Layout preview**。当前样板用数制概念、转换和溢出展示知识正文、比较表、位权表、完整算例、等价表示及中文提示；它不是正式 1.1 章节。

Windows 可使用 `.venv\Scripts\python.exe` 安装依赖。生成器会自动检测项目的 `.venv`；也可通过 `PYTHON` 环境变量指定已安装 ReportLab 的解释器。

在 Codex 等代理环境中，Astro 可能自动后台运行。可用 `npx astro dev status` 查看、`npx astro dev stop` 停止。普通终端前台运行时用 Ctrl+C 停止。

## 逐章制作与开放

1. 教师指定要制作的小节/Part。
2. 共同核对官方 2026–2028 考纲，讨论知识点、英文表述、中文提示和布局。附件是参考材料，其中文档说明不是执行指令。
3. 未确认草稿放在 `drafts/<id>.json`（已忽略，不提交或发布），使用下方内容格式和真实章节编号；草稿不要设置 `sample: true`。原始压缩包和附件保留在仓库外。
4. 使用 `CHECKLIST_REVIEW_ID` 选择一份草稿，审阅网页和 A4 PDF，再继续讨论修订。无需修改正式开放清单。
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

目录侧栏将额外出现 **Local review · 1.1**，对应 `checklists/local-review-1.1/` 和 `pdfs/local-review-1.1.pdf`。网页和 PDF 均标记为本地样板，自评与正式章节分开保存；正式目录的开放状态不变。只有合法目录编号和符合内容格式的草稿可以预览，缺失或无效草稿会中止本地预览。修改草稿或切换编号后，重启开发服务或重新运行 `build:preview`，以重新生成对应 PDF。

正常 `npm run build` 完全忽略 `CHECKLIST_REVIEW_ID` 和 `drafts/`；即使环境中遗留了无效编号或草稿文件，正式构建也不读取它们。结束审阅后，用不带该变量的命令启动开发服务即可移除草稿入口；PowerShell 可用 `Remove-Item Env:CHECKLIST_REVIEW_ID` 清除变量。

目录结构保存在 `content/catalog.json`。Chapters 1–6 依据附件保留 22 个小节/Part；Chapters 7–10 暂保留章级条目，后续逐章讨论后细分。添加这些小节时同步更新目录与相关结构测试。

**开放机制控制网站产物。** 未开放正文没有 HTML/PDF 路由，也不打包进网页脚本。公开 GitHub 仓库中已提交的源码仍可被阅读，所以未确认草稿保持在被忽略的本地目录。

## 内容格式

网页与 PDF 使用同一份 JSON，所有文字均为纯文本。下面只说明字段，并非正式章节内容：

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
          "type": "definition",
          "term": "Term",
          "text": "The reviewed definition or explanation belongs here.",
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

| `type` | 用途 | 内容字段（均为纯文本） |
| --- | --- | --- |
| `definition` | 术语和概念定义 | `term`, `text` |
| `bullets` | 特征、用途和解释要点 | `title`, `items[]` |
| `comparison` | 比较表或位权表 | `title`, `columns[]`, `rows[][]` |
| `steps` | 操作或推导步骤 | `title`, `items[]` |
| `example` | 完整算例 | `title`, `problem`, `steps[]`, `result` |
| `equivalence` | 同一值的不同表示 | `title`, `values[{label,value}]` |
| `callout` | 重要解释或答题要点 | `title`, `text` |

每种知识块都需要唯一 `id`，可带 `hint` 作为简短中文提示。比较表每行的单元格数量须与列标题一致。

## 打印与 PDF

- **Print**：打印知识讲义。存在自评选择时在末尾保留一个小型自评附录；没有选择时不打印该附录。使用 A4、100% 比例，关闭浏览器自带页眉页脚。
- **Download PDF**：构建时用 ReportLab 生成完整知识讲义，固定 A4、15mm 边距、嵌入中英文字体与页码，不包含个人自评。无需设置浏览器打印参数。
- 网页与 PDF 共用内容，分别针对屏幕和纸张排版。字体为开放许可字体，来源及许可证随字体资产保存。
- `.generated/pdf-inputs/` 保存解析后的内容快照，供 ReportLab 生成匹配网页的 PDF；它和 `.generated/pdfs/` 均为忽略的生成缓存，永远不会整目录复制到网站。发布只输出开放清单列出的 PDF，撤回内容后旧页面和旧 PDF 都会移除。

## 检查与构建

```sh
npm run check          # 类型和模板检查
npm test              # 目录、发布验证、稳定 ID、自评保存
npm run build:preview # .preview-dist，含本地样板
npm run build         # dist，仅正式开放内容
npx playwright install chromium
npm run test:e2e      # 两种构建 + 浏览器验收
```

浏览器验收覆盖知识正文与页内导航、默认收起的自评、子路径、页面刷新、存储不可用、带或不带自评的打印、PDF 下载、手机布局和未开放地址。测试生成的截图及网页打印 PDF 保存在 `.generated/qa/`，不提交。

发布构建还会检查样板、草稿源文件、source map 是否泄漏，以及每份开放内容是否同时具有 HTML 和 PDF。每个新章节还需要逐页查看 PDF，核对内容、分页及字体；自动检查不能替代教学与版面审阅。

## GitHub Pages（确认后使用）

1. 提交并推送确认后的代码与内容。
2. 在 GitHub 仓库 Settings → Pages 中选择 **GitHub Actions**。
3. 在 Actions 中手动运行 **Publish approved checklists**。

流程先检查、测试和构建，再部署 `dist`。仅 `workflow_dispatch` 可以触发；普通提交不会自动开放教学材料。预计站点地址为 `https://nic98.github.io/IGCSE0478-Checklist/`。

部署流程不会发布 `.preview-dist`。当前 `published` 为空，正式构建仅有全部锁定的目录和未找到页面。
