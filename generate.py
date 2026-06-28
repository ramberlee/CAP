#!/usr/bin/env python3
"""Generate a Douyin video from a topic keyword.

Usage:
    python generate.py "Claude Code 使用技巧"
    python generate.py "AI 编程工具对比" --output my_video.mp4
    python generate.py "GPT-5 发布" --preview
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def main():
    parser = argparse.ArgumentParser(
        description="从话题关键词生成抖音视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python generate.py "Claude Code 使用技巧"
  python generate.py "AI 编程工具对比" --output my_video.mp4
  python generate.py "GPT-5 发布" --category shu
        """,
    )
    parser.add_argument("topic", help="话题关键词或简短描述")
    parser.add_argument("--output", "-o", help="输出视频路径（默认自动生成）")
    parser.add_argument("--category", "-c", default="dao", choices=["dao", "shu"],
                        help="内容分类（默认: dao）")
    parser.add_argument("--preview", action="store_true",
                        help="预览模式（低质量快速渲染）")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="显示详细日志")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Suppress noisy logs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger("generate")

    # Load config
    try:
        from modules.config_model import load_config
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Preview mode adjustments
    if args.preview:
        config.remotion.video_quality = "preview"
        logger.info("Preview mode: low quality, fast render")

    # Create pipeline
    try:
        from modules.pipeline import TopicToVideoPipeline
        pipeline = TopicToVideoPipeline.from_config(config)
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        sys.exit(1)

    # Run pipeline
    logger.info(f"Starting pipeline for topic: {args.topic}")
    result = pipeline.run(args.topic)

    if result["success"]:
        video_path = result["video_path"]
        logger.info(f"✅ Video generated: {video_path}")
        print(f"\n✅ 视频生成成功！")
        print(f"   路径: {video_path}")
        if result.get("audio_path"):
            print(f"   音频: {result['audio_path']}")
        print(f"   文案: {result.get('script', '')[:80]}...")
    else:
        logger.error(f"❌ Pipeline failed: {result.get('error', 'Unknown error')}")
        print(f"\n❌ 视频生成失败: {result.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
