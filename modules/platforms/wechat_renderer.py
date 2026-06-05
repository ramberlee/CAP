"""WeChat Markdown renderer — ported from WeChat-Markdown (github.com/gzyxds/WeChat-Markdown).

Uses markdown-it-py for MD→HTML conversion, BeautifulSoup for theme application
and WeChat compatibility fixes.
"""

import re
from markdown_it import MarkdownIt
from bs4 import BeautifulSoup, NavigableString, Tag

# ---------------------------------------------------------------------------
# Theme definitions (ported from WeChat-Markdown/src/lib/themes/)
# ---------------------------------------------------------------------------

THEMES: dict[str, dict[str, str]] = {
    "claude": {
        "container": "max-width:100%;margin:0 auto;padding:24px 20px 48px 20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:16px;line-height:1.7 !important;color:#2b2b2b !important;background-color:#f8f6f0 !important;word-wrap:break-word;",
        "h1": "font-size:32px;font-weight:700;color:#b75c3d !important;line-height:1.3 !important;margin:38px 0 16px;letter-spacing:-0.015em;",
        "h2": "font-size:26px;font-weight:600;color:#b75c3d !important;line-height:1.35 !important;margin:32px 0 16px;",
        "h3": "font-size:21px;font-weight:600;color:#2b2b2b !important;line-height:1.4 !important;margin:28px 0 14px;",
        "h4": "font-size:18px;font-weight:600;color:#2b2b2b !important;line-height:1.4 !important;margin:24px 0 12px;",
        "p": "margin:18px 0 !important;line-height:1.7 !important;color:#2b2b2b !important;",
        "strong": "font-weight:700;color:#b75c3d !important;background-color:rgba(183,92,61,0.08);padding:0 4px;border-radius:4px;",
        "em": "font-style:italic;color:#666 !important;",
        "a": "color:#b75c3d !important;text-decoration:none;border-bottom:1px solid #b75c3d;padding-bottom:1px;",
        "ul": "margin:16px 0;padding-left:28px;",
        "ol": "margin:16px 0;padding-left:28px;",
        "li": "margin:8px 0;line-height:1.7 !important;color:#2b2b2b !important;",
        "blockquote": "margin:24px 0;padding:16px 20px;background-color:rgba(183,92,61,0.04) !important;border-left:4px solid #b75c3d;color:#555 !important;border-radius:4px;",
        "code": "font-family:'SF Mono',Consolas,monospace;padding:3px 6px;background-color:#f0ece4 !important;color:#b75c3d !important;border-radius:4px;font-size:12px !important;line-height:1.5 !important;",
        "pre": "margin:24px 0;padding:20px;background-color:#f0ece4 !important;border-radius:8px;overflow-x:auto;font-size:12px !important;line-height:1.5 !important;",
        "hr": "margin:36px auto;border:none;height:1px;background-color:#eaeaea !important;width:100%;",
        "img": "max-width:100%;height:auto;display:block;margin:24px auto;border-radius:4px;",
        "table": "width:100%;margin:24px 0;border-collapse:collapse;font-size:15px;",
        "th": "background-color:#f0ece4 !important;padding:12px 16px;text-align:left;font-weight:600;color:#2b2b2b !important;border:1px solid #e0ddd6;",
        "td": "padding:12px 16px;border:1px solid #e0ddd6;color:#2b2b2b !important;",
        "tr": "border:none;",
    },
    "apple": {
        "container": "max-width:100%;margin:0 auto;padding:24px 20px 48px 20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:16px;line-height:1.7 !important;color:#1d1d1f !important;background-color:#ffffff !important;word-wrap:break-word;",
        "h1": "font-size:32px;font-weight:700;color:#111 !important;line-height:1.3 !important;margin:38px 0 16px;letter-spacing:-0.015em;",
        "h2": "font-size:26px;font-weight:600;color:#111 !important;line-height:1.35 !important;margin:32px 0 16px;",
        "h3": "font-size:21px;font-weight:600;color:#1d1d1f !important;line-height:1.4 !important;margin:28px 0 14px;",
        "h4": "font-size:18px;font-weight:600;color:#1d1d1f !important;line-height:1.4 !important;margin:24px 0 12px;",
        "p": "margin:18px 0 !important;line-height:1.7 !important;color:#1d1d1f !important;",
        "strong": "font-weight:700;color:#000 !important;",
        "em": "font-style:italic;color:#666 !important;",
        "a": "color:#0066cc !important;text-decoration:none;border-bottom:1px solid #0066cc;padding-bottom:1px;",
        "ul": "margin:16px 0;padding-left:28px;",
        "ol": "margin:16px 0;padding-left:28px;",
        "li": "margin:8px 0;line-height:1.7 !important;color:#1d1d1f !important;",
        "blockquote": "margin:24px 0;padding:16px 20px;background-color:#f5f5f7 !important;border-left:4px solid #0066cc;color:#555 !important;border-radius:4px;",
        "code": "font-family:'SF Mono',Consolas,monospace;padding:3px 6px;background-color:#f5f5f7 !important;color:#0066cc !important;border-radius:4px;font-size:12px !important;line-height:1.5 !important;",
        "pre": "margin:24px 0;padding:20px;background-color:#f5f5f7 !important;border-radius:8px;overflow-x:auto;font-size:12px !important;line-height:1.5 !important;",
        "hr": "margin:36px auto;border:none;height:1px;background-color:#eaeaea !important;width:100%;",
        "img": "max-width:100%;height:auto;display:block;margin:24px auto;border-radius:12px;",
        "table": "width:100%;margin:24px 0;border-collapse:collapse;font-size:15px;",
        "th": "background-color:#f5f5f7 !important;padding:12px 16px;text-align:left;font-weight:600;color:#1d1d1f !important;border:1px solid #e0e0e0;",
        "td": "padding:12px 16px;border:1px solid #e0e0e0;color:#1d1d1f !important;",
        "tr": "border:none;",
    },
    "wechat": {
        "container": "max-width:100%;margin:0 auto;padding:24px 20px 48px 20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:16px;line-height:1.7 !important;color:#333333 !important;background-color:#ffffff !important;word-wrap:break-word;",
        "h1": "font-size:32px;font-weight:700;color:#111 !important;line-height:1.3 !important;margin:38px 0 16px;letter-spacing:-0.015em;",
        "h2": "font-size:26px;font-weight:600;color:#111 !important;line-height:1.35 !important;margin:32px 0 16px;",
        "h3": "font-size:21px;font-weight:600;color:#333333 !important;line-height:1.4 !important;margin:28px 0 14px;",
        "h4": "font-size:18px;font-weight:600;color:#333333 !important;line-height:1.4 !important;margin:24px 0 12px;",
        "p": "margin:18px 0 !important;line-height:1.7 !important;color:#333333 !important;",
        "strong": "font-weight:700;color:#07c160 !important;background-color:rgba(7,193,96,0.08);padding:0 4px;border-radius:4px;",
        "em": "font-style:italic;color:#666 !important;",
        "a": "color:#07c160 !important;text-decoration:none;border-bottom:1px solid #07c160;padding-bottom:1px;",
        "ul": "margin:16px 0;padding-left:28px;",
        "ol": "margin:16px 0;padding-left:28px;",
        "li": "margin:8px 0;line-height:1.7 !important;color:#333333 !important;",
        "blockquote": "margin:24px 0;padding:16px 20px;background-color:#f0f7f2 !important;border-left:4px solid #07c160;color:#555 !important;border-radius:4px;",
        "code": "font-family:'SF Mono',Consolas,monospace;padding:3px 6px;background-color:#f0f7f2 !important;color:#07c160 !important;border-radius:4px;font-size:12px !important;line-height:1.5 !important;",
        "pre": "margin:24px 0;padding:20px;background-color:#f0f7f2 !important;border-radius:8px;overflow-x:auto;font-size:12px !important;line-height:1.5 !important;",
        "hr": "margin:36px auto;border:none;height:1px;background-color:#eaeaea !important;width:100%;",
        "img": "max-width:100%;height:auto;display:block;margin:24px auto;border-radius:4px;",
        "table": "width:100%;margin:24px 0;border-collapse:collapse;font-size:15px;",
        "th": "background-color:#f0f7f2 !important;padding:12px 16px;text-align:left;font-weight:600;color:#333333 !important;border:1px solid #d8e8dc;",
        "td": "padding:12px 16px;border:1px solid #d8e8dc;color:#333333 !important;",
        "tr": "border:none;",
    },
    "notion": {
        "container": "max-width:100%;margin:0 auto;padding:24px 20px 48px 20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:16px;line-height:1.6 !important;color:#37352f !important;background-color:#ffffff !important;word-wrap:break-word;",
        "h1": "font-size:34px;font-weight:700;color:#37352f !important;line-height:1.2 !important;margin:38px 0 8px;letter-spacing:-0.02em;",
        "h2": "font-size:26px;font-weight:600;color:#37352f !important;line-height:1.3 !important;margin:32px 0 8px;",
        "h3": "font-size:21px;font-weight:600;color:#37352f !important;line-height:1.35 !important;margin:28px 0 8px;",
        "h4": "font-size:18px;font-weight:600;color:#37352f !important;line-height:1.4 !important;margin:24px 0 8px;",
        "p": "margin:4px 0 !important;line-height:1.6 !important;color:#37352f !important;",
        "strong": "font-weight:700;color:#37352f !important;",
        "em": "font-style:italic;color:#37352f !important;",
        "a": "color:#37352f !important;text-decoration:underline;text-underline-offset:3px;text-decoration-color:rgba(55,53,47,0.4);",
        "ul": "margin:4px 0;padding-left:26px;",
        "ol": "margin:4px 0;padding-left:26px;",
        "li": "margin:2px 0;line-height:1.6 !important;color:#37352f !important;",
        "blockquote": "margin:8px 0;padding:4px 16px;background-color:transparent !important;border-left:3px solid #37352f;color:#37352f !important;border-radius:0;",
        "code": "font-family:'SF Mono',Consolas,monospace;padding:2px 5px;background-color:#f7f6f3 !important;color:#eb5757 !important;border-radius:3px;font-size:13px !important;line-height:1.5 !important;",
        "pre": "margin:16px 0;padding:20px;background-color:#f7f6f3 !important;border-radius:4px;overflow-x:auto;font-size:13px !important;line-height:1.5 !important;",
        "hr": "margin:24px auto;border:none;height:1px;background-color:#e9e9e7 !important;width:100%;",
        "img": "max-width:100%;height:auto;display:block;margin:16px auto;border-radius:2px;",
        "table": "width:100%;margin:16px 0;border-collapse:collapse;font-size:15px;",
        "th": "background-color:#f7f6f3 !important;padding:8px 12px;text-align:left;font-weight:600;color:#37352f !important;border:1px solid #e9e9e7;",
        "td": "padding:8px 12px;border:1px solid #e9e9e7;color:#37352f !important;",
        "tr": "border:none;",
    },
}


