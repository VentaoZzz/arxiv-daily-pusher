"""
Fetches arXiv papers with automatic fallback mechanism.
- Primary: arxiv library (with timeout protection)
- Fallback: direct HTTP API
- Configurable via api_mode in config.yaml
"""

import arxiv
import requests
import time
import signal
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET
from contextlib import contextmanager
from typing import Optional


TZ_LOCAL = timezone(timedelta(hours=8))


# ==========================================================================
# Timeout Protection (for arxiv library method)
# ==========================================================================


class TimeoutException(Exception):
    """Raised when operation times out"""

    pass


@contextmanager
def time_limit(seconds: int):
    """Context manager for timeout (Unix/Linux/macOS only)."""

    def signal_handler(signum, frame):
        raise TimeoutException(f"Timed out after {seconds}s")

    old_handler = signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# ==========================================================================
# Common Utilities
# ==========================================================================


def get_yesterday_range_utc(tz_offset_hours: int = 8) -> tuple[datetime, datetime]:
    """Calculate yesterday's date range in UTC."""

    local_tz = timezone(timedelta(hours=tz_offset_hours))
    now_local = datetime.now(local_tz)
    yesterday_start = (now_local - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    yesterday_end = yesterday_start.replace(hour=23, minute=59, second=59)
    return yesterday_start.astimezone(timezone.utc), yesterday_end.astimezone(timezone.utc)


def build_date_query(keyword: str, start_utc: datetime, end_utc: datetime) -> str:
    """Build arXiv query string with date filter."""

    fmt = "%Y%m%d%H%M%S"
    date_filter = f"submittedDate:[{start_utc.strftime(fmt)} TO {end_utc.strftime(fmt)}]"
    return f"all:{keyword} AND {date_filter}"


# ==========================================================================
# Method 1: arxiv Library (with timeout protection)
# ==========================================================================


def fetch_with_arxiv_library(
    keyword: str,
    start_utc: datetime,
    end_utc: datetime,
    tz_offset_hours: int,
    max_results: int = 50,
    timeout_seconds: int = 60,
) -> Optional[list[dict]]:
    """Fetch papers using arxiv library with timeout protection.

    Returns None if timeout or error occurs.
    """

    query = build_date_query(keyword, start_utc, end_utc)
    client = arxiv.Client(page_size=max_results, delay_seconds=3.0, num_retries=2)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    local_tz = timezone(timedelta(hours=tz_offset_hours))

    try:
        with time_limit(timeout_seconds):
            for result in client.results(search):
                arxiv_id = result.entry_id.split("/abs/")[-1]
                published_local = result.published.astimezone(local_tz)
                papers.append(
                    {
                        "title": result.title.strip().replace("\n", " "),
                        "abstract": result.summary.strip().replace("\n", " "),
                        "arxiv_id": arxiv_id,
                        "alphaxiv_url": f"https://alphaxiv.org/overview/{arxiv_id}",
                        "published_local": published_local.strftime("%Y-%m-%d %H:%M"),
                        "matched_keyword": keyword,
                    }
                )
        return papers

    except TimeoutException:
        print(f"     ⚠ arxiv library timeout ({timeout_seconds}s)")
        return None
    except Exception as e:
        # Add richer diagnostics: exception type + message
        print(f"     ⚠ arxiv library error ({type(e).__name__}): {e}")
        return None


# ==========================================================================
# Method 2: Direct HTTP API
# ==========================================================================


def fetch_with_http_api(
    keyword: str,
    start_utc: datetime,
    end_utc: datetime,
    tz_offset_hours: int,
    max_results: int = 50,
) -> list[dict]:
    """Fetch papers using direct HTTP API.

    Returns empty list on error.
    """

    query = build_date_query(keyword, start_utc, end_utc)
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }

    try:
        # Longer timeouts to tolerate unstable arXiv connectivity
        response = requests.get(
            url,
            params=params,
            timeout=(10, 45),  # 10s connect, 45s read
            headers={"User-Agent": "arXiv-Daily-Recommender/1.0"},
        )
        response.raise_for_status()
        return parse_arxiv_xml(response.content, keyword, tz_offset_hours)

    except requests.exceptions.ConnectTimeout as e:
        print(f"     ⚠ HTTP API connect timeout: {e}")
        return []
    except requests.exceptions.ReadTimeout as e:
        print(f"     ⚠ HTTP API read timeout: {e}")
        return []
    except requests.exceptions.Timeout as e:
        print(f"     ⚠ HTTP API timeout: {e}")
        return []
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", None)
        print(f"     ⚠ HTTP API HTTPError (status={status}): {e}")
        return []
    except Exception as e:
        print(f"     ⚠ HTTP API error ({type(e).__name__}): {e}")
        return []


