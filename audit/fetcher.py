import time
import requests
from typing import Optional

from config import DEFAULT_TIMEOUT, DEFAULT_USER_AGENT, DEFAULT_MAX_RETRIES

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": DEFAULT_USER_AGENT})


def fetch_page(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """
    Downloads a single page.
    Returns a dict with: url, final_url, status_code, html, content_type, error, response_time_ms.
    Never raises — errors are captured in the 'error' key.
    'html' is None if fetch failed or response is not HTML.
    """
    result = {
        "url": url,
        "final_url": url,
        "status_code": None,
        "html": None,
        "content_type": None,
        "error": None,
        "response_time_ms": None,
    }

    for attempt in range(1, DEFAULT_MAX_RETRIES + 1):
        try:
            start = time.monotonic()
            resp = SESSION.get(url, timeout=timeout, allow_redirects=True)
                elapsed = int((time.monotonic() - start) * 1000)

            result["final_url"] = resp.url
            result["status_code"] = resp.status_code
            result["response_time_ms"] = elapsed

            content_type = resp.headers.get("Content-Type", "")
            result["content_type"] = content_type

            if resp.status_code == 200:
                # Only parse text/html responses — skip PDFs, binaries, feeds, etc.
                if "text/html" not in content_type.lower():
                    result["error"] = f"Non-HTML content-type: {content_type}"
                    return result

                result["html"] = resp.text
                result["error"] = None
                return result
            else:
                result["error"] = f"HTTP {resp.status_code}"
                # Don't retry 4xx — it's a permanent client error
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


def fetch_pages(urls: list[str], delay_seconds: float = 0.0) -> list[dict]:
    """
    Sequentially fetches multiple URLs.
    A failure on one URL does not stop the rest.
    """
    results = []
    for i, url in enumerate(urls):
        result = fetch_page(url)
        results.append(result)

        if delay_seconds > 0 and i < len(urls) - 1:
            time.sleep(delay_seconds)

    return results
