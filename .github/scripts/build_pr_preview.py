#!/usr/bin/env python3
"""
Build a Discord-themed side-by-side PR preview (Previous vs. Proposed)
with reflow-aware semantic diffing and in-place image rendering.

Uses only the Python 3 standard library.
"""

import argparse
import difflib
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

TEXT_EXTS = {".md"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
SUPPORTED_EXTS = TEXT_EXTS | IMAGE_EXTS
MAX_CHARS = 2000


@dataclass
class Block:
    kind: str  # "text" | "image"
    file_name: str
    post_index: int
    raw: str  # markdown block text or image filename
    norm_key: str  # normalized text or image sha256
    image_rel_url: str = ""
    file_char_len: int = 0


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_for_compare(text: str) -> str:
    """Normalize whitespace so minor spacing/reflow doesn't look like a rewrite."""
    return re.sub(r"\s+", " ", text.strip())


def split_markdown_blocks(text: str) -> list[str]:
    """
    Split a markdown post into semantic blocks (headings, paragraphs,
    fenced code blocks, and individual list items) so adding/editing one
    section or item doesn't mark an entire reflowed file as changed.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").strip().split("\n")
    blocks: list[str] = []
    buf: list[str] = []
    in_fence = False
    fence_marker = ""

    def flush():
        if buf:
            joined = "\n".join(buf).strip()
            if joined:
                blocks.append(joined)
            buf.clear()

    for line in lines:
        stripped = line.lstrip()
        if in_fence:
            buf.append(line)
            if stripped.startswith(fence_marker):
                in_fence = False
                flush()
            continue

        if stripped.startswith("```") or stripped.startswith("~~~"):
            flush()
            in_fence = True
            fence_marker = stripped[:3]
            buf.append(line)
            continue

        if not stripped:
            flush()
            continue

        # Start a new block on headings or list items so edits stay tightly scoped
        if re.match(r"^(#{1,3}\s+|[-*]\s+|\d+\.\s+)", stripped):
            flush()
            buf.append(line)
            continue

        # Continuation lines for a list item (indented under a bullet/numbered item)
        if buf and re.match(r"^(?:[-*]\s+|\d+\.\s+)", buf[0].lstrip()) and (
            line.startswith("  ") or line.startswith("\t") or stripped.startswith("→")
        ):
            buf.append(line)
            continue

        # If previous buffer was a heading, flush before starting body paragraph
        if buf and re.match(r"^#{1,3}\s+", buf[0].lstrip()):
            flush()

        buf.append(line)

    flush()
    return blocks


def load_channel_blocks(
    root: Path, channel: str, side: str, assets_dir: Path
) -> tuple[list[Block], list[dict]]:
    """Load ordered posts and semantic blocks for ``channels/<channel>``."""
    chan_dir = root / "channels" / channel
    if not chan_dir.is_dir():
        return [], []

    entries = sorted(
        (
            p
            for p in chan_dir.iterdir()
            if p.is_file()
            and not p.name.startswith(".")
            and p.suffix.lower() in SUPPORTED_EXTS
        ),
        key=lambda p: (p.name.lower(), p.name),
    )

    blocks: list[Block] = []
    posts_meta: list[dict] = []

    for post_idx, entry in enumerate(entries):
        suffix = entry.suffix.lower()
        if suffix in TEXT_EXTS:
            raw = entry.read_text(encoding="utf-8", errors="replace")
            normalized = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
            char_len = len(normalized)
            posts_meta.append(
                {
                    "index": post_idx,
                    "file": entry.name,
                    "kind": "text",
                    "chars": char_len,
                }
            )
            for blk in split_markdown_blocks(normalized):
                blocks.append(
                    Block(
                        kind="text",
                        file_name=entry.name,
                        post_index=post_idx,
                        raw=blk,
                        norm_key="T:" + normalize_for_compare(blk),
                        file_char_len=char_len,
                    )
                )
        elif suffix in IMAGE_EXTS:
            data = entry.read_bytes()
            digest = sha256_bytes(data)
            rel_asset = f"assets/{side}/{channel}/{entry.name}"
            dest = assets_dir / side / channel / entry.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            posts_meta.append(
                {
                    "index": post_idx,
                    "file": entry.name,
                    "kind": "image",
                    "bytes": len(data),
                }
            )
            blocks.append(
                Block(
                    kind="image",
                    file_name=entry.name,
                    post_index=post_idx,
                    raw=entry.name,
                    norm_key="I:" + digest,
                    image_rel_url=rel_asset,
                )
            )

    return blocks, posts_meta


def render_inline_markdown(text: str) -> str:
    """Render Discord-style inline markdown safely to HTML."""
    # Protect inline code spans first
    code_tokens: list[str] = []

    def _stash_code(m: re.Match) -> str:
        idx = len(code_tokens)
        code_tokens.append(f'<code class="inline-code">{html.escape(m.group(1))}</code>')
        return f"\x00CODE{idx}\x00"

    escaped = html.escape(text)
    # Restore markdown link syntax characters unaffected by escape, then parse
    escaped = re.sub(r"`([^`]+)`", _stash_code, escaped)

    # Template variables {{VAR_NAME}}
    escaped = re.sub(
        r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}",
        r'<span class="var-pill" title="Template variable">{{&#8203;\1}}</span>',
        escaped,
    )

    # Discord mentions: <@123>, <@&123>, <#123>, <id:browse>
    escaped = re.sub(
        r"&lt;@&amp;(\d+)&gt;",
        r'<span class="mention">@role-\1</span>',
        escaped,
    )
    escaped = re.sub(
        r"&lt;@(\d+)&gt;",
        r'<span class="mention">@user-\1</span>',
        escaped,
    )
    escaped = re.sub(
        r"&lt;#(\d+)&gt;",
        r'<span class="mention">#channel-\1</span>',
        escaped,
    )
    escaped = re.sub(
        r"&lt;id:([a-zA-Z0-9_-]+)&gt;",
        r'<span class="mention">#\1</span>',
        escaped,
    )

    # Markdown links [label](https://...)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        escaped,
    )

    # Bare URLs not already inside href="..."
    escaped = re.sub(
        r'(?<!href=")(https?://[^\s<)]+)',
        r'<a href="\1" target="_blank" rel="noopener noreferrer">\1</a>',
        escaped,
    )

    # Bold & Italic
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)

    # Restore code tokens
    for idx, tok in enumerate(code_tokens):
        escaped = escaped.replace(f"\x00CODE{idx}\x00", tok)

    return escaped


def render_block_html(raw: str) -> str:
    """Render a single markdown block as Discord-styled HTML."""
    stripped = raw.lstrip()
    if stripped.startswith("```") or stripped.startswith("~~~"):
        lines = raw.split("\n")
        body = "\n".join(lines[1:-1] if len(lines) >= 2 else lines)
        return f'<pre class="code-block"><code>{html.escape(body)}</code></pre>'

    m_h = re.match(r"^(#{1,3})\s+(.*)$", stripped)
    if m_h:
        level = len(m_h.group(1))
        return f'<h{level} class="md-h{level}">{render_inline_markdown(m_h.group(2))}</h{level}>'

    m_ul = re.match(r"^[-*]\s+(.*)$", stripped, re.DOTALL)
    if m_ul:
        body = m_ul.group(1).replace("\n", "<br>")
        return f'<div class="md-li"><span class="bullet">•</span><span>{render_inline_markdown(body)}</span></div>'

    m_ol = re.match(r"^(\d+\.)\s+(.*)$", stripped, re.DOTALL)
    if m_ol:
        body = m_ol.group(2).replace("\n", "<br>")
        return f'<div class="md-li"><span class="bullet">{m_ol.group(1)}</span><span>{render_inline_markdown(body)}</span></div>'

    return f'<p class="md-p">{render_inline_markdown(raw).replace(chr(10), "<br>")}</p>'


def word_diff_html(old_text: str, new_text: str) -> tuple[str, str]:
    """Produce word-level highlighted HTML for a modified text block."""
    old_tokens = re.findall(r"\S+|\s+", old_text)
    new_tokens = re.findall(r"\S+|\s+", new_text)
    sm = difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=False)
    left_parts: list[str] = []
    right_parts: list[str] = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        old_seg = "".join(old_tokens[i1:i2])
        new_seg = "".join(new_tokens[j1:j2])
        if tag == "equal":
            rendered = render_inline_markdown(old_seg).replace("\n", "<br>")
            left_parts.append(rendered)
            right_parts.append(rendered)
        elif tag == "delete":
            left_parts.append(
                f'<del class="w-del">{render_inline_markdown(old_seg).replace(chr(10), "<br>")}</del>'
            )
        elif tag == "insert":
            right_parts.append(
                f'<ins class="w-ins">{render_inline_markdown(new_seg).replace(chr(10), "<br>")}</ins>'
            )
        elif tag == "replace":
            left_parts.append(
                f'<del class="w-del">{render_inline_markdown(old_seg).replace(chr(10), "<br>")}</del>'
            )
            right_parts.append(
                f'<ins class="w-ins">{render_inline_markdown(new_seg).replace(chr(10), "<br>")}</ins>'
            )

    return f'<p class="md-p">{"".join(left_parts)}</p>', f'<p class="md-p">{"".join(right_parts)}</p>'


def diff_channel_blocks(
    base_blocks: list[Block], head_blocks: list[Block]
) -> tuple[list[dict], list[dict], dict]:
    """
    Compute a reflow-aware diff across the entire channel.

    Returns ``(left_items, right_items, stats)`` where each item carries its
    original post boundary metadata and diff status (equal/insert/delete/replace).
    """
    base_keys = [b.norm_key for b in base_blocks]
    head_keys = [b.norm_key for b in head_blocks]
    sm = difflib.SequenceMatcher(None, base_keys, head_keys, autojunk=False)

    left_items: list[dict] = []
    right_items: list[dict] = []
    stats = {"equal": 0, "added": 0, "removed": 0, "modified": 0, "moved_posts": 0}

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for b, h in zip(base_blocks[i1:i2], head_blocks[j1:j2]):
                moved = b.file_name != h.file_name
                if moved:
                    stats["moved_posts"] += 1
                stats["equal"] += 1
                left_items.append(
                    {
                        "block": b,
                        "status": "equal",
                        "moved": moved,
                        "html": _render_image_or_text(b),
                    }
                )
                right_items.append(
                    {
                        "block": h,
                        "status": "equal",
                        "moved": moved,
                        "html": _render_image_or_text(h),
                    }
                )
        elif tag == "delete":
            for b in base_blocks[i1:i2]:
                stats["removed"] += 1
                left_items.append(
                    {
                        "block": b,
                        "status": "delete",
                        "moved": False,
                        "html": _render_image_or_text(b),
                    }
                )
        elif tag == "insert":
            for h in head_blocks[j1:j2]:
                stats["added"] += 1
                right_items.append(
                    {
                        "block": h,
                        "status": "insert",
                        "moved": False,
                        "html": _render_image_or_text(h),
                    }
                )
        elif tag == "replace":
            # Pair similar text blocks for inline word-diff; treat unmatched as del/ins
            b_slice = base_blocks[i1:i2]
            h_slice = head_blocks[j1:j2]
            paired = min(len(b_slice), len(h_slice))
            for k in range(paired):
                b, h = b_slice[k], h_slice[k]
                if b.kind == "text" and h.kind == "text":
                    ratio = difflib.SequenceMatcher(None, b.raw, h.raw).ratio()
                    if ratio >= 0.45:
                        stats["modified"] += 1
                        l_html, r_html = word_diff_html(b.raw, h.raw)
                        left_items.append(
                            {"block": b, "status": "replace", "moved": False, "html": l_html}
                        )
                        right_items.append(
                            {"block": h, "status": "replace", "moved": False, "html": r_html}
                        )
                        continue
                stats["removed"] += 1
                stats["added"] += 1
                left_items.append(
                    {"block": b, "status": "delete", "moved": False, "html": _render_image_or_text(b)}
                )
                right_items.append(
                    {"block": h, "status": "insert", "moved": False, "html": _render_image_or_text(h)}
                )
            for b in b_slice[paired:]:
                stats["removed"] += 1
                left_items.append(
                    {"block": b, "status": "delete", "moved": False, "html": _render_image_or_text(b)}
                )
            for h in h_slice[paired:]:
                stats["added"] += 1
                right_items.append(
                    {"block": h, "status": "insert", "moved": False, "html": _render_image_or_text(h)}
                )

    return left_items, right_items, stats


def _render_image_or_text(blk: Block) -> str:
    if blk.kind == "image":
        return (
            f'<div class="img-wrap">'
            f'<img src="{html.escape(blk.image_rel_url)}" alt="{html.escape(blk.file_name)}" loading="lazy">'
            f'<div class="img-caption">{html.escape(blk.file_name)}</div>'
            f"</div>"
        )
    return render_block_html(blk.raw)


def render_pane_html(items: list[dict], posts_meta: list[dict], empty_label: str) -> str:
    """Group rendered diff items back into Discord message cards per file."""
    if not items:
        return f'<div class="empty-pane">{html.escape(empty_label)}</div>'

    meta_by_file = {m["file"]: m for m in posts_meta}
    groups: list[tuple[str, list[dict]]] = []
    for item in items:
        fname = item["block"].file_name
        if not groups or groups[-1][0] != fname:
            groups.append((fname, [item]))
        else:
            groups[-1][1].append(item)

    cards: list[str] = []
    for fname, grp in groups:
        meta = meta_by_file.get(fname, {})
        if meta.get("kind") == "text":
            chars = meta.get("chars", 0)
            warn_cls = " char-warn" if chars > MAX_CHARS else ""
            badge = f'<span class="post-badge{warn_cls}">{chars:,} / {MAX_CHARS:,} chars</span>'
        else:
            size_kb = meta.get("bytes", 0) / 1024
            badge = f'<span class="post-badge">image · {size_kb:.1f} KB</span>'

        has_changes = any(i["status"] != "equal" for i in grp)
        all_moved = all(i["status"] == "equal" and i["moved"] for i in grp)
        card_cls = "msg-card has-changes" if has_changes else "msg-card unchanged-card"
        moved_tag = ' <span class="reflow-pill" title="Moved across post boundary without text changes">reflowed</span>' if all_moved else ""

        inner_blocks: list[str] = []
        for it in grp:
            st = it["status"]
            inner_blocks.append(f'<div class="blk blk-{st}">{it["html"]}</div>')

        cards.append(
            f'<article class="{card_cls}">'
            f'  <div class="msg-header">'
            f'    <div class="avatar">AZ</div>'
            f'    <div class="msg-meta">'
            f'      <span class="bot-name">AZMSH Bot</span><span class="app-tag">APP</span>'
            f'      <span class="file-tag">{html.escape(fname)}</span>{badge}{moved_tag}'
            f"    </div>"
            f"  </div>"
            f'  <div class="msg-body">{"".join(inner_blocks)}</div>'
            f"</article>"
        )

    return "".join(cards)


def extract_git_tree(repo_dir: Path, ref: str, dest: Path) -> None:
    """Export ``channels/`` at ``ref`` into ``dest``."""
    dest.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["git", "-C", str(repo_dir), "ls-tree", "-r", "--name-only", ref, "channels"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return
    for rel in proc.stdout.splitlines():
        rel = rel.strip()
        if not rel:
            continue
        blob = subprocess.run(
            ["git", "-C", str(repo_dir), "show", f"{ref}:{rel}"],
            capture_output=True,
            check=True,
        )
        out_path = dest / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(blob.stdout)


def build_html_page(
    channels_data: list[dict],
    pr_number: str,
    pr_title: str,
    base_sha: str,
    head_sha: str,
) -> str:
    tabs_html: list[str] = []
    panels_html: list[str] = []

    for idx, ch in enumerate(channels_data):
        active = " active" if idx == 0 else ""
        st = ch["stats"]
        change_total = st["added"] + st["removed"] + st["modified"]
        pill = (
            f'<span class="tab-badge changed">{change_total} change(s)</span>'
            if change_total > 0
            else (
                '<span class="tab-badge reflow">reflowed</span>'
                if st["moved_posts"] > 0
                else '<span class="tab-badge clean">unchanged</span>'
            )
        )
        tabs_html.append(
            f'<button class="tab-btn{active}" data-channel="{html.escape(ch["name"])}">'
            f'  <span class="hash">#</span>{html.escape(ch["name"])} {pill}'
            f"</button>"
        )

        stat_line = (
            f'<span class="st-add">+{st["added"]} added</span> · '
            f'<span class="st-mod">~{st["modified"]} modified</span> · '
            f'<span class="st-del">-{st["removed"]} removed</span>'
            + (
                f' · <span class="st-reflow">{st["moved_posts"]} block(s) reflowed across posts</span>'
                if st["moved_posts"]
                else ""
            )
        )

        panels_html.append(
            f'<section class="channel-panel{active}" id="panel-{html.escape(ch["name"])}">'
            f'  <div class="channel-bar">'
            f'    <div class="channel-title"><span class="hash">#</span> {html.escape(ch["name"])}</div>'
            f'    <div class="channel-stats">{stat_line}</div>'
            f"  </div>"
            f'  <div class="split-grid">'
            f'    <div class="pane">'
            f'      <div class="pane-head pane-old">Previous (<code>main</code> @ <code>{html.escape(base_sha)}</code>)</div>'
            f'      <div class="pane-body">{ch["left_html"]}</div>'
            f"    </div>"
            f'    <div class="pane">'
            f'      <div class="pane-head pane-new">Proposed (PR #{html.escape(pr_number)} @ <code>{html.escape(head_sha)}</code>)</div>'
            f'      <div class="pane-body">{ch["right_html"]}</div>'
            f"    </div>"
            f"  </div>"
            f"</section>"
        )

    title_safe = html.escape(pr_title or f"PR #{pr_number}")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Discord Preview — PR #{html.escape(pr_number)}</title>
  <style>
    :root {{
      --bg-base: #313338;
      --bg-sidebar: #2b2d31;
      --bg-deep: #1e1f22;
      --text-normal: #dbdee1;
      --text-muted: #949ba4;
      --text-header: #f2f3f5;
      --blurple: #5865f2;
      --green: #23a55a;
      --red: #da373c;
      --amber: #f0b232;
      --border: #3f4147;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "gg sans", "Segoe UI", system-ui, -apple-system, sans-serif;
      background: var(--bg-deep);
      color: var(--text-normal);
      line-height: 1.45;
    }}
    .topbar {{
      background: var(--bg-sidebar);
      border-bottom: 1px solid var(--border);
      padding: 12px 20px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      position: sticky;
      top: 0;
      z-index: 20;
    }}
    .topbar h1 {{
      margin: 0;
      font-size: 16px;
      color: var(--text-header);
      font-weight: 700;
    }}
    .topbar .sub {{ font-size: 12px; color: var(--text-muted); margin-top: 2px; }}
    .controls {{ display: flex; align-items: center; gap: 10px; }}
    .toggle-btn {{
      background: var(--bg-base);
      color: var(--text-normal);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 13px;
      cursor: pointer;
    }}
    .toggle-btn.on {{ background: var(--blurple); border-color: var(--blurple); color: #fff; }}
    .tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      padding: 10px 20px;
      background: var(--bg-deep);
      border-bottom: 1px solid var(--border);
    }}
    .tab-btn {{
      background: var(--bg-sidebar);
      color: var(--text-muted);
      border: 1px solid transparent;
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 14px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }}
    .tab-btn:hover {{ background: #35373c; color: var(--text-normal); }}
    .tab-btn.active {{ background: #404249; color: var(--text-header); border-color: var(--blurple); }}
    .hash {{ color: var(--text-muted); font-weight: 600; }}
    .tab-badge {{
      font-size: 11px;
      padding: 1px 6px;
      border-radius: 10px;
      font-weight: 600;
    }}
    .tab-badge.changed {{ background: rgba(88,101,242,0.25); color: #b5bdfc; }}
    .tab-badge.reflow {{ background: rgba(240,178,50,0.2); color: var(--amber); }}
    .tab-badge.clean {{ background: rgba(148,155,164,0.15); color: var(--text-muted); }}
    .channel-panel {{ display: none; }}
    .channel-panel.active {{ display: block; }}
    .channel-bar {{
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      padding: 10px 20px;
      background: var(--bg-base);
      border-bottom: 1px solid var(--border);
      gap: 8px;
    }}
    .channel-title {{ font-size: 16px; font-weight: 700; color: var(--text-header); }}
    .channel-stats {{ font-size: 13px; color: var(--text-muted); }}
    .st-add {{ color: #4ade80; font-weight: 600; }}
    .st-mod {{ color: var(--amber); font-weight: 600; }}
    .st-del {{ color: #f87171; font-weight: 600; }}
    .st-reflow {{ color: #93c5fd; }}
    .split-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      padding: 14px;
      align-items: start;
    }}
    @media (max-width: 980px) {{
      .split-grid {{ grid-template-columns: 1fr; }}
    }}
    .pane {{
      background: var(--bg-base);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    .pane-head {{
      padding: 8px 14px;
      font-size: 13px;
      font-weight: 600;
      border-bottom: 1px solid var(--border);
      background: var(--bg-sidebar);
    }}
    .pane-old {{ border-top: 3px solid var(--text-muted); }}
    .pane-new {{ border-top: 3px solid var(--blurple); }}
    .pane-body {{ padding: 12px; display: flex; flex-direction: column; gap: 14px; }}
    .empty-pane {{ color: var(--text-muted); font-style: italic; padding: 20px; text-align: center; }}
    .msg-card {{
      background: rgba(0, 0, 0, 0.12);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      padding: 12px 14px;
    }}
    body.only-changes .unchanged-card {{ display: none; }}
    .msg-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
    .avatar {{
      width: 34px; height: 34px; border-radius: 50%;
      background: var(--blurple); color: #fff; font-weight: 700; font-size: 13px;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }}
    .msg-meta {{ display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 13px; }}
    .bot-name {{ font-weight: 700; color: var(--text-header); }}
    .app-tag {{
      background: var(--blurple); color: #fff; font-size: 10px; font-weight: 700;
      padding: 1px 5px; border-radius: 3px; letter-spacing: 0.3px;
    }}
    .file-tag {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px; color: var(--text-muted);
    }}
    .post-badge {{
      font-size: 11px; color: var(--text-muted); background: var(--bg-deep);
      padding: 1px 6px; border-radius: 4px;
    }}
    .post-badge.char-warn {{ color: var(--amber); border: 1px solid rgba(240,178,50,0.4); }}
    .reflow-pill {{
      font-size: 11px; color: #93c5fd; background: rgba(147,197,253,0.12);
      padding: 1px 6px; border-radius: 4px;
    }}
    .msg-body {{ padding-left: 44px; font-size: 15px; overflow-wrap: anywhere; }}
    .blk {{ padding: 2px 8px; margin: 3px 0; border-radius: 4px; border-left: 3px solid transparent; }}
    .blk-insert {{ background: rgba(35, 165, 90, 0.16); border-left-color: var(--green); }}
    .blk-delete {{ background: rgba(218, 55, 60, 0.16); border-left-color: var(--red); }}
    .blk-replace {{ background: rgba(240, 178, 50, 0.11); border-left-color: var(--amber); }}
    .w-ins {{ background: rgba(35, 165, 90, 0.38); color: #ecfdf5; text-decoration: none; border-radius: 3px; padding: 0 2px; }}
    .w-del {{ background: rgba(218, 55, 60, 0.38); color: #fef2f2; text-decoration: line-through; border-radius: 3px; padding: 0 2px; }}
    .md-h1 {{ font-size: 20px; margin: 6px 0 4px; color: var(--text-header); }}
    .md-h2 {{ font-size: 17px; margin: 6px 0 3px; color: var(--text-header); }}
    .md-h3 {{ font-size: 15px; margin: 5px 0 2px; color: var(--text-header); }}
    .md-p {{ margin: 4px 0; }}
    .md-li {{ display: flex; gap: 8px; margin: 2px 0; }}
    .bullet {{ color: var(--text-muted); flex-shrink: 0; }}
    .inline-code {{
      background: var(--bg-deep); padding: 1px 5px; border-radius: 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
    }}
    .code-block {{
      background: var(--bg-deep); border: 1px solid var(--border); border-radius: 6px;
      padding: 10px 12px; margin: 6px 0; overflow-x: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
    }}
    .mention {{
      background: rgba(88, 101, 242, 0.3); color: #c9cdfb;
      padding: 0 4px; border-radius: 3px; font-weight: 500;
    }}
    .var-pill {{
      background: rgba(240, 178, 50, 0.22); color: #fde68a;
      border: 1px solid rgba(240, 178, 50, 0.45);
      padding: 0 5px; border-radius: 4px;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px;
    }}
    a {{ color: #00a8fc; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .img-wrap {{ margin: 6px 0; }}
    .img-wrap img {{
      max-width: 100%; max-height: 420px; border-radius: 6px;
      border: 1px solid var(--border); display: block;
    }}
    .img-caption {{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }}
  </style>
</head>
<body>
  <header class="topbar">
    <div>
      <h1>Discord Channel Preview — PR #{html.escape(pr_number)}: {title_safe}</h1>
      <div class="sub">Reflow-aware diff: unchanged text shifted across posts is marked <code>reflowed</code> instead of changed.</div>
    </div>
    <div class="controls">
      <button id="toggleChanges" class="toggle-btn" type="button">Show Changed Posts Only</button>
    </div>
  </header>
  <nav class="tabs">{"".join(tabs_html)}</nav>
  <main>{"".join(panels_html)}</main>
  <script>
    const tabs = document.querySelectorAll('.tab-btn');
    const panels = document.querySelectorAll('.channel-panel');
    tabs.forEach(btn => {{
      btn.addEventListener('click', () => {{
        tabs.forEach(t => t.classList.remove('active'));
        panels.forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('panel-' + btn.dataset.channel).classList.add('active');
      }});
    }});
    const toggleBtn = document.getElementById('toggleChanges');
    toggleBtn.addEventListener('click', () => {{
      document.body.classList.toggle('only-changes');
      const on = document.body.classList.contains('only-changes');
      toggleBtn.classList.toggle('on', on);
      toggleBtn.textContent = on ? 'Showing Changed Posts Only' : 'Show Changed Posts Only';
    }});
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Discord PR preview site.")
    parser.add_argument("--repo", default=".", help="Path to git repository")
    parser.add_argument("--base-ref", required=True, help="Base git ref/SHA")
    parser.add_argument("--head-ref", default="HEAD", help="Head git ref/SHA")
    parser.add_argument("--out-dir", required=True, help="Output directory for HTML & assets")
    parser.add_argument("--pr-number", default="local", help="Pull request number")
    parser.add_argument("--pr-title", default="", help="Pull request title")
    args = parser.parse_args()

    repo_dir = Path(args.repo).resolve()
    out_dir = Path(args.out_dir).resolve()
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = out_dir / "assets"

    base_short = subprocess.check_output(
        ["git", "-C", str(repo_dir), "rev-parse", "--short", args.base_ref], text=True
    ).strip()
    head_short = subprocess.check_output(
        ["git", "-C", str(repo_dir), "rev-parse", "--short", args.head_ref], text=True
    ).strip()

    with tempfile.TemporaryDirectory() as tmp:
        base_root = Path(tmp) / "base"
        head_root = Path(tmp) / "head"
        extract_git_tree(repo_dir, args.base_ref, base_root)
        extract_git_tree(repo_dir, args.head_ref, head_root)

        base_chans = {
            p.name for p in (base_root / "channels").iterdir() if p.is_dir()
        } if (base_root / "channels").is_dir() else set()
        head_chans = {
            p.name for p in (head_root / "channels").iterdir() if p.is_dir()
        } if (head_root / "channels").is_dir() else set()

        all_channels = sorted(base_chans | head_chans)
        channels_data: list[dict] = []

        for ch in all_channels:
            b_blocks, b_meta = load_channel_blocks(base_root, ch, "base", assets_dir)
            h_blocks, h_meta = load_channel_blocks(head_root, ch, "head", assets_dir)
            left_items, right_items, stats = diff_channel_blocks(b_blocks, h_blocks)
            channels_data.append(
                {
                    "name": ch,
                    "stats": stats,
                    "changed": (stats["added"] + stats["removed"] + stats["modified"] + stats["moved_posts"]) > 0,
                    "left_html": render_pane_html(left_items, b_meta, "Channel did not exist yet."),
                    "right_html": render_pane_html(right_items, h_meta, "Channel was removed."),
                }
            )

        # Put changed channels first so reviewers immediately see what changed
        channels_data.sort(key=lambda c: (not c["changed"], c["name"]))

    page = build_html_page(
        channels_data=channels_data,
        pr_number=str(args.pr_number),
        pr_title=args.pr_title,
        base_sha=base_short,
        head_sha=head_short,
    )
    (out_dir / "index.html").write_text(page, encoding="utf-8")

    # Emit JSON summary for PR comment helper
    summary = {
        "pr_number": str(args.pr_number),
        "base_sha": base_short,
        "head_sha": head_short,
        "channels": [
            {"name": c["name"], "changed": c["changed"], "stats": c["stats"]}
            for c in channels_data
        ],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Built preview for {len(channels_data)} channel(s) in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
