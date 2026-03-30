import time
import threading
import concurrent.futures
import requests
from typing import Optional, Callable

from config import (
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_WORKERS,
)

# Thread-local sessions — requests.Session is not thread-safe for concurrent use.
_thread_local = threading.local()


def _get_session() -> requests.Session:
    """Returns a per-thread Session (created on first access per thread)."""
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        _thread_local.session = session
    return _thread_local.session


def fetch_page(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    use_playwright: bool = False,
) -> dict:
    """
    Downloads a single page.
    Returns a dict with: url, final_url, status_code, html, content_type, error, response_time_ms.
    Never raises — errors are captured in the 'error' key.
    'html' is None if fetch failed or response is not HTML.
    """
    if use_playwright:
        return _fetch_page_playwright(url, timeout)

    result = {
        "url": url,
        "final_url": url,
        "status_code": None,
        "html": None,
        "content_type": None,
        "error": None,
        "response_time_ms": None,
    }

    session = _get_session()

    for attempt in range(1, DEFAULT_MAX_RETRIES + 1):
        try:
            start = time.monotonic()
            resp = session.get(url, timeout=timeout, allow_redirects=True)
            elapsed = int((time.monotonic() - start) * 1000)

            result["final_url"] = resp.url
            result["status_code"] = resp.status_code
            result["response_time_ms"] = elapsed

            content_type = resp.headers.get("Content-Type", "")
            result["content_type"] = content_type

            if resp.status_code == 200:
                if "text/html" not in content_type.lower():
                    result["error"] = f"Non-HTML content-type: {content_type}"
                    return result
                result["html"] = resp.text
                result["error"] = None
                return result

            elif resp.status_code == 429:
                # Rate limited — exponential backoff, longer than normal
                result["error"] = "HTTP 429 (rate limited)"
                if attempt < DEFAULT_MAX_RETRIES:
                    time.sleep(2 ** attempt * 3)
                continue

            else:
                result["error"] = f"HTTP {resp.status_code}"
                # Don't retry 4xx — permanent client error
                if 400 <= resp.status_code < 500:
                    return result

        except requests.exceptions.Timeout:
            result["error"] = "Timeout"
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"ConnectionError: {e}"
        except Exception as e:
            result["error"] = f"UnexpectedError: {e}"

        if attempt < DEFAULT_MAX_RETRIES:
            time.sleep(1.5 * attempt)

    return result


def _fetch_page_playwright(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    Fetches a page using Playwright so JS-rendered content is fully evaluated.
    Falls back gracefully if playwright is not installed.
    """
    result = {
        "url": url,
        "final_url": url,
        "status_code": None,
        "html": None,
        "content_type": "text/html",
        "error": None,
        "response_time_ms": None,
    }
    try:
        from playwright.sync_api import sync_playwright  # noqa: PLC0415

        start = time.monotonic()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": DEFAULT_USER_AGENT})
            response = page.goto(
                url,
                timeout=timeout * 1000,
                wait_until="networkidle",
            )
            elapsed = int((time.monotonic() - start) * 1000)
            result["final_url"] = page.url
            result["response_time_ms"] = elapsed

            if response:
                result["status_code"] = response.status
                if response.status == 200:
                    result["html"] = page.content()
                else:
                    result["error"] = f"HTTP {response.status}"
            else:
                result["error"] = "No response"

            browser.close()

    except ImportError:
        result["error"] = (
            "Playwright not installed. "
            "Run: pip install playwright && playwright install chromium"
        )
    except Exception as e:
        result["error"] = f"PlaywrightError: {e}"

    return result


def fetch_pages(
    urls: list[str],
    delay_seconds: float = 0.0,
    max_workers: int = DEFAULT_MAX_WORKERS,
    use_playwright: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[dict]:
    """
    Fetches multiple URLs using a thread pool (concurrent).

    Strategy: process URLs in batches of `max_workers`.  Within each batch
    all requests run in parallel; between batches we sleep `delay_seconds`.
    This gives roughly `max_workers`x speedup while still honouring a
    politeness delay between bursts.

    Playwright mode falls back to sequential because the sync API is not
    thread-safe across pages.

    Args:
        urls: List of URLs to fetch.
        delay_seconds: Pause between batches (or between URLs in sequential mode).
        max_workers: Number of parallel threads.
        use_playwright: Use Playwright for JS-rendered pages (forces sequential).
        progress_callback: Called after each completed URL with (done, total).
    """
    total = len(urls)

    # Sequential path — Playwright or explicit single-worker
    if use_playwright or max_workers <= 1:
        results = []
        for i, url in enumerate(urls):
            result = fetch_page(url, use_playwright=use_playwright)
            results.append(result)
            if progress_callback:
                progress_callback(i + 1, total)
            if delay_seconds > 0 and i < total - 1:
                time.sleep(delay_seconds)
        return results

    # Concurrent path
    results: list[Optional[dict]] = [None] * total
    completed_lock = threading.Lock()
    completed_count = [0]

    def _fetch_one(index: int, url: str) -> None:
        result = fetch_page(url)
        results[index] = result
        with completed_lock:
            completed_count[0] += 1
            done = completed_count[0]
        if progress_callback:
            progress_callback(done, total)

    batch_size = max_workers
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = [(i, urls[i]) for i in range(batch_start, batch_end)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as executor:
            futures = [executor.submit(_fetch_one, i, url) for i, url in batch]
            concurrent.futures.wait(futures)

        if delay_seconds > 0 and batch_end < total:
            time.sleep(delay_seconds)

    return results  # type: ignore[return-value]