# ---------------------------------------------------------------------------
# Markdown-it renderer
# ---------------------------------------------------------------------------

def _create_md() -> MarkdownIt:
    """Create a markdown-it instance with commonmark + html + linkify."""
    md = MarkdownIt("commonmark", {"html": True, "linkify": True, "typographer": False})
    md.enable("table")
    return md


_MD = _create_md()


def render_markdown(text: str) -> str:
    """Render markdown text to HTML."""
    return _MD.render(text)


# ---------------------------------------------------------------------------
# Theme application (ported from applyTheme)
# ---------------------------------------------------------------------------

_HEADING_INLINE_OVERRIDES = {
    "strong": "font-weight:700;color:inherit !important;background-color:transparent !important;",
    "em": "font-style:italic;color:inherit !important;background-color:transparent !important;",
    "a": "color:inherit !important;text-decoration:none !important;border-bottom:1px solid currentColor !important;background-color:transparent !important;",
    "code": "color:inherit !important;background-color:transparent !important;border:none !important;padding:0 !important;",
}


def _get_single_image_node(p_tag: Tag) -> Tag | None:
    """If a <p> contains exactly one <img> (possibly wrapped in <a>), return it."""
    children = [
        c for c in p_tag.children
        if not (isinstance(c, NavigableString) and not c.strip())
        and not (isinstance(c, Tag) and c.name == "br")
    ]
    if len(children) != 1:
        return None
    only = children[0]
    if isinstance(only, Tag) and only.name == "img":
        return only
    if isinstance(only, Tag) and only.name == "a" and len(only.find_all("img", recursive=False)) == 1:
        return only
    return None


