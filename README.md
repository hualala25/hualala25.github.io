# hualala25.github.io

个人站点仓库。根路径是一个索引页，下面是各个并列子站：

| 路径 | 内容 | 源码位置 |
|---|---|---|
| `/Assignment1/` | 《你当像鸟飞往你的山》· 交互式名著解说作品 | `Assignment1/`（纯静态） |
| `/her-march/` | 《她的行军》· 交互式三维叙事作品 | 独立仓库 [hualala25/her-march](https://github.com/hualala25/her-march) |

## 部署

主仓库使用 GitHub Actions 构建（`.github/workflows/deploy.yml`）：

1. `Assignment1/` 原样复制到 `_site/Assignment1/`
2. 根路径使用 `.github/placeholder/index.html` 作为索引页
3. 合并上传为 Pages 站点

推送到 `main` 分支即自动发布。

## 放新内容

在仓库里新建一个目录（如 `Assignment2/`），把静态文件放进去，再在 workflow 的 Assemble 步骤里加两行复制逻辑：

```bash
if [ -d Assignment2 ]; then
  mkdir -p _site/Assignment2
  rsync -a --exclude '.gitkeep' Assignment2/ _site/Assignment2/
fi
```

如果内容需要构建流程（Astro、Vue 等），在 workflow 里补上 `npm ci && npm run build`，把 `dist/` 复制到对应位置。

索引页在 `.github/placeholder/index.html`，新增子站后记得同步加一条入口。

## 图片

图床仓库是 [hualala25/images](https://github.com/hualala25/images)（PicGo 上传），引用形式：

```
https://hualala25.github.io/images/xxx.webp
```
