import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

/**
 * 文章集合。
 *
 * 这个博客只收录两类内容：
 *   - 课程作业：策划案、读后感、调研报告、方案等
 *   - 学年论文：正式学术论文
 *
 * 分类（category）决定归属哪个分区，课程（course）标明出处。
 * 两者都由 frontmatter 驱动，新增文章不需要改任何页面代码。
 */
const posts = defineCollection({
  loader: glob({ base: './src/content/posts', pattern: '**/*.md' }),
  schema: z.object({
    /** 文章标题 */
    title: z.string(),
    /** 一句话摘要，用于卡片与列表 */
    summary: z.string(),
    /** 分类：课程作业 / 学年论文 */
    category: z.string(),
    /** 出处课程或来源说明 */
    course: z.string(),
    /** 完成日期 */
    date: z.coerce.date(),
    /** 标签 */
    tags: z.array(z.string()).default([]),
    /** 封面图（PicGo 图床链接） */
    cover: z.string().optional(),
  }),
});

export const collections = { posts };

/** 全站分类顺序，未列出的按字母排到后面。 */
export const CATEGORY_ORDER = ['课程作业', '学年论文'];

export function sortCategories(categories: string[]): string[] {
  return [...categories].sort((a, b) => {
    const ia = CATEGORY_ORDER.indexOf(a);
    const ib = CATEGORY_ORDER.indexOf(b);
    if (ia === -1 && ib === -1) return a.localeCompare(b, 'zh');
    if (ia === -1) return 1;
    if (ib === -1) return -1;
    return ia - ib;
  });
}
