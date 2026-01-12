# 搜索功能演示 GIF 生成器

## 快速开始

### 自动生成（推荐）

```bash
# 安装依赖
pip install playwright Pillow
playwright install chromium

# 运行脚本
python scripts/generate_search_demo_gif.py
```

脚本会自动：
1. 访问 GitHub Pages 页面
2. 等待数据加载完成
3. 执行搜索操作（"文学"、"历史"、"沟通 励志"）
4. 截图并生成 GIF 动画
5. 保存到 `.github/search-demo.gif`

### 手动生成

如果自动脚本无法使用，请参考 `.github/create-search-demo-gif.md` 中的其他方法。

## 脚本说明

`scripts/generate_search_demo_gif.py` 是一个自动化脚本，使用 Playwright 控制浏览器：

- **浏览器**: Chromium (无头模式)
- **分辨率**: 1280x720
- **帧率**: 每帧 1.5 秒
- **操作**: 自动执行搜索并截图

## 自定义

可以修改脚本中的以下参数：

- `viewport`: 浏览器窗口大小
- `duration`: GIF 每帧显示时间（毫秒）
- `asyncio.sleep()`: 操作之间的等待时间
- 搜索关键词: 修改搜索的文本内容

## 故障排除

### playwright 未安装
```bash
pip install playwright
playwright install chromium
```

### Pillow 未安装
```bash
pip install Pillow
```

### 页面加载超时
增加脚本中的 `timeout` 参数，或检查网络连接。
