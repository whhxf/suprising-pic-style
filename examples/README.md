# 参考图说明

**这个目录默认不放图。**

8 种风格的参考图是小红书真实笔记的封面，版权归原笔记作者。放进公开仓库有风险，所以不入库。

## 本地怎么看

把参考图放在这个目录下，`.gitignore` 已经挡掉了：

```
examples/reference/*.jpg
examples/reference/*.png
```

命名建议 `S1-真人出镜+大字压脸.jpg` … `S8-爆炸贴纸标题.jpg`，和 `prompts/` 里的文件名对应。

## 如果你想让仓库自带参考图

先确认仓库是**私有**的，再删掉 `.gitignore` 里那两行，然后：

```bash
git add examples/reference
git commit -m "add reference covers"
```

## 更稳妥的替代方案

用提示词自己复刻 8 张，放进 `examples/generated/`。这些图的版权归你，可以公开。

复刻时注意：**不要复刻原图的文案和人物**，只复刻版式结构（构图、字号关系、配色关系）。