def apply_theme(html: str, theme_id: str = "claude") -> str:
    """Apply inline styles from a theme to the HTML (ported from applyTheme)."""
    style = THEMES.get(theme_id, THEMES["claude"])
    soup = BeautifulSoup(html, "html.parser")

    # --- Merge consecutive single-image paragraphs into side-by-side grids ---
    paragraphs = soup.find_all("p")
    processed = set()
    for p in paragraphs:
        if id(p) in processed or not p.parent:
            continue
        if _get_single_image_node(p) is None:
            continue

        run = [p]
        cursor = p.find_next_sibling()
        while cursor and cursor.name == "p":
            if _get_single_image_node(cursor) is None:
                break
            run.append(cursor)
            cursor = cursor.find_next_sibling()

        if len(run) < 2:
            continue

        for i in range(0, len(run) - 1, 2):
            first_img = _get_single_image_node(run[i])
            second_img = _get_single_image_node(run[i + 1])
            if first_img is None or second_img is None:
                continue

            grid_p = soup.new_tag("p", **{"class": "image-grid"})
            grid_p["style"] = "display:flex;justify-content:center;gap:8px;margin:24px 0;align-items:flex-start;"
            grid_p.append(first_img.extract())
            grid_p.append(second_img.extract())
            run[i].insert_before(grid_p)
            run[i].decompose()
            run[i + 1].decompose()
            processed.add(id(run[i]))
            processed.add(id(run[i + 1]))

    # --- Process image grids (multiple images in one <p>) ---
    for p in soup.find_all("p"):
        children = [
            c for c in p.children
            if not (isinstance(c, NavigableString) and not c.strip())
        ]
        if len(children) < 2:
            continue
        all_images = all(
            (isinstance(c, Tag) and c.name == "img") or
            (isinstance(c, Tag) and c.name == "a" and c.find("img"))
            for c in children
        )
        if not all_images:
            continue

        p["class"] = p.get("class", []) + ["image-grid"]
        p["style"] = "display:flex;justify-content:center;gap:8px;margin:24px 0;align-items:flex-start;"
        for img in p.find_all("img"):
            w = 100 / len(children)
            gap = 8 * (len(children) - 1) / len(children)
            img["style"] = f"width:calc({w}% - {gap}px);margin:0;border-radius:8px;height:auto;"

    # --- Apply theme styles to matching elements ---
    for selector, css in style.items():
        if selector == "pre code":
            continue
        for el in soup.select(selector):
            if selector == "code" and el.parent and el.parent.name == "pre":
                continue
            if el.name == "img" and el.find_parent(class_="image-grid"):
                continue
            existing = el.get("style", "")
            el["style"] = f"{existing};{css}" if existing else css

    # --- Restore list markers (Tailwind preflight removes them) ---
    for ul in soup.find_all("ul"):
        ul["style"] = ul.get("style", "") + ";list-style-type:disc !important;list-style-position:outside;"
    for ul_ul in soup.select("ul ul"):
        ul_ul["style"] = ul_ul.get("style", "") + ";list-style-type:circle !important;"
    for ul_ul_ul in soup.select("ul ul ul"):
        ul_ul_ul["style"] = ul_ul_ul.get("style", "") + ";list-style-type:square !important;"
    for ol in soup.find_all("ol"):
        ol["style"] = ol.get("style", "") + ";list-style-type:decimal !important;list-style-position:outside;"

    # --- Heading inline overrides ---
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        for tag, override in _HEADING_INLINE_OVERRIDES.items():
            for node in heading.find_all(tag):
                node["style"] = node.get("style", "") + ";" + override

    # --- Image styling ---
    for img in soup.find_all("img"):
        in_grid = bool(img.find_parent(class_="image-grid"))
        existing = img.get("style", "")
        if in_grid:
            extra = "display:block;max-width:100%;height:auto;margin:0 !important;padding:8px !important;border-radius:14px !important;box-sizing:border-box;box-shadow:0 12px 28px rgba(15,23,42,0.18),0 2px 8px rgba(15,23,42,0.12);border:1px solid rgba(255,255,255,0.75);"
        else:
            extra = "display:block;width:100%;max-width:100%;height:auto;margin:30px auto !important;padding:8px !important;border-radius:14px !important;box-sizing:border-box;box-shadow:0 16px 34px rgba(15,23,42,0.22),0 4px 10px rgba(15,23,42,0.12);border:1px solid rgba(15,23,42,0.12);"
        img["style"] = f"{existing};{extra}" if existing else extra

    # --- Wrap in container div ---
    container = soup.new_tag("div", style=style["container"])
    for child in list(soup.body.children) if soup.body else list(soup.children):
        container.append(child.extract())
    return str(container)


