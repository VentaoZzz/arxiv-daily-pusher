"""
Scores each paper by keyword relevance (local, no external API needed).
Title match = 2pts per keyword, abstract match = 1pt per keyword.
Score is normalized to [0, 1].
"""


def compute_relevance_score(paper: dict, keywords: list[str]) -> float:
    title_lower = paper["title"].lower()
    abstract_lower = paper["abstract"].lower()
    max_possible = len(keywords) * 3
    score = 0.0
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in title_lower:
            score += 2
        if kw_lower in abstract_lower:
            score += 1
    return round(score / max_possible, 4) if max_possible > 0 else 0.0


def rank_and_filter(papers: list[dict], keywords: list[str], top_k: int = 6) -> list[dict]:
    for paper in papers:
        paper["score"] = compute_relevance_score(paper, keywords)
    ranked = sorted(papers, key=lambda p: (p["score"], p["published_local"]), reverse=True)
    return ranked[:top_k]
