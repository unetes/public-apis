#!/usr/bin/env python3
"""Script to validate links in the README.md file.

This script checks all URLs found in the README.md to ensure they are
accessible and return valid HTTP status codes.
"""

import re
import sys
import time
import argparse
from typing import List, Tuple

import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

# Timeout for each HTTP request in seconds
REQUEST_TIMEOUT = 10

# Delay between requests to avoid rate limiting
REQUEST_DELAY = 0.5

# HTTP status codes considered as valid
VALID_STATUS_CODES = {200, 201, 301, 302, 307, 308}

# User-Agent header to avoid being blocked by some servers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; public-apis-validator/1.0; "
        "+https://github.com/public-apis/public-apis)"
    )
}


def extract_urls(filepath: str) -> List[str]:
    """Extract all URLs from a markdown file.

    Args:
        filepath: Path to the markdown file.

    Returns:
        A list of unique URLs found in the file.
    """
    url_pattern = re.compile(
        r'https?://[^\s\)\]\"]+',
        re.IGNORECASE
    )

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    urls = url_pattern.findall(content)
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        # Strip trailing punctuation that may have been captured
        url = url.rstrip(".,;:!?")
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def check_url(url: str) -> Tuple[str, int | None, str]:
    """Check if a URL is accessible.

    Args:
        url: The URL to check.

    Returns:
        A tuple of (url, status_code, message).
        status_code is None if the request failed entirely.
    """
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS,
            allow_redirects=True
        )
        status_code = response.status_code
        if status_code in VALID_STATUS_CODES:
            return (url, status_code, "OK")
        else:
            return (url, status_code, f"Unexpected status code: {status_code}")
    except Timeout:
        return (url, None, "Request timed out")
    except ConnectionError:
        return (url, None, "Connection error")
    except TooManyRedirects:
        return (url, None, "Too many redirects")
    except Exception as e:
        return (url, None, f"Unexpected error: {str(e)}")


def validate_links(filepath: str, verbose: bool = False) -> bool:
    """Validate all links in the given markdown file.

    Args:
        filepath: Path to the markdown file.
        verbose: If True, print status for every URL checked.

    Returns:
        True if all links are valid, False otherwise.
    """
    urls = extract_urls(filepath)
    print(f"Found {len(urls)} unique URLs in '{filepath}'.\n")

    failed_urls = []

    for i, url in enumerate(urls, start=1):
        result_url, status_code, message = check_url(url)

        if status_code not in VALID_STATUS_CODES:
            failed_urls.append((result_url, status_code, message))
            print(f"[FAIL] ({i}/{len(urls)}) {result_url} — {message}")
        elif verbose:
            print(f"[ OK ] ({i}/{len(urls)}) {result_url} — {status_code}")

        time.sleep(REQUEST_DELAY)

    print(f"\nValidation complete: {len(failed_urls)} failed out of {len(urls)} URLs.")

    if failed_urls:
        print("\nFailed URLs:")
        for url, code, msg in failed_urls:
            print(f"  - {url} [{code}] {msg}")
        return False

    return True


def main():
    """Entry point for the link validation script."""
    parser = argparse.ArgumentParser(
        description="Validate all URLs in a markdown file."
    )
    parser.add_argument(
        "filepath",
        nargs="?",
        default="README.md",
        help="Path to the markdown file (default: README.md)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print status for every URL checked"
    )
    args = parser.parse_args()

    success = validate_links(args.filepath, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
