from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class DeepSearchCandidate:
    title: str
    url: str
    description: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
        }


@dataclass(frozen=True)
class FetchedPage:
    title: str
    url: str
    description: str
    excerpt: str

    def to_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "excerpt": self.excerpt,
        }


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    return _WHITESPACE_RE.sub(" ", text)


def extract_json_payload(raw: str) -> str:
    text = raw.strip()
    if not text:
        raise ValueError("搜索结果为空")

    fence_match = _JSON_FENCE_RE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()

    decoder = json.JSONDecoder()
    for marker in ("[", "{"):
        start = text.find(marker)
        while start != -1:
            try:
                _, end = decoder.raw_decode(text[start:])
                return text[start : start + end]
            except json.JSONDecodeError:
                start = text.find(marker, start + 1)

    raise ValueError("未找到可解析的 JSON 结果")


def parse_search_results(raw: str) -> list[DeepSearchCandidate]:
    payload = extract_json_payload(raw)
    data = json.loads(payload)

    if isinstance(data, dict):
        if isinstance(data.get("results"), list):
            items = data["results"]
        elif isinstance(data.get("data"), list):
            items = data["data"]
        else:
            raise ValueError("JSON 结果缺少 results/data 数组")
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("JSON 结果不是数组或对象")

    normalized: list[DeepSearchCandidate] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = _clean_text(item.get("title") or item.get("name") or item.get("headline"))
        url = _clean_text(item.get("url") or item.get("link"))
        description = _clean_text(
            item.get("description")
            or item.get("summary")
            or item.get("snippet")
            or item.get("content")
        )
        if not title and not url:
            continue
        normalized.append(DeepSearchCandidate(title=title or url, url=url, description=description))

    if not normalized:
        raise ValueError("未解析到有效搜索结果")

    return normalized


def canonicalize_url(url: str) -> str:
    raw = _clean_text(url)
    if not raw:
        return ""
    parts = urlsplit(raw)
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    query = parts.query
    return urlunsplit(("", netloc, path, query, ""))


def deduplicate_candidates(
    candidates: Iterable[DeepSearchCandidate],
    *,
    limit: int | None = None,
) -> list[DeepSearchCandidate]:
    deduped: list[DeepSearchCandidate] = []
    seen: set[str] = set()

    for candidate in candidates:
        key = canonicalize_url(candidate.url) or candidate.title.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
        if limit is not None and len(deduped) >= limit:
            break

    return deduped


def markdown_excerpt(markdown: str, *, max_chars: int = 4000) -> str:
    text = markdown.strip()
    text = _FRONTMATTER_RE.sub("", text, count=1)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) <= max_chars:
        return text

    clipped = text[:max_chars]
    paragraph_cut = clipped.rfind("\n\n")
    if paragraph_cut > max_chars // 2:
        clipped = clipped[:paragraph_cut]
    return clipped.rstrip() + "\n\n[内容已截断]"


def build_deep_search_user_prompt(
    query: str,
    candidates: list[DeepSearchCandidate],
    fetched_pages: list[FetchedPage],
) -> str:
    candidate_block = json.dumps([item.to_dict() for item in candidates], ensure_ascii=False, indent=2)
    fetched_block = json.dumps([page.to_dict() for page in fetched_pages], ensure_ascii=False, indent=2)
    return (
        f"用户查询：{query}\n\n"
        "你会收到两部分材料：\n"
        "1. search_results：搜索阶段返回的候选结果列表。\n"
        "2. fetched_pages：对部分高相关 URL 抓取后的正文摘录。\n\n"
        "请基于这些材料输出一份详细、全面、结构化的 Markdown 研究答案。\n"
        "要求：\n"
        "- 使用中文输出。\n"
        "- 先给 3-6 条结论摘要。\n"
        "- 然后给详细分析，按主题分节。\n"
        "- 每个关键判断都要带来源引用，例如 [来源1]。\n"
        "- 最后必须有 `## 来源` 小节，列出所有实际引用到的来源，格式为 `- [来源1] 标题 - URL`。\n"
        "- 如果材料之间存在冲突或不确定性，要单独指出。\n"
        "- 不要编造未提供的事实；优先引用 fetched_pages，其次引用 search_results。\n"
        "- 如果 fetched_pages 不足，也要尽量整合 search_results 给出完整回答。\n\n"
        f"search_results = {candidate_block}\n\n"
        f"fetched_pages = {fetched_block}\n"
    )


def build_fallback_report(
    query: str,
    candidates: list[DeepSearchCandidate],
    fetched_pages: list[FetchedPage],
) -> str:
    lines = [
        f"# {query}",
        "",
        "## 结论摘要",
    ]

    if fetched_pages:
        for idx, page in enumerate(fetched_pages, 1):
            summary = page.description or "已抓取正文，建议查看下方详细摘录。"
            lines.append(f"- {page.title}：[来源{idx}] {summary}")
    else:
        lines.append("- 未能抓取到详细正文，以下保留搜索结果摘要。")

    if fetched_pages:
        lines.extend(["", "## 详细分析"])
        for idx, page in enumerate(fetched_pages, 1):
            lines.extend(
                [
                    "",
                    f"### {page.title}",
                    f"[来源{idx}] {page.url}",
                    "",
                    page.excerpt,
                ]
            )

    if candidates:
        lines.extend(["", "## 更多候选来源"])
        for candidate in candidates:
            lines.append(f"- {candidate.title} - {candidate.url}")
            if candidate.description:
                lines.append(f"  - {candidate.description}")

    lines.extend(["", "## 来源"])
    if fetched_pages:
        for idx, page in enumerate(fetched_pages, 1):
            lines.append(f"- [来源{idx}] {page.title} - {page.url}")
    else:
        for idx, candidate in enumerate(candidates, 1):
            lines.append(f"- [来源{idx}] {candidate.title} - {candidate.url}")

    return "\n".join(lines).strip() + "\n"
