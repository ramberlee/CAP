"""Human review module with Rich CLI interface."""

import json
import logging
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from modules.database import Database

logger = logging.getLogger(__name__)
console = Console()

PLATFORM_LABELS = {
    "xiaohongshu": "[red]小红书[/red]",
    "wechat": "[green]微信公众号[/green]",
    "douyin": "[blue]抖音[/blue]",
}


class ContentReviewer:
    def __init__(self, db: Database):
        self.db = db

    def _display_content(self, content: dict):
        """Display a single content item in a panel."""
        platform = PLATFORM_LABELS.get(content["platform"], content["platform"])
        tags_str = " ".join(content.get("tags", []))

        body = content["body"]
        # Truncate long body for display
        if len(body) > 800:
            body = body[:800] + "\n... (truncated)"

        panel_content = f"""[bold]平台:[/bold] {platform}
[bold]标题:[/bold] {content['title']}
[bold]标签:[/bold] {tags_str}

---
{body}"""

        console.print(
            Panel(panel_content, title=f"内容 #{content['id']}", border_style="cyan")
        )

    def _edit_content(self, content: dict) -> dict:
        """Allow user to edit content fields."""
        console.print("\n[yellow]编辑模式 - 直接回车跳过不修改的字段[/yellow]")

        new_title = Prompt.ask("标题", default=content["title"])
        console.print("输入新正文（输入空行结束，或直接回车跳过）：")
        new_body_lines = []
        try:
            while True:
                line = input()
                if line == "":
                    if not new_body_lines:
                        new_body = content["body"]
                        break
                    new_body = "\n".join(new_body_lines)
                    break
                new_body_lines.append(line)
        except EOFError:
            new_body = "\n".join(new_body_lines) if new_body_lines else content["body"]

        new_tags_str = Prompt.ask(
            "标签（逗号分隔）", default=",".join(content.get("tags", []))
        )
        new_tags = [t.strip() for t in new_tags_str.split(",") if t.strip()]

        return {
            "title": new_title,
            "body": new_body,
            "tags": new_tags,
        }

    def review_batch(self, limit: int = 10) -> dict:
        """Review a batch of draft contents. Returns summary."""
        contents = self.db.get_contents(status="draft", limit=limit)
        if not contents:
            console.print("[yellow]没有待审核的内容[/yellow]")
            return {"reviewed": 0, "approved": 0, "rejected": 0, "edited": 0}

        console.print(f"\n[bold cyan]=== 内容审核 ({len(contents)} 条待审) ===[/bold cyan]\n")

        approved = 0
        rejected = 0
        edited = 0

        for i, content in enumerate(contents, 1):
            console.print(f"\n[bold]--- 第 {i}/{len(contents)} 条 ---[/bold]")
            self._display_content(content)

            while True:
                action = Prompt.ask(
                    "\n操作",
                    choices=["a", "e", "s", "r", "q"],
                    default="s",
                    show_choices=False,
                )
                console.print(
                    "  [green]a[/green]=通过  "
                    "[yellow]e[/yellow]=编辑  "
                    "[dim]s[/dim]=跳过  "
                    "[red]r[/red]=拒绝  "
                    "[dim]q[/dim]=退出审核"
                )

                if action == "a":
                    self.db.update_content(content["id"], status="approved")
                    console.print("[green]✓ 已通过[/green]")
                    approved += 1
                    break
                elif action == "e":
                    edits = self._edit_content(content)
                    self.db.update_content(content["id"], **edits, status="approved")
                    console.print("[green]✓ 已编辑并通过[/green]")
                    edited += 1
                    approved += 1
                    break
                elif action == "s":
                    console.print("[dim]跳过[/dim]")
                    break
                elif action == "r":
                    self.db.update_content(content["id"], status="rejected")
                    console.print("[red]✗ 已拒绝[/red]")
                    rejected += 1
                    break
                elif action == "q":
                    console.print("[dim]退出审核[/dim]")
                    return {"reviewed": approved + rejected + edited, "approved": approved, "rejected": rejected, "edited": edited}

        summary = {
            "reviewed": approved + rejected + edited,
            "approved": approved,
            "rejected": rejected,
            "edited": edited,
        }
        console.print(f"\n[bold]审核完成: {summary}[/bold]")
        return summary
