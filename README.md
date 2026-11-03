# hualala25.github.io

个人站点仓库。根路径是一个索引页，下面是三个并列子站：

| 路径 | 内容 | 源码位置 |
|---|---|---|
| `/Assignment1/` | 《你当像鸟飞往你的山》· 交互式名著解说作品 | `Assignment1/`（纯静态） |
| `/Assignment2/` | 课程作业与学年论文 | `assignment2/`（Astro） |
| `/her-march/` | 《她的行军》· 交互式三维叙事作品 | 独立仓库 [hualala25/her-march](https://github.com/hualala25/her-march) |

## 部署

主仓库使用 GitHub Actions 构建（`.github/workflows/deploy.yml`）：

1. 在 `assignment2/` 下 `npm ci && npm run build` 生成 Astro 产物
2. 产物复制到 `_site/Assignment2/`，`Assignment1/` 原样复制到 `_site/Assignment1/`
3. 根路径生成索引页，合并上传为 Pages 站点

推送到 `main` 分支即自动发布。

## 博客的写作流程

博客收录课程作业与学年论文，内容来源只有作者本人提供的文档。

新增一篇：

1. 把源文档（.docx）转换：
   ```bash
   cd assignment2
   python3 tools/docx_to_md.py <源文件.docx> src/content/posts/<slug>.md \
     --title "标题" --summary "一句话摘要" \
     --category "课程作业" --course "课程名" \
     --date "2026-10-20" --tags "标签1,标签2" \
     --cover "https://hualala25.github.io/images/xxx.webp"
   ```
2. 图片上传到图床仓库 [hualala25/images](https://github.com/hualala25/images)，正文里引用 `https://hualala25.github.io/images/xxx.webp`
3. 提交推送，Actions 自动发布

`tools/docx_to_md.py` 按段落字号与 `pStyle` 判定标题层级，表格转 Markdown 表格，内嵌图按序号映射到图床链接。

## 分类

- **课程作业** — 策划案、读后感、调研报告等
- **学年论文** — 正式学术论文

分类由 frontmatter 驱动，新增文章或新增分类都不需要改页面代码。
