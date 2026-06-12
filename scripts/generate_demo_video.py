"""
FinAgent Pro 3分钟演示视频自动生成脚本
自动生成：屏幕录制 + 旁白配音 + 字幕，三者完全同步
"""

import asyncio
import subprocess
import json
from pathlib import Path
from playwright.async_api import async_playwright
import edge_tts

# 输出目录
OUTPUT_DIR = Path(__file__).parent / "video_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 演示场景定义（4个场景，总时长约3分钟）
SCENES = [
    {
        "name": "开场介绍",
        "duration": 15,
        "url": "https://finagent-pro-afac2026-gxz4.vercel.app/",
        "narration": "欢迎体验FinAgent Pro金融自主智能体平台。这是一个基于大语言模型与多智能体协同技术的数字员工，为金融行业提供主动智能服务。",
        "actions": [
            {"type": "wait", "seconds": 3},
            {"type": "screenshot", "name": "dashboard"},
            {"type": "wait", "seconds": 12},
        ]
    },
    {
        "name": "智能体协同分析",
        "duration": 50,
        "url": "https://finagent-pro-afac2026-gxz4.vercel.app/analyze",
        "narration": "现在演示智能体协同分析。输入股票代码600519，点击分析。系统自动触发三阶段流水线：第一阶段，市场分析智能体和新闻舆情智能体并行工作；第二阶段，风控合规智能体进行四维风控检查；第三阶段，投资策略智能体生成建议。整个过程中，思维链实时可视化展示。",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "fill", "selector": "input[placeholder*='股票代码']", "value": "600519"},
            {"type": "wait", "seconds": 1},
            {"type": "click", "selector": "button:has-text('开始分析')"},
            {"type": "wait", "seconds": 47},
        ]
    },
    {
        "name": "对话式交互",
        "duration": 45,
        "url": "https://finagent-pro-afac2026-gxz4.vercel.app/chat",
        "narration": "接下来展示对话式交互能力。向数字员工提问：分析贵州茅台的投资价值。智能体自动识别意图，调用市场分析和新闻智能体，返回专业的投资建议。这种自然语言交互方式，让非专业用户也能轻松获取投研服务。",
        "actions": [
            {"type": "wait", "seconds": 2},
            {"type": "fill", "selector": "input[placeholder*='输入']", "value": "分析贵州茅台的投资价值"},
            {"type": "wait", "seconds": 1},
            {"type": "click", "selector": "button:has-text('发送')"},
            {"type": "wait", "seconds": 42},
        ]
    },
    {
        "name": "主动智能与收尾",
        "duration": 50,
        "url": "https://finagent-pro-afac2026-gxz4.vercel.app/alerts",
        "narration": "最后展示主动智能能力。系统通过定时巡检和事件驱动，自动发现持仓异动、突发新闻、风险预警，并主动推送通知。同时，合规规则引擎确保所有操作符合监管要求，审计日志完整记录。这就是FinAgent Pro，从被动响应迈向主动智能的金融自主智能体平台。",
        "actions": [
            {"type": "wait", "seconds": 3},
            {"type": "screenshot", "name": "alerts"},
            {"type": "wait", "seconds": 47},
        ]
    },
]


async def generate_narration():
    """生成旁白音频"""
    print("🎙️ 生成旁白音频...")
    audio_files = []

    for i, scene in enumerate(SCENES):
        output_file = OUTPUT_DIR / f"narration_{i}.mp3"
        communicate = edge_tts.Communicate(
            scene["narration"],
            voice="zh-CN-YunxiNeural",  # 男声，专业感
            rate="+10%",  # 语速稍快
        )
        await communicate.save(str(output_file))
        audio_files.append(output_file)
        print(f"  ✓ 场景{i+1}: {output_file.name}")

    return audio_files


def get_audio_duration(audio_file):
    """获取音频时长"""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_file)],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


