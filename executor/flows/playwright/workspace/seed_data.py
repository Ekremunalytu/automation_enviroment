"""Aggregated seed data for the Playwright workspace fixtures."""

from .seed_project_1 import WORKSPACE_FILES as WORKSPACE_FILES_PART_1
from .seed_project_2 import WORKSPACE_FILES as WORKSPACE_FILES_PART_2
from .seed_project_3 import WORKSPACE_FILES as WORKSPACE_FILES_PART_3

LANGUAGE_EXTENSIONS = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "java": ".java",
    "rust": ".rs",
    "go": ".go",
    "c": ".c",
    "cpp": ".cpp",
    "csharp": ".cs",
    "html": ".html",
    "css": ".css",
    "json": ".json",
    "markdown": ".md",
    "yaml": ".yaml",
    "xml": ".xml",
    "ruby": ".rb",
    "php": ".php",
    "swift": ".swift",
    "kotlin": ".kt",
    "shellscript": ".sh",
}

WORKSPACE_FILES = {
    **WORKSPACE_FILES_PART_1,
    **WORKSPACE_FILES_PART_2,
    **WORKSPACE_FILES_PART_3,
}
