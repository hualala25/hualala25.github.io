import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// site 指向 GitHub Pages 用户站点根域名，base 指定本项目所在的子路径。
// 仓库路径 /Assignment2/ → 线上路径 /Assignment2/
export default defineConfig({
  site: 'https://hualala25.github.io',
  base: '/Assignment2',
  integrations: [sitemap()],
  build: {
    format: 'directory',
  },
});
