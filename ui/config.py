"""Shared UI configuration."""

from __future__ import annotations

import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
API_ACTIVATIONS_URL = f"{API_BASE_URL}/api/activations"
API_MARKETPLACE_SEARCH_URL = f"{API_BASE_URL}/api/marketplace/search"
API_MARKETPLACE_DOWNLOAD_URL = f"{API_BASE_URL}/api/marketplace/download"
API_MARKETPLACE_ANALYZE_URL = f"{API_BASE_URL}/api/marketplace/analyze"
API_MARKETPLACE_ANALYZE_START_URL = f"{API_MARKETPLACE_ANALYZE_URL}/start"

DEFAULT_CHART_THEME = "plasma"
NAVIGATION_PAGES = ["Dashboard", "Simulation", "Marketplace", "Theme"]
THEME_OPTIONS = ["turbo", "plasma", "inferno", "magma"]
