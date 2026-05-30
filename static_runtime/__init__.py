"""Hardened static-analysis container runtime (ES-2, ADR 0016).

This is a **top-level** package (deliberately NOT under
``packages.analysis_engine``) so importing it does not pull the dynamic
detection engine into the minimal hardened ``automation_static_analyzer``
image: ``packages/analysis_engine/__init__.py`` eagerly imports
``run_detection`` and its whole closure. The stub here needs only
``packages.analysis_contracts.static_detection`` (pydantic-only, no back-edge
into ``analysis_engine``), keeping the container's import + dependency surface
minimal per ADR 0016 §Decision 2 / ADR 0013. See
``documents/active-work/static-analysis-pre-check-stream.md`` §ES-2.
"""
