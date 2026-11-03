/**
 * base 路径工具。
 *
 * Astro 配置了 `base` 后，HTML 里手写的绝对路径不会自动补上 base 前缀，
 * 会直接 404。`import.meta.env.BASE_URL` 的值不带结尾斜杠
 * （如 "/Assignment2"），直接拼接会导致路径粘连。
 *
 * 所以全站所有站内链接与静态资源地址，一律通过 src() 生成。
 */
const raw = import.meta.env.BASE_URL ?? '/';

export const base = raw.endsWith('/') ? raw : `${raw}/`;

/** 拼接站内路径，自动处理 base 前缀与多余斜杠。 */
export function src(path = ''): string {
  const clean = String(path).replace(/^\/+/, '');
  return clean ? `${base}${clean}` : base;
}
