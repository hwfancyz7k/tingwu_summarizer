#!/usr/bin/env python3
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI


QWEN_API_KEY = os.getenv("QWEN_API_KEY")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL")

if not QWEN_API_KEY:
    raise ValueError("环境变量 QWEN_API_KEY 未设置，请在 ~/.zshrc 中配置")
if not QWEN_BASE_URL:
    raise ValueError("环境变量 QWEN_BASE_URL 未设置，请在 ~/.zshrc 中配置")

client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)

PROMPT = """你是专业的中文写作编辑。请将字幕内容整理成 Markdown 格式的文章：

要求：
1. **尽可能保留原文内容和表达**，只删除明显的重复句子、填充词（"就是"、"然后"、"那个"等）和无意义语气词
2. 保持原有的逻辑结构和论述顺序，不要大幅改写或压缩
3. 按主题自然划分章节，使用 Markdown 标题（## 二级标题、### 三级标题）
4. 段落之间空行分隔，保持可读性
5. 不保留字幕的时间戳和序号

字幕内容：
{}"""

out_dir = Path("tingwu_markdown")
out_dir.mkdir(exist_ok=True)

def extract_content(response) -> str:
    for choice in getattr(response, "choices", []):
        message = getattr(choice, "message", None)
        if message and getattr(message, "content", None):
            return message.content.strip()
    return ""


def process_srt_file(srt_file: Path) -> bool:
    print(f"处理 {srt_file.name}")
    text = srt_file.read_text(encoding="utf-8")
    response = client.chat.completions.create(
        model="qwen3-max",
        messages=[{"role": "user", "content": PROMPT.format(text)}],
        extra_body={"enable_thinking": False},
    )
    content = extract_content(response)
    if not content:
        print(f"  跳过：无内容")
        return False
    (out_dir / f"{srt_file.stem}.md").write_text(content + "\n", encoding="utf-8")
    print(f"  完成 {srt_file.name}")
    return True


def main() -> None:
    srt_files = sorted(Path("tingwu_exports").glob("*.srt"))
    if not srt_files:
        print("未在 tingwu_exports 目录中找到 .srt 文件")
        return

    max_workers = int(os.getenv("SRT_TO_MD_WORKERS", "10"))

    print(f"共发现 {len(srt_files)} 个字幕文件，使用 {max_workers} 个并发任务。")

    success_count = 0
    failure_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_srt_file, srt): srt for srt in srt_files}
        for future in as_completed(future_to_file):
            srt_path = future_to_file[future]
            try:
                if future.result():
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as exc:
                failure_count += 1
                print(f"  失败：{srt_path.name} -> {exc}")

    print(f"处理完成：成功 {success_count} 个，失败 {failure_count} 个。")


if __name__ == "__main__":
    main()
