"""Week 5 detection contract namespace.

Detection rules will live behind framework-agnostic contracts in this package.
Runtime layers may depend on exported DTOs, but the detection package must not
import from appcore, workflows, executor, or ui.
"""

__all__: list[str] = []
