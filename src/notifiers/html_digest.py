"""Single-page HTML digest (Simplified Chinese summaries only)."""

from __future__ import annotations

import html
from pathlib import Path

from src.models import Digest, DigestItem

TYPE_LABELS_ZH = {
    "university": "高校",
    "policy": "招生政策",
    "education": "教育部门",
    "media": "行业媒体",
    "immigration": "移民机构",
}


def _type_label(source_type: str) -> str:
    return TYPE_LABELS_ZH.get(source_type, "资讯")


def _item_block(item: DigestItem, index: int) -> str:
    title = html.escape(item.title_en)
    summary = html.escape(item.summary_zh or "详见原文链接。")
    source = html.escape(item.source_name)
    category = html.escape(item.category)
    country = html.escape(item.country_name)
    link = html.escape(item.link, quote=True)
    label = _type_label(item.source_type)

    return f"""
    <article class="item">
      <div class="item-meta">
        <span class="badge">{index}</span>
        <span class="country">{item.country_flag} {country}</span>
        <span class="tag">{category}</span>
        <span class="tag muted">{label}</span>
      </div>
      <h2 class="item-title">{title}</h2>
      <p class="item-source">{source}</p>
      <p class="item-summary">{summary}</p>
      <a class="item-link" href="{link}" target="_blank" rel="noopener">阅读原文 →</a>
    </article>
    """


def build_digest_html(digest: Digest) -> str:
    if digest.items:
        items_html = "".join(_item_block(item, i) for i, item in enumerate(digest.items, 1))
        count_text = f"共 {len(digest.items)} 条"
    else:
        items_html = '<p class="empty">今日暂无符合筛选条件的新政策动态。</p>'
        count_text = "今日无更新"

    date_label = html.escape(digest.date_label)
    disclaimer = html.escape(digest.disclaimer_zh)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>全球留学政策日报 {date_label}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      background: #f4f6fb;
      color: #1f2937;
      line-height: 1.6;
    }}
    .page {{
      max-width: 720px;
      margin: 0 auto;
      padding: 20px 16px 40px;
    }}
    .header {{
      background: linear-gradient(135deg, #1d4ed8, #4338ca);
      color: #fff;
      border-radius: 16px;
      padding: 24px 20px;
      margin-bottom: 20px;
      box-shadow: 0 10px 30px rgba(37, 99, 235, 0.25);
    }}
    .header h1 {{
      margin: 0 0 8px;
      font-size: 1.5rem;
      font-weight: 700;
    }}
    .header p {{
      margin: 0;
      opacity: 0.92;
      font-size: 0.95rem;
    }}
    .item {{
      background: #fff;
      border-radius: 14px;
      padding: 18px 16px;
      margin-bottom: 14px;
      box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
      border: 1px solid #e5e7eb;
    }}
    .item-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin-bottom: 10px;
      font-size: 0.82rem;
    }}
    .badge {{
      background: #1d4ed8;
      color: #fff;
      width: 1.6rem;
      height: 1.6rem;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
    }}
    .country {{ font-weight: 600; }}
    .tag {{
      background: #eff6ff;
      color: #1d4ed8;
      padding: 2px 8px;
      border-radius: 999px;
    }}
    .tag.muted {{
      background: #f3f4f6;
      color: #6b7280;
    }}
    .item-title {{
      margin: 0 0 6px;
      font-size: 1.05rem;
      line-height: 1.45;
    }}
    .item-source {{
      margin: 0 0 10px;
      color: #6b7280;
      font-size: 0.88rem;
    }}
    .item-summary {{
      margin: 0 0 12px;
      font-size: 0.98rem;
    }}
    .item-link {{
      color: #2563eb;
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 600;
    }}
    .empty {{
      background: #fff;
      border-radius: 14px;
      padding: 24px;
      text-align: center;
      color: #6b7280;
    }}
    .footer {{
      margin-top: 24px;
      text-align: center;
      font-size: 0.78rem;
      color: #9ca3af;
    }}
  </style>
</head>
<body>
  <div class="page">
    <header class="header">
      <h1>🎓 全球留学政策日报</h1>
      <p>{date_label} · {count_text}</p>
    </header>
    <main>
      {items_html}
    </main>
    <footer class="footer">{disclaimer}</footer>
  </div>
</body>
</html>
"""


def write_digest_html(digest: Digest, directory: Path | str = "digests") -> Path:
    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)
    content = build_digest_html(digest)
    latest = out_dir / "latest.html"
    dated = out_dir / f"{digest.date_label}.html"
    latest.write_text(content, encoding="utf-8")
    dated.write_text(content, encoding="utf-8")
    return latest