async def record_screen():
    """录制屏幕操作"""
    print("\n🎬 录制屏幕操作...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(OUTPUT_DIR / "videos"),
            record_video_size={"width": 1280, "height": 720},
        )
        page = await context.new_page()

        for i, scene in enumerate(SCENES):
            print(f"  录制场景{i+1}: {scene['name']}")
            await page.goto(scene["url"], wait_until="networkidle")
            await asyncio.sleep(2)

            for action in scene["actions"]:
                if action["type"] == "wait":
                    await asyncio.sleep(action["seconds"])
                elif action["type"] == "click":
                    try:
                        await page.click(action["selector"], timeout=3000)
                    except:
                        print(f"    ⚠️ 点击失败: {action['selector']}")
                elif action["type"] == "fill":
                    try:
                        await page.fill(action["selector"], action["value"], timeout=3000)
                    except:
                        print(f"    ⚠️ 填写失败: {action['selector']}")
                elif action["type"] == "screenshot":
                    await page.screenshot(path=OUTPUT_DIR / f"screenshot_{action['name']}.png")

        await context.close()
        await browser.close()

    # 找到录制的视频文件
    video_files = list((OUTPUT_DIR / "videos").glob("*.webm"))
    if video_files:
        return video_files[-1]  # 返回最新的视频
    return None


def generate_srt(audio_files):
    """生成SRT字幕文件"""
    print("\n📝 生成字幕文件...")
    srt_content = []
    current_time = 0.0
    subtitle_index = 1

    for i, (scene, audio_file) in enumerate(zip(SCENES, audio_files)):
        duration = get_audio_duration(audio_file)
        start_time = current_time
        end_time = current_time + duration

        # 将旁白按句子分割
        sentences = scene["narration"].replace("。", "。\n").split("\n")
        sentences = [s.strip() for s in sentences if s.strip()]

        # 计算每句时长
        total_chars = sum(len(s) for s in sentences)
        sentence_duration = duration / len(sentences)

        for j, sentence in enumerate(sentences):
            sent_start = start_time + j * sentence_duration
            sent_end = sent_start + sentence_duration

            # 格式化时间
            start_str = format_srt_time(sent_start)
            end_str = format_srt_time(sent_end)

            srt_content.append(f"{subtitle_index}")
            srt_content.append(f"{start_str} --> {end_str}")
            srt_content.append(sentence)
            srt_content.append("")

            subtitle_index += 1

        current_time = end_time

    # 写入SRT文件
    srt_file = OUTPUT_DIR / "subtitles.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_content))

    print(f"  ✓ 字幕文件: {srt_file.name}")
    return srt_file


def format_srt_time(seconds):
    """格式化SRT时间"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def merge_video_audio(video_file, audio_files, srt_file, output_file):
    """合并视频、音频、字幕"""
    print("\n🎞️ 合成最终视频...")

    # 先合并所有音频
    audio_list_file = OUTPUT_DIR / "audio_list.txt"
    with open(audio_list_file, "w") as f:
        for audio_file in audio_files:
            f.write(f"file '{audio_file}'\n")

    merged_audio = OUTPUT_DIR / "merged_audio.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(audio_list_file),
        "-c", "copy", str(merged_audio)
    ], capture_output=True)

    # 合并视频和音频，添加字幕
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_file),
        "-i", str(merged_audio),
        "-vf", f"subtitles={srt_file}:force_style='FontSize=20,PrimaryColour=&HFFFFFF&,OutlineColour=&H000000&,Outline=2'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(output_file)
    ], capture_output=True)

    print(f"  ✓ 最终视频: {output_file.name}")


async def main():
    """主流程"""
    print("=" * 50)
    print("FinAgent Pro 3分钟演示视频生成")
    print("=" * 50)

    # 1. 生成旁白
    audio_files = await generate_narration()

    # 2. 录制屏幕
    video_file = await record_screen()
    if not video_file:
        print("❌ 屏幕录制失败")
        return

    # 3. 生成字幕
    srt_file = generate_srt(audio_files)

    # 4. 合成最终视频
    output_file = OUTPUT_DIR / "FinAgent_Pro_Demo_3min.mp4"
    merge_video_audio(video_file, audio_files, srt_file, output_file)

    print("\n" + "=" * 50)
    print("✅ 视频生成完成！")
    print(f"📁 输出文件: {output_file}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
