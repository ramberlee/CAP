#!/usr/bin/env python3
"""
v3 科技风视频渲染脚本

使用方法:
    # 使用默认 demo
    python scripts/render_v3.py

    # 使用自定义 JSON
    python scripts/render_v3.py --input my_plan.json

    # 使用模板快速生成
    python scripts/render_v3.py --template techShowcase --title "我的产品演示"

    # 预览模式 (仅渲染前 10 秒)
    python scripts/render_v3.py --preview
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from remotion.src.templates import quickVideoPlan, composeVideo
from remotion.src.templates import (
    createTitleScene,
    createTechMultiPanel,
    createConnectedCards,
    createStackHighlight,
    createArchitectureFlow,
    createCardGrid,
    createEndingScene,
)


def load_plan_from_template(template: str, title: str, theme: str = "dark_tech_v3") -> dict:
    """从模板生成视频计划"""
    plan = quickVideoPlan(template, title, {"theme": theme, "subtitle": ""})
    return plan


def load_plan_from_file(file_path: str) -> dict:
    """从文件加载视频计划"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"找不到文件: {file_path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_demo_plan(theme: str = "dark_tech_v3") -> dict:
    """创建演示视频计划"""
    title = "v3 科技风演示视频"
    scenes = [
        createTitleScene(title, "动态粒子 · 数据流动 · 发光边框", {"duration": 4}),
        createTechMultiPanel({"duration": 6, "sceneSubtitle": "多面板信息展示")),
        createConnectedCards({"duration": 5, "sceneSubtitle": "三步完成工作流"}),
        createStackHighlight("核心优势", {"duration": 5, "sceneSubtitle": "六大核心竞争力"}),
        createArchitectureFlow("系统架构", {"duration": 6, "sceneSubtitle": "模块化设计，弹性扩展"}),
        createCardGrid({"duration": 5, "title": "功能模块", "sceneSubtitle": "持续迭代，功能越来越强"}),
        createEndingScene("感谢观看", "期待与您的合作", {"duration": 4}),
    ]
    return composeVideo(scenes, {"title": title, "theme": theme})


def render_video(plan: dict, output_path: str, concurrency: int = 6, quality: int = 80, scale: float = 1.0) -> int:
    """调用 Remotion 渲染视频"""
    # 保存临时计划文件
    plan_file = Path("out") / "temp_plan.json"
    plan_file.parent.mkdir(parents=True, exist_ok=True)
    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    print(f"📋 计划文件已保存: {plan_file}")
    print(f"🎬 开始渲染视频...")
    print(f"   场景数: {len(plan.get('scenes', []))}")
    print(f"   主题: {plan.get('theme', 'dark_tech_v3')}")
    print()

    # 构建命令
    cmd = [
        "npx",
        "remotion",
        "render",
        "src/Root.tsx",
        "CAPVideo",
        output_path,
        f"--props={plan_file}",
        f"--concurrency={concurrency}",
        f"--quality={quality}",
        f"--scale={scale}",
    ]

    print(f"执行命令: {' '.join(cmd)}")
    print()

    # 执行渲染
    result = subprocess.run(cmd, cwd=project_root / "remotion")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="v3 科技风视频渲染工具")
    parser.add_argument("--input", "-i", help="输入 JSON 文件路径")
    parser.add_argument("--template", "-t", choices=["techShowcase", "productIntro", "minimal"], help="使用模板")
    parser.add_argument("--title", default="v3 科技风演示", help="视频标题")
    parser.add_argument("--theme", default="dark_tech_v3", help="主题名称")
    parser.add_argument("--output", "-o", default="out/v3-demo.mp4", help="输出文件路径")
    parser.add_argument("--preview", action="store_true", help="预览模式 (低质量快速渲染)")
    parser.add_argument("--concurrency", type=int, default=6, help="并发数")
    parser.add_argument("--quality", type=int, default=80, help="视频质量 (0-100)")
    parser.add_argument("--scale", type=float, default=1.0, help="缩放比例 (0.5 0.75 1.0)")

    args = parser.parse_args()

    # 调整预览模式设置
    if args.preview:
        args.quality = 60
        args.scale = 0.5
        args.concurrency = 8

    # 生成视频计划
    if args.input:
        plan = load_plan_from_file(args.input)
    elif args.template:
        plan = load_plan_from_template(args.template, args.title, args.theme)
    else:
        plan = create_demo_plan(args.theme)

    # 确保输出目录存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 渲染视频
    return_code = render_video(
        plan,
        str(output_path),
        args.concurrency,
        args.quality,
        args.scale,
    )

    if return_code == 0:
        print(f"\n✅ 渲染成功！视频已保存到: {output_path.resolve()}")
    else:
        print(f"\n❌ 渲染失败，返回码: {return_code}")

    return return_code


if __name__ == "__main__":
    sys.exit(main())
