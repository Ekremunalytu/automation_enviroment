"""
Container-side trigger payload loading.

Reads the JSON trigger file written by the host-side ``scanner.triggers``
module and returns a ``TriggerPayload`` so the entrypoint can select
scenarios and run extra activation triggers.
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from packages.analysis_contracts import TriggerPayload

if TYPE_CHECKING:
    from packages.analysis_contracts import TriggerPayload as TriggerPayloadModel
else:
    TriggerPayloadModel = Any


def load_trigger_file(path: str) -> TriggerPayloadModel | None:
    """Load a trigger payload from a JSON file.

    Args:
        path: Absolute path to the trigger JSON file inside the container.

    Returns:
        A ``TriggerPayload`` if the file exists and is valid, otherwise ``None``.
    """
    p = Path(path)
    if not p.exists():
        return None

    try:
        data = json.loads(p.read_text())
        if not isinstance(data, dict):
            return None
        payload = TriggerPayload.model_validate(data)
    except (json.JSONDecodeError, TypeError, ValidationError):
        return None
    finally:
        # Clean up the trigger file after reading
        with contextlib.suppress(OSError):
            p.unlink()

    return payload
