# hualala25.github.io

个人站点仓库。根路径是一个索引页，下面是各个并列子站：

| 路径 | 内容 | 源码位置 |
|---|---|---|
| `/Assignment1/` | 《你当像鸟飞往你的山》· 交互式名著解说作品 | `Assignment1/`（纯静态） |
| `/Assignment2/` | 新作品 | `Assignment2/`（纯静态） |
| `/her-march/` | 《她的行军》· 交互式三维叙事作品 | 独立仓库 [hualala25/her-march](https://github.com/hualala25/her-march) |

## 部署

主仓库使用 GitHub Actions 构建（`.github/workflows/deploy.yml`）：

1. `Assignment1/` 原样复制到 `_site/Assignment1/`
2. `Assignment2/` 原样复制到 `_site/Assignment2/`
3. 根路径生成索引页
4. 合并上传为 Pages 站点

推送到 `main` 分支即自动发布。

## 放新内容

`Assignment2/` 是静态目录，把文件放进去就能上线：

```
Assignment2/
├── index.html
└── ...（任意静态资源）
```

如果内容需要构建流程（比如 Astro、Vue 项目），在 `Assignment2/` 下加 `package.json` 并在 workflow 里补上构建步骤即可。

## 图片

图床仓库是 [hualala25/images](https://github.com/hualala25/images)（PicGo 上传），引用形式：

```
https://hualala25.github.io/images/xxx.webp
```
