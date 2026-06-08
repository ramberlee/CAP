"""Content Pipeline CLI - 内容自动生产线"""

import sys
import io

# Fix Windows terminal encoding for emoji/Chinese output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import logging
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.logging import RichHandler

from modules.config import load_config
from modules.database import Database
from modules.content_store import ContentStore
from modules.monitor import TopicMonitor
from modules.generator import ContentGenerator
from modules.publisher import PublishDispatcher

app = typer.Typer(help="内容自动生产线 - 热点监控 → AI生成 → 编辑 → 多平台发布")
console = Console()


def setup_logging(config: dict):
    log_config = config.get("logging", {})
    logging.basicConfig(
        level=getattr(logging, log_config.get("level", "INFO")),
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


def get_db_and_config():
    config = load_config()
    db = Database(config.get("database", {}).get("path", "db/pipeline.db"))
    return db, config


def get_store(config: dict) -> ContentStore:
    return ContentStore(
        output_dir=config.get("output_dir", "output"),
        media_dir=config.get("dashscope", {}).get("media_dir", "media"),
    )


@app.command()
def monitor(
    topic: list[str] = typer.Option([], "--topic", "-t", help="手动添加热点话题"),
    category: str = typer.Option(None, "--category", "-c", help="只采集指定类别: dao(社会热点) / shu(AI技术)"),
):
    """采集热点话题。"""
    db, config = get_db_and_config()
    setup_logging(config)

    m = TopicMonitor(db, config)
    manual = list(topic) if topic else None
    new_count = m.run(manual_topics=manual, category=category)

    cat_label = {"dao": "道(社会热点)", "shu": "术(AI技术)"}.get(category, "全部")
    console.print(f"\n[bold green]采集完成: {new_count} 个新热点已保存 [{cat_label}][/bold green]")

    # Show current topics
    topics = db.get_topics(status="new", category=category, limit=10)
    if topics:
        table = Table(title="待处理热点")
        table.add_column("ID", style="dim")
        table.add_column("类别")
        table.add_column("来源")
        table.add_column("话题")
        table.add_column("热度")
        for t in topics:
            cat_display = "道" if t.get("category") == "dao" else "术"
            table.add_row(str(t["id"]), cat_display, t["source"], t["title"][:40], str(t["heat"]))
        console.print(table)


@app.command()
def generate(
    limit: int = typer.Option(None, "--limit", "-l", help="每类别最大处理热点数 (默认: 配置文件中的 default_limit 或 1)"),
    topic: list[str] = typer.Option([], "--topic", "-t", help="手动添加热点话题并生成"),
    category: str = typer.Option(None, "--category", "-c", help="只生成指定类别: dao(道) / shu(术)"),
):
    """AI 生成内容，保存到 output/ 文件夹。"""
    db, config = get_db_and_config()
    setup_logging(config)

    # If manual topics provided, add them first
    if topic:
        m = TopicMonitor(db, config)
        m.run(manual_topics=list(topic), category=category or "dao")

    # 从配置文件读取默认生成数量，如果未指定则使用配置值或默认值1
    if limit is None:
        limit = config.get("generation", {}).get("default_limit", 1)

    g = ContentGenerator(db, config)
    summary = g.run(limit=limit, category=category)

    cat_label = {"dao": "道", "shu": "术"}.get(category, "全部")
    console.print(f"\n[bold green]生成完成 [{cat_label}]: 处理 {summary['topics_processed']} 个热点, 创建 {summary['contents_created']} 条内容[/bold green]")
    console.print("[dim]文件保存在 output/ 文件夹，可直接编辑[/dim]")
    if not category:
        console.print(f"[dim]提示: 每类别默认生成 {limit} 篇，使用 --limit 参数可调整数量[/dim]")


@app.command()
def publish(
    platform: str = typer.Option(None, "--platform", "-p", help="指定平台: wechat/xiaohongshu/douyin"),
    dry_run: bool = typer.Option(False, "--dry-run", help="试运行，不实际发布"),
):
    """发布已生成的内容（发布前会确认）。"""
    _, config = get_db_and_config()
    setup_logging(config)

    d = PublishDispatcher(config)
    summary = d.run(platform=platform, dry_run=dry_run)

    if summary.get("cancelled"):
        return

    status = "试运行" if dry_run else "发布"
    console.print(f"\n[bold green]{status}完成: 总计 {summary['total']}, 成功 {summary['success']}, 失败 {summary['failed']}[/bold green]")


@app.command()
def run(
    topic: list[str] = typer.Option([], "--topic", "-t", help="手动添加热点话题"),
    limit: int = typer.Option(None, "--limit", "-l", help="每类别最大处理数 (默认: 配置文件中的 default_limit 或 1)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="试运行"),
    category: str = typer.Option(None, "--category", "-c", help="只处理指定类别: dao(道) / shu(术)"),
):
    """一键执行全流程: 采集 → 生成 → 发布（确认后）。"""
    db, config = get_db_and_config()
    setup_logging(config)

    console.print("[bold cyan]===== 内容自动生产线 =====[/bold cyan]\n")

    # 从配置文件读取默认生成数量，如果未指定则使用配置值或默认值1
    if limit is None:
        limit = config.get("generation", {}).get("default_limit", 1)

    # Step 1: Monitor
    console.print("[bold]Step 1/3: 热点采集[/bold]")
    m = TopicMonitor(db, config)
    new_count = m.run(manual_topics=list(topic) if topic else None, category=category)
    console.print(f"  采集到 {new_count} 个新热点\n")

    # Step 2: Generate
    console.print("[bold]Step 2/3: AI 内容生成[/bold]")
    g = ContentGenerator(db, config)
    gen_summary = g.run(limit=limit, category=category)
    console.print(f"  生成 {gen_summary['contents_created']} 条内容")
    console.print("  [dim]文件保存在 output/，可编辑后发布[/dim]\n")

    # Step 3: Publish (with confirmation)
    if gen_summary["contents_created"] > 0:
        console.print("[bold]Step 3/3: 发布[/bold]")
        d = PublishDispatcher(config)
        pub_summary = d.run(dry_run=dry_run)
        if pub_summary.get("success", 0) > 0:
            console.print(f"  发布 {pub_summary['success']} 条内容")
    else:
        console.print("[bold]Step 3/3: 跳过发布 (无内容)[/bold]")

    console.print("\n[bold cyan]===== 流水线执行完毕 =====[/bold cyan]")


@app.command()
def status():
    """查看流水线状态。"""
    db, config = get_db_and_config()
    store = get_store(config)
    db_stats = db.get_stats()
    file_stats = store.get_stats()

    table = Table(title="流水线状态")
    table.add_column("指标", style="bold")
    table.add_column("数量", justify="right")

    table.add_row("热点总数", str(db_stats["topics_total"]))
    table.add_row("待处理热点", str(db_stats["topics_new"]))
    table.add_row("  ├ 道(社会热点)", str(db_stats.get("dao_new", 0)))
    table.add_row("  └ 术(AI技术)", str(db_stats.get("shu_new", 0)))
    table.add_row("")
    table.add_row("内容文件总数", str(file_stats["total"]))
    table.add_row("待发布 (approved)", str(file_stats.get("approved", 0)))
    table.add_row("已发布 (published)", str(file_stats.get("published", 0)))

    console.print(table)


PLATFORM_LABELS = {
    "xiaohongshu": "[red]小红书[/red]",
    "wechat": "[green]微信公众号[/green]",
    "douyin": "[blue]抖音[/blue]",
}


@app.command(name="show")
def show(
    platform: str = typer.Option(None, "--platform", "-p", help="按平台筛选: xiaohongshu/wechat/douyin"),
    status: str = typer.Option("approved", "--status", "-s", help="内容状态: approved/published/all"),
):
    """查看内容列表（从文件读取）。"""
    _, config = get_db_and_config()
    store = get_store(config)

    status_filter = None if status == "all" else status
    contents = store.load_contents(platform=platform, status=status_filter)

    if not contents:
        console.print(f"[yellow]没有 {status} 状态的内容[/yellow]")
        return

    for c in contents:
        platform_label = PLATFORM_LABELS.get(c["platform"], c["platform"])
        tags_str = " ".join(c.get("tags", []))

        panel_content = f"""[bold]平台:[/bold] {platform_label}
[bold]标题:[/bold] {c['title']}
[bold]标签:[/bold] {tags_str}
[bold]文件:[/bold] {c['filepath']}

---
{c['body'][:500]}"""

        console.print(
            Panel(panel_content, title=f"[{c['status']}]", border_style="cyan")
        )


@app.command()
def edit(
    platform: str = typer.Argument(..., help="平台: xiaohongshu/wechat/douyin"),
    index: int = typer.Argument(..., help="内容序号 (从 show 命令查看)"),
):
    """用系统默认编辑器打开内容文件。"""
    import subprocess
    _, config = get_db_and_config()
    store = get_store(config)

    contents = store.load_contents(platform=platform)
    if index < 1 or index > len(contents):
        console.print(f"[red]序号 {index} 无效，共有 {len(contents)} 条内容[/red]")
        return

    filepath = contents[index - 1]["filepath"]
    console.print(f"打开文件: {filepath}")
    if sys.platform == "win32":
        subprocess.Popen(["notepad", filepath])
    else:
        subprocess.Popen(["xdg-open", filepath])


if __name__ == "__main__":
    app()
