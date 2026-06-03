"""Reports-screen bundle schema (activation + detection + optional static).

``GET /api/activations/{name}/bundle`` returns the dynamic ``AnalysisBundle``
(activation report + live detection report). When the analyzed extension also
went through the static pre-check stage (ES-0..ES-5, ADR 0016), a sibling
``static_report_{job_id}.json`` (a ``CombinedAnalysisBundle``) was persisted
next to the activation report; the route folds its ``StaticAnalysisReport`` in
here so the Reports UI can render static + dynamic rule activation together.

``static_report`` is ``None`` for direct executor runs / fixtures that never ran
the static gate — an additive, optional field, so existing ``AnalysisBundle``
consumers are unaffected.
"""

from __future__ import annotations

from appcore.contracts.schema_defs.analysis_bundle import AnalysisBundle
from appcore.contracts.schema_defs.static_analysis_bundle import StaticAnalysisReport


class ReportBundle(AnalysisBundle):
    static_report: StaticAnalysisReport | None = None


__all__ = ["ReportBundle"]
