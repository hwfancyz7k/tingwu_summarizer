# 听悟字幕批量下载与转换工具

批量下载阿里云听悟平台的字幕文件，并将 SRT 格式转换为 Markdown 文章。

## 功能

1. **tingwu_batch_export.py** - 批量下载听悟字幕
2. **srt_to_markdown_simple.py** - 并发转换 SRT 为 Markdown

## 环境配置

在 `~/.zshrc` 中添加以下环境变量：

```bash
# Tingwu API Credentials
export TINGWU_COOKIE="你的听悟Cookie"
export QWEN_API_KEY="你的通义千问API Key"
export QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
```

重新加载配置：
```bash
source ~/.zshrc
```

## 安装依赖

```bash
pip install requests openai
```

## 使用方法

### 1. 下载字幕文件

```bash
python tingwu_batch_export.py <DIR_ID>
```

**参数说明：**
- `DIR_ID`: 听悟文件夹 ID（从 URL 中获取，如 `https://tingwu.aliyun.com/folders/216791` 中的 `216791`）

**示例：**
```bash
python tingwu_batch_export.py 216791
```

**输出：**
- 下载的 SRT 文件保存在 `tingwu_exports/` 目录
- 自动跳过已存在的文件

### 2. 转换为 Markdown

```bash
python srt_to_markdown_simple.py
```

**功能：**
- 读取 `tingwu_exports/` 目录下的所有 `.srt` 文件
- 使用通义千问 API 将字幕整理成 Markdown 格式
- 并发处理，默认 8 个线程

**输出：**
- Markdown 文件保存在 `tingwu_markdown/` 目录
- 每个 SRT 对应一个同名 `.md` 文件

**自定义并发数：**
```bash
export SRT_TO_MD_WORKERS=4
python srt_to_markdown_simple.py
```

## 完整流程示例

```bash
# 1. 下载字幕
python tingwu_batch_export.py 216791

# 2. 转换为 Markdown
python srt_to_markdown_simple.py
```

## 目录结构

```
tingwu/
├── tingwu_batch_export.py      # 下载脚本
├── srt_to_markdown_simple.py   # 转换脚本
├── tingwu_exports/              # SRT 字幕文件
└── tingwu_markdown/             # Markdown 文章
```

## Markdown 输出特点

- 删除重复句子、填充词和语气词
- 保留原文内容和表达
- 按主题自然分段，使用二级、三级标题
- 清晰的段落结构，空行分隔

## 注意事项

1. **Cookie 获取**: 在浏览器中登录听悟，从开发者工具 Network 标签中复制完整 Cookie
2. **Cookie 有效期**: Cookie 会过期，需要定期更新 `~/.zshrc` 中的 `TINGWU_COOKIE`
3. **API 限流**: 转换脚本会自动处理并发，避免 API 限流
4. **费用**: 使用通义千问 API 会产生费用，请注意控制用量
