import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  const posts = (await getCollection('posts')).sort(
    (a, b) => b.data.date.valueOf() - a.data.date.valueOf(),
  );

  return rss({
    title: '罗语墨 · 课程作业与论文',
    description: '课程作业与学年论文的整理记录',
    site: context.site ?? 'https://hualala25.github.io/Assignment2/',
    trailingSlash: true,
    items: posts.map((p) => ({
      title: p.data.title,
      description: p.data.summary,
      pubDate: p.data.date,
      link: `/Assignment2/posts/${p.id}/`,
      categories: [p.data.category, p.data.course, ...p.data.tags],
    })),
    customData: '<language>zh-cn</language>',
  });
}
