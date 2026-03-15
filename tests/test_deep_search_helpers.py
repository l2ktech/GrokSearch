from grok_search.deep_search import (
    DeepSearchCandidate,
    deduplicate_candidates,
    extract_json_payload,
    markdown_excerpt,
    parse_search_results,
)


def test_extract_json_payload_from_fenced_block():
    raw = """下面是结果：
```json
[{"title": "A", "url": "https://example.com", "description": "desc"}]
```
"""
    payload = extract_json_payload(raw)
    assert payload.startswith("[")
    assert '"title": "A"' in payload


def test_parse_search_results_accepts_summary_aliases():
    raw = "[{" \
        '"title": "A", "url": "https://example.com/a", "summary": "alpha"},' \
        ' {"name": "B", "link": "https://example.com/b", "snippet": "beta"}' \
        "]"
    results = parse_search_results(raw)
    assert [item.title for item in results] == ["A", "B"]
    assert results[0].description == "alpha"
    assert results[1].description == "beta"


def test_deduplicate_candidates_preserves_first_match_and_limit():
    candidates = [
        DeepSearchCandidate("A", "https://example.com/path", "first"),
        DeepSearchCandidate("A2", "http://example.com/path#frag", "duplicate"),
        DeepSearchCandidate("B", "https://example.com/other", "second"),
    ]
    deduped = deduplicate_candidates(candidates, limit=2)
    assert len(deduped) == 2
    assert deduped[0].title == "A"
    assert deduped[1].title == "B"


def test_markdown_excerpt_strips_frontmatter_and_truncates():
    markdown = "---\nsource: https://example.com\n---\n\n# Title\n\n" + ("content " * 1000)
    excerpt = markdown_excerpt(markdown, max_chars=500)
    assert not excerpt.startswith("---")
    assert "# Title" in excerpt
    assert "[内容已截断]" in excerpt