def parse_arxiv_xml(xml_content: bytes, keyword: str, tz_offset_hours: int) -> list[dict]:
    """Parse arXiv Atom XML response."""

    root = ET.fromstring(xml_content)
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

    papers = []
    local_tz = timezone(timedelta(hours=tz_offset_hours))

    for entry in root.findall("atom:entry", ns):
        title_elem = entry.find("atom:title", ns)
        summary_elem = entry.find("atom:summary", ns)
        id_elem = entry.find("atom:id", ns)
        published_elem = entry.find("atom:published", ns)

        if title_elem is None or id_elem is None or not id_elem.text:
            continue

        arxiv_id = id_elem.text.strip().split("/abs/")[-1]

        published_local_str = "unknown"
        if published_elem is not None and published_elem.text:
            try:
                pub_str = published_elem.text.strip()
                if pub_str.endswith("Z"):
                    pub_str = pub_str[:-1] + "+00:00"
                published_dt = datetime.fromisoformat(pub_str)
                published_local = published_dt.astimezone(local_tz)
                published_local_str = published_local.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass

        papers.append(
            {
                "title": title_elem.text.strip().replace("\n", " ") if title_elem.text else "No title",
                "abstract": summary_elem.text.strip().replace("\n", " ")
                if summary_elem is not None and summary_elem.text
                else "",
                "arxiv_id": arxiv_id,
                "alphaxiv_url": f"https://alphaxiv.org/overview/{arxiv_id}",
                "published_local": published_local_str,
                "matched_keyword": keyword,
            }
        )

    return papers


# ==========================================================================
# Main Entry Point with Auto-Fallback
# ==========================================================================


def fetch_papers_for_group(
    keywords: list[str],
    tz_offset_hours: int = 8,
    max_per_keyword: int = 50,
    api_mode: str = "auto",  # "auto" | "arxiv_only" | "http_only"
) -> list[dict]:
    """Fetch papers for a research group with automatic fallback."""

    start_utc, end_utc = get_yesterday_range_utc(tz_offset_hours)
    seen_ids: set[str] = set()
    papers: list[dict] = []

    for keyword in keywords:
        print(f"  → Querying '{keyword}'...")

        keyword_papers: Optional[list[dict]] = None

        if api_mode == "http_only":
            print("     [Mode: HTTP API only]")
            keyword_papers = fetch_with_http_api(
                keyword, start_utc, end_utc, tz_offset_hours, max_per_keyword
            )

        elif api_mode == "arxiv_only":
            print("     [Mode: arxiv library only]")
            keyword_papers = fetch_with_arxiv_library(
                keyword, start_utc, end_utc, tz_offset_hours, max_per_keyword
            )
            if keyword_papers is None:
                keyword_papers = []

        else:
            print("     [Mode: auto - trying arxiv library first]")
            keyword_papers = fetch_with_arxiv_library(
                keyword,
                start_utc,
                end_utc,
                tz_offset_hours,
                max_per_keyword,
                timeout_seconds=15,
            )

            if keyword_papers is None or len(keyword_papers) == 0:
                print("     [Fallback: switching to HTTP API]")
                keyword_papers = fetch_with_http_api(
                    keyword, start_utc, end_utc, tz_offset_hours, max_per_keyword
                )

        if keyword_papers:
            for paper in keyword_papers:
                if paper["arxiv_id"] not in seen_ids:
                    seen_ids.add(paper["arxiv_id"])
                    papers.append(paper)
            print(f"     ✓ Found {len(keyword_papers)} papers for '{keyword}'")
        else:
            print(f"     ✗ No papers found for '{keyword}'")

        time.sleep(3)

    return papers
