"""HTTP helpers for the Streamlit UI."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse, urlunparse

import requests
import streamlit as st
from config import (
    API_ACTIVATIONS_URL,
    API_MARKETPLACE_ANALYZE_START_URL,
    API_MARKETPLACE_ANALYZE_URL,
    API_MARKETPLACE_DOWNLOAD_URL,
    API_MARKETPLACE_SEARCH_URL,
)


def _build_url_with_host(url: str, host: str) -> str:
    parsed = urlparse(url)
    netloc = host
    if parsed.port is not None:
        netloc = f"{host}:{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


def _candidate_urls(url: str) -> list[str]:
    parsed = urlparse(url)
    if parsed.hostname is None:
        return [url]

    candidates = [url]
    fallback_hosts = {
        "api": ["localhost", "127.0.0.1", "host.docker.internal"],
        "localhost": ["127.0.0.1"],
    }
    for host in fallback_hosts.get(parsed.hostname, []):
        candidates.append(_build_url_with_host(url, host))

    return candidates


def _request_json(
    method: str,
    url: str,
    *,
    timeout: int,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> Any:
    last_error: requests.RequestException | None = None

    for candidate_url in _candidate_urls(url):
        try:
            response = requests.request(
                method,
                candidate_url,
                params=params,
                json=json,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_error = exc
            continue
        except requests.HTTPError:
            raise

    if last_error is not None:
        raise last_error

    raise requests.RequestException(f"API request failed for {url}")


@st.cache_data(ttl=2)
def _fetch_report_list_cached() -> list[dict[str, Any]]:
    return _request_json("GET", API_ACTIVATIONS_URL, timeout=2)


def fetch_report_list() -> tuple[list[dict[str, Any]], str | None]:
    try:
        return _fetch_report_list_cached(), None
    except requests.RequestException as exc:
        return [], f"Report list unavailable: {exc}"


@st.cache_data(ttl=2)
def _fetch_report_cached(filename: str) -> dict[str, Any]:
    url = (
        f"{API_ACTIVATIONS_URL}/latest"
        if filename == "latest"
        else f"{API_ACTIVATIONS_URL}/{filename}"
    )
    return _request_json("GET", url, timeout=5)


def is_valid_activation_report(data: dict[str, Any]) -> bool:
    return (
        isinstance(data, dict)
        and isinstance(data.get("summary"), dict)
        and isinstance(data.get("activated"), list)
    )


def fetch_report(filename: str) -> tuple[dict[str, Any], str | None]:
    try:
        payload = _fetch_report_cached(filename)
    except requests.RequestException as exc:
        return {}, f"Error loading report: {exc}"

    if not is_valid_activation_report(payload):
        return {}, "Selected file is not a valid activation report."

    return payload, None


def search_marketplace(query: str) -> tuple[list[dict[str, Any]], str | None]:
    try:
        payload = _request_json(
            "GET",
            API_MARKETPLACE_SEARCH_URL,
            params={"query": query},
            timeout=15,
        )
        return payload, None
    except requests.RequestException as exc:
        return [], f"Search error: {exc}"


def download_extension(
    publisher: str,
    name: str,
    version: str,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = _request_json(
            "POST",
            API_MARKETPLACE_DOWNLOAD_URL,
            json={"publisher": publisher, "name": name, "version": version},
            timeout=180,
        )
        return payload, None
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 409:
            return {"status": "already_exists"}, None
        return None, f"Download error: {exc}"
    except requests.RequestException as exc:
        return None, f"Download error: {exc}"


def start_analysis_job(
    publisher: str,
    name: str,
    version: str,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = _request_json(
            "POST",
            API_MARKETPLACE_ANALYZE_START_URL,
            json={"publisher": publisher, "name": name, "version": version},
            timeout=30,
        )
        return payload, None
    except requests.RequestException as exc:
        return None, f"Analysis start error: {exc}"


def fetch_analysis_job(job_id: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = _request_json(
            "GET",
            f"{API_MARKETPLACE_ANALYZE_URL}/{job_id}",
            timeout=5,
        )
        return payload, None
    except requests.RequestException as exc:
        return None, f"Analysis status error: {exc}"