# ---------------------------------------------------------------------------
# WeChat compatibility (ported from makeWeChatCompatible)
# ---------------------------------------------------------------------------

_CJK_PUNCT = re.compile(r"^\s*([：；，。！？、：])(.*)$", re.DOTALL)
_INLINE_EMPHASIS_TAGS = {"strong", "b", "em", "span", "a", "code"}


def make_wechat_compatible(html: str, theme_id: str = "claude") -> str:
    """Apply WeChat-specific fixes (ported from makeWeChatCompatible).

    Note: does NOT convert images to base64 (WeChat API uploads images separately).
    """
    style = THEMES.get(theme_id, THEMES["claude"])
    container_style = style.get("container", "")
    soup = BeautifulSoup(html, "html.parser")

    # 1. Wrap in <section> (WeChat prefers section as root)
    root_children = list(soup.body.children) if soup.body else list(soup.children)
    section = soup.new_tag("section", style=container_style)

    # If root is a single div, unwrap it
    if len(root_children) == 1 and isinstance(root_children[0], Tag) and root_children[0].name == "div":
        for child in list(root_children[0].children):
            section.append(child.extract())
    else:
        for child in root_children:
            section.append(child.extract())

    # 2. Convert flex image wrappers to table layout (WeChat ignores flex)
    for node in section.find_all(["div", "p"]):
        if node.find_parent(["pre", "code"]):
            continue
        style_str = node.get("style", "")
        is_flex = "display:flex" in style_str.replace(" ", "") or "display: flex" in style_str
        is_grid = "image-grid" in " ".join(node.get("class", []))
        if not is_flex and not is_grid:
            continue

        flex_children = list(node.children)
        # Filter out whitespace
        flex_children = [c for c in flex_children if not (isinstance(c, NavigableString) and not c.strip())]
        if not flex_children:
            continue

        all_imgs = all(
            (isinstance(c, Tag) and c.name == "img") or
            (isinstance(c, Tag) and c.find("img"))
            for c in flex_children
        )
        if not all_imgs:
            if is_flex:
                node["style"] = style_str.replace("display:flex", "display:block").replace("display: flex", "display:block")
            continue

        table = soup.new_tag("table", style="width:100%;border-collapse:collapse;margin:16px 0;border:none !important;")
        tbody = soup.new_tag("tbody")
        tr = soup.new_tag("tr", style="border:none !important;background:transparent !important;")

        for child in flex_children:
            td = soup.new_tag("td", style="padding:0 4px;vertical-align:top;border:none !important;background:transparent !important;")
            if isinstance(child, Tag):
                child_copy = child.extract()
                td.append(child_copy)
                if child_copy.name == "img":
                    existing = child_copy.get("style", "")
                    existing = re.sub(r"width:\s*[^;]+;?", "", existing)
                    child_copy["style"] = f"{existing};width:100% !important;display:block;margin:0 auto;"
            tr.append(td)

        tbody.append(tr)
        table.append(tbody)
        node.replace_with(table)

    # 3. List item flattening (WeChat misrenders nested <li>)
    for li in section.find_all("li"):
        for p in li.find_all("p"):
            span = soup.new_tag("span")
            if p.get("style"):
                span["style"] = p["style"]
            span.extend(p.children)
            p.replace_with(span)

    # 3b. Convert <ol>/<ul> to styled <p> tags (WeChat renders list numbers incorrectly)
    p_style = style.get("p", "")
    # Ordered lists → manual numbered paragraphs
    for ol in section.find_all("ol"):
        counter = 0
        for li in ol.find_all("li", recursive=False):
            counter += 1
            p = soup.new_tag("p", style=p_style)
            num_span = soup.new_tag("span", style="font-weight:bold;")
            num_span.string = f"{counter}. "
            p.append(num_span)
            # Move li's children into p
            for child in list(li.children):
                p.append(child.extract())
            li.replace_with(p)
        ol.unwrap()
    # Unordered lists → bullet paragraphs
    for ul in section.find_all("ul"):
        for li in ul.find_all("li", recursive=False):
            p = soup.new_tag("p", style=p_style)
            bullet = soup.new_tag("span", style="font-weight:bold;")
            bullet.string = "· "
            p.append(bullet)
            for child in list(li.children):
                p.append(child.extract())
            li.replace_with(p)
        ul.unwrap()

    # 4. Force font inheritance (WeChat overrides inherited fonts)
    font_match = re.search(r"font-family:\s*([^;]+);", container_style)
    size_match = re.search(r"font-size:\s*([^;]+);", container_style)
    color_match = re.search(r"color:\s*([^;]+);", container_style)
    lh_match = re.search(r"line-height:\s*([^;]+);", container_style)

    text_tags = section.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "span"])
    for node in text_tags:
        if node.name == "span" and node.find_parent(["pre", "code"]):
            continue
        current = node.get("style", "")
        additions = []
        if font_match and "font-family:" not in current:
            additions.append(f"font-family:{font_match.group(1)};")
        if lh_match and "line-height:" not in current:
            additions.append(f"line-height:{lh_match.group(1)};")
        if size_match and "font-size:" not in current and node.name in ("p", "li", "blockquote", "span"):
            additions.append(f"font-size:{size_match.group(1)};")
        if color_match and "color:" not in current:
            additions.append(f"color:{color_match.group(1)};")
        if additions:
            node["style"] = (current + " " + " ".join(additions)).strip()

    # 5. CJK punctuation attachment (keep punctuation with preceding emphasis)
    for node in section.find_all(_INLINE_EMPHASIS_TAGS):
        next_sib = node.next_sibling
        if not isinstance(next_sib, NavigableString):
            continue
        text = str(next_sib)
        m = _CJK_PUNCT.match(text)
        if not m:
            continue
        punct = m.group(1)
        rest = m.group(2) or ""
        node.append(NavigableString(punct))
        if rest:
            next_sib.replace_with(NavigableString(rest))
        else:
            next_sib.extract()

    # 6. Prevent line breaks between inline emphasis and CJK punctuation
    output = str(section)
    output = re.sub(
        r"(</(?:strong|b|em|span|a|code)>)\s*([：；，。！？、])",
        r"\1⁠\2",
        output,
    )

    return output


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def markdown_to_wechat_html(md_text: str, theme_id: str = "claude") -> str:
    """Convert Markdown to WeChat-compatible HTML with inline styles.

    This is the main entry point that replaces the old _md_to_html() function.
    """
    html = render_markdown(md_text)
    html = apply_theme(html, theme_id)
    html = make_wechat_compatible(html, theme_id)
    return html


def list_themes() -> list[dict[str, str]]:
    """Return available theme info."""
    return [
        {"id": tid, "name": tid.title()}
        for tid in THEMES
    ]
