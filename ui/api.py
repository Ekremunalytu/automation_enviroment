"""HTTP helpers for the Streamlit UI."""

from __future__ import annotations

from typing import Any

import requests
import streamlit as st
from config import (
    API_ACTIVATIONS_URL,
    API_MARKETPLACE_ANALYZE_START_URL,
    API_MARKETPLACE_ANALYZE_URL,
    API_MARKETPLACE_DOWNLOAD_URL,
    API_MARKETPLACE_SEARCH_URL,
)


@st.cache_data(ttl=2)
def _fetch_report_list_cached() -> list[dict[str, Any]]:
    response = requests.get(API_ACTIVATIONS_URL, timeout=2)
    response.raise_for_status()
    return response.json()


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
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()


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
        response = requests.get(
            API_MARKETPLACE_SEARCH_URL,
            params={"query": query},
            timeout=15,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return [], f"Search error: {exc}"


def download_extension(
    publisher: str,
    name: str,
    version: str,
) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = requests.post(
            API_MARKETPLACE_DOWNLOAD_URL,
            json={"publisher": publisher, "name": name, "version": version},
            timeout=180,
        )
        response.raise_for_status()
        return response.json(), None
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
        response = requests.post(
            API_MARKETPLACE_ANALYZE_START_URL,
            json={"publisher": publisher, "name": name, "version": version},
            timeout=30,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, f"Analysis start error: {exc}"


def fetch_analysis_job(job_id: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        response = requests.get(f"{API_MARKETPLACE_ANALYZE_URL}/{job_id}", timeout=5)
        response.raise_for_status()
        return response.json(), None
    except requests.RequestException as exc:
        return None, f"Analysis status error: {exc}"
