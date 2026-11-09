# Photo credits

这个目录现在是空的 —— 上游的示例照片已经删掉了。把你自己的照片放进来，
一张一行，记下作者和来源，格式如下：

```
| 文件 | 作者 | 来源 | 许可 |
|---|---|---|---|
| photos/my-photo.jpg | 你的名字 | https://… | Unsplash License |
```

**要点**

- 来自 Unsplash 等图库的照片保留作者和链接；你自己拍的就写「本人拍摄」。
- 许可写清楚。Unsplash 允许免费商用与修改，但不允许原样出售照片或把它们做成竞品的图库。
- 明信片裁成 **148 : 105**，拍立得裁成 **1 : 1**；宽度 1200–1600 px，sRGB，JPEG q74–82。
- 同时在 `manifest.json` 里登记一条（file、use、place、caption_en、caption_ja、photographer、
  source、license、aspect），两份对照着写，漏了哪份就查不出来。
- 明信片和拍立得**不配图也好看**：没有 `src` 时，册子会自己画一片黄昏天空。
