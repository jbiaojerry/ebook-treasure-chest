# 如何创建搜索功能演示 GIF

> **注意**：当前 `.github/search-demo.gif` 是一个占位符。请按照以下步骤创建真实的演示 GIF。

## 🚀 方法 0: 使用自动化脚本（推荐）

我们提供了一个自动化脚本，可以自动访问 GitHub Pages 并生成演示 GIF：

```bash
# 1. 安装依赖
pip install playwright Pillow
playwright install chromium

# 2. 运行脚本
python scripts/generate_search_demo_gif.py
```

脚本会自动：
- ✅ 访问 GitHub Pages 页面
- ✅ 等待数据加载
- ✅ 执行多个搜索操作（"文学"、"历史"、"沟通 励志"）
- ✅ 截图并生成 GIF 动画
- ✅ 保存到 `.github/search-demo.gif`

**优点**：完全自动化，无需手动操作，可重复执行

## 方法 1: 使用 Kap（推荐，macOS）

1. 下载并安装 [Kap](https://getkap.co/)
2. 打开 GitHub Pages 页面：https://jbiaojerry.github.io/ebook-treasure-chest/
3. 使用 Kap 录制以下操作：
   - 展示页面加载和统计信息
   - 在搜索框输入关键词（如"文学"、"历史"）
   - 展示实时搜索结果
   - 展示点击下载链接
4. 导出为 GIF，保存为 `.github/search-demo.gif`

## 方法 2: 使用 macOS 屏幕录制 + ffmpeg 转换

1. 打开 GitHub Pages 页面：https://jbiaojerry.github.io/ebook-treasure-chest/
2. 使用 macOS 内置的屏幕录制功能（Command+Shift+5）录制搜索演示
3. 安装 gifsicle（如果未安装）：
   ```bash
   brew install gifsicle
   ```
4. 将录制的视频转换为 GIF：
   ```bash
   ffmpeg -i input.mov -vf "fps=10,scale=1280:-1:flags=lanczos" -c:v gif - | \
   gifsicle --optimize=3 --delay=10 > .github/search-demo.gif
   ```

## 方法 3: 使用其他工具

- **Gifox** (macOS): https://gifox.io/
- **ScreenToGif** (Windows): https://www.screentogif.com/
- **Peek** (Linux): https://github.com/phw/peek

## 录制内容建议

- ✅ 展示页面加载和统计信息（总书籍数、分类数）
- ✅ 在搜索框输入关键词（如"文学"、"历史"、"沟通"）
- ✅ 展示实时搜索结果（高亮关键词）
- ✅ 展示多关键词搜索（用空格分隔）
- ✅ 展示点击下载链接
- ⏱️ 总时长：10-15 秒
- 📐 分辨率：1280x720 或更高
- 🎨 保持与页面 Solarized Dark 主题一致
